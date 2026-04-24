import speech_recognition as sr
import soundcard as sc
import sounddevice as sd
import numpy as np
import scipy.signal as signal
import noisereduce as nr
import queue
import threading
import logging


class MotorVoz:
    """
    Motor de reconocimiento de voz (Speech-to-Text).
    Detecta automáticamente el modo de captura:
    - 'loopback': si hay audio del sistema sonando (videos, YouTube)
    - 'microfono': si no hay audio del sistema (voz real del usuario)
    """

    def __init__(self, fs=16000):
        self.fs = fs
        self.is_recording = False
        self._cancelado = False
        self._buffer = []
        self._hilo = None
        self._loopback_mic = None
        self._modo = None
        # Para modo micrófono
        self.queue = queue.Queue()
        self.stream = None
        self.recording = []

    def callback_audio(self, indata, frames, time, status):
        """Callback para captura de micrófono en tiempo real."""
        if status:
            logging.warning(f"Audio status: {status}")
        self.queue.put(indata.copy())

    def _detectar_modo(self):
        """
        Escucha 300ms del loopback y mide el volumen RMS.
        Si hay señal, usa loopback. Si no, usa micrófono.
        """
        try:
            speaker = sc.default_speaker()
            mic = sc.get_microphone(speaker.id, include_loopback=True)
            with mic.recorder(samplerate=self.fs, channels=1) as rec:
                muestra = rec.record(numframes=int(self.fs * 0.3))  # 300ms

            rms = np.sqrt(np.mean(muestra**2))
            logging.info(f"Detección automática — RMS loopback: {rms:.6f}")

            if rms > 0.005:  # Umbral: hay audio en el sistema
                logging.info("Modo detectado: LOOPBACK")
                return "loopback"
            else:
                logging.info("Modo detectado: MICROFONO")
                return "microfono"
        except Exception as e:
            logging.warning(f"Error en detección automática, usando micrófono: {e}")
            return "microfono"

    def iniciar_grabacion(self):
        """
        Detecta automáticamente el modo e inicia la captura de audio.
        """
        self._cancelado = False
        self._buffer = []
        self.recording = []
        self.is_recording = True
        self._modo = self._detectar_modo()

        if self._modo == "loopback":
            try:
                speaker = sc.default_speaker()
                self._loopback_mic = sc.get_microphone(speaker.id, include_loopback=True)
                logging.info(f"Grabación loopback iniciada — dispositivo: {speaker.name}")
            except Exception as e:
                self.is_recording = False
                logging.error(f"Error iniciando loopback: {e}")
                raise Exception(f"No se pudo iniciar captura de audio del sistema: {e}")

            def _grabar():
                try:
                    with self._loopback_mic.recorder(samplerate=self.fs, channels=1) as rec:
                        while self.is_recording:
                            chunk = rec.record(numframes=self.fs // 10)  # chunks 100ms
                            self._buffer.append(chunk)
                except Exception as e:
                    logging.error(f"Error en hilo loopback: {e}")

            self._hilo = threading.Thread(target=_grabar, daemon=True)
            self._hilo.start()

        else:  # microfono
            while not self.queue.empty():
                self.queue.get()

            self.stream = sd.InputStream(
                samplerate=self.fs, channels=1, callback=self.callback_audio
            )
            self.stream.start()
            logging.info("Grabación micrófono iniciada")

    def detener_grabacion(self):
        """Detiene la captura y retorna el audio grabado en RAM."""
        if not self.is_recording:
            raise Exception("No hay grabación activa")

        logging.info(f"Deteniendo grabación — modo: {self._modo}")
        self.is_recording = False

        if self._modo == "loopback":
            self._hilo.join(timeout=2)
            if not self._buffer:
                raise Exception("El audio está vacío")
            return [np.concatenate(self._buffer, axis=0)]

        else:  # microfono
            try:
                self.stream.stop()
                self.stream.close()
            except Exception as e:
                logging.warning(f"Error cerrando stream micrófono: {e}")

            while not self.queue.empty():
                self.recording.append(self.queue.get())

            if not self.recording:
                raise Exception("El audio está vacío")

            return self.recording

    def cancelar(self):
        """Cancela la grabación sin procesar el audio."""
        logging.info("Grabación cancelada")
        self._cancelado = True
        self.is_recording = False

        if self._modo == "loopback" and self._hilo:
            self._hilo.join(timeout=2)
        elif self._modo == "microfono" and self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception as e:
                logging.warning(f"Error cerrando stream en cancelación: {e}")

        self._buffer = []
        self.recording = []

    def preprocesar_audio(self, audio_raw):
        """
        Preprocesamiento según el modo detectado:
        - loopback:   solo normalización (audio ya viene limpio del sistema)
        - microfono:  reducción de ruido + filtro pasa-banda + normalización
        """
        try:
            audio_flatten = audio_raw.flatten()

            if self._modo == "microfono":
                # --- 1. REDUCCIÓN DE RUIDO ESPECTRAL ---
                audio_limpio = nr.reduce_noise(
                    y=audio_flatten,
                    sr=self.fs,
                    prop_decrease=0.4,
                    stationary=True,
                    n_fft=2048,
                    win_length=2048,
                )

                # --- 2. FILTRO PASA-BANDA ---
                nyquist = self.fs / 2
                low = 60 / nyquist
                high = 7000 / nyquist
                b, a = signal.butter(4, [low, high], btype="band")
                audio_flatten = signal.filtfilt(b, a, audio_limpio)
                logging.debug("Preprocesamiento micrófono aplicado")

            # --- NORMALIZACIÓN (ambos modos) ---
            max_val = np.max(np.abs(audio_flatten))
            if max_val > 0:
                audio_flatten = audio_flatten / max_val

            return audio_flatten

        except Exception as e:
            logging.warning(f"Error en preprocesamiento: {e}")
            return audio_raw.flatten()

    def transcribir(self, audio_data, lang_code):
        """Transcribe audio a texto usando Google Speech API."""
        if self._cancelado:
            logging.info("Transcripción omitida — fue cancelada")
            return None

        audio_raw = np.concatenate(audio_data, axis=0)
        audio_procesado = self.preprocesar_audio(audio_raw)

        audio_int16 = (audio_procesado * 32767).astype(np.int16)
        audio_bytes = audio_int16.tobytes()

        audio_obj = sr.AudioData(audio_bytes, self.fs, 2)
        recognizer = sr.Recognizer()

        recognizer.energy_threshold = 200
        recognizer.dynamic_energy_threshold = True
        recognizer.dynamic_energy_adjustment_damping = 0.15
        recognizer.dynamic_energy_ratio = 1.5
        recognizer.pause_threshold = 0.8
        recognizer.phrase_threshold = 0.3
        recognizer.non_speaking_duration = 0.5

        logging.info(f"Enviando audio a Google Speech — idioma: {lang_code}")

        try:
            texto = recognizer.recognize_google(audio_obj, language=lang_code)
            logging.info(f"Transcripción exitosa: {texto[:60]}")
            return texto
        except sr.UnknownValueError:
            logging.warning("Google Speech no entendió el audio")
            raise Exception("No se entendió el audio")
        except sr.RequestError as e:
            logging.error(f"Error de conexión con Google Speech: {e}")
            raise Exception("Error de conexión con Google Speech")