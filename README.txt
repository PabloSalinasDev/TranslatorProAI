==========================================================
          TRADUCTOR PRO AI - Manual de Usuario
==========================================================

¡Gracias por instalar Traductor Pro AI! Esta aplicación es una 
herramienta de alto rendimiento diseñada para traducciones 
fluidas de texto y voz, enfocada en la estabilidad y la 
experiencia del usuario.

----------------------------------------------------------
1. REQUISITOS DEL SISTEMA
----------------------------------------------------------
- Conexión a Internet: Necesaria para el motor de traducción.
- Micrófono: Requerido para el procesamiento de voz a texto.
- Audio: Altavoces o auriculares para la síntesis de voz.

----------------------------------------------------------
2. FUNCIONAMIENTO
----------------------------------------------------------
MODO TEXTO:
- Entrada de texto con detección automática de idioma.
- Traducción instantánea a múltiples idiomas.
- Control de reproducción de voz con funciones de Pausa/Reanudar.

MODO VOZ:
- Reconocimiento de voz con reducción activa de ruido de fondo.
- Temporizador en tiempo real (límite de 60s por sesión).
- Pipeline automatizado de transcripción y traducción.

----------------------------------------------------------
3. ARQUITECTURA TÉCNICA (Para Desarrolladores / IT)
----------------------------------------------------------
Esta aplicación ha sido desarrollada siguiendo estándares de
ingeniería de software profesional:

- Diseño: Arquitectura desacoplada (Patrón inspirado en MVC).
- Compilación: Ejecutable nativo optimizado mediante Nuitka (C++).
- Concurrencia: Ejecución multihilo (Multithreading) para una 
  interfaz fluida y sin bloqueos durante llamadas a APIs.
- Resiliencia: Monitor de conectividad integrado basado en sockets.
- Diagnóstico: Sistema de logs persistentes en %LOCALAPPDATA%.

----------------------------------------------------------
4. TECNOLOGÍAS UTILIZADAS
----------------------------------------------------------
- Interfaz Gráfica: Flet (Basado en Flutter).
- Traducción: Motores de Traducción Neuronal (NMT).
- Audio y Voz: gTTS, Pygame Audio y SpeechRecognition.
- Procesamiento: Noisereduce para la limpieza de señal de audio.

==========================================================
Traductor Pro AI - Versión 1.0.0
Desarrollado por PyBloSoft © 2026
==========================================================