"""Pruebas de la ayuda: la ventana, el signo «?» y los textos."""
import os

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QPoint, QRect, Qt  # noqa: E402
from PySide6.QtGui import QMouseEvent  # noqa: E402
from PySide6.QtWidgets import QLabel, QPushButton  # noqa: E402

from yajol import config  # noqa: E402
from yajol.interfaz import ayuda as modulo_ayuda  # noqa: E402
from yajol.interfaz import contenido_ayuda as C  # noqa: E402
from yajol.interfaz.ayuda import (PESTANAS, VentanaAyuda, bienvenida_pendiente,  # noqa: E402
                                  marca_bienvenida_vista)
from yajol.interfaz.icono import IconoFlotante  # noqa: E402
from yajol.interfaz.popup import PanelSugerencias  # noqa: E402
from yajol.nucleo.hallazgo import Hallazgo  # noqa: E402


def _clic(icono, punto):
    icono.mousePressEvent(QMouseEvent(QMouseEvent.MouseButtonPress, punto,
                                      Qt.LeftButton, Qt.LeftButton, Qt.NoModifier))
    icono.mouseReleaseEvent(QMouseEvent(QMouseEvent.MouseButtonRelease, punto,
                                        Qt.LeftButton, Qt.LeftButton, Qt.NoModifier))


def _textos(ventana) -> str:
    return " ".join(e.text() for e in ventana.findChildren(QLabel))


@pytest.fixture
def ventana(qt_app):
    v = VentanaAyuda()
    yield v
    v.close()
    v.deleteLater()


class TestSignoDeInterrogacion:
    def test_el_icono_tiene_una_zona_de_ayuda(self, qt_app):
        icono = IconoFlotante()
        zona = icono.zona_ayuda()
        assert icono.rect().contains(zona)
        assert zona.width() >= 20, "tiene que ser fácil de pulsar"
        assert zona.right() >= icono.width() - 2 and zona.top() == 0, "va en la esquina superior derecha"
        icono.deleteLater()

    def test_pulsar_el_signo_abre_la_ayuda_y_no_revisa(self, qt_app):
        icono = IconoFlotante()
        ayudas, revisiones = [], []
        icono.ayuda_pedida.connect(lambda: ayudas.append(1))
        icono.pulsado.connect(lambda: revisiones.append(1))
        _clic(icono, icono.zona_ayuda().center())
        assert ayudas == [1] and revisiones == []
        icono.deleteLater()

    def test_pulsar_el_pajaro_revisa_y_no_abre_la_ayuda(self, qt_app):
        icono = IconoFlotante()
        ayudas, revisiones = [], []
        icono.ayuda_pedida.connect(lambda: ayudas.append(1))
        icono.pulsado.connect(lambda: revisiones.append(1))
        _clic(icono, QPoint(20, 44))
        assert revisiones == [1] and ayudas == []
        icono.deleteLater()

    def test_el_signo_se_dibuja(self, qt_app):
        icono = IconoFlotante()
        imagen = icono.grab().toImage()
        centro = icono.zona_ayuda().center()
        escala = imagen.width() / icono.width()
        color = imagen.pixelColor(int((centro.x() - 6) * escala), int(centro.y() * escala))
        assert color.blue() > color.red() + 60, "el círculo del signo ? es azul"
        icono.deleteLater()

    def test_el_panel_de_revision_tiene_boton_de_ayuda(self, qt_app):
        panel = PanelSugerencias()
        pedidas = []
        panel.ayuda_pedida.connect(lambda: pedidas.append(1))
        assert panel.boton_ayuda.text() == "?"
        panel.boton_ayuda.click()
        assert pedidas == [1]
        panel.deleteLater()


