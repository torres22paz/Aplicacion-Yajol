"""Pruebas del léxico: diccionario, listas propias y palabras aprendidas."""
import pytest

from yajol.nucleo.lexico import Lexico, carga_frecuencias, carga_hunspell


class TestCarga:
    def test_el_diccionario_comprimido_abre(self):
        assert carga_hunspell() is not None

    def test_hay_frecuencias(self):
        frecuencias = carga_frecuencias()
        assert len(frecuencias) > 10000
        assert frecuencias["de"] > frecuencias["murciélago"]

    def test_el_lexico_tiene_muchas_palabras(self, lexico):
        assert lexico.total_palabras > 50000


class TestExiste:
    @pytest.mark.parametrize("palabra", [
        "casa", "corrección", "niño", "pingüino", "haber", "cocer", "coser",
        "México", "whatsapp", "python", "compilador", "tecnológico",
    ])
    def test_reconoce_palabras_correctas(self, lexico, palabra):
        assert lexico.existe(palabra)

    @pytest.mark.parametrize("palabra", [
        "hazer", "corecion", "kansado", "jente", "abia", "dirijir",
    ])
    def test_rechaza_palabras_mal_escritas(self, lexico, palabra):
        assert not lexico.existe(palabra)

    def test_acepta_mayusculas_de_palabras_comunes(self, lexico):
        assert lexico.existe("Casa") and lexico.existe("CASA")

    def test_las_palabras_extra_se_cargan(self, lexico):
        assert lexico.existe("hardware") and lexico.existe("cubrebocas")


class TestNombresPropios:
    def test_reconoce_un_nombre(self, lexico):
        assert lexico.es_nombre_propio("hernandez")
        assert lexico.forma_del_nombre("hernandez") == "Hernández"

    def test_un_nombre_en_minuscula_no_es_correcto(self, lexico):
        assert not lexico.existe("hernandez")

    def test_un_nombre_bien_escrito_si_es_correcto(self, lexico):
        assert lexico.existe("Hernández")

    def test_lo_que_no_es_nombre_devuelve_none(self, lexico):
        assert lexico.forma_del_nombre("mesa") is None


class TestSugerencias:
    def test_propone_algo_parecido(self, lexico):
        assert "gente" in [s.lower() for s in lexico.sugerencias("jente")]

    def test_usa_la_cache(self, lexico):
        primera = lexico.sugerencias("kansado")
        assert lexico.sugerencias("kansado") is primera


class TestAprender:
    def test_guarda_y_reconoce_la_palabra(self, tmp_path):
        archivo = tmp_path / "mis_palabras.txt"
        lx = Lexico(hunspell=None, extra=[], nombres=[], frecuencias={},
                    usuario_path=str(archivo))
        assert lx.aprende("yajolizar")
        assert "yajolizar" in lx.usuario
        assert archivo.read_text(encoding="utf-8").strip() == "yajolizar"

    def test_no_guarda_dos_veces(self, tmp_path):
        archivo = tmp_path / "mis.txt"
        lx = Lexico(hunspell=None, extra=[], nombres=[], frecuencias={},
                    usuario_path=str(archivo))
        lx.aprende("tecnopalabra")
        assert not lx.aprende("tecnopalabra")

    def test_ignora_lo_vacio(self, tmp_path):
        lx = Lexico(hunspell=None, extra=[], nombres=[], frecuencias={},
                    usuario_path=str(tmp_path / "m.txt"))
        assert not lx.aprende("   ")


class TestSinDiccionario:
    def test_sin_diccionario_no_inventa_errores(self, tmp_path):
        lx = Lexico(hunspell=None, extra=[], nombres=[], frecuencias={},
                    usuario_path=str(tmp_path / "m.txt"))
        assert lx.existe("cualquiercosarara")
