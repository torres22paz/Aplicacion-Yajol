"""Configuración común de las pruebas."""
import gc
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402

from yajol.nucleo.corrector import Corrector  # noqa: E402
from yajol.nucleo.lexico import Lexico  # noqa: E402
from yajol.nucleo.nombres import RevisorNombres  # noqa: E402


@pytest.fixture(scope="session")
def lexico():
    lx = Lexico()
    assert lx.hunspell is not None, "Debe cargarse el diccionario es_MX.zip de yajol/datos"
    return lx


@pytest.fixture(scope="session")
def corrector(lexico):
    return Corrector(lexico=lexico, usar_languagetool=False)


@pytest.fixture(scope="session")
def revisor_nombres(lexico):
    return RevisorNombres(lexico)


@pytest.fixture(scope="session")
def qt_app():
    pytest.importorskip("PySide6")
    from PySide6.QtCore import qInstallMessageHandler
    from PySide6.QtWidgets import QApplication
    qInstallMessageHandler(lambda *a: None)     # sin pantalla, Qt avisa de cosas que no importan
    app = QApplication.instance() or QApplication([])
    yield app
    for w in app.topLevelWidgets():
        w.close()
        w.deleteLater()
    app.processEvents()
    gc.collect()


def corrige(corrector, texto: str) -> str:
    """Atajo: devuelve el texto ya corregido."""
    return corrector.corrige(texto)[0]


def sugerencias_de(corrector, texto: str, palabra: str) -> list:
    for h in corrector.analiza(texto):
        if h.original.lower() == palabra.lower():
            return h.sugerencias
    return []