class TestVentanaDeAyuda:
    def test_tiene_cuatro_pestanas(self, ventana):
        assert ventana.paginas.count() == len(PESTANAS) == 4
        assert [b.text() for b in ventana.botones] == PESTANAS

    def test_empieza_en_como_se_usa(self, ventana):
        assert ventana.paginas.currentIndex() == 0
        assert ventana.botones[0].isChecked()

    @pytest.mark.parametrize("indice", [0, 1, 2, 3])
    def test_cambia_de_pestana(self, ventana, indice):
        ventana.botones[indice].click()
        assert ventana.paginas.currentIndex() == indice
        assert [b.isChecked() for b in ventana.botones].count(True) == 1

    def test_un_indice_imposible_no_rompe_nada(self, ventana):
        ventana.ve_a(99)
        assert ventana.paginas.currentIndex() == 3
        ventana.ve_a(-5)
        assert ventana.paginas.currentIndex() == 0

    def test_explica_los_tres_pasos(self, ventana):
        texto = _textos(ventana)
        for titulo, _, _ in C.PASOS:
            assert titulo in texto

    def test_muestra_los_atajos_como_teclas(self, ventana):
        teclas = [e.text() for e in ventana.findChildren(QLabel) if e.objectName() == "tecla"]
        assert teclas.count("Ctrl") >= 2 and "Alt" in teclas and "C" in teclas

    def test_incluye_ejemplos_de_correccion(self, ventana):
        texto = _textos(ventana)
        assert "hazer" in texto and "hacer" in texto

    def test_responde_las_dudas_comunes(self, ventana):
        texto = _textos(ventana)
        for pregunta, _ in C.PROBLEMAS:
            assert pregunta in texto

    def test_el_boton_entendido_la_cierra(self, ventana):
        ventana.muestra()
        assert ventana.isVisible()
        ventana.boton_cerrar.click()
        assert not ventana.isVisible()

    def test_avisa_al_cerrarse(self, ventana):
        avisos = []
        ventana.cerrada.connect(lambda: avisos.append(1))
        ventana.muestra()
        ventana.close()
        assert avisos == [1]

    def test_se_puede_abrir_en_una_pestana_concreta(self, ventana):
        ventana.muestra(2)
        assert ventana.paginas.currentIndex() == 2

    def test_cabe_en_una_pantalla_de_portatil(self, ventana):
        assert ventana.height() <= 700 and ventana.width() <= 640

    def test_se_dibuja_sin_fallar(self, ventana):
        for indice in range(4):
            ventana.ve_a(indice)
            assert not ventana.grab().isNull()

    def test_es_una_ventana_normal_que_se_puede_cerrar(self, ventana):
        assert ventana.windowFlags() & Qt.WindowCloseButtonHint
        assert "Ayuda" in ventana.windowTitle()

    def test_no_usa_texto_azul_de_enlace(self, ventana):
        for etiqueta in ventana.findChildren(QLabel):
            assert "<a " not in etiqueta.text().lower()

    def test_abre_la_guia_completa(self, ventana, monkeypatch, tmp_path):
        guia = tmp_path / "Guia.html"
        guia.write_text("<html></html>", encoding="utf-8")
        abiertas = []
        monkeypatch.setattr(modulo_ayuda.config, "GUIA_PATH", str(guia))
        monkeypatch.setattr(modulo_ayuda.QDesktopServices, "openUrl",
                            staticmethod(lambda url: abiertas.append(url.toLocalFile()) or True))
        assert ventana.abre_guia()
        assert abiertas and abiertas[0].endswith("Guia.html")

    def test_sin_guia_no_falla(self, ventana, monkeypatch, tmp_path):
        monkeypatch.setattr(modulo_ayuda.config, "GUIA_PATH", str(tmp_path / "no_esta.html"))
        assert ventana.abre_guia() is False

    def test_los_botones_tienen_texto(self, ventana):
        for boton in ventana.findChildren(QPushButton):
            assert boton.text().strip()


class TestBienvenida:
    def test_la_primera_vez_esta_pendiente(self, tmp_path):
        assert bienvenida_pendiente(str(tmp_path / "vista.txt"))

    def test_despues_de_verla_ya_no(self, tmp_path):
        marca = str(tmp_path / "datos" / "vista.txt")
        assert marca_bienvenida_vista(marca)
        assert not bienvenida_pendiente(marca)

    def test_si_no_se_puede_escribir_no_falla(self, tmp_path):
        bloqueo = tmp_path / "archivo"
        bloqueo.write_text("x")
        assert marca_bienvenida_vista(str(bloqueo / "dentro" / "vista.txt")) is False


