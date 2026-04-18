# ui/vistas.py
import flet as ft
from config.settings import IDIOMAS, APP_TITLE, APP_VERSION

# ==========================================
# INDICADOR DE CONEXIÓN
# ==========================================
icono_conexion = ft.Icon(name=ft.Icons.WIFI_OFF, color=ft.Colors.RED, size=16)
texto_conexion = ft.Text("Sin conexión", size=10, color=ft.Colors.RED)
indicador_conexion = ft.Row([icono_conexion, texto_conexion], spacing=5)

# ==========================================
# ELEMENTOS COMUNES Y DE TEXTO
# ==========================================
texto_proceso = ft.Text(value="Esperando carga...", size=12, color=ft.Colors.GREY_400)
texto_out_entrada = ft.Text(value="", selectable=True, size=14)
texto_out_salida = ft.Text(value="", selectable=True, size=14)
textfield = ft.Text("Traducción detectada:", weight="bold")
pr = ft.ProgressRing(width=16, height=16, stroke_width=2, visible=False)
contenedor_vacio = ft.Container(height=3)

# ==========================================
# PANTALLA DE CARGA
# ==========================================
texto_app = ft.Text(APP_TITLE, color=ft.Colors.WHITE, size=40, weight="bold")
texto_titulo = ft.Text("Iniciando sistema...", color=ft.Colors.WHITE, size=16)
texto_loading = ft.Text(value="", color=ft.Colors.WHITE, size=14)
barra_loading = ft.ProgressBar(width=350, color=ft.Colors.ORANGE_500, bgcolor=ft.Colors.GREY_800)
version = ft.Text(APP_VERSION, color=ft.Colors.GREY_300, size=12)

capa_cargando = ft.Container(
    content=ft.Column(
        [ft.Container(height=150), texto_app, ft.Container(height=70), texto_titulo, ft.Container(height=10),texto_loading, barra_loading, ft.Container(height=200), version],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    ),
    width=500, height=646, bgcolor=ft.Colors.BLACK,
    alignment=ft.alignment.center,
    border=ft.border.all(2, ft.Colors.ORANGE_900), border_radius=7, visible=True, expand=True, clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
)

# ==========================================
# SELECTORES (IDIOMA Y MODO)
# ==========================================
dropdown_origen = ft.Dropdown(
    width=140,
    options=[ft.dropdown.Option(k) for k in IDIOMAS.keys()],
    value="Auto (Texto)",
    label="Origen (Voz/Texto)",
    border_radius=9,
    tooltip="Selecciona origen de traducción",
    border_color=ft.Colors.ORANGE_900,
    text_size=12,
    content_padding=10,
    disabled=False,
)

icono_flecha = ft.Icon(ft.Icons.ARROW_FORWARD, color=ft.Colors.GREY_500, size=16)

dropdown_destino = ft.Dropdown(
    width=140,
    options=[ft.dropdown.Option(k) for k in IDIOMAS.keys() if k != "Auto (Texto)"],
    value="Inglés",
    label="Destino",
    border_radius=9,
    tooltip="Selecciona destino de traducción",
    border_color=ft.Colors.ORANGE_900,
    text_size=12,
    content_padding=10,
)

fila_idiomas = ft.Row([dropdown_origen, icono_flecha, dropdown_destino], alignment=ft.MainAxisAlignment.CENTER, spacing=5)
selector_idioma = ft.Row([fila_idiomas], alignment=ft.MainAxisAlignment.CENTER)

selector_modo = ft.CupertinoSlidingSegmentedButton(
    selected_index=0,
    tooltip="Cambio de modo de traducción",
    bgcolor=ft.Colors.BLACK87,
    thumb_color=ft.Colors.ORANGE_900,
    controls=[ft.Text("Texto"), ft.Text("Voz")],
)

