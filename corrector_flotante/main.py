"""Corrector flotante para Windows: icono en pantalla que revisa lo escrito en cualquier programa."""
import ctypes
import logging
import os
import sys
import threading
import time
import traceback

from PySide6.QtCore import QObject, QPoint, QTimer, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

import motor
from ventanas import FloatingIcon, SuggestionPopup, Toast

LOG_PATH = os.path.join(motor.BASE_DIR, "corrector.log")
log = logging.getLogger("corrector")


def avisar(texto: str):
    """Ventana visible de error (funciona con pythonw, sin consola)."""
    try:
        ctypes.windll.user32.MessageBoxW(0, texto, "Corrector flotante", 0x10)
    except Exception:
        print(texto)


# ---- Teclado y portapapeles (pynput y pyperclip) ----
_kb = None


def _teclado():
    global _kb
    if _kb is None:
        from pynput.keyboard import Controller
        _kb = Controller()
    return _kb


def _pulsa(tecla):
    kb = _teclado()
    kb.press(tecla)
    kb.release(tecla)
    time.sleep(motor.KEY_DELAY)


def _combo(modificador, tecla):
    with _teclado().pressed(modificador):
        _pulsa(tecla)


def read_context(n_words: int) -> str:
    """Selecciona las palabras antes del cursor, las copia y restaura el portapapeles."""
    import pyperclip
    from pynput.keyboard import Key
    anterior = pyperclip.paste()
    pyperclip.copy("")
    with _teclado().pressed(Key.shift, Key.ctrl):
        for _ in range(n_words):
            _pulsa(Key.left)
    _combo(Key.ctrl, "c")
    time.sleep(0.12)
    texto = pyperclip.paste()
    pyperclip.copy(anterior)
    return texto


def replace_selection(new_text: str):
    """Pega el texto corregido sobre la selección activa."""
    import pyperclip
    from pynput.keyboard import Key
    anterior = pyperclip.paste()
    pyperclip.copy(new_text)
    time.sleep(0.05)
    _combo(Key.ctrl, "v")
    time.sleep(0.2)
    pyperclip.copy(anterior)


# ---- Aplicación ----
def make_app_icon() -> QIcon:
    pm = QPixmap(64, 64)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#2563EB"))
    p.drawEllipse(4, 4, 56, 56)
    p.setPen(QColor("white"))
    font = p.font()
    font.setBold(True)
    font.setPointSize(24)
    p.setFont(font)
    p.drawText(pm.rect(), Qt.AlignCenter, "✓")
    p.end()
    return QIcon(pm)


class Bridge(QObject):
    """Pasa resultados de hilos secundarios al hilo de la interfaz."""
    result = Signal(str, list)
    error = Signal(str)
    ready = Signal()
    grammar = Signal(str)
    fatal = Signal(str)
    toggle = Signal()


