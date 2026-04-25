import threading
import time
import logging
import numpy as np
import re
import flet as ft
from deep_translator import GoogleTranslator
from config.settings import IDIOMAS

class AppController:
    """
    Controlador central de la aplicación.
    Coordina la interacción entre la interfaz (Flet) y los motores de lógica.
    Gestiona la ejecución de tareas asíncronas, el flujo de datos entre 
    componentes y la actualización dinámica de la interfaz de usuario.
    """
    def __init__(self, page, ui, estado, motor_traduccion, motor_audio, motor_voz, gestor_red):
        """
        Inicializa el controlador con las dependencias del sistema.
        """
        self.page = page
        self.ui = ui
        self.estado = estado
        self.motor_traduccion = motor_traduccion
        self.motor_audio = motor_audio
        self.motor_voz = motor_voz
        self.gestor_red = gestor_red

    def limpiar_campos(self, _):
        """
        Limpia los campos y detiene el audio al cambiar configuraciones.
        """
        self.motor_audio.detener()
        self.ui.texto_in.value = ""
        self.ui.texto_out_entrada.value = ""
        self.ui.texto_out_salida.value = ""
        self.ui.texto_proceso.value = "Campos limpiados."
        self.ui.btn_hablar_txt.disabled = True
        self.estado.ultimo_idioma = ""
        self.estado.ultimo_texto_trad = ""
        self.ui.texto_in.focus()
        self.page.update()

    def actualizar_ui(self, index):
        """
        Reconfigura la interfaz gráfica según el modo seleccionado.
        Ajusta la visibilidad de controles, resetea selectores de idioma 
        y asegura que el motor de audio se detenga al cambiar de pestaña.
        """
        es_texto = index == 0
        self.motor_audio.detener()
        self.motor_voz.cancelar()
        self.ui.texto_in.value = ""
        self.ui.texto_out_entrada.value = ""
        self.ui.texto_out_salida.value = ""
        self.ui.btn_hablar_txt.disabled = True
        self.ui.btn_detener.disabled = True
        
        if es_texto:
            self.ui.dropdown_origen.value = "Auto (Texto)"
            self.ui.dropdown_origen.disabled = True
        else:
            self.ui.dropdown_origen.value = "Español"
            self.ui.dropdown_origen.disabled = False

        self.ui.btn_traducir_txt.visible = es_texto
        self.ui.traduccion_contenedor_texto.visible = es_texto
        self.ui.contenedor_vacio.visible = not es_texto
        self.ui.textfield.visible = not es_texto
        self.ui.traduccion_out_salida.visible = not es_texto
        self.ui.btn_grabar.visible = not es_texto
        
        self.ui.texto_proceso.value = "Sistema listo."
        self.page.update()

    def traducir_texto(self, _):
        """
        Coordina la validación de red y la llamada al motor de traducción.
        """
        if not self.gestor_red.verificar_conexion():
            self.ui.texto_proceso.value = "Sin conexión"
            self.page.update()
            return
            
        if not self.ui.texto_in.value:
            return

        try:
            self.ui.btn_traducir_txt.disabled = True
            self.ui.pr.visible = True
            self.ui.texto_proceso.value = "Traduciendo..."
            self.page.update()

            nom_dest = self.ui.dropdown_destino.value
            code_dest = IDIOMAS[nom_dest]
            tgt_clean = code_dest.split("-")[0] if "zh" not in code_dest else code_dest

            trad, lang = self.motor_traduccion.traducir(self.ui.texto_in.value, tgt_clean)
            
            trad_corregida = trad[0].upper() + trad[1:] if trad else trad
            
            # Se pone mayúscula después de cada . ! o ? (y espacios)
            trad_corregida = re.sub(r'([\.!\?]\s*)([a-z])', lambda m: m.group(1) + m.group(2).upper(), trad_corregida)
            
            self.ui.texto_out_entrada.value = trad_corregida
            self.estado.ultimo_idioma = lang
            self.estado.ultimo_texto_trad = trad
            self.ui.texto_proceso.value = "Completado"
        except Exception as ex:
            self.ui.texto_proceso.value = f"Error"
            logging.error(ex)
        finally:
            self.ui.pr.visible = False
            self.ui.btn_hablar_txt.disabled = False
            self.ui.btn_traducir_txt.disabled = False
            self.page.update()

    def hablar_texto(self, _):
        """
        Gestiona la síntesis de voz del texto traducido.
        Implementa una protección de 0.5s entre clics para evitar errores de buffer.
        Maneja la máquina de estados del reproductor: Iniciar, Pausar o Reanudar.
        """
        ahora = time.time()
        if ahora - self.estado.ultimo_click_pausa < 0.5: return
        self.estado.ultimo_click_pausa = ahora

        if self.motor_audio.estado == "playing":
            self.motor_audio.pausar()
            self.ui.btn_hablar_txt.text = "Reanudar"
            self.ui.btn_hablar_txt.icon = ft.Icons.PLAY_ARROW
            self.ui.btn_hablar_txt.style = self.ui.estilo_naranja
            self.page.update()
            return

        if self.motor_audio.estado == "paused":
            self.motor_audio.reanudar()
            self.ui.btn_hablar_txt.text = "Pausar"
            self.ui.btn_hablar_txt.icon = ft.Icons.PAUSE
            self.ui.btn_hablar_txt.style = self.ui.estilo_azul
            self.page.update()
            return

        if not self.estado.ultimo_texto_trad: return

        self.ui.btn_detener.disabled = False
        self.ui.btn_detener.on_click = lambda _: self.motor_audio.detener()
        self.ui.btn_hablar_txt.text = "Pausar"
        self.ui.btn_hablar_txt.icon = ft.Icons.PAUSE
        self.ui.btn_hablar_txt.style = self.ui.estilo_azul
        self.page.update()

        def _audio_thread():
            try:
                self.ui.texto_proceso.value = "Reproduciendo..."
                self.page.update()
                def cb(est):
                    if est == "stopped":
                        self.ui.texto_proceso.value = "Finalizado"
                        self.page.update()
                self.motor_audio.reproducir(self.estado.ultimo_texto_trad, self.estado.ultimo_idioma, cb)
            finally:
                self.ui.btn_hablar_txt.text = "Reproducir"
                self.ui.btn_hablar_txt.style = self.ui.estilo_naranja
                self.ui.btn_hablar_txt.icon = ft.Icons.PLAY_ARROW
                self.ui.btn_detener.disabled = True
                self.ui.btn_detener.on_click = self.stop_voice
                self.page.update()

        threading.Thread(target=_audio_thread, daemon=True).start()

    def start_voice(self, _):
        """
        Inicia el proceso de captura de audio.
        Arranca micrófono y loopback en paralelo desde el inicio.
        Al detener, evalúa automáticamente cuál tiene audio real y lo usa.
        Realiza una validación de conectividad antes de proceder. Si es exitosa:
        1. Limpia los campos de texto anteriores.
        2. Activa micrófono y loopback en paralelo en el MotorVoz.
        3. Bloquea los controles para evitar conflictos.
        4. Transforma el botón de 'Detener' en un controlador de grabación ('Stop rec').
        """
        if not self.gestor_red.verificar_conexion():
            self.ui.texto_proceso.value = "Sin conexión"
            self.page.update()
            return
        try:
            self.ui.texto_out_entrada.value = ""
            self.ui.texto_out_salida.value = ""  
            self.motor_voz.iniciar_grabacion()
            
            self.ui.btn_grabar.disabled = True
            self.ui.btn_detener.disabled = False
            self.ui.btn_detener.text = "Stop rec"
            self.ui.btn_detener.on_click = self.stop_voice
            self.ui.texto_proceso.value = "Grabando... 59s"
            self.page.update()

            def timer():
                self.ui.texto_proceso.value = "Esperando audio..."
                self.page.update()
                # Espera hasta que haya audio real, máximo 5 segundos
                tiene_audio = False
                for _ in range(10):  # 10 × 0.5s = 5 segundos
                    time.sleep(0.5)
                    if not self.motor_voz.is_recording:
                        return
                    # Evaluar loopback por RMS
                    if self.motor_voz._buffer:
                        audio_lb = np.concatenate(self.motor_voz._buffer, axis=0).flatten()
                        rms_lb = float(np.sqrt(np.mean(audio_lb**2)))
                        if rms_lb > 0.014:
                            tiene_audio = True

                    # Evaluar micrófono
                    if not tiene_audio:
                        chunks = list(self.motor_voz.queue.queue)
                        if chunks:
                            audio = np.concatenate(chunks, axis=0).flatten()
                            rms = float(np.sqrt(np.mean(audio**2)))
                            if rms > 0.014:
                                tiene_audio = True

                    if tiene_audio:
                        break

                if not tiene_audio:
                    self.motor_voz.cancelar()
                    self.ui.texto_proceso.value = "No se detectó audio"
                    self.ui.btn_grabar.disabled = False
                    self.ui.btn_detener.disabled = True
                    self.ui.btn_detener.text = "Stop"
                    self.ui.pr.visible = False
                    self.page.update()
                    return
                # Recién acá arranca el contador real de 59 segundos
                s = 59
                while self.motor_voz.is_recording and s > 0:
                    time.sleep(1)
                    s -= 1
                    if self.motor_voz.is_recording:
                        self.ui.texto_proceso.value = f"Grabando... {s}s"
                        self.page.update()

                if s <= 0 and self.motor_voz.is_recording:
                    self.stop_voice(None)

            threading.Thread(target=timer, daemon=True).start()
        except Exception as ex:
            self.ui.texto_proceso.value = f"Error micrófono"
            logging.error(f"Error en start_voice: {ex}")
            self.page.update()

    def stop_voice(self, _):
        """
        Finaliza la captura de audio y procesa la traducción.
        Detiene micrófono y loopback, evalúa cuál tiene audio real
        y lanza un hilo secundario para realizar la transcripción
        y traducción sin bloquear la interfaz.
        """
        try:
            audio_data = self.motor_voz.detener_grabacion()
            self.ui.btn_detener.disabled = True
            self.ui.pr.visible = True
            self.ui.texto_proceso.value = "Procesando..."
            self.page.update()

            def _proc():
                try:
                    code_origen = IDIOMAS[self.ui.dropdown_origen.value]
                    code_dest = IDIOMAS[self.ui.dropdown_destino.value]
                    texto = self.motor_voz.transcribir(audio_data, code_origen)
                    
                    tgt = code_dest.split("-")[0] if "zh" not in code_dest else code_dest
                    src = code_origen.split("-")[0] if "zh" not in code_origen else code_origen
                    
                    trad = GoogleTranslator(source=src, target=tgt).translate(texto)
                    
                    self.estado.ultimo_texto_trad = trad
                    self.estado.ultimo_idioma = tgt
                    self.ui.texto_out_entrada.value = f"{src.upper()}: {texto.capitalize()}"
                    self.ui.texto_out_salida.value = f"{tgt.upper()}: {trad.capitalize()}"
                    self.ui.texto_proceso.value = "Completado"
                    self.ui.btn_hablar_txt.disabled = False
                except Exception as e:
                    self.ui.texto_proceso.value = str(e)
                finally:
                    self.ui.pr.visible = False
                    self.ui.btn_grabar.disabled = False
                    self.ui.btn_detener.text = "Stop"
                    self.page.update()

            threading.Thread(target=_proc, daemon=True).start()
        except Exception as ex:
            self.ui.texto_proceso.value = str(ex)
            self.ui.pr.visible = False
            self.ui.btn_grabar.disabled = False
            self.ui.btn_detener.text = "Stop"
            self.page.update()

    def cerrar_app(self, _=None):
        """Detiene todos los procesos de hardware y cierra la aplicación."""
        try:
            self.page.window.visible = False
            self.motor_audio.detener()
            self.motor_voz.cancelar()

        except Exception as e:
            logging.error(f"Error durante el cierre: {e}")

        self.page.window.destroy()

    def minimizar_ventana(self, _=None):
        """Minimiza la ventana de la aplicación."""
        self.page.window.minimized = True
        self.page.update()

    def inicializar_sistema(self):
        """
        Lógica de inicialización que corre MIENTRAS se ve la capa_cargando.
        Usa el GestorConectividad real de utils.py.
        """
        try:
            # 1. Feedback en la pantalla de carga
            self.ui.texto_loading.value = "Cargando componentes..."
            self.ui.barra_loading.value = 0.2
            self.page.update()
            time.sleep(0.5)

            # 2. Verificación de red
            self.ui.texto_loading.value = "Verificando conexión a Google..."
            self.ui.barra_loading.value = 0.5
            self.page.update()
            
            red_ok = self.gestor_red.verificar_conexion(timeout=5)
            
            # 3. Verificación de servicio específico
            if red_ok:
                self.ui.texto_loading.value = "Validando servicio de traducción..."
                self.ui.barra_loading.value = 0.8
                self.page.update()
                self.gestor_red.verificar_servicio("translate")

            # 4. Finalización
            self.ui.barra_loading.value = 1.0
            self.ui.texto_loading.value = "Conexión Exitosa" if red_ok else "Modo Offline"
            self.page.update()
            time.sleep(1.0)

            # 5. Salto a la App
            self.ui.capa_cargando.visible = False
            self.ui.layout_app.visible = True
            self.actualizar_ui(0) # Iniciamos en modo texto
            self.page.update()

        except Exception as e:
            logging.error(f"Error en inicialización: {e}")
            self.ui.texto_loading.value = "Error al iniciar"
            self.page.update()