"""Ventana de ayuda: recuerda cómo funciona el corrector.

Se abre con el signo «?» del icono flotante, con el botón «?» del recuadro de
revisión, desde los menús y, sola, la primera vez que se usa el programa.
"""
import html
import os

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (QButtonGroup, QFrame, QHBoxLayout, QLabel, QPushButton,
                               QScrollArea, QStackedWidget, QVBoxLayout, QWidget)

from .. import config
from . import contenido_ayuda as C
from . import estilos
from .icono import pixmap_logo

PESTANAS = ["Cómo se usa", "Qué corrige", "Atajos", "Si algo falla"]


def bienvenida_pendiente(ruta: str = None) -> bool:
    """True si el usuario todavía no ha visto la ayuda (primera vez que abre el programa)."""
    return not os.path.exists(ruta or config.BIENVENIDA_VISTA)


def marca_bienvenida_vista(ruta: str = None) -> bool:
    ruta = ruta or config.BIENVENIDA_VISTA
    try:
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        with open(ruta, "w", encoding="utf-8") as f:
            f.write("La ayuda ya se mostró una vez. Borra este archivo para verla de nuevo al abrir.\n")
        return True
    except OSError:
        return False


def _logo_en_disco(tam: int) -> QPixmap:
    """El logotipo sobre un círculo blanco, para la cabecera azul."""
    lienzo = QPixmap(tam, tam)
    lienzo.fill(Qt.transparent)
    pintor = QPainter(lienzo)
    pintor.setRenderHint(QPainter.Antialiasing)
    pintor.setRenderHint(QPainter.SmoothPixmapTransform)
    pintor.setPen(Qt.NoPen)
    pintor.setBrush(QColor("white"))
    pintor.drawEllipse(0, 0, tam, tam)
    pintor.drawPixmap(0, 0, pixmap_logo(tam))
    pintor.end()
    return lienzo


def _fila_teclas(teclas: list) -> QHBoxLayout:
    """Dibuja un atajo como teclas: [Ctrl] + [Alt] + [C]."""
    fila = QHBoxLayout()
    fila.setSpacing(4)
    fila.setContentsMargins(0, 0, 0, 0)
    for n, tecla in enumerate(teclas):
        if n:
            fila.addWidget(QLabel("+", objectName="mas"))
        fila.addWidget(QLabel(tecla, objectName="tecla"))
    fila.addStretch()
    return fila


def _pagina() -> tuple:
    """Una página con barra de desplazamiento. Devuelve (área, layout del contenido)."""
    area = QScrollArea()
    area.setWidgetResizable(True)
    area.setFrameShape(QFrame.NoFrame)
    area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    dentro = QWidget(objectName="pagina")
    caja = QVBoxLayout(dentro)
    caja.setContentsMargins(22, 18, 22, 18)
    caja.setSpacing(10)
    area.setWidget(dentro)
    return area, caja