modo_row = ft.Row([selector_idioma, selector_modo], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

# ==========================================
# INPUTS Y SALIDAS DE TEXTO
# ==========================================
texto_in = ft.TextField(
    multiline=True, min_lines=9, max_lines=9, text_size=14,
    bgcolor=ft.Colors.BLACK87, border_color=ft.Colors.ORANGE_900,
    autofocus=True, focused_border_color=ft.Colors.ORANGE_500,
    border_radius=9, cursor_color=ft.Colors.ORANGE_500,
)

traduccion_contenedor_texto = ft.Container(
    content=ft.Column([ft.Text("Ingrese texto:", weight="bold"), texto_in], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
    width=500, alignment=ft.alignment.center,
)

traduccion_out_entrada = ft.Container(
    content=ft.Column([texto_out_entrada], scroll="auto"),
    width=500, height=200, padding=12, bgcolor=ft.Colors.BLACK87,
    border=ft.border.all(1, ft.Colors.ORANGE_900), border_radius=9,
)

traduccion_out_salida = ft.Container(
    content=ft.Column([texto_out_salida], scroll="auto"),
    width=500, height=200, padding=12, bgcolor=ft.Colors.BLACK87,
    border=ft.border.all(1, ft.Colors.ORANGE_900), border_radius=9,
)

# ==========================================
# BOTONES Y ESTILOS
# ==========================================
estilo_naranja = ft.ButtonStyle(
    color=ft.Colors.WHITE,
    bgcolor={ft.ControlState.DISABLED: ft.Colors.BLACK87, ft.ControlState.DEFAULT: ft.Colors.ORANGE_900},
    shape=ft.RoundedRectangleBorder(radius=9), side=ft.BorderSide(width=2, color=ft.Colors.BLACK),
)

estilo_rojo = ft.ButtonStyle(
    color=ft.Colors.WHITE,
    bgcolor={ft.ControlState.DISABLED: ft.Colors.BLACK87, ft.ControlState.DEFAULT: ft.Colors.RED_900},
    shape=ft.RoundedRectangleBorder(radius=9), side=ft.BorderSide(width=2, color=ft.Colors.BLACK),
)

estilo_azul = ft.ButtonStyle(
    color=ft.Colors.WHITE,
    bgcolor={ft.ControlState.DISABLED: ft.Colors.BLACK87, ft.ControlState.DEFAULT: ft.Colors.BLUE_900},
    shape=ft.RoundedRectangleBorder(radius=9), side=ft.BorderSide(width=2, color=ft.Colors.BLACK),
)

btn_traducir_txt = ft.ElevatedButton("Traducir", style=estilo_naranja, icon=ft.Icons.TRANSLATE, tooltip="Traducir texto", height=33, width=113)
btn_hablar_txt = ft.ElevatedButton("Reproducir", style=estilo_naranja, icon=ft.Icons.PLAY_ARROW, tooltip="Reproducir texto", disabled=True, height=33, width=113)
btn_grabar = ft.ElevatedButton("Grabar", style=estilo_naranja, icon=ft.Icons.MIC, tooltip="Grabar audio", height=33, width=113)
btn_detener = ft.ElevatedButton("Stop", style=estilo_rojo, icon=ft.Icons.STOP, tooltip="Detener audio", disabled=True, height=33, width=113)

boton_cerrar = ft.IconButton(icon=ft.Icons.CANCEL, icon_color=ft.Colors.ORANGE_900, icon_size=20, padding=0, visual_density=ft.VisualDensity.COMPACT, tooltip="Cerrar App")
boton_minimizar = ft.IconButton(icon=ft.Icons.REMOVE, icon_color=ft.Colors.ORANGE_900, icon_size=20, padding=0, visual_density=ft.VisualDensity.COMPACT, tooltip="Minimizar")

app_bar = ft.WindowDragArea(
    content=ft.Row(
        [
            ft.Text(APP_TITLE, weight="bold"),
            ft.Row([indicador_conexion, boton_minimizar, boton_cerrar], spacing=5),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    ),
)

# ==========================================
# LAYOUT PRINCIPAL
# ==========================================
layout_app = ft.Container(
    content=ft.Column(
        [
            app_bar, modo_row, contenedor_vacio, traduccion_contenedor_texto,
            ft.Row([btn_traducir_txt, btn_grabar, btn_detener, btn_hablar_txt], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Row([pr, texto_proceso], alignment=ft.MainAxisAlignment.CENTER),
            textfield, traduccion_out_entrada, traduccion_out_salida,
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10,
    ),
    padding=10, bgcolor=ft.Colors.GREY_900,
    border=ft.border.all(2, ft.Colors.ORANGE_900), border_radius=7, visible=False, expand=True, clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
)