import streamlit as st
from openai import OpenAI
import zlib

# Configuración de página
st.set_page_config(page_title="Mentor-AI Diagramas UML", layout="wide")
st.title("🤖 AI Challenge Mentor - Generador de Diagramas UML")
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
    - Comunicaciones

    
    Completa el formulario y deja que el asistente genere automáticamente el diagrama en formato visual.
    """
)

# Leer la API Key desde Streamlit Secrets
API_KEY = st.secrets["OPENROUTER_API_KEY"]
API_BASE = "https://openrouter.ai/api/v1"
MODEL_NAME = "deepseek/deepseek-r1:free"

# Instrucciones para el sistema (modelo)
INSTRUCCIONES_UML = """
Eres un asistente experto en integración de sistemas mecatrónicos y diseño de software. Un alumno ha descrito un sistema con árbol de funciones, storyboard y una selección técnica mediante la matriz de Pugh.

Tu tarea es generar un diagrama UML en formato PlantUML en español. Usa actores, clases, componentes, actividades, nodos o comunicaciones según el tipo solicitado.

Incluye siempre @startuml al inicio y @enduml al final del código UML. No incluyas explicaciones ni texto adicional.
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
                "HTTP-Referer": "https://mentor-ai-uml.streamlit.app",
                "X-Title": "Mentor-AI UML Generator"
            }
        )
        if completion and completion.choices:
            return completion.choices[0].message.content
        else:
            return "⚠️ No se recibió una respuesta válida del modelo."
    except Exception as e:
        return f"❌ Error al conectarse con el modelo: {str(e)}"

# Codificación PlantUML para la API online
def plantuml_encode(text):
    def deflate_and_encode(string):
        data = zlib.compress(string.encode("utf-8"))
        data = data[2:-4]
        return encode_base64(data)

    def encode_base64(data):
        alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"
        res = ""
        buffer = 0
        bits_left = 0
        for byte in data:
            buffer = (buffer << 8) | byte
            bits_left += 8
            while bits_left >= 6:
                res += alphabet[(buffer >> (bits_left - 6)) & 0x3F]
                bits_left -= 6
        if bits_left > 0:
            res += alphabet[(buffer << (6 - bits_left)) & 0x3F]
        return res

    return deflate_and_encode(text)

# Formulario del usuario
with st.form("formulario_uml"):
    proyecto = st.text_input("Nombre del proyecto")
    arbol = st.text_area("Árbol de funciones")
    storyboard = st.text_area("Storyboard del usuario")
    concepto = st.text_area("Concepto técnico ganador (matriz de Pugh)")
    tipo_diagrama = st.selectbox("Selecciona el tipo de diagrama UML", [
        "Casos de Uso", "Actividades", "Máquina de Estados",
        "Clases", "Componentes", "Deployment", "Comunicaciones"
    ])
    submitted = st.form_submit_button("Generar Diagrama")

if submitted:
    entrada = {
        "proyecto": proyecto,
        "arbol": arbol,
        "storyboard": storyboard,
        "concepto": concepto
    }

    codigo_uml = obtener_diagrama_uml(entrada, tipo_diagrama)

    # Forzar delimitadores si el modelo los omite
    if "@startuml" not in codigo_uml:
        codigo_uml = "@startuml\n" + codigo_uml.strip()

    if "@enduml" not in codigo_uml:
        codigo_uml += "\n@enduml"

    # Verificar si el contenido es válido
    if "@startuml" in codigo_uml and "@enduml" in codigo_uml:
        st.subheader("🖼️ Imagen del diagrama UML generada:")
        uml_url = "https://www.plantuml.com/plantuml/png/" + plantuml_encode(codigo_uml)
        st.image(uml_url, caption=f"Diagrama UML: {tipo_diagrama}", use_container_width=True)

        with st.expander("📄 Ver código UML (opcional)"):
            st.code(codigo_uml, language='text')

        st.markdown(f"[Haz clic aquí para abrir el diagrama en una nueva pestaña]({uml_url})")
    else:
        st.warning("El código UML generado no contiene una estructura válida con @startuml y @enduml.")
