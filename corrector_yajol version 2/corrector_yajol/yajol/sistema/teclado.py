"""Lectura y escritura de texto en el programa que esté enfrente.

Funciona igual en Word, en el navegador, en el bloc de notas o en cualquier
cuadro de texto, porque solo usa el portapapeles y las teclas del sistema.
"""
import logging
import time

from .. import config

log = logging.getLogger("yajol")
_teclado = None


def _controlador():
    global _teclado
    if _teclado is None:
        from pynput.keyboard import Controller
        _teclado = Controller()
    return _teclado


def _pulsa(tecla):
    kb = _controlador()
    kb.press(tecla)
    kb.release(tecla)
    time.sleep(config.RETARDO_TECLA)


def _combo(modificador, tecla):
    with _controlador().pressed(modificador):
        _pulsa(tecla)


def _portapapeles():
    import pyperclip
    return pyperclip


def copia_seleccion(intentos: int = None) -> str:
    """Copia lo que esté seleccionado. Cadena vacía si no hay nada."""
    pyperclip = _portapapeles()
    from pynput.keyboard import Key
    intentos = intentos or config.INTENTOS_COPIA
    for n in range(intentos):
        pyperclip.copy("")
        _combo(Key.ctrl, "c")
        time.sleep(config.RETARDO_COPIA * (1 + n * 0.5))
        texto = pyperclip.paste()
        if texto:
            return texto
    return ""


def selecciona_atras(palabras: int):
    """Selecciona hacia atrás el número de palabras indicado."""
    from pynput.keyboard import Key
    with _controlador().pressed(Key.shift, Key.ctrl):
        for _ in range(palabras):
            _pulsa(Key.left)


def lee_contexto(palabras: int = None):
    """
    Devuelve (texto, habia_seleccion).

    Si el usuario ya tenía algo seleccionado se revisa eso; si no, se
    seleccionan las últimas palabras escritas antes del cursor.
    """
    palabras = palabras or config.PALABRAS_CONTEXTO
    pyperclip = _portapapeles()
    anterior = ""
    try:
        anterior = pyperclip.paste()
    except Exception:
        log.warning("No se pudo leer el portapapeles anterior")

    try:
        seleccionado = copia_seleccion(1)
        if seleccionado.strip():
            return seleccionado, True
        selecciona_atras(palabras)
        texto = copia_seleccion()
        return texto, False
    finally:
        try:
            pyperclip.copy(anterior)
        except Exception:
            pass


def reemplaza_seleccion(texto_nuevo: str):
    """Pega el texto corregido encima de lo que esté seleccionado."""
    from pynput.keyboard import Key
    pyperclip = _portapapeles()
    anterior = ""
    try:
        anterior = pyperclip.paste()
    except Exception:
        pass
    pyperclip.copy(texto_nuevo)
    time.sleep(0.05)
    _combo(Key.ctrl, "v")
    time.sleep(config.RETARDO_PEGADO)
    try:
        pyperclip.copy(anterior)
    except Exception:
        pass


def disponible() -> bool:
    """True si se pueden usar el teclado y el portapapeles en este equipo."""
    try:
        import pynput  # noqa: F401
        import pyperclip  # noqa: F401
    except ImportError:
        return False
    return True
