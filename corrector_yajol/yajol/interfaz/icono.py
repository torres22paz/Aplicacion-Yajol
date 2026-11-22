"""Icono flotante que se queda encima de todas las ventanas."""
from PySide6.QtCore import QRect, Qt, Signal
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPen, QPixmap
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
    ayuda_pedida = Signal()
    alternar_pedido = Signal()
    salir_pedido = Signal()

    TAM_AYUDA = 22          # diámetro del botón «?»

    def __init__(self):
        super().__init__()
        self.setWindowFlags(FLOTANTE)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setFixedSize(config.TAM_ICONO, config.TAM_ICONO)
        self.setToolTip("Revisar lo escrito  ·  ? ayuda  ·  clic derecho: opciones")
        self.setMouseTracking(True)
        self._ocupado = False
        self._sobre_ayuda = False
        self._en_ayuda = False
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
        self._pinta_ayuda(pintor)
        pintor.end()

    # ---- Botón «?» ----
    def zona_ayuda(self) -> QRect:
        """El círculo del signo «?», en la esquina superior derecha del icono."""
        return QRect(config.TAM_ICONO - self.TAM_AYUDA, 0, self.TAM_AYUDA, self.TAM_AYUDA)

    def _pinta_ayuda(self, pintor: QPainter):
        zona = self.zona_ayuda().adjusted(1, 1, -1, -1)
        pintor.setOpacity(1.0)
        pintor.setPen(QPen(QColor("white"), 2))
        pintor.setBrush(QColor("#1D4ED8" if self._sobre_ayuda else "#2563EB"))
        pintor.drawEllipse(zona)
        fuente = QFont("Segoe UI")
        fuente.setPixelSize(14)
        fuente.setBold(True)
        pintor.setFont(fuente)
        pintor.setPen(QColor("white"))
        pintor.drawText(zona, Qt.AlignCenter, "?")

    def contextMenuEvent(self, evento):
        menu = QMenu(self)
        menu.addAction("Revisar ahora", self.pulsado.emit)
        menu.addAction("¿Cómo funciona?", self.ayuda_pedida.emit)
        menu.addSeparator()
        menu.addAction("Ocultar icono", self.alternar_pedido.emit)
        menu.addSeparator()
        menu.addAction("Salir", self.salir_pedido.emit)
        menu.exec(evento.globalPos())

    def mousePressEvent(self, evento):
        if evento.button() == Qt.LeftButton:
            self._arrastre = evento.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._movido = False
            self._en_ayuda = self.zona_ayuda().contains(evento.position().toPoint())

    def mouseMoveEvent(self, evento):
        sobre = self.zona_ayuda().contains(evento.position().toPoint())
        if sobre != self._sobre_ayuda:
            self._sobre_ayuda = sobre
            self.setToolTip("¿Cómo funciona? Abre la ayuda" if sobre
                            else "Revisar lo escrito  ·  ? ayuda  ·  clic derecho: opciones")
            self.update()
        if self._arrastre is not None:
            nueva = evento.globalPosition().toPoint() - self._arrastre
            if (nueva - self.pos()).manhattanLength() > 3:
                self._movido = True
            self.move(nueva)

    def mouseReleaseEvent(self, _):
        if self._arrastre is not None and not self._movido:
            if self._en_ayuda:
                self.ayuda_pedida.emit()
            else:
                self.pulsado.emit()
        self._arrastre = None

    def leaveEvent(self, _):
        if self._sobre_ayuda:
            self._sobre_ayuda = False
            self.update()
