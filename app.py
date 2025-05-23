import streamlit as st
from bs4 import BeautifulSoup
import requests
import pandas as pd
import re
import os
import json
from openai import OpenAI
import fitz  # PyMuPDF

st.set_page_config(page_title="Subastas Públicas de Andorra", page_icon="🔍")
st.title("🔍 Subastas Públicas de Andorra")
st.markdown("Versión Agentes (con PDF) - Diego Soro & Jefe 🇦🇩")

client = OpenAI()
model = os.getenv("OPENAI_MODEL", "gpt-4")

# Agente 1: Scraper del listado principal
def obtener_subastas():
    url = "https://www.saigandorra.com/ca/subhastes/subhastes.html"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    bloques = soup.find_all("div", class_="text-box-inner")

    subastas = []
    for bloque in bloques:
        titulo = bloque.find("h4")
        fecha = bloque.find("i", class_="fa-calendar")
        lugar = bloque.find("i", class_="fa-location-arrow")
        enlace_tag = bloque.find("a", class_="btn")
        enlace_detalle = "https://www.saigandorra.com" + enlace_tag["href"] if enlace_tag else None

        subastas.append({
            "Título": titulo.get_text(strip=True) if titulo else None,
            "Fecha y hora": fecha.find_next_sibling(string=True).strip() if fecha else None,
            "Lugar": lugar.find_next_sibling(string=True).strip() if lugar else None,
            "Enlace a detalle": enlace_detalle
        })
    return subastas

# Agente 2: Encuentra el enlace al PDF del BOPA
def encontrar_url_bopa_pdf(url_detalle):
    try:
        # Paso 1: Entramos en la página de detalle de la subasta
        detalle_html = requests.get(url_detalle).text
        soup = BeautifulSoup(detalle_html, "html.parser")

        # Paso 2: Buscamos el botón que enlaza al contenido del BOPA
        link_bopa = soup.find("a", string=re.compile("BOPA", re.IGNORECASE))
        if not link_bopa:
            return None

        url_bopa = "https://www.bopa.ad" + link_bopa["href"]

        # Paso 3: Entramos a la página del BOPA y buscamos el PDF real
        bopa_html = requests.get(url_bopa).text
        soup_bopa = BeautifulSoup(bopa_html, "html.parser")
        pdf_tag = soup_bopa.find("a", href=re.compile(r"\\.pdf$"))
        if pdf_tag:
            return "https://www.bopa.ad" + pdf_tag["href"]
        return None
    except Exception as e:
        st.error(f"❌ Error al buscar PDF real del BOPA: {e}")
        return None

# Agente 3: Descarga y analiza el contenido del PDF con GPT
def analizar_pdf_con_gpt(url_pdf):
    try:
        response = requests.get(url_pdf)
        with open("temp_bopa.pdf", "wb") as f:
            f.write(response.content)

        with fitz.open("temp_bopa.pdf") as doc:
            texto = "\n".join([page.get_text() for page in doc])

        st.text_area("Texto legal crudo (preview)", texto[:3000], key=f"pdf_preview_{hash(url_pdf)}")

        prompt = f"""
Eres un asistente experto en análisis legal. A continuación tienes el texto completo de una subasta publicada en el Boletín Oficial del Principado de Andorra.

Extrae únicamente la siguiente información y devuelve un **JSON válido**, con exactamente estas 6 claves:
- tipo_bien
- precio_salida
- fecha_limite
- cargas_adicionales
- esta_alquilado
- valor_mercado

No incluyas explicaciones. Solo responde con un JSON puro. Ejemplo de formato:
{{
  "tipo_bien": "Vivienda",
  "precio_salida": "150.000€",
  "fecha_limite": "06-05-2025 16:00",
  "cargas_adicionales": "Sí, deuda con FEDA",
  "esta_alquilado": "No",
  "valor_mercado": "200.000€"
}}

Texto:
{texto[:8000]}
"""
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        content = response.choices[0].message.content.strip()
        st.code(content, language="json")

        if not content.startswith("{") or not content.endswith("}"):
            raise ValueError("La respuesta no es un JSON válido")

        return json.loads(content)
    except Exception as e:
        st.error(f"❌ Error al analizar PDF con GPT: {e}")
        return {
            "tipo_bien": None,
            "precio_salida": None,
            "fecha_limite": None,
            "cargas_adicionales": None,
            "esta_alquilado": None,
            "valor_mercado": None
        }

# Ejecutar agentes
def ejecutar_pipeline():
    subastas = obtener_subastas()
    resultados = []

    for sub in subastas:
        url_detalle = sub.get("Enlace a detalle")
        url_bopa = encontrar_url_bopa_pdf(url_detalle) if url_detalle else None
        sub["PDF BOPA"] = url_bopa

        if url_bopa:
            campos = analizar_pdf_con_gpt(url_bopa)
            sub.update(campos)
            sub["fuente_datos"] = "GPT"
        else:
            sub.update({
                "tipo_bien": None,
                "precio_salida": None,
                "fecha_limite": None,
                "cargas_adicionales": None,
                "esta_alquilado": None,
                "valor_mercado": None,
                "fuente_datos": "Fallo PDF"
            })
        resultados.append(sub)

    return pd.DataFrame(resultados)

# Mostrar en Streamlit
df_resultados = ejecutar_pipeline()
st.dataframe(df_resultados, use_container_width=True)
st.markdown("🧠 Agente de análisis legal vía PDF + GPT. Prototipo funcional.")
