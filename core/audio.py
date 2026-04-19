import pygame
from gtts import gTTS
import threading
from io import BytesIO
import traceback
import logging
from core.traduccion import MotorTraduccion
import time

class MotorAudio:
    """ 
    Gestor de reproducción de audio y síntesis de voz (TTS).
    Motor para convertir texto a voz utilizando gTTS, 
    gestionar la reproducción mediante el mixer de pygame y permitir 
    el control de estados (reproducir, pausar, reanudar y detener).
    """
    def __init__(self):
        self.estado = "stopped"  # stopped, playing, paused
        self.evento_stop = threading.Event()
        # Se inicializa de forma segura al arrancar
        self._inicializar_seguro()

    def _inicializar_seguro(self):
        """
        Intenta inicializar o reinicializar el mixer de forma segura.
        Esto permite capturar el nuevo dispositivo de audio (ej. Bluetooth).
        """
        try:
            if pygame.mixer.get_init():
                pygame.mixer.quit()  # Quita el dispositivo anterior

            # Re-inicializa para enganchar el dispositivo actual
            pygame.mixer.init()
        except Exception as e:
            logging.error(f"Error reiniciando mixer: {e}")

    def reproducir(self, texto, idioma, callback_estado=None):
        """
        Reproduce audio con control de estado y reinicio de mixer
        """
        
        if not pygame.mixer.get_init():
            logging.warning("No hay dispositivo de audio disponible, omitiendo reproducción")
            return
        
        try:
            # 1. Reinicia el mixer para asegurar salida de audio actual
            self._inicializar_seguro()

            frases = MotorTraduccion.dividir_texto(texto)
            self.evento_stop.clear()
            self.estado = "playing"

            for frase in frases:
                if self.evento_stop.is_set():
                    break
                if not frase.strip():
                    continue
                # Generar MP3 en memoria
                with BytesIO() as mp3_fp:
                    tts = gTTS(text=frase, lang=idioma)
                    tts.write_to_fp(mp3_fp)
                    mp3_fp.seek(0)

                    # Cargar y reproducir en Pygame
                    pygame.mixer.music.load(mp3_fp)
                    pygame.mixer.music.play()

                    while pygame.mixer.music.get_busy() or self.estado == "paused":
                        if self.evento_stop.is_set():
                            pygame.mixer.music.stop()
                            self.estado = "stopped"
                            return

                        if self.estado == "paused":
                            pygame.mixer.music.pause()
                            if callback_estado:
                                callback_estado("paused")
                            time.sleep(0.1)
                            continue
                        else:
                            pygame.mixer.music.unpause()

                        time.sleep(0.1)

        except Exception as ex:
            logging.error(f"Error audio: {ex}")
            logging.error(traceback.format_exc())
            raise Exception("Error al reproducir audio")
        finally:
            self.estado = "stopped"
            if callback_estado:
                callback_estado("stopped")

    def pausar(self):
        if self.estado == "playing":
            self.estado = "paused"
            pygame.mixer.music.pause()

    def reanudar(self):
        if self.estado == "paused":
            self.estado = "playing"
            pygame.mixer.music.unpause()

    def detener(self):
        self.evento_stop.set()
        self.estado = "stopped"
        # Seguridad extra: verificar si pygame está iniciado antes de parar
        if pygame.mixer.get_init():
            try:
                pygame.mixer.music.stop()
            except:
                pass