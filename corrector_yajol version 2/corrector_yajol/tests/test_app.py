"""Pruebas de la aplicación completa, con el teclado imitado."""
import pytest

pytest.importorskip("PySide6")

from yajol import app as modulo_app  # noqa: E402
from yajol.nucleo.hallazgo import Hallazgo  # noqa: E402


@pytest.fixture
def aplicacion(qt_app, corrector, monkeypatch):
    """Aplicación lista, sin tocar el teclado ni el arranque de Windows."""
    pegados = []
    monkeypatch.setattr(modulo_app.teclado, "reemplaza_seleccion", pegados.append)
    monkeypatch.setattr(modulo_app.teclado, "lee_contexto",
                        lambda *a, **k: ("hazer la tarea", False))
    monkeypatch.setattr(modulo_app.inicio, "esta_activado", lambda: False)
    monkeypatch.setattr(modulo_app.inicio, "alterna", lambda: True)

    aplicacion = modulo_app.Aplicacion(qt_app, fabrica=lambda: corrector)
    aplicacion.corrector = corrector
    aplicacion.pegados = pegados
    yield aplicacion
    aplicacion.cierra()
    aplicacion.icono.close()
    aplicacion.panel.close()
    aplicacion.aviso.close()


class TestArranque:
    def test_se_crea_sin_errores(self, aplicacion):
        assert aplicacion.icono is not None
        assert aplicacion.panel is not None

    def test_el_icono_queda_dentro_de_la_pantalla(self, aplicacion, qt_app):
        pantalla = qt_app.primaryScreen().availableGeometry()
        assert pantalla.left() <= aplicacion.icono.x() <= pantalla.right()
        assert pantalla.top() <= aplicacion.icono.y() <= pantalla.bottom()

    def test_al_estar_listo_deja_de_mostrarse_ocupado(self, aplicacion):
        aplicacion.al_estar_listo()
        assert aplicacion.icono.ocupado is False


class TestOcultarYMostrar:
    def test_alterna_el_icono(self, aplicacion):
        aplicacion.icono.show()
        aplicacion.alterna_icono()
        assert not aplicacion.icono.isVisible()
        aplicacion.alterna_icono()
        assert aplicacion.icono.isVisible()

    def test_el_menu_cambia_de_texto(self, aplicacion):
        if aplicacion.accion_ocultar is None:
            pytest.skip("sin bandeja del sistema en este entorno")
        aplicacion.icono.show()
        aplicacion.alterna_icono()
        assert "Mostrar" in aplicacion.accion_ocultar.text()


class TestRevision:
    def test_muestra_los_resultados(self, aplicacion, corrector):
        texto = "hazer la tarea"
        aplicacion.muestra_resultado(texto, corrector.analiza(texto), False)
        assert aplicacion.contexto == texto
        assert "error" in aplicacion.panel.titulo.text().lower()

    def test_sin_errores_tambien_se_muestra(self, aplicacion):
        aplicacion.muestra_resultado("todo bien escrito", [], False)
        assert "Sin errores" in aplicacion.panel.titulo.text()

    def test_el_panel_no_se_sale_de_la_pantalla(self, aplicacion, qt_app):
        aplicacion.muestra_resultado("hazer", [], False)
        pantalla = qt_app.primaryScreen().availableGeometry()
        assert aplicacion.panel.x() >= pantalla.left()
        assert aplicacion.panel.y() >= pantalla.top()


class TestAplicarCorrecciones:
    def test_aplica_una_sugerencia(self, aplicacion):
        aplicacion.contexto = "hazer la tarea"
        hallazgo = Hallazgo("Ortografía", "hazer", 0, 5, ["hacer"], "x", "c_antes_ei")
        aplicacion.aplica_uno(hallazgo, "hacer")
        assert aplicacion.pegados == ["hacer la tarea"]

    def test_aplica_todas_de_una_vez(self, aplicacion, corrector):
        texto = "hazer la tarea con jente"
        aplicacion.contexto = texto
        aplicacion.aplica_todos(corrector.analiza(texto))
        assert aplicacion.pegados
        assert "hacer" in aplicacion.pegados[0] and "gente" in aplicacion.pegados[0]

    def test_sin_contexto_no_pega_nada(self, aplicacion):
        aplicacion.contexto = ""
        aplicacion.aplica_uno(Hallazgo("x", "a", 0, 1, ["b"], "y"), "b")
        assert aplicacion.pegados == []

    def test_el_contexto_se_limpia_despues(self, aplicacion):
        aplicacion.contexto = "hazer"
        aplicacion.aplica_uno(Hallazgo("x", "hazer", 0, 5, ["hacer"], "y"), "hacer")
        assert aplicacion.contexto == ""


class TestAprenderPalabra:
    def test_aprende_y_avisa(self, aplicacion, monkeypatch):
        guardadas = []
        monkeypatch.setattr(aplicacion.corrector, "aprende",
                            lambda p: guardadas.append(p) or True)
        aplicacion.aprende("yajolita")
        assert guardadas == ["yajolita"]


class TestArranqueConWindows:
    def test_se_puede_encender_desde_el_menu(self, aplicacion):
        if aplicacion.accion_inicio is None:
            pytest.skip("sin bandeja del sistema en este entorno")
        aplicacion.alterna_inicio()
        assert aplicacion.accion_inicio.isChecked()


class TestErrores:
    def test_un_fallo_al_leer_no_tumba_la_aplicacion(self, aplicacion):
        aplicacion.icono.marca_ocupado(True)
        aplicacion.muestra_error("algo salió mal")
        assert aplicacion.icono.ocupado is False

    def test_cerrar_dos_veces_es_seguro(self, aplicacion):
        aplicacion.cierra()
        aplicacion.cierra()