class CorrectorApp:
    def __init__(self, qt: QApplication, corrector_factory=None):
        self.qt = qt
        self.corrector = None
        self.context = ""
        self.hotkey = None
        self.tray = None
        self.toggle_action = None
        self._factory = corrector_factory or (lambda: motor.Corrector())

        self.icon = FloatingIcon()
        self.popup = SuggestionPopup()
        self.toast = Toast()
        self.bridge = Bridge()
        self._connect()

        geo = qt.primaryScreen().availableGeometry()
        self.icon.move(geo.right() - motor.ICON_SIZE - motor.ICON_OFFSET[0],
                       geo.bottom() - motor.ICON_SIZE - motor.ICON_OFFSET[1])
        self.icon.set_busy(True)
        self.icon.setToolTip("Cargando diccionarios...")
        self.icon.show()

        self._setup_tray()
        self._start_hotkey()
        qt.aboutToQuit.connect(self._close)
        threading.Thread(target=self._load, daemon=True).start()

    def _connect(self):
        b = self.bridge
        b.result.connect(self.show_result)
        b.error.connect(self.show_error)
        b.ready.connect(self.on_ready)
        b.grammar.connect(self.on_grammar)
        b.fatal.connect(self.on_fatal)
        b.toggle.connect(self.toggle_icon)
        self.icon.clicked.connect(self.on_click)
        self.icon.toggle_requested.connect(self.toggle_icon)
        self.icon.quit_requested.connect(self.qt.quit)
        self.popup.fix_chosen.connect(self.apply_fix)
        self.popup.fix_all_requested.connect(self.fix_all)

    def _setup_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self.tray = QSystemTrayIcon(make_app_icon(), self.qt)
        menu = QMenu()
        menu.addAction("Revisar ahora", self.on_click)
        self.toggle_action = menu.addAction("Ocultar icono", self.toggle_icon)
        menu.addSeparator()
        menu.addAction("Salir", self.qt.quit)
        self.tray.setContextMenu(menu)
        self.tray.setToolTip("Corrector flotante - cargando...")
        self.tray.activated.connect(lambda r: self.on_click() if r == QSystemTrayIcon.Trigger else None)
        self.tray.show()

    def _start_hotkey(self):
        try:
            from pynput.keyboard import GlobalHotKeys
            self.hotkey = GlobalHotKeys({motor.HOTKEY_TOGGLE: self.bridge.toggle.emit})
            self.hotkey.daemon = True
            self.hotkey.start()
        except Exception:
            log.warning("Atajo no disponible:\n%s", traceback.format_exc())

    def toggle_icon(self):
        if self.icon.isVisible():
            self.icon.hide()
            self.popup.hide()
            self.toast.hide()
            text = "Mostrar icono"
        else:
            self.icon.show()
            text = "Ocultar icono"
        if self.toggle_action:
            self.toggle_action.setText(text)

    def _load(self):
        try:
            self.corrector = self._factory()
            self.bridge.ready.emit()
            self.bridge.grammar.emit(self.corrector.load_grammar())
        except Exception:
            msg = traceback.format_exc()
            log.error(msg)
            self.bridge.fatal.emit(msg)

    def on_ready(self):
        self.icon.set_busy(False)
        self.icon.setToolTip("Revisar lo escrito")
        if self.tray:
            self.tray.setToolTip("Corrector flotante - listo")

    def on_grammar(self, warning: str):
        if warning and self.tray:
            self.tray.showMessage("Corrector flotante", warning, QSystemTrayIcon.Warning, 8000)

    def on_fatal(self, msg: str):
        self.icon.setToolTip("Error al cargar")
        avisar("No se pudo iniciar el corrector.\n\n" + msg[-900:] + f"\n\nDetalle en: {LOG_PATH}")

    def on_click(self):
        if self.icon.busy:
            return
        if self.corrector is None:
            if self.tray:
                self.tray.showMessage("Corrector flotante", "Todavía cargando los diccionarios...")
            return
        self.icon.set_busy(True)
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        try:
            text = read_context(motor.CONTEXT_WORDS)
            self.bridge.result.emit(text, self.corrector.analyze(text))
        except Exception:
            msg = traceback.format_exc()
            log.error(msg)
            self.bridge.error.emit(msg)

    def show_result(self, text: str, issues: list):
        self.icon.set_busy(False)
        self.context = text
        screen = self.qt.primaryScreen().availableGeometry()
        pos = self.icon.pos() + QPoint(-360, -motor.ICON_SIZE * 4)
        pos.setX(max(screen.left(), min(pos.x(), screen.right() - 400)))
        pos.setY(max(screen.top(), pos.y()))
        self.popup.show_issues(text, issues, pos)

    def show_error(self, msg: str):
        self.icon.set_busy(False)
        if self.tray:
            self.tray.showMessage("Error al revisar", "Detalle en corrector.log", QSystemTrayIcon.Warning, 6000)

    def apply_fix(self, issue, replacement: str):
        self._replace([(issue.start, issue.end, replacement, issue.category)])

    def fix_all(self, issues):
        self._replace([(i.start, i.end, i.suggestions[0], i.category) for i in issues if i.suggestions])

    def _replace(self, fixes: list):
        if not fixes:
            return
        plain = [(s, e, r) for s, e, r, _ in fixes]
        new_text, applied = motor.apply_fixes(self.context, plain)
        if applied:
            replace_selection(new_text)
            info = {(s, e): (r, c) for s, e, r, c in fixes}
            # Recupera el original desde el contexto anterior
            pairs = [(self.context[s:e], r, info[(s, e)][1]) for s, e, r in applied]
            QTimer.singleShot(250, lambda: self.toast.show_near(
                motor.toast_message(pairs), self.icon.pos(), motor.TOAST_MS))
        self.context = ""

    def _close(self):
        if self.hotkey:
            self.hotkey.stop()
        if self.corrector:
            self.corrector.close()


def main() -> int:
    logging.basicConfig(filename=LOG_PATH, level=logging.INFO, encoding="utf-8",
                        format="%(asctime)s %(levelname)s %(message)s")
    try:
        qt = QApplication(sys.argv)
        qt.setQuitOnLastWindowClosed(False)
        CorrectorApp(qt)
        return qt.exec()
    except Exception:
        log.exception("Error fatal")
        avisar("No se pudo iniciar el corrector.\n\n" + traceback.format_exc()[-900:]
               + f"\n\nDetalle en: {LOG_PATH}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
