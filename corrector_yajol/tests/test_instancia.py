"""Pruebas de «una sola copia a la vez»."""
import uuid

import pytest

pytest.importorskip("PySide6")

from yajol.sistema import instancia  # noqa: E402


def _canal() -> str:
    return "yajol_prueba_" + uuid.uuid4().hex[:10]


def _espera(qt_app, condicion, ms=1500):
    from PySide6.QtCore import QDeadlineTimer
    limite = QDeadlineTimer(ms)
    while not condicion() and not limite.hasExpired():
        qt_app.processEvents()
    return condicion()


class TestUnaSolaCopia:
    def test_sin_otra_copia_no_hay_a_quien_avisar(self, qt_app):
        assert instancia.avisa_a_la_otra("mostrar", canal=_canal(), espera_ms=150) is False

    @pytest.mark.parametrize("mensaje", ["mostrar", "ayuda", "salir"])
    def test_la_copia_abierta_recibe_el_mensaje(self, qt_app, mensaje):
        canal = _canal()
        escucha = instancia.Escucha(canal)
        recibidos = []
        escucha.mensaje.connect(recibidos.append)
        assert escucha.abre()
        assert instancia.avisa_a_la_otra(mensaje, canal=canal)
        assert _espera(qt_app, lambda: recibidos == [mensaje])
        escucha.cierra()

    def test_los_mensajes_desconocidos_se_ignoran(self, qt_app):
        canal = _canal()
        escucha = instancia.Escucha(canal)
        recibidos = []
        escucha.mensaje.connect(recibidos.append)
        escucha.abre()
        instancia.avisa_a_la_otra("formatear disco", canal=canal)
        instancia.avisa_a_la_otra("ayuda", canal=canal)
        assert _espera(qt_app, lambda: bool(recibidos))
        assert recibidos == ["ayuda"]
        escucha.cierra()

    def test_tras_cerrar_ya_no_hay_copia(self, qt_app):
        canal = _canal()
        escucha = instancia.Escucha(canal)
        escucha.abre()
        escucha.cierra()
        assert instancia.avisa_a_la_otra("mostrar", canal=canal, espera_ms=150) is False

    def test_se_puede_abrir_tras_un_cierre_brusco(self, qt_app):
        canal = _canal()
        primera = instancia.Escucha(canal)
        assert primera.abre()
        segunda = instancia.Escucha(canal)       # como si la primera hubiera muerto sin cerrar
        assert segunda.abre()
        segunda.cierra()
        primera.cierra()

    def test_el_canal_es_distinto_para_cada_usuario(self, monkeypatch):
        monkeypatch.setattr(instancia.getpass, "getuser", lambda: "ana maría")
        uno = instancia.nombre_canal()
        monkeypatch.setattr(instancia.getpass, "getuser", lambda: "omar")
        assert uno != instancia.nombre_canal()
        assert " " not in uno

    def test_si_no_se_sabe_el_usuario_no_falla(self, monkeypatch):
        def falla():
            raise OSError("sin usuario")
        monkeypatch.setattr(instancia.getpass, "getuser", falla)
        assert instancia.nombre_canal().startswith("corrector_yajol_")
