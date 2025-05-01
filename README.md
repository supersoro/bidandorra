# bidandorra
🧠 Subastas Públicas de Andorra · Versión Agentes
Aplicación Streamlit que permite visualizar las subastas públicas en Andorra, organizada por agentes especializados. Este proyecto forma parte del sistema de inteligencia para oportunidades en licitaciones desarrollado por Diego Soro.

📌 Características actuales
✅ Scraper directo del portal saigandorra.com

✅ Extracción del PDF oficial del BOPA (si lo hay)

📄 Visualización tabular interactiva

🚫 No usa Selenium (más ligero, compatible con Streamlit Cloud)

🔜 Pendiente: integración de agentes GPT y fuentes externas de valoración (Idealista, Registro, etc.)

🧩 Estructura por agentes

Agente	Función	Estado
Agente 1	Extrae listado principal de subastas	✅ Implementado
Agente 2	Extrae el enlace del PDF oficial en BOPA	✅ Implementado
Agente 3	Interpreta legalmente el PDF con GPT	🔜 En desarrollo
Agente 4	Compara con precios de mercado	🔜 En desarrollo
Agente 5	Calcula ROI y riesgo estimado	🔜 En diseño
