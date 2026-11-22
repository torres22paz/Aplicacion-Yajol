"""Aplicación: une el icono flotante, el corrector y el teclado."""
import ctypes
import logging
import os
import sys
import threading
import traceback

from PySide6.QtCore import QObject, QPoint, QTimer, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from . import config
from .interfaz.aviso import Aviso
from .interfaz.icono import IconoFlotante, pixmap_logo
from .interfaz.popup import PanelSugerencias
from .nucleo.corrector import Corrector
from .nucleo.texto import aplica_cambios, mensaje_aviso
from .sistema import inicio, teclado

log = logging.getLogger("yajol")


def avisa_error(texto: str):
    """Ventana de error visible aunque no haya consola."""
    try:
        ctypes.windll.user32.MessageBoxW(0, texto, "Corrector YAJOL", 0x10)
    except Exception:
        print(texto, file=sys.stderr)


class Puente(QObject):
    """Lleva los resultados de los hilos secundarios al hilo de la ventana."""
    resultado = Signal(str, list, bool)
    error = Signal(str)
    listo = Signal()
    aviso_gramatica = Signal(str)
    fatal = Signal(str)
    alternar = Signal()
    revisar = Signal()


class Aplicacion:
    def __init__(self, qt: QApplication, fabrica=None):
        self.qt = qt
        self.corrector = None
        self.contexto = ""
        self.habia_seleccion = False
        self.atajos = []
        self.bandeja = None
        self.accion_ocultar = None
        self.accion_inicio = None
        self._fabrica = fabrica or (lambda: Corrector())

        self.icono = IconoFlotante()
        self.panel = PanelSugerencias()
        self.aviso = Aviso()
        self.puente = Puente()
        self._conecta()
        self._coloca_icono()

        self.icono.marca_ocupado(True)
        self.icono.setToolTip("Cargando diccionarios…")
        self.icono.show()

        self._crea_bandeja()
        self._registra_atajos()
        qt.aboutToQuit.connect(self.cierra)
        threading.Thread(target=self._carga, daemon=True).start()

    # ---- Preparación ----
    def _coloca_icono(self):
        pantalla = self.qt.primaryScreen().availableGeometry()
        self.icono.move(pantalla.right() - config.TAM_ICONO - config.MARGEN_ICONO[0],
                        pantalla.bottom() - config.TAM_ICONO - config.MARGEN_ICONO[1])

    def _conecta(self):
        p = self.puente
        p.resultado.connect(self.muestra_resultado)
        p.error.connect(self.muestra_error)
        p.listo.connect(self.al_estar_listo)
        p.aviso_gramatica.connect(self.al_cargar_gramatica)
        p.fatal.connect(self.al_fallar)
        p.alternar.connect(self.alterna_icono)
        p.revisar.connect(self.revisa)
        self.icono.pulsado.connect(self.revisa)
        self.icono.alternar_pedido.connect(self.alterna_icono)
        self.icono.salir_pedido.connect(self.qt.quit)
        self.panel.arreglo_elegido.connect(self.aplica_uno)
        self.panel.arreglar_todo.connect(self.aplica_todos)
        self.panel.aprender_palabra.connect(self.aprende)

    def _crea_bandeja(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self.bandeja = QSystemTrayIcon(QIcon(pixmap_logo(64)), self.qt)
        menu = QMenu()
        menu.addAction("Revisar ahora", self.revisa)
        self.accion_ocultar = menu.addAction("Ocultar icono", self.alterna_icono)
        menu.addSeparator()
        self.accion_inicio = menu.addAction("Iniciar con Windows", self.alterna_inicio)
        self.accion_inicio.setCheckable(True)
        self.accion_inicio.setChecked(inicio.esta_activado())
        menu.addSeparator()
        menu.addAction("Salir", self.qt.quit)
        self.bandeja.setContextMenu(menu)
        self.bandeja.setToolTip("Corrector YAJOL — cargando…")
        self.bandeja.activated.connect(
            lambda razon: self.revisa() if razon == QSystemTrayIcon.Trigger else None)
        self.bandeja.show()

    def _registra_atajos(self):
        try:
            from pynput.keyboard import GlobalHotKeys
            oyente = GlobalHotKeys({
                config.ATAJO_MOSTRAR: self.puente.alternar.emit,
                config.ATAJO_REVISAR: self.puente.revisar.emit,
            })
            oyente.daemon = True
            oyente.start()
            self.atajos.append(oyente)
        except Exception:
            log.warning("No se pudieron registrar los atajos:\n%s", traceback.format_exc())

    def _carga(self):
        try:
            self.corrector = self._fabrica()
            self.puente.listo.emit()
            self.puente.aviso_gramatica.emit(self.corrector.carga_gramatica())
        except Exception:
            mensaje = traceback.format_exc()
            log.error(mensaje)
            self.puente.fatal.emit(mensaje)

    # ---- Estados ----
    def al_estar_listo(self):
        self.icono.marca_ocupado(False)
        total = self.corrector.lexico.total_palabras if self.corrector else 0
        self.icono.setToolTip("Revisar lo escrito")
        if self.bandeja:
            self.bandeja.setToolTip(f"Corrector YAJOL — listo ({total:,} palabras)".replace(",", " "))

    def al_cargar_gramatica(self, aviso: str):
        if aviso and self.bandeja:
            self.bandeja.showMessage("Corrector YAJOL", aviso, QSystemTrayIcon.Information, 7000)

    def al_fallar(self, mensaje: str):
        self.icono.setToolTip("Error al cargar")
        avisa_error("No se pudo iniciar el corrector.\n\n" + mensaje[-900:]
                    + f"\n\nDetalle en: {config.LOG_PATH}")

    def alterna_icono(self):
        if self.icono.isVisible():
            self.icono.hide()
            self.panel.hide()
            self.aviso.hide()
            texto = "Mostrar icono"
        else:
            self.icono.show()
            texto = "Ocultar icono"
        if self.accion_ocultar:
            self.accion_ocultar.setText(texto)

    def alterna_inicio(self):
        activo = inicio.alterna()
        if self.accion_inicio:
            self.accion_inicio.setChecked(activo)
        if self.bandeja:
            self.bandeja.showMessage(
                "Corrector YAJOL",
                "Se abrirá solo al encender el equipo." if activo
                else "Ya no se abrirá al encender el equipo.",
                QSystemTrayIcon.Information, 4000)

    # ---- Revisión ----
    def revisa(self):
        if self.icono.ocupado:
            return
        if self.corrector is None:
            if self.bandeja:
                self.bandeja.showMessage("Corrector YAJOL", "Todavía estoy cargando…")
            return
        self.icono.marca_ocupado(True)
        threading.Thread(target=self._trabaja, daemon=True).start()

    def _trabaja(self):
        try:
            texto, habia_seleccion = teclado.lee_contexto()
            self.puente.resultado.emit(texto, self.corrector.analiza(texto), habia_seleccion)
        except Exception:
            mensaje = traceback.format_exc()
            log.error(mensaje)
            self.puente.error.emit(mensaje)

    def muestra_resultado(self, texto: str, hallazgos: list, habia_seleccion: bool):
        self.icono.marca_ocupado(False)
        self.contexto = texto
        self.habia_seleccion = habia_seleccion
        pantalla = self.qt.primaryScreen().availableGeometry()
        posicion = self.icono.pos() + QPoint(-380, -config.TAM_ICONO * 4)
        posicion.setX(max(pantalla.left(), min(posicion.x(), pantalla.right() - 430)))
        posicion.setY(max(pantalla.top(), posicion.y()))
        self.panel.muestra(texto, hallazgos, posicion)

    def muestra_error(self, _mensaje: str):
        self.icono.marca_ocupado(False)
        if self.bandeja:
            self.bandeja.showMessage("No pude leer el texto",
                                     "Coloca el cursor donde escribiste y vuelve a intentarlo.",
                                     QSystemTrayIcon.Warning, 6000)

    # ---- Aplicar correcciones ----
    def aplica_uno(self, hallazgo, reemplazo: str):
        self._aplica([(hallazgo.inicio, hallazgo.fin, reemplazo, hallazgo.categoria)])

    def aplica_todos(self, hallazgos):
        self._aplica([(h.inicio, h.fin, h.sugerencias[0], h.categoria)
                      for h in hallazgos if h.sugerencias])

    def _aplica(self, cambios: list):
        if not cambios or not self.contexto:
            return
        simples = [(i, f, r) for i, f, r, _ in cambios]
        texto_nuevo, aplicados = aplica_cambios(self.contexto, simples)
        if not aplicados:
            return
        categorias = {(i, f): c for i, f, _, c in cambios}
        pares = [(self.contexto[i:f], r, categorias[(i, f)]) for i, f, r in aplicados]
        teclado.reemplaza_seleccion(texto_nuevo)
        QTimer.singleShot(250, lambda: self.aviso.muestra_cerca(
            mensaje_aviso(pares), self.icono.pos()))
        self.contexto = ""

    def aprende(self, palabra: str):
        if self.corrector and self.corrector.aprende(palabra):
            self.panel.hide()
            self.aviso.muestra_cerca(f"«{palabra}» añadida a tu diccionario.",
                                     self.icono.pos(), 3000)

    def cierra(self):
        for oyente in self.atajos:
            try:
                oyente.stop()
            except Exception:
                pass
        if self.corrector:
            self.corrector.cierra()


def main(argv=None) -> int:
    os.makedirs(os.path.dirname(config.LOG_PATH) or ".", exist_ok=True)
    logging.basicConfig(filename=config.LOG_PATH, level=logging.INFO, encoding="utf-8",
                        format="%(asctime)s %(levelname)s %(message)s")
    try:
        qt = QApplication(argv if argv is not None else sys.argv)
        qt.setQuitOnLastWindowClosed(False)
        qt.setApplicationName("Corrector YAJOL")
        Aplicacion(qt)
        return qt.exec()
    except Exception:
        log.exception("Error fatal")
        avisa_error("No se pudo iniciar el corrector.\n\n"
                    + traceback.format_exc()[-900:]
                    + f"\n\nDetalle en: {config.LOG_PATH}")
        return 1
