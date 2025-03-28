import moviepy.editor as mp
import numpy as np
import librosa
import cv2
import tempfile
import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from streamlit_extras.metric_cards import style_metric_cards

PARAMETROS_EDAD = {
    '0-3': {'cortes': 2, 'volumen': 60, 'complejidad_visual': 50, 'densidad_sonora': 2, 'icon': '🍼'},
    '4-6': {'cortes': 4, 'volumen': 70, 'complejidad_visual': 100, 'densidad_sonora': 4, 'icon': '🎨'},
    '7-12': {'cortes': 8, 'volumen': 80, 'complejidad_visual': 150, 'densidad_sonora': 6, 'icon': '📚'},
    '13+': {'cortes': float('inf'), 'volumen': 85, 'complejidad_visual': float('inf'), 'densidad_sonora': float('inf'), 'icon': '🎬'}
}

def detectar_cortes_visual(clip, intervalo=1.0, umbral=0.6):
    cambios = 0
    anterior_hist = None
    for t in np.arange(0, clip.duration, intervalo):
        frame = cv2.resize(clip.get_frame(t), (320, 180))
        hist = cv2.calcHist([frame], [0, 1, 2], None, [8,8,8], [0,256]*3)
        hist = cv2.normalize(hist, hist).flatten()
        if anterior_hist is not None:
            diferencia = cv2.compareHist(anterior_hist, hist, cv2.HISTCMP_CORREL)
            if diferencia < umbral:
                cambios += 1
        anterior_hist = hist
    return round(cambios / (clip.duration / 60), 2)

def analizar_volumen_audio(clip):
    with tempfile.NamedTemporaryFile(suffix=".wav") as audio_temp:
        clip.audio.write_audiofile(audio_temp.name, verbose=False, logger=None)
        y, _ = librosa.load(audio_temp.name, sr=22050)
        rms = librosa.feature.rms(y=y)[0]
        volumen_db = librosa.amplitude_to_db(rms, ref=np.max)
        return round(float(np.mean(np.abs(volumen_db))), 2)

def calcular_complejidad_visual(clip, sample_frames=30):
    complejidades = []
    for t in np.linspace(0, clip.duration, sample_frames):
        frame = cv2.resize(clip.get_frame(t), (320, 180))
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 100, 200)
        contornos, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        complejidades.append(len(contornos))
    return round(float(np.mean(complejidades)), 2)

def calcular_densidad_sonora(clip):
    with tempfile.NamedTemporaryFile(suffix=".wav") as audio_temp:
        clip.audio.write_audiofile(audio_temp.name, verbose=False, logger=None)
        y, sr = librosa.load(audio_temp.name, sr=22050)
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        picos = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, units='time', backtrack=True, delta=0.7, wait=2)
        sonidos_filtrados = []
        ultimo_sonido = -np.inf
        for pico in picos:
            if pico - ultimo_sonido >= 1.0:
                sonidos_filtrados.append(pico)
                ultimo_sonido = pico
        duracion_min = clip.duration / 60
        return round(len(sonidos_filtrados) / duracion_min, 2)

def clasificar_intervalo(cortes, volumen, complejidad, densidad_sonora):
    for rango, params in PARAMETROS_EDAD.items():
        if (cortes <= params['cortes'] and volumen <= params['volumen'] and
            complejidad <= params['complejidad_visual'] and densidad_sonora <= params['densidad_sonora']):
            return rango
    return "13+"

def generar_informe(analisis_intervalos):
    conteo = {"0-3": 0, "4-6": 0, "7-12": 0, "13+": 0}
    for intervalo in analisis_intervalos:
        conteo[intervalo['edad']] += 1
    edad_final = max(conteo, key=conteo.get)
    icono = PARAMETROS_EDAD[edad_final]['icon']
    texto = f"{icono} Edad recomendada general: {edad_final}\n\n"
    return edad_final, texto, analisis_intervalos

def mostrar_grafico_y_resumen(intervalos):
    df = pd.DataFrame(intervalos)
    st.markdown("## 📊 Indicadores por intervalo")

    col1, col2 = st.columns([2, 1])
    with col1:
        fig, ax = plt.subplots(figsize=(6, 4))
        x = [f"{int(i['inicio'])}-{int(i['fin'])}" for i in intervalos]
        ax.plot(x, df['cortes'], label="Cortes visuales/min", marker='o')
        ax.plot(x, df['complejidad'], label="Complejidad visual", marker='o')
        ax.plot(x, df['volumen'], label="Volumen promedio (dB)", marker='o')
        ax.plot(x, df['densidad_sonora'], label="Densidad sonora", marker='o')
        ax.set_xlabel("Intervalos (s)")
        ax.set_ylabel("Valor")
        ax.set_title("Evolución de indicadores")
        ax.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig)

    with col2:
        st.markdown("### 📌 Resumen visual de métricas")
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            st.metric("Cortes visuales/min (máx)", f"{df['cortes'].max()}", help="Promedio de cambios de escena por minuto")
            st.metric("Complejidad visual (máx)", f"{df['complejidad'].max()}", help="Número promedio de contornos detectados")
        with col_v2:
            st.metric("Volumen promedio (dB)", f"{df['volumen'].max()}", help="Nivel de intensidad sonora en decibelios")
            st.metric("Densidad sonora (máx)", f"{df['densidad_sonora'].max()}", help="Cantidad de sonidos diferenciados por minuto")
        style_metric_cards()