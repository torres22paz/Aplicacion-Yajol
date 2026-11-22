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

    def __init__(self):
        super().__init__()
        self.setWindowFlags(FLOTANTE)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setStyleSheet(estilos.TARJETA)
        self._hallazgos = []

        fuera = QVBoxLayout(self)
        tarjeta = QFrame(objectName="card")
        fuera.addWidget(tarjeta)
        raiz = QVBoxLayout(tarjeta)
        raiz.setContentsMargins(10, 8, 10, 8)
        raiz.setSpacing(6)
        self.titulo = QLabel("Revisión", objectName="title")
        raiz.addWidget(self.titulo)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.lista = QWidget(objectName="list")
        self.lista_layout = QVBoxLayout(self.lista)
        self.lista_layout.setContentsMargins(0, 0, 0, 0)
        self.lista_layout.setSpacing(6)
        self.scroll.setWidget(self.lista)
        self.scroll.setMaximumHeight(430)
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
            self.lista_layout.addWidget(QLabel("No encontré errores en las últimas palabras."))
        else:
            plural = "es" if len(hallazgos) != 1 else ""
            self.titulo.setText(f"Se encontr{'aron' if len(hallazgos) != 1 else 'ó'} "
                                f"{len(hallazgos)} posible{plural} error{plural}")
            for hallazgo in hallazgos[:config.MAX_TARJETAS]:
                self.lista_layout.addWidget(self._tarjeta(texto, hallazgo))
            if len(hallazgos) > config.MAX_TARJETAS:
                restantes = len(hallazgos) - config.MAX_TARJETAS
                self.lista_layout.addWidget(QLabel(f"… y {restantes} más"))

        self.lista_layout.addStretch()
        self.boton_todo.setText(f"Corregir todo ({len(arreglables)})")
        self.boton_todo.setVisible(len(arreglables) > 1)
        self.setFixedWidth(420)
        self.adjustSize()
        self.move(posicion)
        self.show()

    def _elige(self, hallazgo, sugerencia):
        self.hide()
        self.arreglo_elegido.emit(hallazgo, sugerencia)

    def _todo(self):
        self.hide()
        self.arreglar_todo.emit([h for h in self._hallazgos if h.sugerencias])
