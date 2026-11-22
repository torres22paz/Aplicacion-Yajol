"""Pruebas de las operaciones de texto."""
import pytest

from yajol.nucleo.texto import (aplica_cambios, clase_acentual, conserva_forma,
                                distancia, es_misma_con_tilde, fragmento,
                                mensaje_aviso, normaliza, nucleos, sin_tildes)


class TestNormalizacion:
    @pytest.mark.parametrize("entrada,esperado", [
        ("corrección", "correccion"),
        ("niña", "niña"),
        ("pingüino", "pingüino"),
        ("ÁRBOL", "ARBOL"),
        ("México", "Mexico"),
        ("sin cambios", "sin cambios"),
    ])
    def test_sin_tildes_conserva_ene_y_dieresis(self, entrada, esperado):
        assert sin_tildes(entrada) == esperado

    def test_normaliza_baja_y_quita_tildes(self):
        assert normaliza("CORRECCIÓN") == "correccion"

    @pytest.mark.parametrize("a,b", [("publico", "público"), ("canto", "cantó")])
    def test_detecta_misma_palabra_con_tilde(self, a, b):
        assert es_misma_con_tilde(a, b)

    @pytest.mark.parametrize("a,b", [("casa", "caza"), ("publico", "publico")])
    def test_no_confunde_palabras_distintas(self, a, b):
        assert not es_misma_con_tilde(a, b)


class TestConservaForma:
    @pytest.mark.parametrize("original,nueva,esperado", [
        ("casa", "caza", "caza"),
        ("Casa", "caza", "Caza"),
        ("CASA", "caza", "CAZA"),
        ("A", "a", "A"),            # una sola letra mayúscula se conserva
    ])
    def test_copia_las_mayusculas(self, original, nueva, esperado):
        assert conserva_forma(original, nueva) == esperado


class TestDistancia:
    def test_palabras_iguales_cuestan_cero(self):
        assert distancia("casa", "casa") == 0

    def test_letras_que_suenan_igual_cuestan_menos(self):
        assert distancia("casa", "caza") < distancia("casa", "cama")

    def test_la_tilde_cuesta_muy_poco(self):
        assert distancia("publico", "público") < 0.5

    def test_el_orden_no_importa(self):
        assert distancia("hola", "ola") == distancia("ola", "hola")


class TestSilabas:
    @pytest.mark.parametrize("palabra,cuantos", [
        ("casa", 2), ("corrección", 3), ("a", 1), ("aire", 2), ("día", 2),
    ])
    def test_cuenta_nucleos(self, palabra, cuantos):
        assert len(nucleos(palabra)) == cuantos

    @pytest.mark.parametrize("palabra,clase", [
        ("público", "esdrújula"),
        ("canción", "aguda"),
        ("árbol", "llana"),
        ("sí", "monosílaba"),
    ])
    def test_clasifica_por_el_acento(self, palabra, clase):
        assert clase_acentual(palabra)[0] == clase

    def test_sin_tilde_no_se_puede_clasificar(self):
        assert clase_acentual("casa")[0] is None


class TestFragmento:
    def test_marca_el_trozo_con_error(self):
        texto = "hola mundo bonito"
        p = fragmento(texto, 5, 10)
        assert p["error"] == "mundo"
        assert p["antes"].strip() == "hola"
        assert p["despues"].strip() == "bonito"

    def test_recorta_textos_largos(self):
        texto = "palabra " * 40
        p = fragmento(texto, 160, 167)
        assert p["corte_izq"] and p["corte_der"]


class TestAplicaCambios:
    def test_aplica_en_orden_correcto(self):
        nuevo, aplicados = aplica_cambios("abc def", [(0, 3, "XYZ"), (4, 7, "123")])
        assert nuevo == "XYZ 123"
        assert len(aplicados) == 2

    def test_omite_los_cambios_que_se_pisan(self):
        nuevo, aplicados = aplica_cambios("abcdef", [(0, 4, "X"), (2, 6, "Y")])
        assert len(aplicados) == 1
        assert nuevo in ("Xef", "abY")

    def test_sin_cambios_devuelve_lo_mismo(self):
        assert aplica_cambios("hola", []) == ("hola", [])

    def test_ignora_posiciones_imposibles(self):
        nuevo, aplicados = aplica_cambios("hola", [(-1, 2, "X"), (3, 2, "Y")])
        assert nuevo == "hola" and aplicados == []


class TestMensajeAviso:
    def test_vacio_si_no_hubo_cambios(self):
        assert mensaje_aviso([]) == ""

    def test_resume_cuando_hay_muchos(self):
        pares = [(f"a{i}", f"b{i}", "Ortografía") for i in range(7)]
        mensaje = mensaje_aviso(pares, max_lineas=3)
        assert "y 4 más" in mensaje
        assert mensaje.count("→") == 3
