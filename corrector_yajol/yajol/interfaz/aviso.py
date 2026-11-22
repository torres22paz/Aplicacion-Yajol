"""Aviso breve que aparece junto al icono tras corregir."""
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QLabel

from .. import config
from . import estilos
from .icono import FLOTANTE


class Aviso(QLabel):
    def __init__(self):
        super().__init__(None, FLOTANTE)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setWordWrap(True)
        self.setFixedWidth(320)
        self.setStyleSheet(estilos.AVISO)
        self._temporizador = QTimer(self, singleShot=True)
        self._temporizador.timeout.connect(self.hide)

    def muestra_cerca(self, texto: str, ancla, ms: int = None):
        if not texto:
            return
        self.setText(texto)
        self.adjustSize()
        self.move(max(0, ancla.x() + config.TAM_ICONO - self.width()),
                  max(0, ancla.y() - self.height() - 8))
        self.show()
        self._temporizador.start(ms or config.AVISO_MS)
