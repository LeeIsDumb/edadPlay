import streamlit as st
import os
import yt_dlp
from core import analizar_video

st.set_page_config(page_title="EdadPlay", page_icon="🎬", layout="wide")

st.markdown("<h1 style='text-align:center;color:#4B0082;'>🎬 EdadPlay</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align:center;'>Analiza vídeos y obtén una edad recomendada según criterios científicos.</h3>", unsafe_allow_html=True)

# Inicializar estados
if "procesando" not in st.session_state:
    st.session_state["procesando"] = False
if "ruta_video" not in st.session_state:
    st.session_state["ruta_video"] = None

# Mostrar inputs solo si no se está procesando
if not st.session_state["procesando"] and st.session_state["ruta_video"] is None:
    video_file = st.file_uploader("🎞️ Sube un vídeo (máx 200 MB)", type=["mp4", "mov", "avi"])
    video_url = st.text_input("🌐 O pega URL de YouTube o Vimeo:")

    if video_file:
        if video_file.size > 200 * 1024 * 1024:
            st.error("⚠️ El archivo supera el límite de 200 MB.")
        else:
            ruta_video = f"/tmp/{video_file.name}"
            with open(ruta_video, "wb") as f:
                f.write(video_file.getbuffer())
            st.session_state["ruta_video"] = ruta_video

    elif video_url:
        ruta_video = "/tmp/video_descargado.mp4"
        try:
            with st.spinner('Descargando vídeo...'):
                ydl_opts = {
                    'outtmpl': 'video_descargado.mp4',
                    'format': 'mp4[height<=480]',
                    'noplaylist': True,
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([video_url])
            st.session_state["ruta_video"] = ruta_video
            st.success("✅ Vídeo descargado correctamente.")
        except Exception as e:
            st.error(f"⚠️ Error descargando vídeo: {e}")
            st.session_state["ruta_video"] = None

# Botón de analizar vídeo desaparece durante el procesamiento
if st.session_state["ruta_video"] and not st.session_state["procesando"]:
    if st.button("🔍 Analizar vídeo ahora"):
        st.session_state["procesando"] = True
        st.rerun()

# Proceso de análisis con barra de progreso detallada
if st.session_state["procesando"]:
    placeholder = st.empty()
    placeholder.info('Analizando vídeo, por favor espera...')

    edad, reporte = analizar_video(st.session_state["ruta_video"])

    placeholder.success("✅ ¡Análisis finalizado con éxito!")

    st.markdown(f"<h2 style='color:#8B008B;'>Edad recomendada: {edad}</h2>", unsafe_allow_html=True)
    st.markdown("### 📝 Informe detallado:")
    st.info(reporte)

    if os.path.exists(st.session_state["ruta_video"]):
        os.remove(st.session_state["ruta_video"])

    st.session_state["ruta_video"] = None
    st.session_state["procesando"] = False

    if st.button("🔄 Analizar otro vídeo"):
        st.session_state.clear()
        st.rerun()

# Tablas visibles siempre
st.markdown("---")
st.markdown("## 📌 Recomendaciones generales según la edad")
st.table({
    "Edad": ["0–3 años", "4–6 años", "7–12 años", "13+ años"],
    "Cortes/min": ["<2", "2–4", "5–8", "8+"],
    "Complejidad Visual (objetos/frame)": ["<50", "50-100", "100-150", "150+"],
    "Volumen Promedio (dB)": ["<60", "60–70", "70–80", "80–85"],
    "Densidad Sonora (sonidos/min)": ["<2", "2–4", "4–6", "6+"],
    "Tiempo pantalla/día": ["Evitar", "Máx 1 hora", "1-2 horas", "Equilibrado"]
})

st.markdown("---")
st.markdown("## 🛠️ **¿Cómo calculamos los indicadores del vídeo?**")
st.markdown("""
**EdadPlay** utiliza técnicas avanzadas y criterios científicos para analizar vídeos infantiles y determinar claramente la edad mínima recomendada. Estos son los métodos específicos para cada indicador:

### 📌 **1. Cortes visuales (por minuto)**

Contamos cada cambio notable de escena o plano visual:

- Se analiza el vídeo en intervalos cortos (cada segundo).
- Para cada intervalo, se compara el histograma de color del fotograma actual con el anterior usando técnicas robustas de comparación estadística (histogramas normalizados).
- Si la diferencia supera un umbral establecido (0.6), se considera un "corte visual".
- Finalmente, calculamos cuántos de estos cambios suceden por minuto.

### 🎨 **2. Complejidad visual (objetos por escena)**

Medimos el número promedio de elementos visuales (objetos o contornos diferenciados) presentes en cada fotograma analizado:

- Seleccionamos una muestra representativa de fotogramas (aproximadamente 30 por vídeo).
- Cada fotograma es procesado en escala de grises, reduciendo ruido con suavizado Gaussiano y detectando contornos mediante algoritmos (Canny).
- El número promedio de estos contornos en toda la muestra representa claramente la "complejidad visual" del vídeo.

### 🔊 **3. Volumen promedio (dB)**

Medimos el nivel de volumen medio del audio del vídeo:

- Extraemos el audio del vídeo en formato WAV.
- Calculamos la intensidad sonora usando técnicas profesionales (RMS - Valor Cuadrático Medio).
- Transformamos esos valores de intensidad en decibelios (dB).
- Finalmente, calculamos el promedio absoluto del volumen en dB de todo el audio.

### 🎵 **4. Densidad sonora (sonidos nuevos por minuto)**

Evaluamos cuántos sonidos distintos ocurren cada minuto del vídeo, identificando nuevos eventos auditivos claramente diferenciados:

- Extraemos el audio y analizamos cambios notables en la señal sonora usando algoritmos especializados (detección robusta de "onsets" de audio).
- Usamos filtros adicionales para asegurar que solo contamos sonidos realmente diferenciados (al menos 1 segundo entre sonidos para evitar contar múltiples golpes o efectos similares cercanos).
- Calculamos cuántos de estos sonidos aparecen por cada minuto del vídeo, obteniendo la "densidad sonora".

Estos métodos permiten a **EdadPlay** proporcionar recomendaciones claras y basadas en criterios científicos sólidos sobre qué contenido audiovisual es adecuado según la etapa del desarrollo infantil.
""")

st.markdown("""
### 📚 Estudios científicos detallados:
**1\. Organización Mundial de la Salud (OMS, 2019):**
- **Conclusión principal:** Limitar el uso de pantallas en niños menores de 5 años. Nada antes del año, máximo 1 hora diaria de contenido supervisado entre 2 y 4 años.
- **Razón científica:** Mayor tiempo de pantallas tempranas se vincula directamente con retrasos en el desarrollo motor, cognitivo y lingüístico.

**2\. Academia Americana de Pediatría (AAP, 2020):**
- **Conclusión principal:** Evitar pantallas en niños menores de 18 meses excepto videollamadas familiares. Entre 2–5 años, máximo 1 hora diaria de contenido educativo.
- **Razón científica:** Vídeos rápidos y con muchos estímulos visuales o sonoros generan sobreestimulación, perjudicando atención, memoria y autorregulación emocional.

**3\. Estudio de Dimitri Christakis (2011, Pediatrics):**
- **Conclusión principal:** Exposición frecuente a vídeos rápidos en menores de 3 años aumenta significativamente el riesgo de problemas atencionales posteriores.
- **Razón científica:** El ritmo acelerado de estímulos audiovisuales sobrecarga los circuitos neuronales en desarrollo, afectando negativamente la atención sostenida a largo plazo.

**4\. UNICEF (2021):**
- **Conclusión principal:** Los niños necesitan principalmente interacciones reales y contenido pausado si utilizan pantallas.
- **Razón científica:** La exposición excesiva a estímulos rápidos afecta la capacidad de aprendizaje, generando ansiedad y comportamientos impulsivos en menores.

**5\. Canadian Paediatric Society (CPS, 2019):**
- **Conclusión principal:** Menores de 5 años no deben superar 1 hora diaria de contenido audiovisual lento y educativo, siempre supervisado por adultos.
- **Razón científica:** Contenido audiovisual de alta intensidad está claramente vinculado a dificultades académicas, irritabilidad e impulsividad en edades posteriores.

**6\. Estudios sobre estrés y cortisol en niños expuestos a vídeos violentos (Gentile et al., 2017):**
- **Conclusión principal:** Los niños expuestos a contenidos violentos o altamente estimulantes presentan niveles elevados de cortisol, generando estrés crónico y comportamientos agresivos.
- **Razón científica:** Altos niveles de cortisol prolongado están relacionados con trastornos emocionales y problemas de conducta, especialmente en menores de 12 años.

**7\. Sobre el riesgo de adicción digital (OMS, 2018 - reconocimiento trastorno por videojuegos):**
- **Conclusión principal:** Adolescentes expuestos constantemente a estímulos audiovisuales rápidos (videojuegos, redes sociales) tienen un riesgo aumentado de desarrollar adicción digital.
- **Razón científica:** La dopamina generada por contenidos rápidos e intensos puede producir dependencia psicológica y efectos similares a otras adicciones.
""")

st.markdown("""
#### 🔖 Referencias bibliográficas completas:
- **OMS (2019):** Guidelines on Physical Activity, Sedentary Behaviour and Sleep for Children under 5 Years of Age. [Ver estudio](https://apps.who.int/iris/handle/10665/311664)
- **AAP (2020):** Media and Young Minds. Pediatrics, Official AAP Guidelines. [Ver estudio](https://publications.aap.org/pediatrics/article/138/5/e20162591/60321/Media-and-Young-Minds)
- **Christakis DA (2011):** The effects of fast-paced cartoons. Pediatrics, Volume 128. [Ver estudio](https://doi.org/10.1542/peds.2011-2071)
- **UNICEF (2021):** Children in a digital world. [Ver estudio](https://www.unicef.org/reports/state-worlds-children-2017)
- **Canadian Paediatric Society (2019):** Screen time and young children: Promoting health and development in a digital world. [Ver estudio](https://cps.ca/en/documents/position/screen-time-and-young-children)
- **Gentile et al. (2017):** The effects of violent video game habits. JAMA Pediatrics. [Ver estudio](https://jamanetwork.com/journals/jamapediatrics/fullarticle/2612159)
- **OMS (2018):** International Classification of Diseases (ICD-11), Gaming disorder. [Ver estudio](https://www.who.int/news-room/questions-and-answers/item/addictive-behaviours-gaming-disorder)
""")