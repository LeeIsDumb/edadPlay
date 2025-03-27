import moviepy.editor as mp
import librosa
import numpy as np
import cv2

PARAMETROS_EDAD = {
    '0-3': {'cortes': 2, 'volumen': 60, 'complejidad_visual': 50, 'densidad_sonora': 2},
    '4-6': {'cortes': 4, 'volumen': 70, 'complejidad_visual': 100, 'densidad_sonora': 4},
    '7-12': {'cortes': 8, 'volumen': 80, 'complejidad_visual': 150, 'densidad_sonora': 6},
    '13+': {'cortes': float('inf'), 'volumen': 85, 'complejidad_visual': float('inf'), 'densidad_sonora': float('inf')}
}

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
        if anterior is not None and abs(frame - anterior) > 15:
            cambios.append(t)
        anterior = frame
    cortes_por_minuto = len(cambios) / (clip.duration / 60)
    return cortes_por_minuto

def analizar_audio(ruta_video):
    audio_path = "audio_temp.wav"
    clip = mp.VideoFileClip(ruta_video)
    clip.audio.write_audiofile(audio_path, verbose=False, logger=None)

    y, sr = librosa.load(audio_path)
    rms = librosa.feature.rms(y=y)
    volumen_promedio = np.mean(librosa.amplitude_to_db(rms, ref=np.max))
    return abs(volumen_promedio)

def calcular_complejidad_visual(ruta_video):
    cap = cv2.VideoCapture(ruta_video)
    complejidades = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        contornos, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        complejidades.append(len(contornos))

    cap.release()
    return np.mean(complejidades)

def calcular_densidad_sonora(ruta_video):
    audio_path = "audio_temp.wav"
    clip = mp.VideoFileClip(ruta_video)
    clip.audio.write_audiofile(audio_path, verbose=False, logger=None)

    y, sr = librosa.load(audio_path)
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    picos = librosa.util.peak_pick(onset_env, pre_max=3, post_max=3, pre_avg=3, post_avg=5, delta=0.5, wait=5)

    duracion_min = clip.duration / 60
    densidad_promedio = len(picos) / duracion_min
    return densidad_promedio

def clasificar_video(cortes, volumen, complejidad, densidad_sonora):
    razones = []
    edad = "0-3"
    for rango, params in PARAMETROS_EDAD.items():
        if (cortes > params['cortes'] or volumen > params['volumen'] or
            complejidad > params['complejidad_visual'] or densidad_sonora > params['densidad_sonora']):
            edad = rango
            razones = []
            if cortes > params['cortes']:
                razones.append(f"Número alto de cortes visuales ({cortes:.1f} cortes/min)")
            if volumen > params['volumen']:
                razones.append(f"Volumen alto ({volumen:.1f} dB)")
            if complejidad > params['complejidad_visual']:
                razones.append(f"Complejidad visual alta ({complejidad:.1f} objetos/frame)")
            if densidad_sonora > params['densidad_sonora']:
                razones.append(f"Densidad sonora alta ({densidad_sonora:.1f} sonidos/min)")
        else:
            break
    return edad, razones

def generar_informe(cortes, volumen, complejidad, densidad_sonora, edad, razones):
    informe = f"Edad mínima recomendada: {edad}\n"
    informe += "\nRazones para esta clasificación:\n"
    if razones:
        for razon in razones:
            informe += f"- {razon}\n"
    else:
        informe += "El video es adecuado para todas las edades.\n"

    informe += "\nSugerencias para reducir la clasificación por edad:\n"
    if "cortes" in ' '.join(razones):
        informe += "- Reducir el ritmo visual (menos cambios de escena por minuto).\n"
    if "Volumen" in ' '.join(razones):
        informe += "- Disminuir el volumen general del audio.\n"
    if "Complejidad visual" in ' '.join(razones):
        informe += "- Simplificar visualmente las escenas (menos objetos simultáneos).\n"
    if "Densidad sonora" in ' '.join(razones):
        informe += "- Reducir la cantidad de efectos sonoros simultáneos.\n"
    if not razones:
        informe += "- Ninguna acción requerida."

    return informe
