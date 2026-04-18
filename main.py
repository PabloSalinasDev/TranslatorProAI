import ctypes
import sys
import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import flet as ft
import threading
import time

from config.settings import myappid
from core.traduccion import MotorTraduccion
from core.audio import MotorAudio
from core.voz import MotorVoz
from utils import GestorConectividad
from core.controllers import AppController
import ui.vistas as ui
import ssl

# Configuración de certificados SSL para el entorno compilado (Nuitka/PyInstaller)
# Garantiza que las peticiones HTTPS (Google Translate API) sean seguras y funcionen en el .exe
if getattr(sys, 'frozen', False):
    import certifi
    os.environ['SSL_CERT_FILE'] = certifi.where()
    os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
    ssl._create_default_https_context = lambda: ssl.create_default_context(cafile=certifi.where())

# Establece una identidad única para el proceso en Windows (AppUserModelID)
# Esto asegura que el icono se agrupe correctamente en la barra de tareas y permita anclar la app
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

# --- CÁLCULO DE RUTA ABSOLUTA ---
if getattr(sys, 'frozen', False):
    base_path = os.path.dirname(sys.executable)
else:
    base_path = os.path.dirname(__file__)

ASSETS_PATH = os.path.join(base_path, "assets")

# Carpeta de la App donde se va a guardar el archivo de log
BASE_DIR = Path(os.environ.get("LOCALAPPDATA")) / "TranslatorProAI"
LOG_DIR  = BASE_DIR / "logs"

LOG_DIR.mkdir(parents=True, exist_ok=True)

ruta_log = LOG_DIR / "debug.log"

# Se configura el Handler Rotativo
# maxBytes = 5 * 1024 * 1024 (5 Megabytes)
# backupCount = 1 (mantiene el archivo actual y uno anterior de respaldo)
handler = RotatingFileHandler(
    ruta_log, 
    maxBytes=5*1024*1024, 
    backupCount=1, 
    encoding='utf-8'
)

# Configuración del logging
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[handler]
)

class EstadoApp:
    def __init__(self):
        self.ultimo_idioma = ""
        self.ultimo_texto_trad = ""
        self.ultimo_click_pausa = 0

def main(page: ft.Page):
    # Configuración de Ventana
    page.title = "Translator Pro AI"
    page.window.icon = os.path.join(ASSETS_PATH, "icon.ico")
    page.theme_mode = ft.ThemeMode.DARK
    page.window.bgcolor = ft.Colors.GREY_900
    page.bgcolor = ft.Colors.GREY_900
    page.window.title_bar_hidden = True
    page.window.width, page.window.height = 500, 655
    page.window.frameless = False
    page.window.resizable = False
    page.window.maximizable = False
    page.window.alignment = ft.alignment.center
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.padding = 0

    # Instancias
    estado = EstadoApp()
    motor_traduccion = MotorTraduccion()
    motor_audio = MotorAudio()
    motor_voz = MotorVoz()
    gestor_red = GestorConectividad()
    
    # Controlador
    ctrl = AppController(page, ui, estado, motor_traduccion, motor_audio, motor_voz, gestor_red)

    # Conexión de Eventos
    ui.dropdown_origen.on_change = ctrl.limpiar_campos
    ui.dropdown_destino.on_change = ctrl.limpiar_campos
    ui.selector_modo.on_change = lambda e: ctrl.actualizar_ui(int(e.data))
    ui.boton_cerrar.on_click = ctrl.cerrar_app
    ui.boton_minimizar.on_click = lambda _: setattr(page.window, 'minimized', True) or page.update()
    ui.btn_traducir_txt.on_click = ctrl.traducir_texto
    ui.btn_hablar_txt.on_click = ctrl.hablar_texto
    ui.btn_grabar.on_click = ctrl.start_voice
    ui.btn_detener.on_click = ctrl.stop_voice

    # Lógica de Red y Carga
    def check_red():
        while True:
            con = gestor_red.verificar_conexion()
            ui.icono_conexion.name = ft.Icons.WIFI_OFF if not con else ft.Icons.WIFI
            ui.icono_conexion.color = ft.Colors.GREEN if con else ft.Colors.RED
            ui.texto_conexion.value = "Conectado" if con else "Sin conexión"
            ui.texto_conexion.color = ui.icono_conexion.color
            page.update()
            time.sleep(5)

    def init_app():
        
        ctrl.inicializar_sistema()

    page.add(ft.Stack([ui.layout_app, ui.capa_cargando]))
    threading.Thread(target=check_red, daemon=True).start()
    threading.Thread(target=init_app, daemon=True).start()
    ctrl.actualizar_ui(0)

if __name__ == "__main__":
    ft.app(target=main)