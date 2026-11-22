"""Pruebas de las reglas que necesitan ver la frase."""
import pytest

from yajol import config
from yajol.nucleo import reglas_texto as RT


def arregla(texto: str, regla: str = None) -> str:
    """Aplica los hallazgos de las reglas de contexto y devuelve el texto nuevo."""
    from yajol.nucleo.texto import aplica_cambios
    if regla is None:
        # la mayúscula inicial se prueba aparte: aquí estorba al comparar
        hallazgos = [h for h in RT.revisa(texto)
                     if h.regla not in ("mayuscula_inicial", "coma_antes_pero")]
    else:
        hallazgos = [h for h in RT.revisa(texto) if h.regla == regla]
    hallazgos = _sin_solapes(hallazgos)
    return aplica_cambios(texto, [(h.inicio, h.fin, h.mejor) for h in hallazgos if h.mejor])[0]


def _sin_solapes(hallazgos):
    elegidos = []
    for h in sorted(hallazgos, key=lambda x: (-x.confianza, x.inicio)):
        if not any(h.solapa(e) for e in elegidos):
            elegidos.append(h)
    return elegidos


def reglas_que_saltan(texto: str) -> set:
    return {h.regla for h in RT.revisa(texto)}


class TestPalabrasSeparadas:
    @pytest.mark.parametrize("malo,bueno", [
        ("osea no entiendo", "o sea no entiendo"),
        ("aveces me pierdo", "a veces me pierdo"),
        ("enserio lo digo", "en serio lo digo"),
        ("talvez venga", "tal vez venga"),
        ("almenos llegaste", "al menos llegaste"),
        ("apartir de hoy", "a partir de hoy"),
        ("nose la respuesta", "no sé la respuesta"),
        ("vamos ala escuela", "vamos a la escuela"),
        ("dile ami hermano", "dile a mí hermano"),
        ("esque no puedo", "es que no puedo"),
        ("porfavor ayúdame", "por favor ayúdame"),
        ("nisiquiera vino", "ni siquiera vino"),
    ])
    def test_separa_lo_que_va_separado(self, malo, bueno):
        assert arregla(malo) == bueno

    def test_la_categoria_es_la_correcta(self):
        hallazgo = next(h for h in RT.revisa("osea") if h.regla.startswith("separar"))
        assert hallazgo.categoria == config.CAT_SEPARADAS

    def test_respeta_la_mayuscula(self):
        assert arregla("Aveces me pierdo").startswith("A veces")


class TestPalabrasJuntas:
    @pytest.mark.parametrize("malo,bueno", [
        ("vino a demás tarde", "vino además tarde"),
        ("a penas llegó", "apenas llegó"),
        ("ven con migo", "ven conmigo"),
        ("tam bien yo", "también yo"),
    ])
    def test_une_lo_que_va_junto(self, malo, bueno):
        assert arregla(malo) == bueno


class TestHaberAVer:
    def test_haber_si_es_a_ver(self):
        assert arregla("Haber si vienes") == "A ver si vienes"

    def test_voy_haber_es_voy_a_ver(self):
        assert arregla("voy haber qué pasa") == "voy a ver qué pasa"

    def test_tiene_que_a_ver_es_haber(self):
        assert arregla("tiene que a ver una solución") == "tiene que haber una solución"


class TestHechoEcho:
    @pytest.mark.parametrize("malo,bueno", [
        ("ha echo la tarea", "ha hecho la tarea"),
        ("no he echo nada", "no he hecho nada"),
        ("de echo es cierto", "de hecho es cierto"),
    ])
    def test_distingue_hecho_de_echo(self, malo, bueno):
        assert arregla(malo) == bueno


class TestDequeismo:
    @pytest.mark.parametrize("malo,bueno", [
        ("pienso de que sí", "pienso que sí"),
        ("creo de que no", "creo que no"),
        ("dijo de que vendría", "dijo que vendría"),
        ("creyó de que era fácil", "creyó que era fácil"),
        ("pensaba de que no", "pensaba que no"),
        ("aseguró de que vendría", "aseguró que vendría"),
    ])
    def test_quita_el_de_que_sobrante(self, malo, bueno):
        assert arregla(malo) == bueno

    @pytest.mark.parametrize("texto", [
        "me di cuenta de que llovía",
        "estoy seguro de que vendrá",
        "se acordó de que era tarde",
    ])
    def test_no_quita_el_de_que_correcto(self, texto):
        assert "dequeismo" not in reglas_que_saltan(texto)

    def test_pone_el_de_que_que_falta(self):
        assert "cuenta de que" in arregla("me di cuenta que llovía")


class TestConcordancia:
    @pytest.mark.parametrize("malo,bueno", [
        ("la problema es grande", "el problema es grande"),
        ("una tema difícil", "un tema difícil"),
        ("la agua está fría", "el agua está fría"),
    ])
    def test_corrige_el_genero(self, malo, bueno):
        assert arregla(malo) == bueno


