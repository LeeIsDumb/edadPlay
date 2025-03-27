import streamlit as st
from urllib.request import urlretrieve
import os
from main import analizar_video

# Configuración inicial
st.set_page_config(page_title="Clasificador de Edad para Vídeos", page_icon="🎬", layout="wide")

# Título y descripción
st.title("🎬 Clasificador Automático de Edad Recomendada para Vídeos")
st.write("""
Analiza vídeos para determinar la edad mínima recomendada según criterios visuales y sonoros.
Sube tu vídeo (máx. 50MB) o proporciona un enlace público para comenzar el análisis.
""")

# Manejo de vídeo subido o URL
video_file = st.file_uploader("Sube un vídeo", type=["mp4", "mov", "avi"])
video_url = st.text_input("O introduce la URL pública del vídeo:")

ruta_video = None

if video_file:
    if video_file.size <= 50 * 1024 * 1024:
        ruta_video = f"uploaded_{video_file.name}"
        with open(ruta_video, "wb") as f:
            f.write(video_file.read())
    else:
        st.error("El archivo excede el tamaño máximo permitido de 50 MB.")
elif video_url:
    try:
        ruta_video = "video_descargado.mp4"
        urlretrieve(video_url, ruta_video)
        st.success("Vídeo descargado correctamente.")
    except:
        st.error("No se pudo descargar el vídeo. Verifica el enlace.")

# Analizar el vídeo al tener una ruta válida
if ruta_video and st.button("Analizar vídeo"):
    with st.spinner('Analizando vídeo, esto puede tardar varios minutos...'):
        edad_recomendada, informe = analizar_video(ruta_video)
    st.success('¡Análisis completado!')

    st.subheader("📌 Edad mínima recomendada:")
    st.markdown(f"### **{edad_recomendada} años**")

    st.subheader("📑 Informe detallado:")
    st.text(informe)

# Información adicional explicativa
st.sidebar.header("📚 Información Adicional")

if st.sidebar.checkbox("Mostrar tablas explicativas"):
    st.sidebar.markdown("""
    ### 🔸 Indicadores - Edad recomendada:
    | Indicador | 0–3 años | 4–6 años | 7–12 años | +13 años |
    |---|---|---|---|---|
    | Cortes/min | <2 | 2-4 | 5-8 | >8 |
    | Complejidad visual | Muy baja | Baja-Mod | Moderada-Alta | Alta |
    | Volumen promedio | <60 dB | 60-70 dB | 70-80 dB | 80-85 dB |
    | Densidad sonora | Muy baja | Moderada | Alta | Muy alta |

    ### 🔸 Comparativa edad – recomendaciones:
    | Edad | Recomendaciones uso pantallas | Posibles efectos negativos |
    |------|-------------------------------|----------------------------|
    | 0-3 | Evitar o mínimamente pantallas; ritmo lento y supervisado | Retrasos lenguaje, atención; irritabilidad |
    | 4-6 | Max 1h/día; contenidos lentos/educativos supervisados | Dificultad atención; impulsividad |
    | 7-12 | Uso equilibrado supervisado; alternar actividades offline | Problemas atención; agresividad; ansiedad |
    | +13 | Autocontrol guiado; contenido adecuado; equilibrado | Estrés, trastornos sueño; riesgo adicción |

    """)

    st.sidebar.markdown("""
    ### 🔸 Estudios científicos de referencia:
    - [OMS Directrices sobre actividad física y pantallas](https://www.who.int/)
    - [AAP Uso medios digitales en niños](https://www.aap.org/)
    - [UNICEF Informe uso pantallas](https://www.unicef.org/)
    """)

# Limpiar archivos temporales tras análisis (opcional para evitar almacenamiento innecesario)
def limpiar_archivos_temporales():
    archivos = ["uploaded_video.mp4", "video_descargado.mp4", "audio_temp.wav"]
    for archivo in archivos:
        if os.path.exists(archivo):
            os.remove(archivo)

limpiar_archivos_temporales()
