import speech_recognition as sr
import sounddevice as sd
import numpy as np
import scipy.signal as signal
import noisereduce as nr
import queue
import logging

class MotorVoz:
    """
    Motor de reconocimiento de voz (Speech-to-Text).
    Captura audio del micrófono y lo transcribe usando Google Speech API.
    """

    def __init__(self, fs=16000):
        """
        Inicializa el motor de voz.
        """
        self.fs = fs
        self.queue = queue.Queue()
        self.stream = None
        self.recording = []
        self.is_recording = False

    def callback_audio(self, indata, frames, time, status):
        """
        Callback para captura de audio en tiempo real.
        Se ejecuta automáticamente por sounddevice.
        """
        if status:
            logging.warning(f"Audio status: {status}")
        self.queue.put(indata.copy())

    def iniciar_grabacion(self):
        """
        Inicia la captura de audio desde el micrófono.
        """
        self.recording = []
        self.is_recording = True

        while not self.queue.empty():
            self.queue.get()

        self.stream = sd.InputStream(
            samplerate=self.fs, channels=1, callback=self.callback_audio
        )
        self.stream.start()

    def detener_grabacion(self):
        """
        Detiene la captura y retorna el audio grabado.
        """
        if not self.is_recording or self.stream is None:
            raise Exception("No hay grabación activa")

        try:
            self.stream.stop()
            self.stream.close()
        except:
            pass

        self.is_recording = False

        while not self.queue.empty():
            self.recording.append(self.queue.get())

        if not self.recording:
            raise Exception("El audio está vacío")

        return self.recording

    def preprocesar_audio(self, audio_raw):
        """
        Pre-procesamiento avanzado:
        1. Filtro Pasa-Banda más amplio (recupera nitidez humana).
        2. Reducción de ruido espectral (limpia audio de video).
        3. Normalización.
        """
        try:
            audio_flatten = audio_raw.flatten()

            # --- 1. REDUCCIÓN DE RUIDO ESPECTRAL ---
            # Analiza el audio, busca patrones de ruido constante,
            # (como el soplido de fondo de un video) y lo elimina sin borrar la voz.
            # prop_decrease=0.4 significa que reduce el ruido un 40%.
            audio_limpio = nr.reduce_noise(
                y=audio_flatten,
                sr=self.fs,
                prop_decrease=0.4,
                stationary=True,  # Asume ruido constante (ventiladores, estática)
                n_fft=2048,  # Mayor precisión en frecuencias bajas
                win_length=2048,  # Ventana más grande para mejor análisis
            )

            # --- 2. FILTRO PASA-BANDA AJUSTADO ---
            # 60-7000 (Voz completa, mantiene nitidez para Google)
            nyquist = self.fs / 2
            low = 60 / nyquist  # Bajos naturales de la voz
            high = 7000 / nyquist  # Agudos necesarios para distinguir palabras

            b, a = signal.butter(4, [low, high], btype="band")
            audio_filtrado = signal.filtfilt(b, a, audio_limpio)

            # --- 3. NORMALIZACIÓN ---
            max_val = np.max(np.abs(audio_filtrado))
            if max_val > 0:
                audio_filtrado = audio_filtrado / max_val

            return audio_filtrado

        except Exception as e:
            logging.warning(f"Error en preprocesamiento: {e}")
            # Si falla, devolvemos el audio crudo para no romper la app
            return audio_raw.flatten()

    def transcribir(self, audio_data, lang_code):
        """
        Transcribe audio a texto usando Google Speech API.
        Incluye preprocesamiento y ajustes de sensibilidad.
        """
        # Concatenar y preprocesar audio
        audio_raw = np.concatenate(audio_data, axis=0)
        audio_procesado = self.preprocesar_audio(audio_raw)

        # Convertir a int16 para Google Speech
        audio_int16 = (audio_procesado * 32767).astype(np.int16)
        audio_bytes = audio_int16.tobytes()

        # Crear objeto AudioData
        audio_obj = sr.AudioData(audio_bytes, self.fs, 2)
        recognizer = sr.Recognizer()

        # AJUSTES PARA MEJORAR RECONOCIMIENTO
        recognizer.energy_threshold = 200  # Más sensible (default: 300)
        recognizer.dynamic_energy_threshold = True
        recognizer.dynamic_energy_adjustment_damping = 0.15
        recognizer.dynamic_energy_ratio = 1.5
        recognizer.pause_threshold = 0.8  # Más tolerante a pausas
        recognizer.phrase_threshold = 0.3  # Menos exigente con frases
        recognizer.non_speaking_duration = 0.5

        try:
            texto = recognizer.recognize_google(audio_obj, language=lang_code)
            return texto
        except sr.UnknownValueError:
            raise Exception("No se entendió el audio")
        except sr.RequestError:
            raise Exception("Error de conexión con Google Speech")
