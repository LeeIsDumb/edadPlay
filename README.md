# 🎬 EdadPlay – Analizador Audiovisual Infantil

**EdadPlay** es una aplicación web interactiva basada en **Streamlit** que analiza automáticamente videos y contenidos audiovisuales para recomendar la edad mínima adecuada según criterios científicos relacionados con la estimulación visual y auditiva.

Está orientada a padres, educadores, creadores de contenido y profesionales del sector audiovisual que buscan evaluar rápidamente si un video es apropiado para niños según su ritmo, complejidad visual y auditiva.

---

## 🚀 Características principales

- **🔍 Análisis automático:**  
  Evalúa videos subidos o enlaces directos de YouTube o Vimeo.

- **📊 Indicadores precisos:**  
  - Cortes visuales por minuto
  - Complejidad visual (cantidad de objetos por escena)
  - Volumen promedio (dB)
  - Densidad sonora (sonidos nuevos por minuto)

- **📝 Informe detallado:**  
  Explicaciones claras sobre la clasificación obtenida con sugerencias de mejora.

- **📖 Basado en evidencia científica:**  
  Fundado en estudios neuropsicológicos, pediátricos y técnicos sobre estimulación infantil.

- **⚙️ Rendimiento optimizado:**  
  Análisis rápido y eficiente mediante métodos avanzados de procesamiento.

---

## 🔧 Tecnologías utilizadas

- Python 3.8+
- Streamlit
- MoviePy
- Librosa
- OpenCV
- NumPy
- YT-DLP (descarga de videos YouTube y Vimeo)

---

## 📥 Instalación local y uso

### **1. Clonar repositorio**
```bash
git clone https://github.com/tuusuario/edadplay.git
cd edadplay
```

2. Crear entorno virtual
```bash
Copy
Edit
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. Instalar dependencias
```bash
Copy
Edit
pip install -r requirements.txt
```

4. Ejecutar aplicación
```bash
Copy
Edit
streamlit run app.py
```

## 📗 Estructura del proyecto

```bash
edadplay
├── app.py              # Aplicación principal Streamlit
├── core.py             # Métodos de análisis audiovisual
├── requirements.txt    # Dependencias Python
├── packages.txt        # Dependencias Linux (Streamlit Cloud)
├── README.md           # Este archivo
└── .gitignore          # Exclusión de archivos no deseados
```
