# Changelog — TranslatorPro AI

Todos los cambios notables del proyecto se documentan en este archivo.

---

## [1.2.1] - 2026-04-25

### Corregido
- Micrófono no capturaba audio por error en callback_audio al limpiar logging
- cancelar() no cerraba el stream correctamente cuando _modo era None

---

## [1.2.0] - 2026-04-24

### Cambiado
- `MotorVoz` ahora graba micrófono y loopback en paralelo desde el inicio
- La decisión del modo (loopback vs micrófono) se toma al detener según el RMS real
- Eliminado el sistema de switch dinámico durante la grabación
- Timer inteligente evalúa ambos buffers para detectar audio real

### Corregido
- Se perdía la primera palabra del video al switchear de micrófono a loopback
- El contador de 60 segundos arranca solo cuando hay audio real detectado
- Grabación no se detenía correctamente al cambiar de pestaña

---

## [1.1.0] - 2026-04-23

### Agregado
- Captura de audio por loopback (YouTube, videos del sistema)
- Detección automática de modo de captura (loopback vs micrófono) al iniciar grabación
- Método `cancelar()` en `MotorVoz` para interrumpir grabación limpiamente
- Logging completo en `MotorVoz`: detección de modo, RMS, transcripción, errores

### Cambiado
- `MotorVoz` ahora usa `soundcard` para loopback y `sounddevice` para micrófono
- `preprocesar_audio()` aplica filtro pasa-banda y reducción de ruido solo en modo micrófono
- `iniciar_grabacion()` ya no recibe parámetros, detecta el modo automáticamente
- Umbral de detección de audio calibrado en `0.005` RMS
- Docstrings de `start_voice()` y `stop_voice()` actualizados en el controller
- Al iniciar grabación se limpian los campos de texto anteriores
- Al reproducir se muestra "Reproduciendo..." en el estado

---

## [1.0.1] - 2026-04-22

### Corregido
- Manejo controlado cuando no hay salida de audio.
- Se corrigió el error que forzaba minúsculas después de los puntos, permitiendo una capitalización correcta en párrafos largos.

---

## [1.0.0] - 2026-04-22

### Agregado
- Versión inicial de Traductor Pro AI
- Reconocimiento de voz con Google Speech API
- Traducción con Google Translator
- Síntesis de voz con gTTS y pygame
- Interfaz gráfica con Flet
- Modo texto y modo voz
- Soporte multiidioma