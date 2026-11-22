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
    monkeypatch.setattr(modulo_app, "marca_bienvenida_vista", lambda *a, **k: True)
    monkeypatch.setattr(modulo_app.inicio, "esta_activado", lambda: False)
    monkeypatch.setattr(modulo_app.inicio, "alterna", lambda: True)

    aplicacion = modulo_app.Aplicacion(qt_app, fabrica=lambda: corrector,
                                       mostrar_bienvenida=False, revisar_arranque=False)
    aplicacion.corrector = corrector
    aplicacion.pegados = pegados
    yield aplicacion
    aplicacion.cierra()
    aplicacion.icono.close()
    aplicacion.panel.close()
    aplicacion.aviso.close()
    aplicacion.ayuda.close()


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


class TestArranqueSilencioso:
    """Al encender el equipo no debe aparecer ninguna ventana de error."""

    def test_en_modo_silencioso_un_fallo_no_abre_ventanas(self, aplicacion, monkeypatch):
        abiertas = []
        monkeypatch.setattr(modulo_app, "avisa_error", abiertas.append)
        aplicacion.silencioso = True
        aplicacion.al_fallar("Traceback: algo salió mal")
        assert abiertas == []
        assert aplicacion.icono.ocupado is False

    def test_abierto_a_mano_si_avisa_del_fallo(self, aplicacion, monkeypatch):
        abiertas = []
        monkeypatch.setattr(modulo_app, "avisa_error", abiertas.append)
        aplicacion.silencioso = False
        aplicacion.al_fallar("Traceback: algo salió mal")
        assert len(abiertas) == 1

    def test_main_silencioso_no_muestra_errores(self, monkeypatch, qt_app):
        abiertas = []
        monkeypatch.setattr(modulo_app, "avisa_error", abiertas.append)
        monkeypatch.setattr(modulo_app, "_prepara_registro", lambda: None)

        def revienta(*a, **k):
            raise RuntimeError("fallo al arrancar")
        monkeypatch.setattr(modulo_app, "QApplication", revienta)
        assert modulo_app.main(["yajol", "--inicio"]) == 1
        assert abiertas == []

    def test_main_a_mano_si_muestra_el_error(self, monkeypatch, qt_app):
        abiertas = []
        monkeypatch.setattr(modulo_app, "avisa_error", abiertas.append)
        monkeypatch.setattr(modulo_app, "_prepara_registro", lambda: None)

        def revienta(*a, **k):
            raise RuntimeError("fallo al arrancar")
        monkeypatch.setattr(modulo_app, "QApplication", revienta)
        assert modulo_app.main(["yajol"]) == 1
        assert len(abiertas) == 1

    def test_si_ya_esta_abierto_la_segunda_copia_se_cierra(self, monkeypatch, qt_app):
        creadas = []
        monkeypatch.setattr(modulo_app, "_prepara_registro", lambda: None)
        monkeypatch.setattr(modulo_app, "QApplication", lambda *a, **k: qt_app)
        monkeypatch.setattr(modulo_app.instancia, "avisa_a_la_otra", lambda *a, **k: True)
        monkeypatch.setattr(modulo_app, "Aplicacion", lambda *a, **k: creadas.append(1))
        assert modulo_app.main(["yajol", "--inicio"]) == 0
        assert creadas == []

    def test_salir_avisa_a_la_copia_abierta(self, monkeypatch, qt_app):
        enviados = []
        monkeypatch.setattr(modulo_app, "_prepara_registro", lambda: None)
        monkeypatch.setattr(modulo_app, "QApplication", lambda *a, **k: qt_app)
        monkeypatch.setattr(modulo_app.instancia, "avisa_a_la_otra",
                            lambda m="mostrar", *a, **k: enviados.append(m) or True)
        assert modulo_app.main(["yajol", "--salir"]) == 0
        assert enviados == ["salir"]

    def test_el_arranque_antiguo_eliminado_se_refleja_en_el_menu(self, aplicacion):
        aplicacion.al_revisar_arranque({"quitados": ["Inicio: iniciar.lnk"], "activo": True})
        if aplicacion.accion_inicio is not None:
            assert aplicacion.accion_inicio.isChecked()


