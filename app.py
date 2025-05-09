import streamlit as st
from bs4 import BeautifulSoup
import requests
import pandas as pd
import re
import os
import json
from openai import OpenAI

st.set_page_config(page_title="Subastas Públicas de Andorra", page_icon="🔍")
st.title("🔍 Subastas Públicas de Andorra")
st.markdown("Versión Agentes - Diego Soro & Jefe 🇺🇸")

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

# Agente 2: Extrae enlace al documento completo del BOPA (HTML)
def encontrar_url_bopa_html(url_detalle):
    try:
        detalle_html = requests.get(url_detalle).text
        soup = BeautifulSoup(detalle_html, "html.parser")
        enlace_bopa = soup.find("a", string=lambda s: s and "BOPA" in s)
        if enlace_bopa and enlace_bopa.has_attr("href"):
            href = enlace_bopa["href"]
            if href.startswith("/Documents/Detall?doc="):
                return f"https://www.bopa.ad{href}"
        return None
    except Exception as e:
        st.error(f"❌ Error al buscar enlace BOPA: {e}")
        return None

# Agente 3: Extrae texto del HTML del BOPA y lo interpreta con GPT
def analizar_html_con_gpt(url_bopa):
    try:
        res = requests.get(url_bopa)
        soup = BeautifulSoup(res.text, "html.parser")

        texto = soup.get_text(separator="\n")
        texto = re.sub(r"\n+", "\n", texto).strip()

        if not texto or len(texto.strip()) < 100:
            raise ValueError("El texto legal obtenido está vacío o incompleto.")

        st.text_area("Texto legal crudo (preview)", texto[:3000], key=f"preview_{hash(url_bopa)}")

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
        st.code(content, language="json")  # Para depuración visual

        if not content.startswith("{") or not content.endswith("}"):
            raise ValueError("La respuesta no es un JSON válido")

        return json.loads(content)
    except Exception as e:
        st.error(f"❌ Error al analizar con GPT: {e}")
        return {
            "tipo_bien": None,
            "precio_salida": None,
            "fecha_limite": None,
            "cargas_adicionales": None,
            "esta_alquilado": None,
            "valor_mercado": None
        }

# Ejecutar agentes 1, 2 y 3
subastas = obtener_subastas()
resultados = []

for sub in subastas:
    enlace = sub.get("Enlace a detalle")
    url_bopa = encontrar_url_bopa_html(enlace) if enlace else None
    sub["URL BOPA"] = url_bopa

    if url_bopa:
        campos = analizar_html_con_gpt(url_bopa)
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
            "fuente_datos": "HTML"
        })
    resultados.append(sub)

# Mostrar resultados en Streamlit
df = pd.DataFrame(resultados)
st.dataframe(df, use_container_width=True)

st.markdown("🧠 Próximamente: Agente de interpretación legal con GPT + Agente de mercado")
