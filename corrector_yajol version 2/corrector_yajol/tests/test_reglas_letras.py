"""Pruebas de las reglas de letras: s/c/z, b/v, g/j, h, ll/y, tildes."""
import pytest

from yajol.nucleo import reglas_letras as RL


def primera(lexico, palabra):
    candidatos = RL.candidatos(palabra, lexico.existe)
    return candidatos[0] if candidatos else (None, None)


class TestSeseo:
    """El error más común en México: confundir s, c y z."""

    @pytest.mark.parametrize("malo,bueno", [
        ("hazer", "hacer"),
        ("desision", "decisión"),
        ("felizes", "felices"),
        ("rason", "razón"),
        ("veses", "veces"),
        ("entonzes", "entonces"),
        ("nesesito", "necesito"),
    ])
    def test_corrige_s_c_z(self, lexico, malo, bueno):
        palabras = [c for c, _ in RL.candidatos(malo, lexico.existe)]
        assert bueno in palabras, f"{malo} debería proponer {bueno}, dio {palabras[:4]}"

    def test_explica_la_regla_de_la_c(self, lexico):
        _, regla = primera(lexico, "hazer")
        assert regla == "c_antes_ei"
        assert "delante de e o i" in RL.explica(regla, "hazer", "hacer").lower()


class TestBeUve:
    @pytest.mark.parametrize("malo,bueno", [
        ("escrivir", "escribir"),
        ("cantava", "cantaba"),
        ("obserbar", "observar"),
        ("enbiar", "enviar"),
        ("canbio", "cambio"),
    ])
    def test_corrige_b_v(self, lexico, malo, bueno):
        assert primera(lexico, malo)[0] == bueno

    def test_explica_el_imperfecto(self, lexico):
        assert primera(lexico, "cantava")[1] == "imperfecto_b"

    def test_explica_los_verbos_en_bir(self, lexico):
        assert primera(lexico, "escrivir")[1] == "bir"

    def test_explica_la_m_antes_de_b(self, lexico):
        assert primera(lexico, "canbio")[1] == "mb"


class TestGeJota:
    @pytest.mark.parametrize("malo,bueno,regla", [
        ("dirijir", "dirigir", "ger_gir"),
        ("protejer", "proteger", "ger_gir"),
        ("mensage", "mensaje", "aje"),
        ("garage", "garaje", "aje"),
        ("jente", "gente", None),
        ("relog", "reloj", "j_final"),
    ])
    def test_corrige_g_j(self, lexico, malo, bueno, regla):
        correcta, encontrada = primera(lexico, malo)
        assert correcta == bueno
        if regla:
            assert encontrada == regla


class TestHache:
    @pytest.mark.parametrize("malo,bueno", [
        ("ablar", "hablar"),
        ("ermano", "hermano"),
        ("abitacion", "habitación"),
        ("ielo", "hielo"),
        ("ueso", "hueso"),
        ("aora", "ahora"),
        ("proivir", "prohibir"),
    ])
    def test_pone_la_hache(self, lexico, malo, bueno):
        assert primera(lexico, malo)[0] == bueno

    def test_explica_hie_hue(self, lexico):
        assert primera(lexico, "ielo")[1] == "hie_hue"


class TestEleEle:
    @pytest.mark.parametrize("malo,bueno", [
        ("cuchiyo", "cuchillo"),
        ("desarroyo", "desarrollo"),
        ("caye", "calle"),
    ])
    def test_corrige_ll_y(self, lexico, malo, bueno):
        palabras = [c for c, _ in RL.candidatos(malo, lexico.existe)]
        assert bueno in palabras


class TestTildes:
    @pytest.mark.parametrize("malo,bueno", [
        ("ortografia", "ortografía"),
        ("matematicas", "matemáticas"),
        ("kilometro", "kilómetro"),
        ("vehiculo", "vehículo"),
        ("exito", "éxito"),
    ])
    def test_pone_la_tilde(self, lexico, malo, bueno):
        correcta, regla = primera(lexico, malo)
        assert correcta == bueno
        assert regla == "tilde"


class TestVariosCambios:
    @pytest.mark.parametrize("malo,bueno", [
        ("corecion", "corrección"),
        ("tanvien", "también"),
        ("ecselente", "excelente"),
        ("exepcion", "excepción"),
        ("traducion", "traducción"),
    ])
    def test_corrige_dos_o_tres_errores_juntos(self, lexico, malo, bueno):
        palabras = [c for c, _ in RL.candidatos(malo, lexico.existe)]
        assert bueno in palabras, f"{malo}: se propuso {palabras[:4]}"


class TestSinFalsosPositivos:
    @pytest.mark.parametrize("palabra", [
        "casa", "cocer", "coser", "gente", "jirafa", "haber", "hacer", "vaca",
    ])
    def test_las_palabras_correctas_no_cambian(self, lexico, palabra):
        assert lexico.existe(palabra)


class TestExplicaciones:
    def test_toda_regla_tiene_texto(self):
        reglas = {r for _, _, r in RL.CAMBIOS} | {r for _, _, r in RL.INSERCIONES}
        reglas |= {"tilde", "h_intervocal", "imperfecto_b", "bir", "ger_gir",
                   "aje", "illo", "hie_hue", "mb", "mp", "nv", "j_final"}
        faltan = [r for r in reglas if r not in RL.R]
        assert not faltan, f"Reglas sin explicación: {faltan}"

    def test_la_explicacion_menciona_las_dos_palabras(self):
        texto = RL.explica("c_antes_ei", "hazer", "hacer")
        assert "hazer" in texto and "hacer" in texto

    def test_describe_la_diferencia(self):
        assert "falta" in RL.diferencia_simple("ola", "hola")
        assert "sobra" in RL.diferencia_simple("hhola", "hola")
