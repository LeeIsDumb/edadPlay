import streamlit as st
import os
import yt_dlp
from core import analizar_video, mostrar_grafico_y_resumen

st.set_page_config(page_title="EdadPlay", page_icon="🎬", layout="wide")

# Estilo visual moderno y responsive
st.markdown("""
<style>
    html, body {
        background-color: #0F0F0F;
        font-family: 'Poppins', sans-serif;
        color: #333333;
    }

    h1, h2, h3, h4 {
        color: #6a4c93;
    }

    .stButton button {
        background-color: #20D86A;
        color: white;
        font-weight: 600;
        border: none;
        border-radius: 10px;
        padding: 10px 20px;
    }

    .stButton button:hover {
        background-color: #00953C;
    }

    @media screen and (max-width: 768px) {
        .block-container {
            padding: 1rem;
        }
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<h1 style='text-align:center;'>🎬 EdadPlay</h1>
<div style='text-align:center; font-size:1.1em; margin-bottom:1em;'>
Analiza vídeos y obtén una recomendación de edad basada en ciencia para tus hijos.
</div>
""", unsafe_allow_html=True)

if "procesando" not in st.session_state:
    st.session_state["procesando"] = False
if "ruta_video" not in st.session_state:
    st.session_state["ruta_video"] = None

if not st.session_state["procesando"] and st.session_state["ruta_video"] is None:
    with st.container():
        st.subheader("🔹 Sube o introduce un vídeo")
        cols = st.columns([1, 1])
        with cols[0]:
            video_file = st.file_uploader("🎞️ Sube un archivo (máx 200MB)", type=["mp4", "mov", "avi"])
        with cols[1]:
            video_url = st.text_input("🌐 O introduce una URL (YouTube/Vimeo):")

        if video_file:
            if video_file.size > 200 * 1024 * 1024:
                st.error("⚠️ El archivo supera los 200 MB.")
            else:
                ruta = f"/tmp/{video_file.name}"
                with open(ruta, "wb") as f:
                    f.write(video_file.getbuffer())
                st.session_state["ruta_video"] = ruta
        elif video_url:
            ruta = "/tmp/video_descargado.mp4"
            try:
                with st.spinner("Descargando vídeo..."):
                    ydl_opts = {
                        'outtmpl': ruta,
                        'format': 'mp4[height<=480]',
                        'noplaylist': True,
                        'quiet': True
                    }
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([video_url])
                st.session_state["ruta_video"] = ruta
                st.success("✅ Vídeo descargado correctamente.")
            except Exception as e:
                st.error(f"❌ Error: {e}")

if st.session_state["ruta_video"] and not st.session_state["procesando"]:
    st.success("🎥 Vídeo listo para analizar.")
    if st.button("🔍 Analizar vídeo ahora"):
        st.session_state["procesando"] = True
        st.rerun()

if st.session_state["procesando"]:
    st.info("Procesando el vídeo, por favor espera...")
    edad, reporte, intervalos = analizar_video(st.session_state["ruta_video"])
    st.success("✅ ¡Análisis finalizado!")

    col1, col2 = st.columns([2, 1])
    with col1:
        mostrar_grafico_y_resumen(intervalos)
    with col2:
        st.markdown(f"<h3 style='color:#6a4c93;'>📌 Edad recomendada: {edad}</h3>", unsafe_allow_html=True)
        st.info(reporte)

    if os.path.exists(st.session_state["ruta_video"]):
        os.remove(st.session_state["ruta_video"])

    st.session_state["ruta_video"] = None
    st.session_state["procesando"] = False

    if st.button("🔁 Analizar otro vídeo"):
        st.session_state.clear()
        st.rerun()

st.markdown("---")
st.subheader("📌 Recomendaciones generales por edad")
st.dataframe({
    "Edad": ["0–3", "4–6", "7–12", "13+"],
    "Cortes visuales/min": ["<2", "2–4", "5–8", "8+"],
    "Complejidad visual": ["<50", "50–100", "100–150", "150+"],
    "Volumen promedio (dB)": ["<60", "60–70", "70–80", "80–85"],
    "Densidad sonora (sonidos/min)": ["<2", "2–4", "4–6", "6+"],
    "Pantalla diaria": ["Evitar", "1h", "1–2h", "Equilibrado"]
}, use_container_width=True)
st.markdown("Se recomienda que los menores de 6 años no estén expuestos a pantallas, dado su impacto en el desarrollo neurológico, emocional y social a esta edad.")

st.markdown("---")
st.subheader("🔬 ¿Cómo analizamos el contenido?")
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### 📌 1. Cortes visuales por minuto
    - Se analiza cada segundo.
    - Se compara el histograma de color entre fotogramas.
    - Si la diferencia supera cierto umbral, se considera un corte visual.
    - Se calcula la media por minuto.
    
    ### 🎨 2. Complejidad visual
    - Se toman muestras representativas.
    - Cada fotograma se procesa con detección de bordes.
    - Se cuenta el número de contornos presentes.
    """)

with col2:
    st.markdown("""
    ### 🔊 3. Volumen promedio (dB)
    - Se extrae el audio y se calcula la energía (RMS).
    - Se convierte a decibelios.
    - Se obtiene un promedio del volumen.
    
    ### 🎵 4. Densidad sonora
    - Se detectan los eventos auditivos diferenciados ("onsets").
    - Se filtran los sonidos muy cercanos.
    - Se calcula cuántos nuevos sonidos ocurren por minuto.
    """)

st.markdown("---")
st.markdown("### 📚 Estudios científicos de referencia")

st.markdown("""
1. **OMS (2019)**: Recomendación de máximo 1h de pantalla diaria para menores de 5 años. [Ver estudio](https://apps.who.int/iris/handle/10665/311664)  
2. **AAP (2020)**: Evitar pantallas antes de los 18 meses. Contenido educativo y limitado entre 2 y 5 años. [Ver estudio](https://publications.aap.org/pediatrics/article/138/5/e20162591/60321/Media-and-Young-Minds)  
3. **Christakis (2011)**: Ritmo rápido de vídeos vinculado con déficit de atención. [Ver estudio](https://doi.org/10.1542/peds.2011-2071)  
4. **UNICEF (2021)**: Requieren contenido pausado y relaciones reales. [Ver estudio](https://www.unicef.org/reports/state-worlds-children-2017)  
5. **CPS (2019)**: Máximo 1h diaria de contenido lento y supervisado. [Ver estudio](https://cps.ca/en/documents/position/screen-time-and-young-children)  
6. **Gentile et al. (2017)**: Vídeos violentos elevan el cortisol infantil. [Ver estudio](https://jamanetwork.com/journals/jamapediatrics/fullarticle/2612159)  
7. **OMS (2018)**: Riesgo de adicción digital por exposición excesiva. [Ver estudio](https://www.who.int/news-room/questions-and-answers/item/addictive-behaviours-gaming-disorder)
""")
