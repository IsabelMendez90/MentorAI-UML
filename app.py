import streamlit as st
import os
import subprocess
from openai import OpenAI


# Leer la API Key desde Streamlit Secrets
API_KEY = st.secrets["OPENROUTER_API_KEY"]
API_BASE = "https://openrouter.ai/api/v1"
MODEL_NAME = "deepseek/deepseek-r1:free"
PLANTUML_JAR = "plantuml.jar"  

# Instrucción base del sistema
INSTRUCCIONES_UML = """
Eres un asistente experto en integración de sistemas mecatrónicos experto en UML y SysUML. Un alumno ha descrito un sistema con árbol de funciones, storyboard y una selección técnica mediante la matriz de Pugh.

Tu tarea es generar un diagrama UML en formato PlantUML en español. Usa actores, clases, componentes, actividades o nodos según el tipo solicitado.

Devuelve únicamente el código UML entre @startuml y @enduml.
"""

# Llamada al LLM
def obtener_diagrama_uml(entrada_usuario, tipo_diagrama):
    prompt = f"""
Sistema descrito por el alumno:

Árbol de funciones:
{entrada_usuario['arbol']}

Storyboard:
{entrada_usuario['storyboard']}

Concepto técnico seleccionado:
{entrada_usuario['concepto']}

Tipo de diagrama solicitado: {tipo_diagrama.upper()}

Genera el código UML correspondiente.
"""
    try:
        mensajes = [
            {"role": "system", "content": INSTRUCCIONES_UML},
            {"role": "user", "content": prompt}
        ]
        client = OpenAI(api_key=API_KEY, base_url=API_BASE)
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=mensajes,
            extra_headers={
                "HTTP-Referer": "<YOUR_SITE_URL>",
                "X-Title": "<YOUR_SITE_NAME>"
            }
        )
        if completion and completion.choices:
            return completion.choices[0].message.content
        else:
            return "⚠️ No se recibió una respuesta válida del modelo."
    except Exception as e:
        return f"❌ Error al conectarse con el modelo: {str(e)}"

# Función para guardar y renderizar imagen UML
def generar_imagen_uml(codigo_uml, nombre_archivo):
    uml_file = f"{nombre_archivo}.txt"
    with open(uml_file, "w", encoding="utf-8") as f:
        f.write(codigo_uml)

    try:
        subprocess.run(["java", "-jar", PLANTUML_JAR, uml_file], check=True)
        imagen_generada = f"{nombre_archivo}.png"
        if os.path.exists(imagen_generada):
            return imagen_generada
        else:
            return None
    except subprocess.CalledProcessError as e:
        st.error(f"Error al generar imagen UML: {e}")
        return None

# Configuración de página
st.set_page_config(page_title="Mentor-AI Diagramas UML", layout="wide")

st.title("🤖 Mentor-AI - Generador de Diagramas UML")
st.markdown("Creadores: Dra. J. Isabel Méndez Garduño & M.Sc. Miguel de J. Ramírez C., CMfgT")

st.subheader("Asistente inteligente para visualizar tu sistema")

st.markdown(
    """
    Este asistente utiliza inteligencia artificial para ayudarte a generar diagramas UML a partir de la información clave de tu proyecto.
    
    **Entradas requeridas:**  
    • Árbol de funciones  
    • Storyboard del usuario  
    • Concepto ganador derivado de la matriz de Pugh  
    
    **Diagramas disponibles:**  
    - Casos de Uso  
    - Actividades  
    - Máquina de Estados  
    - Clases  
    - Componentes  
    - Deployment
    
    Completa el formulario y deja que el asistente genere automáticamente el diagrama en formato visual.
    """
)


with st.form("formulario_uml"):
    proyecto = st.text_input("Nombre del proyecto")
    arbol = st.text_area("Árbol de funciones")
    storyboard = st.text_area("Storyboard del usuario")
    concepto = st.text_area("Concepto técnico ganador (matriz de Pugh)")
    tipo_diagrama = st.selectbox("Selecciona el tipo de diagrama UML", [
        "Casos de Uso", "Actividades", "Máquina de Estados",
        "Clases", "Componentes", "Deployment"
    ])
    submitted = st.form_submit_button("Generar Diagrama")

if submitted:
    entrada = {
        "proyecto": proyecto,
        "arbol": arbol,
        "storyboard": storyboard,
        "concepto": concepto
    }
    #st.subheader("📄 Código UML generado:")
    codigo_uml = obtener_diagrama_uml(entrada, tipo_diagrama)
    #st.code(codigo_uml, language='text')

    if "@startuml" in codigo_uml and "@enduml" in codigo_uml:
        st.subheader("🖼️ Imagen del diagrama:")
        nombre_archivo = f"uml_{tipo_diagrama.lower().replace(' ', '_')}"
        imagen_path = generar_imagen_uml(codigo_uml, nombre_archivo)

        if imagen_path:
            st.image(imagen_path, caption=f"Diagrama UML: {tipo_diagrama}", use_container_width=True)
            with open(imagen_path, "rb") as f:
                st.download_button("📥 Descargar imagen", f, file_name=imagen_path, mime="image/png")
        else:
            st.warning("No se pudo generar la imagen del diagrama.")
    else:
        st.warning("El código UML no contiene una estructura válida con @startuml y @enduml.")

