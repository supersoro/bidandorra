from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import pandas as pd
import time

# Configuración
CHROMEDRIVER_PATH = "/usr/local/bin/chromedriver"
CHROME_BINARY_PATH = "/Users/diegosoro/Downloads/chrome-mac-x64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"

service = Service(CHROMEDRIVER_PATH)
options = webdriver.ChromeOptions()
options.binary_location = CHROME_BINARY_PATH
options.add_argument("--headless")
driver = webdriver.Chrome(service=service, options=options)

# Cargar la web
driver.get("https://www.saigandorra.com/ca/subhastes/subhastes.html")
time.sleep(6)

# Encontrar todos los bloques de subasta
bloques = driver.find_elements(By.CLASS_NAME, "text-box")

subastas = []
for bloque in bloques:
    try:
        titulo = bloque.find_element(By.TAG_NAME, "h4").text.strip()
        detalles = bloque.find_elements(By.CLASS_NAME, "blog-post-info")
        fecha = detalles[0].text.strip() if len(detalles) > 0 else ""
        lugar = detalles[1].text.strip() if len(detalles) > 1 else ""
        responsable = detalles[2].text.strip() if len(detalles) > 2 else ""
        link = bloque.find_element(By.TAG_NAME, "a").get_attribute("href")

        subastas.append({
            "Título": titulo,
            "Fecha y hora": fecha,
            "Lugar": lugar,
            "Responsable": responsable,
            "Enlace a detalle": link
        })
    except Exception as e:
        print("Error leyendo bloque:", e)

driver.quit()

# Mostrar resultados
df = pd.DataFrame(subastas)
print(df)

