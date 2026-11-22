"""Aplicación: une el icono flotante, el corrector, la ayuda y el teclado."""
import ctypes
import logging
import os
import sys
import threading
import traceback

from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from . import config
from .interfaz.aviso import Aviso
from .interfaz.ayuda import VentanaAyuda, bienvenida_pendiente, marca_bienvenida_vista
from .interfaz.icono import IconoFlotante, pixmap_logo
from .interfaz.popup import PanelSugerencias
from .nucleo.corrector import Corrector
from .nucleo.texto import aplica_cambios, mensaje_aviso
from .sistema import inicio, instancia, teclado

log = logging.getLogger("yajol")

ARG_INICIO = inicio.ARGUMENTO_INICIO      # se abrió solo al encender el equipo
ARG_SALIR = "--salir"                     # cierra la copia que esté abierta
ARG_AYUDA = "--ayuda"                     # abre la ayuda


def avisa_error(texto: str):
    """Ventana de error visible aunque no haya consola."""
    try:
        ctypes.windll.user32.MessageBoxW(0, texto, "Corrector YAJOL", 0x10)
    except Exception:
        try:
            print(texto, file=sys.stderr)
        except Exception:
            pass


class Puente(QObject):
    """Lleva los resultados de los hilos secundarios al hilo de la ventana."""
    resultado = Signal(str, list, bool)
    error = Signal(str)
    listo = Signal()
    aviso_gramatica = Signal(str)
    fatal = Signal(str)
    alternar = Signal()
    revisar = Signal()
    arranque_revisado = Signal(dict)


class Aplicacion:
    def __init__(self, qt: QApplication, fabrica=None, silencioso: bool = False,
                 mostrar_bienvenida: bool = None, revisar_arranque: bool = True):
        """
        silencioso: True cuando se abre solo al encender el equipo. En ese modo
                    nunca se muestran ventanas de error: todo va al registro.
        """
        self.qt = qt
        self.silencioso = silencioso
        self.corrector = None
        self.contexto = ""
        self.habia_seleccion = False
        self.atajos = []
        self.bandeja = None
        self.accion_ocultar = None
        self.accion_inicio = None
        self._intentos_bandeja = 0
        self._revisar_arranque = revisar_arranque
        self._fabrica = fabrica or (lambda: Corrector())

        self.icono = IconoFlotante()
        self.panel = PanelSugerencias()
        self.aviso = Aviso()
        self.ayuda = VentanaAyuda()
        self.puente = Puente()
        self._conecta()
        self._coloca_icono()

        self.icono.marca_ocupado(True)
        self.icono.show()

        self._crea_bandeja()
        self._registra_atajos()
        qt.aboutToQuit.connect(self.cierra)
        threading.Thread(target=self._carga, daemon=True).start()

        if mostrar_bienvenida is None:
            mostrar_bienvenida = bienvenida_pendiente() and not silencioso
        if mostrar_bienvenida:
            QTimer.singleShot(600, self.muestra_bienvenida)

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
        p.revisar.connect(lambda: self.revisa(desde_atajo=True))
        p.arranque_revisado.connect(self.al_revisar_arranque)
        self.icono.pulsado.connect(self.revisa)
        self.icono.ayuda_pedida.connect(self.muestra_ayuda)
        self.icono.alternar_pedido.connect(self.alterna_icono)
        self.icono.salir_pedido.connect(self.qt.quit)
        self.panel.arreglo_elegido.connect(self.aplica_uno)
        self.panel.arreglar_todo.connect(self.aplica_todos)
        self.panel.aprender_palabra.connect(self.aprende)
        self.panel.ayuda_pedida.connect(self.muestra_ayuda)

    def _crea_bandeja(self):
        """Icono junto al reloj. Al encender el equipo puede tardar: se reintenta."""
        if self.bandeja is not None:
            return
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self._intentos_bandeja += 1
            if self._intentos_bandeja <= config.INTENTOS_BANDEJA:
                QTimer.singleShot(config.ESPERA_BANDEJA_MS, self._crea_bandeja)
            return
        self.bandeja = QSystemTrayIcon(QIcon(pixmap_logo(64)), self.qt)
        menu = QMenu()
        menu.addAction("Revisar ahora", self.revisa)
        menu.addAction("¿Cómo funciona?", self.muestra_ayuda)
        menu.addSeparator()
        self.accion_ocultar = menu.addAction(
            "Ocultar icono" if self.icono.isVisible() else "Mostrar icono", self.alterna_icono)
        self.accion_inicio = menu.addAction("Iniciar con Windows", self.alterna_inicio)
        self.accion_inicio.setCheckable(True)
        self.accion_inicio.setChecked(inicio.esta_activado())
        menu.addSeparator()
        menu.addAction("Salir", self.qt.quit)
        self._menu_bandeja = menu
        self.bandeja.setContextMenu(menu)
        self.bandeja.setToolTip("Corrector YAJOL — listo" if self.corrector
                                else "Corrector YAJOL — cargando…")
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
        if self._revisar_arranque:
            try:
                # quita arranques de versiones anteriores y repara el acceso directo
                self.puente.arranque_revisado.emit(inicio.repara())
            except Exception:
                log.warning("No se pudo revisar el arranque:\n%s", traceback.format_exc())

    # ---- Estados ----
    def al_estar_listo(self):
        self.icono.marca_ocupado(False)
        total = self.corrector.lexico.total_palabras if self.corrector else 0
        if self.bandeja:
            self.bandeja.setToolTip(f"Corrector YAJOL — listo ({total:,} palabras)".replace(",", " "))

    def al_cargar_gramatica(self, aviso: str):
        if aviso and self.bandeja and not self.silencioso:
            self.bandeja.showMessage("Corrector YAJOL", aviso, QSystemTrayIcon.Information, 7000)

    def al_fallar(self, mensaje: str):
        """No se pudo cargar el diccionario. Al encender el equipo no se molesta con ventanas."""
        self.icono.marca_ocupado(False)
        self.icono.setToolTip("No se pudo cargar el corrector. Clic derecho → Salir y vuelve a abrirlo.")
        if self.silencioso:
            return                      # ya quedó escrito en corrector.log
        avisa_error("No se pudo iniciar el corrector.\n\n" + mensaje[-900:]
                    + f"\n\nDetalle en: {config.LOG_PATH}")

    def al_revisar_arranque(self, informe: dict):
        if self.accion_inicio:
            self.accion_inicio.setChecked(bool(informe.get("activo")))
        quitados = informe.get("quitados") or []
        if quitados and self.bandeja:
            self.bandeja.showMessage(
                "Corrector YAJOL",
                "Quité el arranque de la versión anterior, que era el que mostraba "
                "un error al encender el equipo.", QSystemTrayIcon.Information, 8000)

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

    def muestra_icono(self):
        if not self.icono.isVisible():
            self.alterna_icono()
        self.aviso.muestra_cerca("El corrector ya está abierto.\nPulsa el pájaro para revisar "
                                 "o el signo ? para ver la ayuda.", self.icono.pos(), 4000)

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

    # ---- Ayuda ----
    def muestra_ayuda(self, pagina: int = 0):
        self.panel.hide()
        self.ayuda.muestra(pagina if isinstance(pagina, int) else 0)

    def muestra_bienvenida(self):
        """La primera vez que se abre el corrector se enseña cómo funciona."""
        self.muestra_ayuda(0)
        marca_bienvenida_vista()

    def atiende_mensaje(self, mensaje: str):
        """Otra copia del programa se abrió y pide algo a esta."""
        if mensaje == "salir":
            self.qt.quit()
        elif mensaje == "ayuda":
            self.muestra_ayuda()
        elif mensaje == "mostrar":
            self.muestra_icono()

    # ---- Revisión ----
    def revisa(self, desde_atajo: bool = False):
        if self.icono.ocupado:
            return
        if self.corrector is None:
            if self.bandeja:
                self.bandeja.showMessage("Corrector YAJOL", "Todavía estoy cargando…")
            return
        self.icono.marca_ocupado(True)
        threading.Thread(target=self._trabaja, args=(bool(desde_atajo),), daemon=True).start()

    def _trabaja(self, desde_atajo: bool = False):
        try:
            texto, habia_seleccion = teclado.lee_contexto(desde_atajo=desde_atajo)
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
        self.panel.muestra(texto, hallazgos, self.icono.pos())
        self.panel.coloca_junto_a(self.icono.geometry(), pantalla)

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
        self.atajos = []
        if self.bandeja:
            self.bandeja.hide()
        if self.corrector:
            self.corrector.cierra()


