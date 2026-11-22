"""Una sola copia del corrector a la vez.

Si el corrector ya está abierto y se vuelve a abrir (por ejemplo, el arranque
automático y un doble clic), la segunda copia le manda un mensaje a la primera
y se cierra. Así nunca hay dos iconos ni dos avisos.
"""
import getpass
import logging

from PySide6.QtCore import QObject, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket

log = logging.getLogger("yajol")

MENSAJES = ("mostrar", "ayuda", "salir")


def nombre_canal() -> str:
    try:
        usuario = getpass.getuser()
    except Exception:
        usuario = "usuario"
    limpio = "".join(c for c in usuario if c.isalnum()) or "usuario"
    return f"corrector_yajol_{limpio}"


def avisa_a_la_otra(mensaje: str = "mostrar", canal: str = None, espera_ms: int = 600) -> bool:
    """Manda un mensaje a la copia que ya está abierta. False si no hay ninguna."""
    enchufe = QLocalSocket()
    enchufe.connectToServer(canal or nombre_canal())
    if not enchufe.waitForConnected(espera_ms):
        return False
    enchufe.write(mensaje.encode("utf-8"))
    enchufe.waitForBytesWritten(espera_ms)
    enchufe.disconnectFromServer()
    return True


class Escucha(QObject):
    """La copia principal escucha lo que le piden las demás."""
    mensaje = Signal(str)

    def __init__(self, canal: str = None):
        super().__init__()
        self.canal = canal or nombre_canal()
        self.servidor = QLocalServer(self)
        self.servidor.newConnection.connect(self._atiende)

    def abre(self) -> bool:
        QLocalServer.removeServer(self.canal)        # limpia restos de un cierre brusco
        if not self.servidor.listen(self.canal):
            log.warning("No se pudo abrir el canal %s: %s", self.canal,
                        self.servidor.errorString())
            return False
        return True

    def _atiende(self):
        while self.servidor.hasPendingConnections():
            conexion = self.servidor.nextPendingConnection()
            if conexion.bytesAvailable() or conexion.waitForReadyRead(300):
                self._lee(conexion)
            else:
                conexion.readyRead.connect(lambda c=conexion: self._lee(c))
            conexion.disconnected.connect(conexion.deleteLater)

    def _lee(self, conexion):
        texto = bytes(conexion.readAll()).decode("utf-8", errors="replace").strip()
        if texto in MENSAJES:
            self.mensaje.emit(texto)

    def cierra(self):
        self.servidor.close()