class TestAyudaEnLaAplicacion:
    def test_el_signo_de_interrogacion_abre_la_ayuda(self, aplicacion):
        aplicacion.icono.ayuda_pedida.emit()
        assert aplicacion.ayuda.isVisible()

    def test_el_boton_del_panel_abre_la_ayuda(self, aplicacion):
        aplicacion.panel.boton_ayuda.click()
        assert aplicacion.ayuda.isVisible()

    def test_abrir_la_ayuda_cierra_el_panel(self, aplicacion):
        aplicacion.muestra_resultado("hazer", [], False)
        aplicacion.muestra_ayuda()
        assert not aplicacion.panel.isVisible()

    def test_la_bienvenida_se_muestra_y_se_marca(self, aplicacion, monkeypatch):
        marcas = []
        monkeypatch.setattr(modulo_app, "marca_bienvenida_vista", lambda *a: marcas.append(1))
        aplicacion.muestra_bienvenida()
        assert aplicacion.ayuda.isVisible()
        assert marcas == [1]

    def test_al_encender_el_equipo_no_hay_bienvenida(self, qt_app, corrector, monkeypatch):
        monkeypatch.setattr(modulo_app, "bienvenida_pendiente", lambda *a: True)
        monkeypatch.setattr(modulo_app.inicio, "esta_activado", lambda: False)
        programadas = []
        monkeypatch.setattr(modulo_app.QTimer, "singleShot",
                            staticmethod(lambda ms, f: programadas.append(getattr(f, "__name__", ""))))
        silenciosa = modulo_app.Aplicacion(qt_app, fabrica=lambda: corrector, silencioso=True,
                                           revisar_arranque=False)
        assert "muestra_bienvenida" not in programadas
        silenciosa.cierra()
        for ventana in (silenciosa.icono, silenciosa.panel, silenciosa.aviso, silenciosa.ayuda):
            ventana.close()

    def test_la_primera_vez_a_mano_si_hay_bienvenida(self, qt_app, corrector, monkeypatch):
        monkeypatch.setattr(modulo_app, "bienvenida_pendiente", lambda *a: True)
        monkeypatch.setattr(modulo_app.inicio, "esta_activado", lambda: False)
        programadas = []
        monkeypatch.setattr(modulo_app.QTimer, "singleShot",
                            staticmethod(lambda ms, f: programadas.append(getattr(f, "__name__", ""))))
        normal = modulo_app.Aplicacion(qt_app, fabrica=lambda: corrector, revisar_arranque=False)
        assert "muestra_bienvenida" in programadas
        normal.cierra()
        for ventana in (normal.icono, normal.panel, normal.aviso, normal.ayuda):
            ventana.close()


class TestMensajesDeOtraCopia:
    def test_mostrar_enseña_el_icono(self, aplicacion):
        aplicacion.icono.hide()
        aplicacion.atiende_mensaje("mostrar")
        assert aplicacion.icono.isVisible()

    def test_ayuda_abre_la_ayuda(self, aplicacion):
        aplicacion.atiende_mensaje("ayuda")
        assert aplicacion.ayuda.isVisible()

    def test_salir_cierra_el_programa(self, aplicacion, monkeypatch):
        cierres = []
        monkeypatch.setattr(aplicacion.qt, "quit", lambda: cierres.append(1))
        aplicacion.atiende_mensaje("salir")
        assert cierres == [1]

    def test_un_mensaje_raro_se_ignora(self, aplicacion):
        aplicacion.atiende_mensaje("borrar todo")


class TestAtajoDeTeclado:
    def test_el_atajo_avisa_de_que_viene_del_teclado(self, aplicacion, monkeypatch):
        recibidos = []
        monkeypatch.setattr(modulo_app.teclado, "lee_contexto",
                            lambda *a, **k: recibidos.append(k.get("desde_atajo")) or ("", False))
        aplicacion.icono.marca_ocupado(False)
        aplicacion._trabaja(True)
        aplicacion._trabaja(False)
        assert recibidos == [True, False]