def _prepara_registro():
    """Abre corrector.log. Si la carpeta no deja escribir, sigue sin registro."""
    try:
        os.makedirs(os.path.dirname(config.LOG_PATH) or ".", exist_ok=True)
        # el registro no crece sin límite: al pasar de 500 KB se empieza de nuevo
        if os.path.exists(config.LOG_PATH) and os.path.getsize(config.LOG_PATH) > 500_000:
            os.replace(config.LOG_PATH, config.LOG_PATH + ".anterior")
        logging.basicConfig(filename=config.LOG_PATH, level=logging.INFO, encoding="utf-8",
                            format="%(asctime)s %(levelname)s %(message)s")
    except Exception:
        logging.basicConfig(level=logging.CRITICAL)


def main(argv=None) -> int:
    argv = list(sys.argv if argv is None else argv)
    silencioso = ARG_INICIO in argv
    _prepara_registro()
    try:
        qt = QApplication([a for a in argv if a not in (ARG_INICIO, ARG_SALIR, ARG_AYUDA)])
        qt.setQuitOnLastWindowClosed(False)
        qt.setApplicationName("Corrector YAJOL")

        # ---- Una sola copia a la vez ----
        if ARG_SALIR in argv:
            instancia.avisa_a_la_otra("salir")
            return 0
        pedido = "ayuda" if ARG_AYUDA in argv else "mostrar"
        if instancia.avisa_a_la_otra("mostrar" if silencioso else pedido):
            log.info("El corrector ya estaba abierto; esta copia se cierra.")
            return 0

        log.info("Corrector YAJOL abierto%s", " (arranque automático)" if silencioso else "")
        aplicacion = Aplicacion(qt, silencioso=silencioso)
        escucha = instancia.Escucha()
        escucha.mensaje.connect(aplicacion.atiende_mensaje)
        escucha.abre()
        if ARG_AYUDA in argv:
            QTimer.singleShot(400, aplicacion.muestra_ayuda)
        return qt.exec()
    except Exception:
        log.exception("Error fatal")
        if not silencioso:
            avisa_error("No se pudo iniciar el corrector.\n\n"
                        + traceback.format_exc()[-900:]
                        + f"\n\nDetalle en: {config.LOG_PATH}")
        return 1
