# TranslatorPro AI
### Traductor de texto y voz con síntesis de audio · Python & Flet · v1.2.1

Aplicación de escritorio con interfaz gráfica frameless y tema oscuro para traducir texto
escrito y voz en tiempo real. Integra reconocimiento de voz, síntesis TTS y traducción
automática vía Google, con cache LRU para optimizar el uso de la API.

<p align="center">
  <a href="https://github.com/PabloSalinasDev/TranslatorProAI/releases/download/v1.0.0/TranslatorProAI-Ver.1.0.0.exe">
    <img src="https://img.shields.io/badge/Descargar-Instalador_Windows-blue?style=for-the-badge&logo=windows" alt="Descargar Instalador">
  </a>
  &nbsp;&nbsp;&nbsp;&nbsp;
  <a href="https://github.com/PabloSalinasDev/TranslatorProAI/issues">
    <img src="https://img.shields.io/badge/Reportar-Error-red?style=for-the-badge&logo=github" alt="Reportar Error">
  </a>
</p>

---

## Capturas de Pantalla

<h3 align="center">Modo Texto</h3>
<p align="center">
  <img src="assets/screenshot_texto.png" width="500" alt="Modo texto"/>
</p>

<h3 align="center">Modo Voz</h3>
<p align="center">
  <img src="assets/screenshot_voz.png" width="500" alt="Modo voz"/>
</p>

---

## Características Principales

- **Traducción de texto** — Detección automática del idioma de origen con caché LRU integrado que evita llamadas repetidas a la API.
- **Traducción por voz** — Grabación simultánea desde micrófono y loopback del sistema (máx. 60 seg.). Al detener, selecciona automáticamente el audio con mayor señal real. Preprocesamiento adaptativo: reducción de ruido y filtro pasa-banda en modo micrófono, normalización en modo loopback.
- **Síntesis de voz (TTS)** — Reproduce la traducción con `gTTS` + `pygame`, con controles de pausar, reanudar y detener. Soporta textos largos mediante división inteligente por puntuación.
- **Monitor de conectividad** — Hilo en segundo plano que verifica la conexión cada 5 segundos y actualiza el indicador WiFi en la barra de título.
- **Interfaz frameless** — Ventana sin bordes (500×655), arrastrable, con modo oscuro y paleta naranja/gris.
- **Arquitectura de Producción (Windows)** — Integración nativa mediante AppUserModelID para gestión correcta en la barra de tareas y manejo dinámico de certificados SSL para garantizar conectividad segura en entornos compilados (.exe).
- **Log de errores** — Registro automático en app.log con gestión de tamaño (máx. 5MB) y rotación de archivos para optimizar el almacenamiento del usuario.

---

## Arquitectura

```
├── config/
│   └── settings.py        # Título, versión, app ID y diccionario de idiomas (10 idiomas)
├── core/
│   ├── traduccion.py      # Motor de traducción (GoogleTranslator + cache LRU + divisor de texto)
│   ├── audio.py           # Motor TTS: gTTS → BytesIO → pygame mixer (estados: playing/paused/stopped)
│   └── voz.py             # Motor STT: soundcard/sounddevice → preprocesamiento → Google Speech API
├── ui/
│   └── vistas.py          # Todos los componentes Flet (layout, botones, dropdowns, estilos)
├── utils.py               # CacheTraduccion (LRU con OrderedDict) + GestorConectividad
├── main.py                # Orquestador: binding de eventos, hilos y lógica de la app
└── requirements.txt
```

---

## Idiomas Soportados

Español · Inglés · Francés · Portugués · Italiano · Alemán · Chino · Japonés · Coreano  
*(Detección automática disponible en modo texto)*

---

## Tecnologías

| Librería | Uso |
|---|---|
| `flet 0.28.3` | Interfaz gráfica de escritorio |
| `deep-translator` | Traducción vía Google Translate |
| `SpeechRecognition` | Transcripción de voz a texto (Google Speech API) |
| `gTTS` | Síntesis de voz (Text-to-Speech) |
| `pygame` | Reproducción y control del mixer de audio |
| `sounddevice` | Captura de audio desde micrófono |
| `soundcard` | Captura de audio del sistema por loopback |
| `noisereduce` + `scipy` | Preprocesamiento y limpieza de audio |
| `certifi` | Manejo de certificados SSL en ejecutables compilados |

---

## Instalación

**Requisitos:** Python 3.10+ · Windows (recomendado) / Linux / macOS  
**Hardware:** Micrófono (modo voz) · Conexión a internet

```bash
# 1. Clonar el repositorio
git clone https://github.com/PabloSalinasDev/translator-pro-ai.git
cd translator-pro-ai

# 2. Crear entorno virtual (recomendado)
python -m venv .venv
source .venv/bin/activate      # Linux/Mac
venv\Scripts\activate         # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar
python main.py
```

---

## Modos de Uso

**Modo Texto**
1. Seleccioná el idioma de destino (el origen se detecta automáticamente).
2. Escribí el texto en el campo de entrada.
3. Presioná **Traducir** → el resultado aparece en pantalla.
4. Opcionalmente, presioná **Reproducir** para escuchar la traducción.

**Modo Voz**
1. Seleccioná el idioma de origen y de destino.
2. Presioná **Grabar** → la app detecta automáticamente si hay audio del sistema (video/YouTube) o voz del micrófono.
3. Presioná **Stop rec** → el sistema transcribe y traduce automáticamente.
4. El texto original y la traducción aparecen en pantalla; presioná **Reproducir** para escucharla.

---

## Aprendizajes Técnicos

- Arquitectura multihilo con `threading` para no bloquear la UI durante grabación, TTS, y monitoreo de red.
- Máquina de estados para el reproductor de audio: `playing → paused → stopped`.
- Cache LRU implementado manualmente con `OrderedDict` (sin librerías externas).
- Grabación simultánea de micrófono y loopback en paralelo con selección automática del mejor audio por análisis de RMS al detener.
- Preprocesamiento adaptativo de señal de audio: reducción de ruido espectral con `noisereduce` y filtro Butterworth pasa-banda con `scipy.signal` en modo micrófono.
- División inteligente de texto largo con `re` y `textwrap` para no exceder límites de la API TTS.
- Manejo de SSL con `certifi` para compatibilidad en ejecutables.
- Pantalla de carga con verificación de conectividad antes de habilitar la interfaz principal.

---

## Licencia

Este proyecto está bajo la Licencia MIT. Para más detalles, consulta el archivo [LICENSE](LICENSE).

---

Nota: Al ser una herramienta de utilidad independiente y no estar firmada digitalmente, es posible que Windows SmartScreen muestre una advertencia. Puede ejecutarla con total seguridad seleccionando 'Más información' -> 'Ejecutar de todas formas'.

---

*Desarrollado por [Pablo Salinas](https://github.com/PabloSalinasDev)* - PyBloSoft © 2026