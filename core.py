import moviepy.editor as mp
import librosa
import numpy as np
import cv2
import streamlit as st

PARAMETROS_EDAD = {
    '0-3': {'cortes': 2, 'volumen': 60, 'complejidad_visual': 50, 'densidad_sonora': 2},
    '4-6': {'cortes': 4, 'volumen': 70, 'complejidad_visual': 100, 'densidad_sonora': 4},
    '7-12': {'cortes': 8, 'volumen': 80, 'complejidad_visual': 150, 'densidad_sonora': 6},
    '13+': {'cortes': float('inf'), 'volumen': 85, 'complejidad_visual': float('inf'), 'densidad_sonora': float('inf')}
}

@st.cache_data(show_spinner=False)
def analizar_video(ruta_video):
    clip = mp.VideoFileClip(ruta_video)
    cortes = detectar_cortes(clip)
    volumen_promedio = analizar_audio(ruta_video)
    complejidad_visual = calcular_complejidad_visual(ruta_video)
    densidad_sonora = calcular_densidad_sonora(ruta_video)
    edad_recomendada, razones = clasificar_video(cortes, volumen_promedio, complejidad_visual, densidad_sonora)
    informe = generar_informe(cortes, volumen_promedio, complejidad_visual, densidad_sonora, edad_recomendada, razones)
    return edad_recomendada, informe

def detectar_cortes(clip):
    cambios = []
    anterior = None
    for t in np.arange(0, clip.duration, 1):
        frame = clip.get_frame(t).mean()
        if anterior and abs(frame - anterior) > 15:
            cambios.append(t)
        anterior = frame
    return len(cambios) / (clip.duration / 60)

def analizar_audio(ruta_video):
    audio_path = "/tmp/audio_temp.wav"
    clip = mp.VideoFileClip(ruta_video)
    clip.audio.write_audiofile(audio_path, verbose=False, logger=None)
    y, _ = librosa.load(audio_path)
    rms = librosa.feature.rms(y=y)
    return abs(np.mean(librosa.amplitude_to_db(rms, ref=np.max)))

def calcular_complejidad_visual(ruta_video):
    cap = cv2.VideoCapture(ruta_video)
    complejidades = []
    while True:
        ret, frame = cap.read()
        if not ret: break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        contornos, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        complejidades.append(len(contornos))
    cap.release()
    return np.mean(complejidades)

def calcular_densidad_sonora(ruta_video):
    audio_path = "/tmp/audio_temp.wav"
    clip = mp.VideoFileClip(ruta_video)
    clip.audio.write_audiofile(audio_path, verbose=False, logger=None)
    y, sr = librosa.load(audio_path)
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    picos = librosa.util.peak_pick(onset_env, pre_max=3, post_max=3, pre_avg=3, post_avg=5, delta=0.5, wait=5)
    return len(picos) / (clip.duration / 60)

def clasificar_video(cortes, volumen, complejidad, densidad_sonora):
    razones = []
    edad = "0-3"
    for rango, params in PARAMETROS_EDAD.items():
        if (cortes > params['cortes'] or volumen > params['volumen'] or
            complejidad > params['complejidad_visual'] or densidad_sonora > params['densidad_sonora']):
            edad = rango
            razones.clear()
            if cortes > params['cortes']: razones.append(f"Muchos cortes visuales ({cortes:.1f}/min)")
            if volumen > params['volumen']: razones.append(f"Volumen alto ({volumen:.1f} dB)")
            if complejidad > params['complejidad_visual']: razones.append(f"Alta complejidad visual ({complejidad:.1f}/frame)")
            if densidad_sonora > params['densidad_sonora']: razones.append(f"Densidad sonora alta ({densidad_sonora:.1f}/min)")
        else:
            break
    return edad, razones

def generar_informe(cortes, volumen, complejidad, densidad_sonora, edad, razones):
    informe = f"Edad recomendada: {edad}\n"
    informe += "\nRazones:\n" + ("\n".join(razones) if razones else "Adecuado para todas las edades.")
    return informe
