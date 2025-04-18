import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

st.set_page_config(page_title="Subastas Andorra", page_icon="🔍")
st.title("🔍 Subastas Públicas de Andorra")
st.markdown("Versión Cloud - Diego Soro & Jefe 🧰")

# URL del portal de subastas
URL_BASE = "https://www.saigandorra.com"
SUBHASTES_URL = f"{URL_BASE}/ca/subhastes/subhastes.html"

# Obtener HTML estático con requests
res = requests.get(SUBHASTES_URL)
soup = BeautifulSoup(res.text, 'html.parser')

# Parsear bloques de subastas
bloques = soup.find_all("div", class_="text-box-inner")
subastas = []

for bloque in bloques:
    titulo = bloque.find("h4")
    fecha = bloque.find("i", class_="fa-calendar")
    lugar = bloque.find("i", class_="fa-location-arrow")
    enlace_tag = bloque.find("a", class_="btn")
    enlace_detalle = URL_BASE + enlace_tag['href'] if enlace_tag else None

    # Buscar enlace PDF en HTML de detalle (sin Selenium)
    valor_mercado = precio_salida = margen = url_pdf = None

    if enlace_detalle:
        try:
            detalle_res = requests.get(enlace_detalle)
            detalle_html = detalle_res.text

            # Buscar enlace al PDF del BOPA
            bopa_match = re.search(r'https?://www\\.bopa\\.ad/documents/detall\\?doc=[^"&\s]+', detalle_html)
            if bopa_match:
                url_pdf = bopa_match.group(0).replace(":=//", "://")
                st.success(f"📄 PDF encontrado: {url_pdf}")
                # Aquí puedes añadir análisis posterior con IA o lectura PDF en el futuro
            else:
                st.warning(f"❌ No se encontró PDF en: {enlace_detalle}")

        except Exception as e:
            st.error(f"Error cargando detalle: {e}")

    subastas.append({
        "Título": titulo.get_text(strip=True) if titulo else None,
        "Fecha y hora": fecha.find_next_sibling(string=True).strip() if fecha else None,
        "Lugar": lugar.find_next_sibling(string=True).strip() if lugar else None,
        "Valor de mercado (€)": valor_mercado,
        "Precio de salida (90%)": precio_salida,
        "Margen (€)": margen,
        "PDF BOPA": url_pdf,
        "Enlace a detalle": enlace_detalle
    })

# Mostrar tabla
st.dataframe(pd.DataFrame(subastas))

st.markdown("\n🔧 Próximamente: IA para interpretar subastas y rellenar campos automáticamente.")
