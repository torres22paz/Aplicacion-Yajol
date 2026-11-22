"""Recuadro con los errores encontrados y sus sugerencias."""
import html

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QPushButton,
                               QScrollArea, QVBoxLayout, QWidget)

from .. import config
from ..nucleo.texto import fragmento
from . import estilos
from .icono import FLOTANTE


def fragmento_html(texto: str, inicio: int, fin: int) -> str:
    """Trozo de texto con el error resaltado. El texto del usuario se escapa."""
    p = fragmento(texto, inicio, fin)
    return ("{pre}{antes}<span style='{estilo}'>{error}</span>{despues}{post}").format(
        pre="… " if p["corte_izq"] else "",
        antes=html.escape(p["antes"]),
        estilo=estilos.RESALTADO,
        error=html.escape(p["error"]),
        despues=html.escape(p["despues"]),
        post=" …" if p["corte_der"] else "")


class PanelSugerencias(QWidget):
    """Lista de tarjetas: una por error, con el motivo y los botones de arreglo."""
    arreglo_elegido = Signal(object, str)
    arreglar_todo = Signal(object)
    aprender_palabra = Signal(str)
    ayuda_pedida = Signal()

    ANCHO = 430
    ALTO_MAXIMO = 420

    def __init__(self):
        super().__init__()
        self.setWindowFlags(FLOTANTE)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setStyleSheet(estilos.TARJETA + estilos.BOTON_AYUDA)
        self._hallazgos = []

        fuera = QVBoxLayout(self)
        tarjeta = QFrame(objectName="card")
        fuera.addWidget(tarjeta)
        raiz = QVBoxLayout(tarjeta)
        raiz.setContentsMargins(10, 8, 10, 8)
        raiz.setSpacing(6)
        cabecera = QHBoxLayout()
        self.titulo = QLabel("Revisión", objectName="title")
        self.boton_ayuda = QPushButton("?", objectName="help")
        self.boton_ayuda.setToolTip("¿Cómo funciona el corrector?")
        self.boton_ayuda.setCursor(Qt.PointingHandCursor)
        self.boton_ayuda.clicked.connect(self.ayuda_pedida.emit)
        cabecera.addWidget(self.titulo, 1)
        cabecera.addWidget(self.boton_ayuda)
        raiz.addLayout(cabecera)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.lista = QWidget(objectName="list")
        self.lista_layout = QVBoxLayout(self.lista)
        self.lista_layout.setContentsMargins(0, 0, 0, 0)
        self.lista_layout.setSpacing(6)
        self.scroll.setWidget(self.lista)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        raiz.addWidget(self.scroll)

        pie = QHBoxLayout()
        self.boton_todo = QPushButton("", objectName="all")
        self.boton_todo.clicked.connect(self._todo)
        cerrar = QPushButton("Cerrar", objectName="close")
        cerrar.clicked.connect(self.hide)
        pie.addWidget(self.boton_todo)
        pie.addStretch()
        pie.addWidget(cerrar)
        raiz.addLayout(pie)

    # ---- Construcción de tarjetas ----
    def _tarjeta(self, texto: str, hallazgo) -> QFrame:
        marco = QFrame(objectName="item")
        caja = QVBoxLayout(marco)
        caja.setContentsMargins(8, 6, 8, 6)
        caja.setSpacing(3)

        contexto = QLabel(fragmento_html(texto, hallazgo.inicio, hallazgo.fin))
        contexto.setTextFormat(Qt.RichText)
        contexto.setWordWrap(True)
        porque = QLabel("<b>Por qué:</b> " + html.escape(hallazgo.explicacion), objectName="why")
        porque.setTextFormat(Qt.RichText)
        porque.setWordWrap(True)

        caja.addWidget(QLabel(html.escape(hallazgo.categoria), objectName="cat"))
        caja.addWidget(contexto)
        caja.addWidget(porque)

        fila = QHBoxLayout()
        if hallazgo.sugerencias:
            fila.addWidget(QLabel("Cambiar por:", objectName="hint"))
            for sugerencia in hallazgo.sugerencias[:3]:
                boton = QPushButton(sugerencia, objectName="sug")
                boton.clicked.connect(
                    lambda _=False, h=hallazgo, s=sugerencia: self._elige(h, s))
                fila.addWidget(boton)
        if hallazgo.regla in ("desconocida", "diccionario"):
            aprender = QPushButton("Aprender palabra", objectName="learn")
            aprender.setToolTip("Guarda esta palabra para no volver a marcarla")
            aprender.clicked.connect(
                lambda _=False, p=hallazgo.original: self.aprender_palabra.emit(p))
            fila.addWidget(aprender)
        fila.addStretch()
        caja.addLayout(fila)
        return marco

    def muestra(self, texto, hallazgos, posicion):
        while self.lista_layout.count():
            item = self.lista_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._hallazgos = list(hallazgos)
        arreglables = [h for h in hallazgos if h.sugerencias]

        if not hallazgos:
            self.titulo.setText("✓ Sin errores detectados")
            vacio = QLabel("No encontré errores en las últimas palabras.")
            vacio.setWordWrap(True)
            self.lista_layout.addWidget(vacio)
        else:
            if len(hallazgos) == 1:
                self.titulo.setText("Se encontró 1 posible error")
            else:
                self.titulo.setText(f"Se encontraron {len(hallazgos)} posibles errores")
            for hallazgo in hallazgos[:config.MAX_TARJETAS]:
                self.lista_layout.addWidget(self._tarjeta(texto, hallazgo))
            if len(hallazgos) > config.MAX_TARJETAS:
                restantes = len(hallazgos) - config.MAX_TARJETAS
                self.lista_layout.addWidget(QLabel(f"… y {restantes} más"))

        self.lista_layout.addStretch()
        self.boton_todo.setText(f"Corregir todo ({len(arreglables)})")
        self.boton_todo.setVisible(len(arreglables) > 1)
        self.setFixedWidth(self.ANCHO)
        self._ajusta_alto()
        self.adjustSize()
        self.move(posicion)
        self.show()

    def _ajusta_alto(self):
        """La lista ocupa lo que necesita, hasta un máximo; a partir de ahí hay barra."""
        ancho = self.ANCHO - 64                 # márgenes de la tarjeta y barra de desplazamiento
        # Las tarjetas recién añadidas a una ventana ya abierta nacen ocultas y
        # no cuentan para el tamaño hasta que se muestran.
        for i in range(self.lista_layout.count()):
            tarjeta = self.lista_layout.itemAt(i).widget()
            if tarjeta is not None:
                tarjeta.show()
        self.lista_layout.invalidate()
        self.lista_layout.activate()
        if self.lista_layout.hasHeightForWidth():
            alto = self.lista_layout.heightForWidth(ancho)
        else:
            alto = self.lista_layout.sizeHint().height()
        self.scroll.setFixedHeight(max(40, min(alto + 4, self.ALTO_MAXIMO)))

    def coloca_junto_a(self, ancla, pantalla):
        """Pone el recuadro encima del icono, sin salirse de la pantalla."""
        self.adjustSize()
        x = ancla.right() - self.width()
        y = ancla.top() - self.height() - 8
        if y < pantalla.top():                  # no cabe arriba: se pone al lado
            y = max(pantalla.top(), min(ancla.top(), pantalla.bottom() - self.height()))
            x = ancla.left() - self.width() - 8
            if x < pantalla.left():
                x = ancla.right() + 8
        x = max(pantalla.left(), min(x, pantalla.right() - self.width()))
        y = max(pantalla.top(), min(y, pantalla.bottom() - self.height()))
        self.move(x, y)

    def _elige(self, hallazgo, sugerencia):
        self.hide()
        self.arreglo_elegido.emit(hallazgo, sugerencia)

    def _todo(self):
        self.hide()
        self.arreglar_todo.emit([h for h in self._hallazgos if h.sugerencias])
