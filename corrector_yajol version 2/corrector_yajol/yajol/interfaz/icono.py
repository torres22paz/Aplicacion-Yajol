"""Icono flotante que se queda encima de todas las ventanas."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPixmap
from PySide6.QtWidgets import QMenu, QWidget

from .. import config

FLOTANTE = (Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
            | Qt.WindowDoesNotAcceptFocus)
_logo = None


def _imagen_logo() -> QImage:
    """Logotipo con el fondo blanco convertido en transparente."""
    global _logo
    if _logo is None:
        origen = QImage(config.LOGO_PATH)
        if origen.isNull():
            _logo = QImage(64, 64, QImage.Format_ARGB32)
            _logo.fill(QColor(30, 58, 138))
            return _logo
        _logo = QImage(origen.size(), QImage.Format_ARGB32)
        for y in range(origen.height()):
            for x in range(origen.width()):
                gris = origen.pixelColor(x, y).red()
                _logo.setPixelColor(x, y, QColor(0, 0, 0, 255 - gris))
    return _logo


def pixmap_logo(tam: int) -> QPixmap:
    return QPixmap.fromImage(_imagen_logo()).scaled(
        tam, tam, Qt.KeepAspectRatio, Qt.SmoothTransformation)


class IconoFlotante(QWidget):
    """Botón redondo que se puede arrastrar por la pantalla."""
    pulsado = Signal()
    alternar_pedido = Signal()
    salir_pedido = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(FLOTANTE)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setFixedSize(config.TAM_ICONO, config.TAM_ICONO)
        self.setToolTip("Revisar lo escrito  ·  clic derecho: opciones  ·  "
                        f"{config.ATAJO_REVISAR.replace('<', '').replace('>', '')} revisa")
        self._ocupado = False
        self._arrastre = None
        self._movido = False

    @property
    def ocupado(self) -> bool:
        return self._ocupado

    def marca_ocupado(self, ocupado: bool):
        self._ocupado = ocupado
        self.update()

    def paintEvent(self, _):
        pintor = QPainter(self)
        pintor.setRenderHint(QPainter.Antialiasing)
        pintor.setRenderHint(QPainter.SmoothPixmapTransform)
        pintor.setOpacity(0.45 if self._ocupado else 1.0)
        pintor.setPen(Qt.NoPen)
        pintor.setBrush(QColor("white"))
        pintor.drawEllipse(0, 0, config.TAM_ICONO, config.TAM_ICONO)
        pintor.drawPixmap(self.rect(), pixmap_logo(config.TAM_ICONO))
        pintor.end()

    def contextMenuEvent(self, evento):
        menu = QMenu(self)
        menu.addAction("Revisar ahora", self.pulsado.emit)
        menu.addAction("Ocultar icono", self.alternar_pedido.emit)
        menu.addSeparator()
        menu.addAction("Salir", self.salir_pedido.emit)
        menu.exec(evento.globalPos())

    def mousePressEvent(self, evento):
        if evento.button() == Qt.LeftButton:
            self._arrastre = evento.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._movido = False

    def mouseMoveEvent(self, evento):
        if self._arrastre is not None:
            nueva = evento.globalPosition().toPoint() - self._arrastre
            if (nueva - self.pos()).manhattanLength() > 3:
                self._movido = True
            self.move(nueva)

    def mouseReleaseEvent(self, _):
        if self._arrastre is not None and not self._movido:
            self.pulsado.emit()
        self._arrastre = None
