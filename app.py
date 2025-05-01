import streamlit as st
from bs4 import BeautifulSoup
import requests
import pandas as pd
import re
import openai
import os
import json

st.set_page_config(page_title="Subastas Públicas de Andorra", page_icon="🔍")
st.title("🔍 Subastas Públicas de Andorra")
st.markdown("Versión Agentes - Diego Soro & Jefe 🇺🇸")

openai.api_key = os.getenv("OPENAI_API_KEY")

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

# Agente 2: Extrae enlace al documento completo del BOPA (HTML, no PDF)
def encontrar_url_bopa_html(url_detalle):
    try:
        detalle_html = requests.get(url_detalle).text
        soup = BeautifulSoup(detalle_html, "html.parser")
        enlaces = soup.find_all("a", href=True)
        for a in enlaces:
            href = a["href"]
            if "bopa.ad/Documents/Detall" in href:
                return href if href.startswith("http") else "https://www.bopa.ad" + href
        return None
    except Exception:
        return None

# Agente 3: Extrae texto del HTML del BOPA y lo interpreta con GPT
def analizar_html_con_gpt(url_bopa):
    try:
        res = requests.get(url_bopa)
        soup = BeautifulSoup(res.text, "html.parser")

        for tag in soup(["script", "style"]):
            tag.decompose()

        texto = soup.get_text(separator="\n")
        texto = re.sub(r"\n+", "\n", texto).strip()

        prompt = f"""
Extrae la siguiente información del texto legal que encontrarás más abajo y responde únicamente con un diccionario JSON que contenga exactamente estas 6 claves:
- tipo_bien
- precio_salida
- fecha_limite
- cargas_adicionales
- esta_alquilado
- valor_mercado

No añadas ninguna explicación adicional, solo devuelve un JSON válido.
Texto:
{texto[:8000]}
"""
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        content = response["choices"][0]["message"]["content"]
        return json.loads(content)
    except Exception:
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
