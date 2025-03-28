import moviepy.editor as mp
import librosa
import numpy as np
import cv2
import streamlit as st
import tempfile

PARAMETROS_EDAD = {
    '0-3': {'cortes': 2, 'volumen': 60, 'complejidad_visual': 50, 'densidad_sonora': 2},
    '4-6': {'cortes': 4, 'volumen': 70, 'complejidad_visual': 100, 'densidad_sonora': 4},
    '7-12': {'cortes': 8, 'volumen': 80, 'complejidad_visual': 150, 'densidad_sonora': 6},
    '13+': {'cortes': float('inf'), 'volumen': 85, 'complejidad_visual': float('inf'), 'densidad_sonora': float('inf')}
}

def analizar_video(ruta_video):
    clip = mp.VideoFileClip(ruta_video)

    progress_bar = st.progress(0)
    progress_bar.progress(10, "Detectando cortes visuales...")
    cortes = detectar_cortes(clip)

    progress_bar.progress(40, "Analizando volumen de audio...")
    volumen_promedio = analizar_audio(ruta_video)

    progress_bar.progress(60, "Calculando complejidad visual...")
    complejidad_visual = calcular_complejidad_visual(ruta_video)

    progress_bar.progress(80, "Calculando densidad sonora...")
    densidad_sonora = calcular_densidad_sonora(ruta_video)

    edad_recomendada, razones = clasificar_video(cortes, volumen_promedio, complejidad_visual, densidad_sonora)

    progress_bar.progress(100, "Análisis completado")
    progress_bar.empty()

    informe = generar_informe(cortes, volumen_promedio, complejidad_visual, densidad_sonora, edad_recomendada, razones)

    return edad_recomendada, informe

def detectar_cortes(clip, intervalo=1.0, umbral=0.6):
    cambios = 0
    anterior_hist = None
    total_checks = 0
    for t in np.arange(0, clip.duration, intervalo):
        frame = clip.get_frame(t)
        frame = cv2.resize(frame, (320, 180))
        hist = cv2.calcHist([frame], [0, 1, 2], None, [8,8,8], [0,256]*3)
        hist = cv2.normalize(hist, hist).flatten()

        if anterior_hist is not None:
            diferencia = cv2.compareHist(anterior_hist, hist, cv2.HISTCMP_CORREL)
            if diferencia < umbral:
                cambios += 1
        anterior_hist = hist
        total_checks += 1

    cortes_por_minuto = cambios / (clip.duration / 60)
    return round(cortes_por_minuto, 2)

# Optimizado: Análisis de audio usando memoria y cálculo en tiempo real
def analizar_audio(ruta_video):
    with tempfile.NamedTemporaryFile(suffix=".wav") as audio_temp:
        clip = mp.VideoFileClip(ruta_video)
        clip.audio.write_audiofile(audio_temp.name, verbose=False, logger=None)
        y, _ = librosa.load(audio_temp.name, sr=None)
        rms = librosa.feature.rms(y=y)[0]
        volumen_db = librosa.amplitude_to_db(rms, ref=np.max)
        return float(np.mean(np.abs(volumen_db)))

# Optimizado: Complejidad visual promedio (análisis eficiente usando sampling de frames)
def calcular_complejidad_visual(ruta_video, sample_frames=30):
    cap = cv2.VideoCapture(ruta_video)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    step = max(1, total_frames // sample_frames)
    complejidades = []

    for i in range(0, total_frames, step):
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ret, frame = cap.read()
        if not ret:
            continue
        frame = cv2.resize(frame, (320, 180))
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 100, 200)
        contornos, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        complejidades.append(len(contornos))

    cap.release()
    complejidad_media = np.mean(complejidades) if complejidades else 0
    return round(complejidad_media, 2)

# Optimizado: Densidad sonora usando detección eficiente de onsets (librosa optimizado)
def calcular_densidad_sonora(ruta_video):
    with tempfile.NamedTemporaryFile(suffix=".wav") as audio_temp:
        clip = mp.VideoFileClip(ruta_video)
        clip.audio.write_audiofile(audio_temp.name, verbose=False, logger=None)
        
        y, sr = librosa.load(audio_temp.name, sr=22050)

        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        picos = librosa.onset.onset_detect(
            onset_envelope=onset_env,
            sr=sr,
            units='time',
            backtrack=True,
            delta=0.7,
            wait=2
        )

        sonidos_filtrados = []
        ultimo_sonido = -np.inf
        intervalo_minimo = 1.0

        for pico in picos:
            if pico - ultimo_sonido >= intervalo_minimo:
                sonidos_filtrados.append(pico)
                ultimo_sonido = pico

        duracion_min = clip.duration / 60
        densidad = len(sonidos_filtrados) / duracion_min

        return round(densidad, 2)

def clasificar_video(cortes, volumen, complejidad, densidad_sonora):
    razones = []
    for rango, params in PARAMETROS_EDAD.items():
        if (cortes <= params['cortes'] and volumen <= params['volumen'] and
            complejidad <= params['complejidad_visual'] and densidad_sonora <= params['densidad_sonora']):
            edad = rango
            break
        else:
            edad = rango
            razones.clear()
            if cortes > params['cortes']:
                razones.append(f"Muchos cortes visuales ({cortes:.1f}/min)")
            if volumen > params['volumen']:
                razones.append(f"Volumen alto ({volumen:.1f} dB)")
            if complejidad > params['complejidad_visual']:
                razones.append(f"Alta complejidad visual ({complejidad:.1f}/frame)")
            if densidad_sonora > params['densidad_sonora']:
                razones.append(f"Densidad sonora alta ({densidad_sonora:.1f}/min)")

    return edad, razones

def generar_informe(cortes, volumen, complejidad, densidad_sonora, edad, razones):
    informe = f"Edad recomendada: {edad}\n\n"
    informe += f"📌 **Detalles del análisis:**\n"
    informe += f"- Cortes visuales: {cortes:.2f}/min\n"
    informe += f"- Complejidad visual: {complejidad:.2f} objetos/frame\n"
    informe += f"- Volumen promedio: {volumen:.2f} dB\n"
    informe += f"- Densidad sonora: {densidad_sonora:.2f} sonidos/min\n\n"
    
    informe += "**Razones de la clasificación:**\n"
    if razones:
        for razon in razones:
            informe += f"- {razon}\n"
    else:
        informe += "Adecuado para todas las edades.\n"

    return informe

