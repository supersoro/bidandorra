import streamlit as st
from bs4 import BeautifulSoup
import requests
import pandas as pd
import openai
from pdfminer.high_level import extract_text
import re

st.set_page_config(page_title="Subastas Públicas de Andorra", page_icon="🔍")
st.title("🔍 Subastas Públicas de Andorra")
st.markdown("Versión Cloud - Diego Soro & Jefe 🇺🇸")

openai.api_key = st.secrets["OPENAI_API_KEY"]

def analizar_pdf_con_gpt(texto_pdf):
    prompt = f"""
Eres un asistente experto en interpretar documentos legales de subastas públicas en Andorra.

Analiza el siguiente texto extraído de un BOPA (Boletín Oficial del Principado de Andorra) y devuelve exclusivamente un diccionario JSON con los siguientes campos:

1. tipo_bien → Tipo de bien subastado (ej. inmueble, vehículo, mobiliario, etc.)
2. precio_salida → Precio de salida de la subasta en euros. Si no se indica, deja None.
3. fecha_limite → Fecha límite para presentar ofertas o acudir a la subasta. Si no está claro, deja None.
4. cargas_adicionales → Deudas, hipotecas u otras cargas asociadas al bien, si se mencionan.
5. esta_alquilado → True si el documento indica que el bien está alquilado, False si se indica que no lo está, y None si no se especifica.
6. valor_mercado → Valor estimado de mercado, si se menciona.

Texto a analizar:
{texto_pdf}

Devuélvelo como un diccionario JSON válido, sin explicaciones, en este formato exacto:
{{
    "tipo_bien": ..., 
    "precio_salida": ..., 
    "fecha_limite": ..., 
    "cargas_adicionales": ..., 
    "esta_alquilado": ..., 
    "valor_mercado": ...
}}
"""

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    try:
        return eval(response["choices"][0]["message"]["content"])
    except:
        return {}

# URL del portal de subastas
url_base = "https://www.saigandorra.com/ca/subhastes/subhastes.html"
res = requests.get(url_base)
soup = BeautifulSoup(res.text, "html.parser")
bloques = soup.find_all("div", class_="text-box-inner")

datos = []
for bloque in bloques:
    titulo = bloque.find("h4")
    fecha = bloque.find("i", class_="fa-calendar")
    lugar = bloque.find("i", class_="fa-location-arrow")
    enlace_tag = bloque.find("a", class_="btn")
    enlace_detalle = "https://www.saigandorra.com" + enlace_tag["href"] if enlace_tag else None

   info = {
    "Título": titulo.get_text(strip=True) if titulo else None,
    "Fecha y hora": fecha.find_next_sibling(string=True).strip() if fecha else None,
    "Lugar": lugar.find_next_sibling(string=True).strip() if lugar else None,
    "PDF BOPA": None,
    "Enlace a detalle": enlace_detalle,
    "tipo_bien": None,
    "precio_salida": None,
    "fecha_limite": None,
    "cargas_adicionales": None,
    "esta_alquilado": None,
    "valor_mercado": None
}

    if enlace_detalle:
        detalle = requests.get(enlace_detalle).text
        match = re.search(r'https[:=]//www\\.bopa\\.ad/documents/detall\\?doc=[^"&\\s]+', detalle)
        if match:
            url_pdf = match.group(0).replace(":=//", "://")
            info["PDF BOPA"] = url_pdf

            # Extraemos el texto
            try:
                text_pdf = extract_text(requests.get(url_pdf).content)
                resultado = analizar_pdf_con_gpt(text_pdf)
                info.update(resultado)
            except Exception as e:
                st.warning(f"⚠️ Error al procesar PDF: {e}")
        else:
            st.warning(f"❌ No se encontró PDF en: {enlace_detalle}")

    datos.append(info)

df = pd.DataFrame(datos)

orden_columnas = [
    "Título", "tipo_bien", "precio_salida", "valor_mercado",
    "Margen (€)", "fecha_limite", "esta_alquilado", "cargas_adicionales",
    "Fecha y hora", "Lugar", "PDF BOPA", "Enlace a detalle"
]

# Mostrar con columnas ordenadas
st.dataframe(df[[col for col in orden_columnas if col in df.columns]])
st.markdown("🛠️ Próximamente: IA para interpretar subastas y rellenar campos automáticamente.")
