"""Pruebas del corrector completo, de punta a punta."""
import pytest

from yajol import config
from yajol.nucleo.corrector import (Corrector, explica_acento, explica_pegadas,
                                    explica_sin_regla)


def corrige(corrector, texto):
    return corrector.corrige(texto)[0]


def categorias(corrector, texto):
    return {h.categoria for h in corrector.analiza(texto)}


class TestOrtografiaGeneral:
    @pytest.mark.parametrize("malo,bueno", [
        ("hazer la tarea", "hacer la tarea"),
        ("tengo ke estudiar", "tengo que estudiar"),
        ("abia mucha jente", "había mucha gente"),
        ("el kansado niño", "el cansado niño"),
        ("una desision dificil", "una decisión difícil"),
        ("estudio ortografia", "estudio ortografía"),
    ])
    def test_corrige_frases_completas(self, corrector, malo, bueno):
        assert corrige(corrector, malo) == bueno


class TestPalabrasPegadas:
    @pytest.mark.parametrize("malo,bueno", [
        ("miscompañeros llegaron", "mis compañeros llegaron"),
        ("megustan los libros", "me gustan los libros"),
        ("vamos ala escuela", "vamos a la escuela"),
        ("nose la respuesta", "no sé la respuesta"),
    ])
    def test_separa_palabras_pegadas(self, corrector, malo, bueno):
        assert corrige(corrector, malo) == bueno

    def test_la_categoria_es_palabras_juntas(self, corrector):
        assert config.CAT_PEGADAS in categorias(corrector, "miscompañeros")

    def test_no_parte_palabras_de_verdad(self, corrector):
        for palabra in ("computadora", "especialmente", "universidad", "desarrollo"):
            assert corrector.separa_pegadas(palabra) is None, palabra

    def test_no_parte_lo_que_no_existe(self, corrector):
        assert corrector.separa_pegadas("xqzvbn") is None

    def test_respeta_el_limite_de_partes(self, corrector):
        resultado = corrector.separa_pegadas("casacasacasacasa")
        if resultado:
            assert resultado.count(" ") + 1 <= config.MAX_PARTES_PEGADAS


class TestNombresEnElCorrector:
    def test_corrige_el_nombre_completo(self, corrector):
        texto = "el alumno omar torres de la paz entregó"
        assert "Omar Torres de la Paz" in corrige(corrector, texto)

    def test_la_categoria_es_nombre_propio(self, corrector):
        assert config.CAT_NOMBRE in categorias(corrector, "jose hernandez vino")

    def test_un_nombre_desconocido_no_se_inventa(self, corrector):
        hallazgos = corrector.analiza("Zyxwvut Qponml")
        assert all(h.categoria != config.CAT_NOMBRE for h in hallazgos)


class TestAcentuacion:
    @pytest.mark.parametrize("malo,bueno", [
        ("matematicas", "matemáticas"),
        ("kilometro", "kilómetro"),
        ("tambien", "también"),
    ])
    def test_pone_tildes(self, corrector, malo, bueno):
        assert corrige(corrector, malo) == bueno

    def test_explica_la_regla_de_acentuacion(self, corrector):
        hallazgo = corrector.analiza("matematicas")[0]
        assert hallazgo.categoria == config.CAT_ACENTO
        assert "esdrújula" in hallazgo.explicacion

    def test_explica_las_agudas(self):
        texto = explica_acento("cancion", "canción")
        assert "aguda" in texto and "canción" in texto

    def test_explica_los_monosilabos(self):
        assert "una sílaba" in explica_acento("si", "sí")


class TestMezclaDeErrores:
    def test_frase_con_muchos_errores(self, corrector):
        texto = "nose que aser, aveces me siento kansado i no e echo la tarea"
        resultado = corrige(corrector, texto)
        for esperado in ("no sé", "hacer", "a veces", "cansado", "y", "he hecho"):
            assert esperado in resultado, f"falta «{esperado}» en: {resultado}"

    def test_devuelve_los_pares_corregidos(self, corrector):
        _, pares = corrector.corrige("hazer la tarea")
        assert pares and pares[0][0] == "hazer" and pares[0][1] == "hacer"


class TestOrdenYLimpieza:
    def test_los_hallazgos_van_en_orden(self, corrector):
        hallazgos = corrector.analiza("hazer aveces jente kansado")
        posiciones = [h.inicio for h in hallazgos]
        assert posiciones == sorted(posiciones)

    def test_no_se_solapan(self, corrector):
        hallazgos = corrector.analiza("la problema de la agua, ¿porque no?")
        for i, a in enumerate(hallazgos):
            for b in hallazgos[i + 1:]:
                assert not a.solapa(b), f"{a.original} y {b.original} se pisan"

    def test_las_posiciones_apuntan_al_texto(self, corrector):
        texto = "nose que aser, ¿porque no vino jose hernandez?"
        for h in corrector.analiza(texto):
            assert texto[h.inicio:h.fin] == h.original

    def test_gana_el_hallazgo_mas_seguro(self, corrector):
        hallazgos = corrector.analiza("¿porque no viniste?")
        coincidencias = [h for h in hallazgos if h.original.lower() == "porque"]
        assert len(coincidencias) == 1


