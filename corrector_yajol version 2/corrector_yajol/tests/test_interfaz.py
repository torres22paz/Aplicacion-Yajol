"""Pruebas de las ventanas (se ejecutan sin pantalla, en modo offscreen)."""
import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QPoint, Qt  # noqa: E402
from PySide6.QtGui import QMouseEvent  # noqa: E402

from yajol import config  # noqa: E402
from yajol.interfaz.aviso import Aviso  # noqa: E402
from yajol.interfaz.icono import IconoFlotante, pixmap_logo  # noqa: E402
from yajol.interfaz.popup import PanelSugerencias, fragmento_html  # noqa: E402
from yajol.nucleo.hallazgo import Hallazgo  # noqa: E402


def hallazgo_de_prueba(**extra):
    datos = dict(categoria=config.CAT_ORTOGRAFIA, original="hazer", inicio=0, fin=5,
                 sugerencias=["hacer"], explicacion="Se escribe «hacer», no «hazer».",
                 regla="c_antes_ei", confianza=0.8)
    datos.update(extra)
    return Hallazgo(**datos)


class TestLogo:
    def test_el_logo_se_carga(self, qt_app):
        pix = pixmap_logo(64)
        assert not pix.isNull()
        assert max(pix.width(), pix.height()) == 64

    def test_se_puede_pedir_en_otros_tamanos(self, qt_app):
        assert max(pixmap_logo(32).width(), pixmap_logo(32).height()) == 32


class TestIconoFlotante:
    def test_tiene_el_tamano_configurado(self, qt_app):
        icono = IconoFlotante()
        assert icono.width() == config.TAM_ICONO
        icono.deleteLater()

    def test_empieza_libre(self, qt_app):
        icono = IconoFlotante()
        assert icono.ocupado is False
        icono.marca_ocupado(True)
        assert icono.ocupado is True
        icono.deleteLater()

    def test_el_clic_avisa(self, qt_app):
        icono = IconoFlotante()
        avisos = []
        icono.pulsado.connect(lambda: avisos.append(1))
        punto = QPoint(10, 10)
        icono.mousePressEvent(QMouseEvent(QMouseEvent.MouseButtonPress, punto,
                                          Qt.LeftButton, Qt.LeftButton, Qt.NoModifier))
        icono.mouseReleaseEvent(QMouseEvent(QMouseEvent.MouseButtonRelease, punto,
                                            Qt.LeftButton, Qt.LeftButton, Qt.NoModifier))
        assert avisos == [1]
        icono.deleteLater()

    def test_se_dibuja_sin_fallar(self, qt_app):
        icono = IconoFlotante()
        icono.resize(64, 64)
        icono.grab()            # fuerza paintEvent
        icono.marca_ocupado(True)
        icono.grab()
        icono.deleteLater()


class TestFragmentoHtml:
    def test_resalta_el_error(self):
        html = fragmento_html("yo hazer algo", 3, 8)
        assert "hazer" in html and "<span" in html

    def test_escapa_el_texto_del_usuario(self):
        html = fragmento_html("<script>alert(1)</script> hazer", 26, 31)
        assert "<script>" not in html
        assert "&lt;script&gt;" in html


class TestPanelSugerencias:
    def test_muestra_una_tarjeta_por_error(self, qt_app):
        panel = PanelSugerencias()
        hallazgos = [hallazgo_de_prueba(), hallazgo_de_prueba(original="jente", inicio=6, fin=11,
                                                              sugerencias=["gente"])]
        panel.muestra("hazer jente", hallazgos, QPoint(0, 0))
        assert "2" in panel.titulo.text()
        panel.close()
        panel.deleteLater()

    def test_sin_errores_lo_dice(self, qt_app):
        panel = PanelSugerencias()
        panel.muestra("todo bien", [], QPoint(0, 0))
        assert "Sin errores" in panel.titulo.text()
        panel.close()
        panel.deleteLater()

    def test_el_boton_de_corregir_todo_solo_sale_con_varios(self, qt_app):
        panel = PanelSugerencias()
        panel.muestra("hazer", [hallazgo_de_prueba()], QPoint(0, 0))
        assert not panel.boton_todo.isVisible()
        panel.close()
        panel.deleteLater()

    def test_elegir_una_sugerencia_avisa(self, qt_app):
        panel = PanelSugerencias()
        recibidos = []
        panel.arreglo_elegido.connect(lambda h, s: recibidos.append((h.original, s)))
        hallazgo = hallazgo_de_prueba()
        panel.muestra("hazer", [hallazgo], QPoint(0, 0))
        panel._elige(hallazgo, "hacer")
        assert recibidos == [("hazer", "hacer")]
        panel.close()
        panel.deleteLater()

    def test_corregir_todo_avisa_con_la_lista(self, qt_app):
        panel = PanelSugerencias()
        recibidos = []
        panel.arreglar_todo.connect(recibidos.append)
        hallazgos = [hallazgo_de_prueba(), hallazgo_de_prueba(inicio=6, fin=11)]
        panel.muestra("hazer hazer", hallazgos, QPoint(0, 0))
        panel._todo()
        assert len(recibidos[0]) == 2
        panel.close()
        panel.deleteLater()

    def test_ofrece_aprender_la_palabra_desconocida(self, qt_app):
        panel = PanelSugerencias()
        pedidas = []
        panel.aprender_palabra.connect(pedidas.append)
        hallazgo = hallazgo_de_prueba(original="yajolina", sugerencias=[], regla="desconocida",
                                      explicacion="No está en el diccionario.")
        panel.muestra("yajolina", [hallazgo], QPoint(0, 0))
        botones = panel.findChildren(type(panel.boton_todo))
        aprender = [b for b in botones if b.objectName() == "learn"]
        assert aprender, "debe haber un botón para aprender la palabra"
        aprender[0].click()
        assert pedidas == ["yajolina"]
        panel.close()
        panel.deleteLater()

    def test_limita_las_tarjetas(self, qt_app):
        panel = PanelSugerencias()
        hallazgos = [hallazgo_de_prueba(inicio=i * 6, fin=i * 6 + 5) for i in range(20)]
        panel.muestra("hazer " * 20, hallazgos, QPoint(0, 0))
        assert "20" in panel.titulo.text()
        panel.close()
        panel.deleteLater()


class TestAviso:
    def test_muestra_el_texto(self, qt_app):
        aviso = Aviso()
        aviso.muestra_cerca("Corregido: «hazer» → «hacer»", QPoint(100, 100), 50)
        assert "hacer" in aviso.text()
        aviso.close()
        aviso.deleteLater()

    def test_el_texto_vacio_no_abre_nada(self, qt_app):
        aviso = Aviso()
        aviso.muestra_cerca("", QPoint(0, 0))
        assert not aviso.isVisible()
        aviso.deleteLater()
