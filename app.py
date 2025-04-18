import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import requests
from urllib.parse import urljoin

def extraer_valor_mercado_desde_pdf(url_pdf):
    try:
        response = requests.get(url_pdf)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(response.content)
            tmp_path = tmp_file.name
        text = extract_text(tmp_path)

        # Debug temporal
        print("=== TEXTO PDF ===")
        print(text[:1000])

        # Extrae valores tipo: (10.500,00.-€)
        match = re.search(r'\(([\d\.,]+)[\.\-€]*\)', text)
        if match:
            valor_str = match.group(1).replace(".", "").replace(",", ".")
            return float(valor_str)
    except Exception as e:
        print(f"Error extrayendo PDF: {e}")
    return None



st.title("🔍 Subastas Públicas de Andorra")
st.markdown("Versión MVP - by Diego Soro & Jefe 🤖")

# Configura Selenium con Chrome for Testing
options = Options()
options.add_argument('--headless')
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.binary_location = "/Users/diegosoro/Downloads/chrome-mac-x64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"

service = Service(executable_path="/usr/local/bin/chromedriver")
driver = webdriver.Chrome(service=service, options=options)

# URL del portal de subastas
driver.get("https://www.saigandorra.com/ca/subhastes/subhastes.html")
time.sleep(2)
soup = BeautifulSoup(driver.page_source, 'html.parser')
driver.quit()

# Buscamos los bloques de subasta
bloques = soup.find_all("div", class_="text-box-inner")

subastas = []
for bloque in bloques:
    titulo = bloque.find("h4")
    fecha = bloque.find("i", class_="fa-calendar")
    lugar = bloque.find("i", class_="fa-location-arrow")
    enlace_tag = bloque.find("a", class_="btn")

    enlace_detalle = urljoin("https://www.saigandorra.com", enlace_tag["href"]) if enlace_tag else None

    # Buscamos el enlace al PDF del BOPA
valor_mercado = None
precio_salida = None
margen = None
url_pdf = None

if enlace_detalle:
    import re

    try:
        detalle_res = requests.get(enlace_detalle)
        detalle_html = detalle_res.text

        # Extraemos el primer enlace al PDF del BOPA
        bopa_match = re.search(r'https[:=]//www\.bopa\.ad/documents/detall\?doc=[\w\d_]+', detalle_html)
        if bopa_match:
            url_pdf = bopa_match.group(0).replace(":=//", "://")  # corregimos la url rota
            st.success(f"📄 PDF encontrado: {url_pdf}")
            
            valor_mercado = extraer_valor_mercado_desde_pdf(url_pdf)
            if valor_mercado:
                precio_salida = round(valor_mercado * 0.9, 2)
                margen = round(valor_mercado - precio_salida, 2)
        else:
            st.warning(f"❌ No se encontró PDF en: {enlace_detalle}")
    except:
        pass


    subastas.append({
        "Título": titulo.get_text(strip=True) if titulo else None,
        "Fecha y hora": fecha.find_next_sibling(text=True).strip() if fecha else None,
        "Lugar": lugar.find_next_sibling(text=True).strip() if lugar else None,
        "Valor de mercado (€)": valor_mercado,
        "Precio de salida (90%)": precio_salida,
        "Margen (€)": margen,
        "PDF BOPA": url_pdf,
        "Enlace a detalle": enlace_detalle
    })


# Convertimos en DataFrame y mostramos
df = pd.DataFrame(subastas)
st.dataframe(df)

st.markdown("🛠️ Próximamente: estimación de valor de mercado, margen potencial, alertas de ocupación y más.")