class TestSugerencias:
    def test_propone_pocas_y_buenas(self, corrector):
        for h in corrector.analiza("hazer kansado jente"):
            assert len(h.sugerencias) <= config.MAX_SUGERENCIAS

    def test_prefiere_la_palabra_mas_usada(self, corrector):
        hallazgo = next(h for h in corrector.analiza("abia") if h.original == "abia")
        assert hallazgo.sugerencias[0] == "había"

    def test_respeta_la_mayuscula_inicial(self, corrector):
        hallazgo = next(h for h in corrector.analiza("Hazer esto") if h.original == "Hazer")
        assert hallazgo.sugerencias[0] == "Hacer"

    def test_una_palabra_en_minuscula_no_se_vuelve_nombre_propio(self, corrector):
        for h in corrector.analiza("kansado"):
            assert not h.sugerencias or h.sugerencias[0][0].islower()


class TestCasosLimite:
    @pytest.mark.parametrize("texto", ["", "   ", "\n\t", None])
    def test_textos_vacios(self, corrector, texto):
        assert corrector.analiza(texto or "") == []

    def test_solo_numeros_y_signos(self, corrector):
        assert corrector.analiza("123 456 !!! ---") == []

    def test_no_marca_las_siglas(self, corrector):
        hallazgos = corrector.analiza("La ONU y el INE")
        assert all(h.original not in ("ONU", "INE") for h in hallazgos)

    def test_texto_muy_largo(self, corrector):
        texto = "hazer la tarea. " * 60
        hallazgos = corrector.analiza(texto)
        assert len(hallazgos) >= 50

    def test_palabra_rarisima_sin_sugerencias(self, corrector):
        hallazgos = corrector.analiza("xkcdqwzpl")
        assert hallazgos and hallazgos[0].explicacion

    def test_sin_tilde_y_sin_diccionario_no_truena(self, tmp_path):
        from yajol.nucleo.lexico import Lexico
        lx = Lexico(hunspell=None, extra=[], nombres=[], frecuencias={},
                    usuario_path=str(tmp_path / "m.txt"))
        c = Corrector(lexico=lx, usar_languagetool=False)
        assert isinstance(c.analiza("cualquier cosa"), list)


class TestSinFalsosPositivos:
    TEXTOS_CORRECTOS = [
        "El Instituto Tecnológico de Pinotepa ofrece Ingeniería en Sistemas Computacionales.",
        "Hoy por la mañana revisé la configuración del servidor y actualicé la base de datos.",
        "Si no vienes mañana, avísame por favor; tengo que entregar el reporte el viernes.",
        "Mi hermana María del Carmen estudia en la Universidad Nacional Autónoma de México.",
        "No sé qué hacer con este problema, pero creo que la solución está en el código.",
        "Aunque llovió mucho, salimos a caminar por el parque y compramos un café.",
        "El agua está fría y el águila vuela alto sobre la montaña.",
        "Le pedí que me dé una oportunidad más, aun así no aceptó.",
        "La corrección ortográfica funciona en Word, en el navegador y en cualquier programa.",
        "Necesito instalar el compilador antes de ejecutar el programa en Python.",
    ]

    @pytest.mark.parametrize("texto", TEXTOS_CORRECTOS)
    def test_un_texto_bien_escrito_no_se_marca(self, corrector, texto):
        hallazgos = [h for h in corrector.analiza(texto) if h.confianza >= 0.6]
        assert hallazgos == [], \
            f"Falso positivo: {[(h.original, h.regla) for h in hallazgos]}"

    def test_tasa_global_de_falsos_positivos(self, corrector):
        total = sum(len([h for h in corrector.analiza(t) if h.confianza >= 0.6])
                    for t in self.TEXTOS_CORRECTOS)
        assert total == 0, f"{total} falsos positivos en textos correctos"


class TestAprender:
    def test_la_palabra_aprendida_deja_de_marcarse(self, tmp_path):
        from yajol.nucleo.lexico import Lexico
        lx = Lexico(usuario_path=str(tmp_path / "mis.txt"))
        c = Corrector(lexico=lx, usar_languagetool=False)
        assert c.analiza("yajolina")
        assert c.aprende("yajolina")
        assert c.analiza("yajolina") == []


class TestExplicaciones:
    def test_toda_sugerencia_trae_explicacion(self, corrector):
        texto = "nose que aser, aveces jente kansado, jose hernandez, ¿porque?"
        for h in corrector.analiza(texto):
            assert h.explicacion.strip(), f"sin explicación: {h.original}"
            assert len(h.explicacion) > 15

    def test_explica_las_palabras_pegadas(self):
        texto = explica_pegadas("miscompañeros", "mis compañeros")
        assert "dos palabras" in texto

    def test_explica_sin_regla(self):
        assert "diccionario" in explica_sin_regla("xyz", "xy")


class TestGramaticaOpcional:
    def test_sin_languagetool_sigue_funcionando(self, lexico):
        c = Corrector(lexico=lexico, usar_languagetool=False)
        assert c.carga_gramatica() == ""
        assert c.herramienta is None
        assert c.analiza("hazer la tarea")

    def test_cerrar_es_seguro(self, lexico):
        c = Corrector(lexico=lexico, usar_languagetool=False)
        c.cierra()
        c.cierra()


class TestRendimiento:
    def test_revisa_rapido(self, corrector):
        import time
        texto = ("nose que aser aveces me siento kansado i no e echo la tarea "
                 "porque la problema es grande ") * 3
        inicio = time.perf_counter()
        corrector.analiza(texto)
        tardanza = time.perf_counter() - inicio
        assert tardanza < 2.0, f"tardó {tardanza:.2f}s"