class VentanaAyuda(QWidget):
    """Guía rápida con cuatro pestañas."""
    cerrada = Signal()

    def __init__(self):
        super().__init__()
        self.setObjectName("ayuda")
        self.setWindowTitle("Corrector YAJOL — Ayuda")
        self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.WindowCloseButtonHint
                            | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(estilos.AYUDA)
        self.setFixedSize(600, 660)
        if os.path.exists(config.ICONO_PATH):
            self.setWindowIcon(QIcon(config.ICONO_PATH))

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(0)
        raiz.addWidget(self._cabecera())
        raiz.addWidget(self._barra_pestanas())

        self.paginas = QStackedWidget()
        for construye in (self._pagina_uso, self._pagina_corrige,
                          self._pagina_atajos, self._pagina_problemas):
            self.paginas.addWidget(construye())
        raiz.addWidget(self.paginas, 1)
        raiz.addWidget(self._pie())
        self.ve_a(0)

    # ---- Partes fijas ----
    def _cabecera(self) -> QFrame:
        marco = QFrame(objectName="cabecera")
        marco.setFixedHeight(92)
        fila = QHBoxLayout(marco)
        fila.setContentsMargins(22, 0, 22, 0)
        fila.setSpacing(16)
        logo = QLabel()
        logo.setPixmap(_logo_en_disco(60))
        logo.setFixedSize(60, 60)
        logo.setStyleSheet("background: transparent;")
        textos = QVBoxLayout()
        textos.setSpacing(2)
        textos.addStretch()
        textos.addWidget(QLabel(C.TITULO, objectName="titulo"))
        textos.addWidget(QLabel(C.LEMA, objectName="lema"))
        textos.addStretch()
        fila.addWidget(logo)
        fila.addLayout(textos, 1)
        return marco

    def _barra_pestanas(self) -> QFrame:
        marco = QFrame(objectName="barra")
        marco.setFixedHeight(48)
        fila = QHBoxLayout(marco)
        fila.setContentsMargins(18, 0, 18, 0)
        fila.setSpacing(6)
        self.grupo = QButtonGroup(self)
        self.grupo.setExclusive(True)
        self.botones = []
        for n, nombre in enumerate(PESTANAS):
            boton = QPushButton(nombre, objectName="pestana")
            boton.setCheckable(True)
            boton.setCursor(Qt.PointingHandCursor)
            boton.clicked.connect(lambda _=False, i=n: self.ve_a(i))
            self.grupo.addButton(boton, n)
            self.botones.append(boton)
            fila.addWidget(boton)
        fila.addStretch()
        return marco

    def _pie(self) -> QFrame:
        marco = QFrame(objectName="pie")
        marco.setFixedHeight(62)
        fila = QHBoxLayout(marco)
        fila.setContentsMargins(22, 0, 22, 0)
        fila.setSpacing(10)
        fila.addWidget(QLabel(C.PIE, objectName="pie_texto"), 1)
        self.boton_guia = QPushButton("Guía completa", objectName="secundario")
        self.boton_guia.setCursor(Qt.PointingHandCursor)
        self.boton_guia.setToolTip("Abre la guía con todos los detalles en el navegador")
        self.boton_guia.clicked.connect(self.abre_guia)
        self.boton_guia.setVisible(os.path.exists(config.GUIA_PATH))
        self.boton_cerrar = QPushButton("Entendido", objectName="primario")
        self.boton_cerrar.setCursor(Qt.PointingHandCursor)
        self.boton_cerrar.clicked.connect(self.close)
        fila.addWidget(self.boton_guia)
        fila.addWidget(self.boton_cerrar)
        return marco

    # ---- Páginas ----
    def _pagina_uso(self) -> QScrollArea:
        area, caja = _pagina()
        for numero, (titulo, texto, teclas) in enumerate(C.PASOS, 1):
            marco = QFrame(objectName="paso")
            fila = QHBoxLayout(marco)
            fila.setContentsMargins(14, 12, 14, 12)
            fila.setSpacing(14)
            circulo = QLabel(str(numero), objectName="numero")
            circulo.setFixedSize(36, 36)
            circulo.setAlignment(Qt.AlignCenter)
            fila.addWidget(circulo, 0, Qt.AlignTop)
            columna = QVBoxLayout()
            columna.setSpacing(4)
            columna.addWidget(QLabel(titulo, objectName="paso_titulo"))
            cuerpo = QLabel(texto, objectName="paso_texto")
            cuerpo.setWordWrap(True)
            columna.addWidget(cuerpo)
            if teclas:
                columna.addSpacing(2)
                columna.addLayout(_fila_teclas(teclas))
            fila.addLayout(columna, 1)
            caja.addWidget(marco)

        consejo = QFrame(objectName="consejo")
        dentro = QVBoxLayout(consejo)
        dentro.setContentsMargins(14, 10, 14, 10)
        dentro.setSpacing(4)
        dentro.addWidget(QLabel("Consejos", objectName="consejo_titulo"))
        for texto in C.CONSEJOS:
            linea = QLabel("•  " + texto, objectName="consejo_texto")
            linea.setWordWrap(True)
            dentro.addWidget(linea)
        caja.addWidget(consejo)
        caja.addStretch()
        return area

    def _pagina_corrige(self) -> QScrollArea:
        area, caja = _pagina()
        caja.setSpacing(0)
        intro = QLabel("Cada corrección viene con la regla de ortografía que la explica.",
                       objectName="paso_texto")
        intro.setWordWrap(True)
        caja.addWidget(intro)
        caja.addSpacing(8)
        for categoria, pares in C.EJEMPLOS:
            marco = QFrame(objectName="fila")
            fila = QHBoxLayout(marco)
            fila.setContentsMargins(0, 9, 0, 9)
            fila.setSpacing(12)
            nombre = QLabel(categoria, objectName="categoria")
            nombre.setFixedWidth(148)
            fila.addWidget(nombre, 0, Qt.AlignTop)
            trozos = []
            for mal, bien in pares:
                # espacios duros: cada pareja «mal → bien» se mantiene en la misma línea
                mal_html = html.escape(mal).replace(" ", "&nbsp;")
                bien_html = html.escape(bien).replace(" ", "&nbsp;")
                trozos.append(
                    f"<span style='{estilos.MAL}'>&nbsp;{mal_html}&nbsp;</span>"
                    f"&nbsp;→&nbsp;"
                    f"<span style='{estilos.BIEN}'>&nbsp;{bien_html}&nbsp;</span>")
            ejemplos = QLabel(" &nbsp;&nbsp; ".join(trozos))
            ejemplos.setTextFormat(Qt.RichText)
            ejemplos.setWordWrap(True)
            fila.addWidget(ejemplos, 1)
            caja.addWidget(marco)
        caja.addStretch()
        return area

    def _pagina_atajos(self) -> QScrollArea:
        area, caja = _pagina()
        caja.setSpacing(0)
        for accion, teclas, raton in C.ATAJOS:
            marco = QFrame(objectName="fila")
            fila = QHBoxLayout(marco)
            fila.setContentsMargins(0, 11, 0, 11)
            fila.setSpacing(12)
            nombre = QLabel(accion, objectName="accion")
            nombre.setFixedWidth(210)
            fila.addWidget(nombre)
            columna = QVBoxLayout()
            columna.setSpacing(4)
            if teclas:
                columna.addLayout(_fila_teclas(teclas))
            columna.addWidget(QLabel(raton, objectName="raton"))
            fila.addLayout(columna, 1)
            caja.addWidget(marco)
        caja.addStretch()
        return area

    def _pagina_problemas(self) -> QScrollArea:
        area, caja = _pagina()
        caja.setSpacing(0)
        for pregunta, respuesta in C.PROBLEMAS:
            marco = QFrame(objectName="fila")
            columna = QVBoxLayout(marco)
            columna.setContentsMargins(0, 10, 0, 10)
            columna.setSpacing(3)
            columna.addWidget(QLabel(pregunta, objectName="pregunta"))
            texto = QLabel(respuesta, objectName="respuesta")
            texto.setWordWrap(True)
            columna.addWidget(texto)
            caja.addWidget(marco)
        caja.addStretch()
        return area

    # ---- Comportamiento ----
    def ve_a(self, indice: int):
        indice = max(0, min(indice, self.paginas.count() - 1))
        self.paginas.setCurrentIndex(indice)
        self.botones[indice].setChecked(True)

    def muestra(self, pagina: int = 0):
        """Abre la ayuda centrada en la pantalla y la trae al frente."""
        self.ve_a(pagina)
        pantalla = self.screen().availableGeometry() if self.screen() else None
        if pantalla is not None:
            self.move(pantalla.center().x() - self.width() // 2,
                      max(pantalla.top(), pantalla.center().y() - self.height() // 2))
        self.show()
        self.raise_()
        self.activateWindow()

    def abre_guia(self) -> bool:
        if not os.path.exists(config.GUIA_PATH):
            return False
        return QDesktopServices.openUrl(QUrl.fromLocalFile(config.GUIA_PATH))

    def closeEvent(self, evento):
        self.cerrada.emit()
        super().closeEvent(evento)
