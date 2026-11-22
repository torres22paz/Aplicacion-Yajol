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
