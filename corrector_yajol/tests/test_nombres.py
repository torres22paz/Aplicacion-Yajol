"""Pruebas de los nombres propios y los nombres completos."""
import pytest


def corrige_nombre(revisor, texto: str) -> str:
    from yajol.nucleo.texto import aplica_cambios
    hallazgos = revisor.revisa(texto)
    return aplica_cambios(texto, [(h.inicio, h.fin, h.mejor) for h in hallazgos if h.mejor])[0]


class TestNombreCompleto:
    @pytest.mark.parametrize("malo,bueno", [
        ("omar torres de la paz", "Omar Torres de la Paz"),
        ("jose hernandez garcia", "José Hernández García"),
        ("maria del carmen lopez", "María del Carmen López"),
        ("juan perez", "Juan Pérez"),
        ("ana sofia ramirez", "Ana Sofía Ramírez"),
    ])
    def test_arregla_mayusculas_y_tildes(self, revisor_nombres, malo, bueno):
        assert corrige_nombre(revisor_nombres, malo) == bueno

    def test_dentro_de_una_frase(self, revisor_nombres):
        texto = "el profesor jose hernandez dio la clase"
        assert corrige_nombre(revisor_nombres, texto) == "el profesor José Hernández dio la clase"

    def test_las_particulas_van_en_minuscula(self, revisor_nombres):
        resultado = corrige_nombre(revisor_nombres, "luis de la cruz")
        assert " de la " in resultado and resultado.startswith("Luis")

    def test_conserva_el_texto_en_mayusculas(self, revisor_nombres):
        assert corrige_nombre(revisor_nombres, "ANGEL RAMIREZ") == "ÁNGEL RAMÍREZ"

    def test_un_nombre_bien_escrito_no_se_toca(self, revisor_nombres):
        texto = "Juan Pérez vino ayer"
        assert revisor_nombres.revisa(texto) == []

    def test_explica_el_motivo(self, revisor_nombres):
        hallazgo = revisor_nombres.revisa("jose hernandez")[0]
        assert "mayúscula" in hallazgo.explicacion
        assert "«jose» → «José»" in hallazgo.explicacion


class TestNombreSuelto:
    @pytest.mark.parametrize("malo,bueno", [
        ("mexico", "México"),
        ("merida", "Mérida"),
        ("queretaro", "Querétaro"),
    ])
    def test_corrige_lugares(self, revisor_nombres, malo, bueno):
        assert corrige_nombre(revisor_nombres, f"vivo en {malo}") == f"vivo en {bueno}"


class TestSinFalsosPositivos:
    @pytest.mark.parametrize("texto", [
        "la paz interior es importante",
        "una flor en el jardín",
        "la cruz roja ayuda",
        "dame la luz por favor",
        "el león come carne",
    ])
    def test_las_palabras_comunes_no_son_apellidos(self, revisor_nombres, texto):
        assert revisor_nombres.revisa(texto) == [], \
            f"Falso positivo en: {texto}"

    def test_no_junta_nombres_separados_por_signos(self, revisor_nombres):
        hallazgos = revisor_nombres.revisa("Juan, Pedro")
        assert all(" " not in h.original or "," not in h.original for h in hallazgos)


class TestPosiciones:
    def test_las_posiciones_son_correctas(self, revisor_nombres):
        texto = "hola jose hernandez adios"
        for h in revisor_nombres.revisa(texto):
            assert texto[h.inicio:h.fin] == h.original
