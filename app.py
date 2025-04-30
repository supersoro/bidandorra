import streamlit as st
import openai
from bs4 import BeautifulSoup
import pandas as pd
import requests
import tempfile
from urllib.parse import urljoin
from pdfminer.high_level import extract_text
import re

st.title("🔍 Subastas Públicas de Andorra")
st.markdown("Versión Cloud - Diego Soro & Jefe 🇦🇩")

openai.api_key = st.secrets["openai_api_key"]

def interpretar_subasta_con_ia(texto):
    prompt = f"""
Extrae de forma estructurada la siguiente información del contenido de una subasta (escrito en catalán o español):

1. Tipo de bien
2. Precio de salida (en euros, si aparece)
3. Fecha límite (si aparece)
4. Cargas adicionales (sí/no o breve descripción)
5. Si el bien está alquilado (sí/no o no consta)
6. Precio de mercado estimado (si aparece)

Texto extraído:
"""
{texto[:4000]}
"""

Devuélvelo como diccionario JSON con esas 6 claves exactas.
"""
def analizar_pdf_con_gpt(prompt):
    import openai

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        return eval(response["choices"][0]["message"]["content"])
    except Exception as e:
        print("Error al procesar con GPT:", e)
        return {}

def extraer_info_desde_pdf(url_pdf):
    try:
        response = requests.get(url_pdf)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(response.content)
            tmp_path = tmp_file.name
            texto = extract_text(tmp_path)
        return interpretar_subasta_con_ia(texto)
    except:
        return {}

# Paso 1: Obtener listado de subastas
res = requests.get("https://www.saigandorra.com/ca/subhastes/subhastes.html")
soup = BeautifulSoup(res.text, "html.parser")

bloques = soup.find_all("div", class_="text-box-inner")
subastas = []

for bloque in bloques:
    titulo = bloque.find("h4")
    fecha = bloque.find("i", class_="fa-calendar")
    lugar = bloque.find("i", class_="fa-location-arrow")
    enlace_tag = bloque.find("a", class_="btn")

    enlace_detalle = urljoin("https://www.saigandorra.com", enlace_tag["href"]) if enlace_tag else None

    info = {
        "Título": titulo.get_text(strip=True) if titulo else None,
        "Fecha y hora": fecha.find_next_sibling(string=True).strip() if fecha else None,
        "Lugar": lugar.find_next_sibling(string=True).strip() if lugar else None,
        "Tipo de bien": None,
        "Precio de salida (€)": None,
        "Fecha límite": None,
        "Cargas": None,
        "Alquilado": None,
        "Valor de mercado (€)": None,
        "PDF BOPA": None,
        "Enlace a detalle": enlace_detalle
    }

    if enlace_detalle:
        detalle_html = requests.get(enlace_detalle).text
        bopa_match = re.search(r'https[:=]//www\\.bopa\\.ad/documents/detall\\?doc=[^"&\\s]+', detalle_html)
        if bopa_match:
            url_pdf = bopa_match.group(0).replace(":=//", "://")
            st.success(f"📄 PDF encontrado: {url_pdf}")
            info["PDF BOPA"] = url_pdf
            resultados = extraer_info_desde_pdf(url_pdf)
            for k in resultados:
                if k in info:
                    info[k] = resultados[k]
        else:
            st.warning(f"❌ No se encontró PDF en: {enlace_detalle}")

    subastas.append(info)

st.dataframe(pd.DataFrame(subastas))
st.markdown("🛠️ Próximamente: IA para interpretar subastas y rellenar campos automáticamente.")

# Mostrar tabla
st.dataframe(pd.DataFrame(subastas))

st.markdown("\n🔧 Próximamente: IA para interpretar subastas y rellenar campos automáticamente.")
