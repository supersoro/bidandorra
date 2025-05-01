import streamlit as st
from bs4 import BeautifulSoup
import requests
import pandas as pd
import re

st.set_page_config(page_title="Subastas Públicas de Andorra", page_icon="🔍")
st.title("🔍 Subastas Públicas de Andorra")
st.markdown("Versión Agentes - Diego Soro & Jefe 🇺🇸")

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

# Agente 2: Analiza si hay PDF y lo extrae
def encontrar_pdf_en_detalle(url_detalle):
    try:
        detalle_html = requests.get(url_detalle).text
        match = re.search(r'https://www\.bopa\.ad/Documents/Detall\?doc=[\w_]+', detalle_html)
        return match.group(0) if match else None
    except Exception as e:
        return None

# Ejecutar agentes 1 y 2
subastas = obtener_subastas()
for sub in subastas:
    enlace = sub.get("Enlace a detalle")
    sub["PDF BOPA"] = encontrar_pdf_en_detalle(enlace) if enlace else None

# Mostrar resultados en Streamlit
df = pd.DataFrame(subastas)
st.dataframe(df, use_container_width=True)

st.markdown("🧠 Próximamente: Agente de interpretación legal con GPT + Agente de mercado")
# Mostrar resultados en Streamlit
df = pd.DataFrame(subastas)
st.dataframe(df, use_container_width=True)

st.markdown("🧠 Próximamente: Agente de interpretación legal con GPT + Agente de mercado")