class TestTildesDiacriticas:
    @pytest.mark.parametrize("malo,bueno", [
        ("Tu eres el mejor", "Tú eres el mejor"),
        ("el dijo que vendría", "él dijo que vendría"),
        ("esto es para mi", "esto es para mí"),
        ("no se qué hacer", "no sé qué hacer"),
        ("quiero un te caliente", "quiero un té caliente"),
        ("mas o menos", "más o menos"),
        ("aun no llega", "aún no llega"),
        ("los de mas se fueron", "los demás se fueron"),
    ])
    def test_pone_la_tilde_que_distingue(self, malo, bueno):
        assert arregla(malo) == bueno

    @pytest.mark.parametrize("texto", ["para mi hermano", "con mi casa", "de mi parte"])
    def test_mi_posesivo_no_lleva_tilde(self, texto):
        assert "a_mi" not in reglas_que_saltan(texto)

    def test_aun_asi_no_lleva_tilde(self):
        assert "aun_no" not in reglas_que_saltan("aun así vino")


class TestHayAhiAy:
    @pytest.mark.parametrize("malo,bueno", [
        ("ay mucha gente", "hay mucha gente"),
        ("ay que estudiar", "hay que estudiar"),
        ("ay dos opciones", "hay dos opciones"),
    ])
    def test_distingue_hay_de_ay(self, malo, bueno):
        assert arregla(malo) == bueno

    def test_la_queja_se_queda_igual(self):
        assert "ay_cantidad" not in reglas_que_saltan("¡ay, qué dolor!")


class TestPreguntas:
    def test_los_interrogativos_llevan_tilde(self):
        assert arregla("¿como estas?", "interrogativo") == "¿cómo estas?"

    @pytest.mark.parametrize("texto,esperado", [
        ("¿que quieres?", "qué"),
        ("¿donde vives?", "dónde"),
        ("¿cuando llegas?", "cuándo"),
        ("¿quien vino?", "quién"),
    ])
    def test_cada_interrogativo(self, texto, esperado):
        assert esperado in arregla(texto, "interrogativo")

    def test_fuera_de_la_pregunta_no_cambia(self):
        assert "interrogativo" not in reglas_que_saltan("como quieras, donde sea")

    def test_avisa_del_signo_de_apertura(self):
        assert "falta_abrir" in reglas_que_saltan("Quieres venir?")

    def test_si_ya_esta_abierta_no_avisa(self):
        assert "falta_abrir" not in reglas_que_saltan("¿Quieres venir?")


class TestPuntuacion:
    def test_quita_el_espacio_doble(self):
        assert arregla("hola  mundo", "doble_espacio") == "hola mundo"

    def test_pide_espacio_tras_el_punto(self):
        assert "falta_espacio" in reglas_que_saltan("Vino.Llegó tarde")

    def test_avisa_de_la_palabra_repetida(self):
        assert arregla("el el perro", "repetida") == "el perro"

    def test_no_avisa_si_no_esta_repetida(self):
        assert "repetida" not in reglas_que_saltan("el perro de mi casa")


class TestMayusculas:
    def test_los_meses_van_en_minuscula(self):
        assert arregla("nos vemos en Enero", "calendario") == "nos vemos en enero"

    def test_los_dias_van_en_minuscula(self):
        assert arregla("llegó el Lunes", "calendario") == "llegó el lunes"

    def test_al_empezar_la_oracion_si_van_en_mayuscula(self):
        assert "calendario" not in reglas_que_saltan("Enero es un mes frío")

    def test_la_oracion_empieza_con_mayuscula(self):
        assert arregla("Vino ayer. llegó tarde", "mayuscula_inicial") == "Vino ayer. Llegó tarde"

    def test_no_toca_el_principio_del_fragmento(self):
        # al revisar las últimas palabras escritas, el trozo casi nunca
        # es el principio de una oración
        assert "mayuscula_inicial" not in reglas_que_saltan("hola mundo")


class TestSinFalsosPositivos:
    @pytest.mark.parametrize("texto", [
        "No sé qué hacer con este problema.",
        "El agua está fría y el águila vuela alto.",
        "Si no vienes mañana, avísame por favor.",
        "Aunque llovió mucho, salimos a caminar.",
        "Le pedí que me dé una oportunidad, aun así no aceptó.",
        "Hoy revisé la configuración del servidor.",
    ])
    def test_el_texto_correcto_no_se_toca(self, texto):
        hallazgos = [h for h in RT.revisa(texto)
                     if h.regla not in ("mayuscula_inicial", "coma_antes_pero")]
        assert hallazgos == [], f"Falso positivo: {[(h.original, h.regla) for h in hallazgos]}"


class TestEstructura:
    def test_hay_muchas_reglas(self):
        assert len(RT.REGLAS) >= 80

    def test_toda_regla_tiene_explicacion(self):
        sin_texto = [r.nombre for r in RT.REGLAS if not r.explicacion.strip()]
        assert not sin_texto, f"Reglas sin explicación: {sin_texto}"

    def test_los_nombres_no_se_repiten(self):
        nombres = [r.nombre for r in RT.REGLAS]
        repetidos = {n for n in nombres if nombres.count(n) > 1}
        assert not repetidos, f"Reglas repetidas: {repetidos}"

    def test_las_posiciones_caen_dentro_del_texto(self):
        texto = "osea aveces no se que aser, ¿porque?"
        for h in RT.revisa(texto):
            assert 0 <= h.inicio < h.fin <= len(texto)
            assert texto[h.inicio:h.fin] == h.original
