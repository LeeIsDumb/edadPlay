import moviepy.editor as mp
import numpy as np
import librosa
import cv2
import tempfile
import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd

PARAMETROS_EDAD = {
    '0-3': {'cortes': 2, 'volumen': 60, 'complejidad_visual': 50, 'densidad_sonora': 2},
    '4-6': {'cortes': 4, 'volumen': 70, 'complejidad_visual': 100, 'densidad_sonora': 4},
    '7-12': {'cortes': 8, 'volumen': 80, 'complejidad_visual': 150, 'densidad_sonora': 6},
    '13+': {'cortes': float('inf'), 'volumen': 85, 'complejidad_visual': float('inf'), 'densidad_sonora': float('inf')}
}

def detectar_cortes(clip, intervalo=1.0, umbral=0.6):
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

def analizar_audio(clip):
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
        intervalo_minimo = 1.0
        for pico in picos:
            if pico - ultimo_sonido >= intervalo_minimo:
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
    conteo_edades = {"0-3":0, "4-6":0, "7-12":0, "13+":0}
    for intervalo in analisis_intervalos:
        conteo_edades[intervalo['edad']] += 1

    edad_recomendada = max(conteo_edades, key=conteo_edades.get)

    informe = f"Edad recomendada general: {edad_recomendada}\n\n"

    return edad_recomendada, informe, analisis_intervalos

def analizar_video(ruta_video, duracion_intervalo=60):
    clip = mp.VideoFileClip(ruta_video)
    resultados_intervalos = []
    intervalos = np.arange(0, clip.duration, duracion_intervalo)
    total = len(intervalos)
    progreso = st.progress(0)

    for idx, inicio in enumerate(intervalos):
        fin = min(inicio + duracion_intervalo, clip.duration)
        subclip = clip.subclip(inicio, fin)

        progreso.progress(10, "Detectando cortes visuales...")
        cortes = detectar_cortes(subclip)
        progreso.progress(40, "Analizando volumen de audio...")
        volumen = analizar_audio(subclip)
        progreso.progress(60, "Calculando complejidad visual...")
        complejidad = calcular_complejidad_visual(subclip)
        progreso.progress(80, "Calculando densidad sonora...")
        densidad = calcular_densidad_sonora(subclip)

        edad = clasificar_intervalo(cortes, volumen, complejidad, densidad)

        resultados_intervalos.append({
            'inicio': inicio,
            'fin': fin,
            'cortes': cortes,
            'volumen': volumen,
            'complejidad': complejidad,
            'densidad_sonora': densidad,
            'edad': edad
        })

        progreso.progress((idx + 1) / total, f"Analizando intervalos ({idx+1}/{total})...")

    progreso.empty()
    return generar_informe(resultados_intervalos)

def mostrar_grafico_y_resumen(intervalos):
    df = pd.DataFrame(intervalos)

    st.markdown("## 📊 Evolución por intervalo")

    fig, ax = plt.subplots(figsize=(10, 6))
    x = [f"{int(i['inicio'])}-{int(i['fin'])}" for i in intervalos]

    ax.plot(x, df['cortes'], label="Cortes/min")
    ax.plot(x, df['complejidad'], label="Complejidad")
    ax.plot(x, df['volumen'], label="Volumen (dB)")
    ax.plot(x, df['densidad_sonora'], label="Densidad sonora")

    ax.axhline(8, color='gray', linestyle='--', linewidth=1, label="Límite edad 7-12")

    ax.set_ylabel("Valor")
    ax.set_xlabel("Intervalos (segundos)")
    ax.set_title("Indicadores audiovisuales por intervalo")
    ax.legend()
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    st.pyplot(fig)

    st.markdown("### 📌 Resumen numérico")

    def resumen_indicador(col, nombre, umbral):
        max_val = df[col].max()
        min_val = df[col].min()
        sobrepasados = (df[col] > umbral).sum()
        st.markdown(f"- **{nombre}**: máx = `{max_val}`, mín = `{min_val}`, sobrepasan umbral `{umbral}`: **{sobrepasados} intervalos**")

    resumen_indicador("cortes", "Cortes visuales", 8)
    resumen_indicador("complejidad", "Complejidad visual", 150)
    resumen_indicador("volumen", "Volumen promedio (dB)", 85)
    resumen_indicador("densidad_sonora", "Densidad sonora", 6)