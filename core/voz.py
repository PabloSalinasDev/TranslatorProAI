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
    Arranca micrófono y loopback en paralelo desde el inicio.
    Al detener, evalúa automáticamente cuál tiene audio real:
    - Si hay audio del sistema (videos, YouTube) → usa loopback
    - Si hay voz del usuario → usa micrófono
    - Si no hay audio en ninguno → lanza excepción
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
        self._buffer_mic = []

    def callback_audio(self, indata, frames, time, status):
        """Callback para captura de micrófono en tiempo real."""
        if status:
            logging.warning(f"Audio status: {status}")
        self.queue.put(indata.copy())

    def iniciar_grabacion(self):
        """
        Arranca micrófono y loopback en paralelo desde el inicio.
        Evalúa cuál tiene audio real y descarta el otro.
        """
        self._cancelado = False
        self._buffer = []
        self._buffer_mic = []
        self.recording = []
        self.is_recording = True
        self._modo = None

        # Limpiar queue
        while not self.queue.empty():
            self.queue.get()

        # --- STREAM MICRÓFONO ---
        if self.stream is not None:
            try:
                self.stream.stop()
                self.stream.close()
            except:
                pass
            self.stream = None

        self.stream = sd.InputStream(
            samplerate=self.fs, channels=1, callback=self.callback_audio
        )
        self.stream.start()

        # --- STREAM LOOPBACK ---
        def _grabar_loopback():
            try:
                speaker = sc.default_speaker()
                loopback_mic = sc.get_microphone(speaker.id, include_loopback=True)
                with loopback_mic.recorder(samplerate=self.fs, channels=1) as rec:
                    while self.is_recording:
                        chunk = rec.record(numframes=self.fs // 10)  # 100ms
                        self._buffer.append(chunk)
            except Exception as e:
                logging.error(f"Error en hilo loopback: {e}")

        self._hilo = threading.Thread(target=_grabar_loopback, daemon=True)
        self._hilo.start()

    def detener_grabacion(self):
        """Detiene ambos streams y retorna el buffer con audio real."""
        if not self.is_recording:
            raise Exception("No se detectó audio")

        self.is_recording = False

        # Detener micrófono
        try:
            self.stream.stop()
            self.stream.close()
        except Exception as e:
            logging.warning(f"Error cerrando micrófono: {e}")
        self.stream = None

        # Esperar que termine el hilo loopback
        if self._hilo:
            self._hilo.join(timeout=2)

        # Recoger audio del micrófono
        while not self.queue.empty():
            self._buffer_mic.append(self.queue.get())

        # Evaluar cuál tiene audio real
        rms_loopback = 0.0
        rms_mic = 0.0

        if self._buffer:
            audio_lb = np.concatenate(self._buffer, axis=0).flatten()
            rms_loopback = float(np.sqrt(np.mean(audio_lb**2)))

        if self._buffer_mic:
            audio_mc = np.concatenate(self._buffer_mic, axis=0).flatten()
            rms_mic = float(np.sqrt(np.mean(audio_mc**2)))

        # Usar el que tiene más señal
        if rms_loopback >= rms_mic and rms_loopback > 0.014:
            self._modo = "loopback"
            return [np.concatenate(self._buffer, axis=0)]
        elif rms_mic > 0.014:
            self._modo = "microfono"
            return self._buffer_mic
        else:
            raise Exception("No se detectó audio")
    
    def cancelar(self):
        """Cancela la grabación sin procesar el audio."""
        logging.info("Grabación cancelada")
        self._cancelado = True
        self.is_recording = False

        if self._hilo:
            self._hilo.join(timeout=2)

        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception as e:
                logging.warning(f"Error cerrando stream en cancelación: {e}")
            self.stream = None

        self._buffer = []
        self._buffer_mic = []
        self.recording = []

    def preprocesar_audio(self, audio_raw):
        """
        Preprocesamiento según el modo detectado:
        - loopback:  solo normalización (audio ya viene limpio del sistema)
        - microfono: reducción de ruido + filtro pasa-banda + normalización
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