class TestContenido:
    def test_convierte_los_atajos_en_teclas(self):
        assert C.teclas("<ctrl>+<alt>+c") == ["Ctrl", "Alt", "C"]

    def test_los_atajos_salen_de_la_configuracion(self):
        assert C.TECLAS_REVISAR == C.teclas(config.ATAJO_REVISAR)
        assert C.TECLAS_MOSTRAR == C.teclas(config.ATAJO_MOSTRAR)

    def test_hay_tres_pasos(self):
        assert len(C.PASOS) == 3

    def test_la_ayuda_menciona_el_signo_de_interrogacion(self):
        assert any("?" in raton for _, _, raton in C.ATAJOS)

    def test_los_ejemplos_los_corrige_de_verdad_el_corrector(self, corrector):
        """Lo que promete la ayuda tiene que ser cierto."""
        fallos = []
        for _, pares in C.EJEMPLOS:
            for mal, bien in pares:
                obtenido = corrector.corrige(mal)[0]
                if obtenido != bien:
                    fallos.append(f"{mal!r}: se esperaba {bien!r} y salió {obtenido!r}")
        assert not fallos, "\n".join(fallos)


class TestPanelDeRevision:
    def _hallazgo(self, n=0):
        return Hallazgo("Ortografía", "hazer", n * 6, n * 6 + 5, ["hacer"],
                        "Se escribe «hacer», no «hazer».", "c_antes_ei", 0.8)

    def test_un_solo_error_va_en_singular(self, qt_app):
        panel = PanelSugerencias()
        panel.muestra("hazer", [self._hallazgo()], QPoint(0, 0))
        assert panel.titulo.text() == "Se encontró 1 posible error"
        panel.close()
        panel.deleteLater()

    def test_varios_errores_van_en_plural(self, qt_app):
        panel = PanelSugerencias()
        panel.muestra("hazer hazer", [self._hallazgo(0), self._hallazgo(1)], QPoint(0, 0))
        assert panel.titulo.text() == "Se encontraron 2 posibles errores"
        panel.close()
        panel.deleteLater()

    def test_la_lista_crece_con_el_contenido(self, qt_app):
        panel = PanelSugerencias()
        panel.muestra("hazer", [self._hallazgo()], QPoint(0, 0))
        alto_uno = panel.scroll.height()
        panel.muestra("hazer " * 3, [self._hallazgo(i) for i in range(3)], QPoint(0, 0))
        assert panel.scroll.height() > alto_uno
        panel.close()
        panel.deleteLater()

    def test_la_lista_tiene_un_alto_maximo(self, qt_app):
        panel = PanelSugerencias()
        panel.muestra("hazer " * 8, [self._hallazgo(i) for i in range(8)], QPoint(0, 0))
        assert panel.scroll.height() <= panel.ALTO_MAXIMO
        panel.close()
        panel.deleteLater()

    @pytest.mark.parametrize("ancla", [
        QRect(1280, 640, 64, 64),      # esquina inferior derecha (lo normal)
        QRect(1280, 10, 64, 64),       # esquina superior derecha
        QRect(5, 5, 64, 64),           # esquina superior izquierda
        QRect(5, 650, 64, 64),         # esquina inferior izquierda
    ])
    def test_nunca_se_sale_de_la_pantalla(self, qt_app, ancla):
        pantalla = QRect(0, 0, 1366, 728)
        panel = PanelSugerencias()
        panel.muestra("hazer " * 6, [self._hallazgo(i) for i in range(6)], QPoint(0, 0))
        panel.coloca_junto_a(ancla, pantalla)
        assert pantalla.contains(panel.geometry()), f"se sale: {panel.geometry()}"
        panel.close()
        panel.deleteLater()

    def test_en_la_esquina_habitual_queda_encima_del_icono(self, qt_app):
        pantalla = QRect(0, 0, 1366, 728)
        ancla = QRect(1280, 640, 64, 64)
        panel = PanelSugerencias()
        panel.muestra("hazer", [self._hallazgo()], QPoint(0, 0))
        panel.coloca_junto_a(ancla, pantalla)
        assert panel.geometry().bottom() < ancla.top()
        panel.close()
        panel.deleteLater()


class TestArchivoDeLaGuia:
    def test_la_ventana_ofrece_la_guia_si_existe(self, ventana):
        assert ventana.boton_guia.isHidden() == (not os.path.exists(config.GUIA_PATH))
