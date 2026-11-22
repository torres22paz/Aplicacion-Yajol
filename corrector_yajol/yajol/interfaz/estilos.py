"""Colores y hojas de estilo de las ventanas."""

AZUL = "#1E3A8A"
AZUL_CLARO = "#2563EB"
VERDE = "#166534"
VERDE_FONDO = "#DCFCE7"
ROJO = "#B91C1C"
ROJO_FONDO = "#FEE2E2"
GRIS_TEXTO = "#111827"
GRIS_SUAVE = "#4B5563"

TARJETA = f"""
    QFrame#card {{ background: #FFFFFF; border: 1px solid #D1D5DB; border-radius: 10px; }}
    QFrame#item {{ background: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 8px; }}
    QLabel {{ color: {GRIS_TEXTO}; font-family: 'Segoe UI'; font-size: 12px; }}
    QLabel#title {{ font-weight: bold; color: {AZUL}; font-size: 13px; }}
    QLabel#why {{ color: {GRIS_SUAVE}; font-size: 11px; }}
    QLabel#cat {{ color: {AZUL}; font-weight: bold; font-size: 11px; }}
    QLabel#hint {{ color: {VERDE}; font-weight: bold; }}
    QScrollArea {{ background: transparent; border: none; }}
    QWidget#list {{ background: transparent; }}
    QPushButton {{ padding: 4px 10px; border: none; border-radius: 6px;
                  font-family: 'Segoe UI'; font-size: 12px; }}
    QPushButton#sug {{ background: {VERDE_FONDO}; color: {VERDE}; font-weight: bold; }}
    QPushButton#sug:hover {{ background: #BBF7D0; }}
    QPushButton#all {{ background: {AZUL_CLARO}; color: white; font-weight: bold; }}
    QPushButton#all:hover {{ background: #1D4ED8; }}
    QPushButton#close, QPushButton#learn {{ background: #F3F4F6; color: #374151; }}
    QPushButton#close:hover, QPushButton#learn:hover {{ background: #E5E7EB; }}
"""

AVISO = ("background:#111827; color:#F9FAFB; border-radius:8px; padding:8px 10px;"
         "font-family:'Segoe UI'; font-size:12px;")

RESALTADO = (f"background:{ROJO_FONDO}; color:{ROJO}; "
             "text-decoration:line-through; font-weight:bold;")

AMBAR_FONDO = "#FFFBEB"
AMBAR_BORDE = "#FDE68A"
AMBAR_TEXTO = "#92400E"
AZUL_SUAVE = "#EEF2FF"

BOTON_AYUDA = f"""
    QPushButton#help {{ background: {AZUL_SUAVE}; color: {AZUL}; font-weight: bold;
                       border-radius: 11px; padding: 0px; font-size: 13px;
                       min-width: 22px; max-width: 22px; min-height: 22px; max-height: 22px; }}
    QPushButton#help:hover {{ background: #C7D2FE; }}
"""

AYUDA = f"""
    QWidget#ayuda {{ background: #FFFFFF; }}
    QLabel {{ color: {GRIS_TEXTO}; font-family: 'Segoe UI'; font-size: 13px; }}
    QFrame#cabecera {{ background: {AZUL}; }}
    QLabel#titulo {{ color: #FFFFFF; font-size: 20px; font-weight: bold; }}
    QLabel#lema {{ color: #C7D2FE; font-size: 12px; }}
    QFrame#barra {{ background: #F3F4F6; border-bottom: 1px solid #E5E7EB; }}
    QPushButton#pestana {{ background: transparent; color: {GRIS_SUAVE}; border: none;
                          border-radius: 15px; padding: 0px 14px;
                          min-height: 30px; max-height: 30px;
                          font-family: 'Segoe UI'; font-size: 12px; font-weight: bold; }}
    QPushButton#pestana:hover {{ background: #E5E7EB; }}
    QPushButton#pestana:checked {{ background: {AZUL}; color: #FFFFFF; }}
    QScrollArea {{ background: #FFFFFF; border: none; }}
    QWidget#pagina {{ background: #FFFFFF; }}
    QFrame#paso {{ background: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 10px; }}
    QLabel#numero {{ background: {AZUL}; color: #FFFFFF; font-size: 16px; font-weight: bold;
                    border-radius: 18px; }}
    QLabel#paso_titulo {{ font-size: 14px; font-weight: bold; color: {GRIS_TEXTO}; }}
    QLabel#paso_texto {{ color: {GRIS_SUAVE}; font-size: 12px; }}
    QLabel#tecla {{ background: #FFFFFF; color: {GRIS_TEXTO}; border: 1px solid #D1D5DB;
                   border-bottom: 2px solid #9CA3AF; border-radius: 5px;
                   padding: 2px 8px; font-size: 12px; font-weight: bold; }}
    QLabel#mas {{ color: {GRIS_SUAVE}; font-weight: bold; }}
    QFrame#consejo {{ background: {AMBAR_FONDO}; border: 1px solid {AMBAR_BORDE};
                     border-radius: 10px; }}
    QLabel#consejo_titulo {{ color: {AMBAR_TEXTO}; font-weight: bold; font-size: 12px; }}
    QLabel#consejo_texto {{ color: {AMBAR_TEXTO}; font-size: 12px; }}
    QFrame#fila {{ background: #FFFFFF; border: none; border-bottom: 1px solid #E5E7EB; }}
    QLabel#categoria {{ color: {AZUL}; font-weight: bold; font-size: 12px; }}
    QLabel#accion {{ font-size: 13px; }}
    QLabel#raton {{ color: {GRIS_SUAVE}; font-size: 12px; }}
    QLabel#pregunta {{ font-weight: bold; font-size: 13px; }}
    QLabel#respuesta {{ color: {GRIS_SUAVE}; font-size: 12px; }}
    QLabel#seccion {{ color: {AZUL}; font-size: 13px; font-weight: bold; }}
    QFrame#pie {{ background: #F9FAFB; border-top: 1px solid #E5E7EB; }}
    QLabel#pie_texto {{ color: {GRIS_SUAVE}; font-size: 11px; }}
    QPushButton#primario {{ background: {AZUL_CLARO}; color: #FFFFFF; font-weight: bold;
                           border: none; border-radius: 8px; padding: 8px 22px;
                           font-family: 'Segoe UI'; font-size: 13px; }}
    QPushButton#primario:hover {{ background: #1D4ED8; }}
    QPushButton#secundario {{ background: #FFFFFF; color: #374151; border: 1px solid #D1D5DB;
                             border-radius: 8px; padding: 7px 16px;
                             font-family: 'Segoe UI'; font-size: 13px; }}
    QPushButton#secundario:hover {{ background: #F3F4F6; }}
"""

MAL = f"background:{ROJO_FONDO}; color:{ROJO}; text-decoration:line-through;"
BIEN = f"background:{VERDE_FONDO}; color:{VERDE}; font-weight:bold;"
