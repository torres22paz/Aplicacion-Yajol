"""Reglas que necesitan ver la frase, no solo la palabra.

Aquí están las confusiones que el diccionario nunca detecta porque las dos
palabras existen: «haber/a ver», «hecho/echo», «porque/por qué», las palabras
que se escriben juntas o separadas, la puntuación y las mayúsculas.

Para añadir una regla nueva basta con agregar una línea a las listas de abajo.
"""
import re

from .. import config
from .hallazgo import Hallazgo

# ---- Utilidades ----
LETRA = r"[a-záéíóúüñA-ZÁÉÍÓÚÜÑ]"
NO_LETRA = r"(?![a-záéíóúüñA-ZÁÉÍÓÚÜÑ])"


def _b(patron: str) -> str:
    """Pone límites de palabra. En Python \\b ya reconoce tildes y ñ como letras."""
    return rf"\b{patron}\b"


class Regla:
    """Una regla: busca un patrón y propone un reemplazo con su explicación."""

    def __init__(self, nombre, patron, reemplazo, explicacion, categoria,
                 confianza=0.85, banderas=re.IGNORECASE):
        self.nombre = nombre
        self.patron = re.compile(patron, banderas)
        self.reemplazo = reemplazo
        self.explicacion = explicacion
        self.categoria = categoria
        self.confianza = confianza

    def busca(self, texto: str) -> list:
        salida = []
        for m in self.patron.finditer(texto):
            # el grupo "e" marca el trozo exacto que está mal; si no hay, es toda la coincidencia
            try:
                ini, fin = m.span("e")
            except (IndexError, error_grupo):
                ini, fin = m.span()
            if ini < 0:
                ini, fin = m.span()
            original = texto[ini:fin]
            propuestas = self.reemplazo(m, original) if callable(self.reemplazo) else [self.reemplazo]
            propuestas = [p for p in propuestas if p and p != original]
            if not propuestas:
                continue
            salida.append(Hallazgo(self.categoria, original, ini, fin, propuestas,
                                   self.explicacion, self.nombre, self.confianza))
        return salida


error_grupo = re.error


def _conserva(original: str, nuevo: str) -> str:
    """Mantiene la mayúscula inicial del original."""
    if original[:1].isupper():
        return nuevo[:1].upper() + nuevo[1:]
    return nuevo


def _rep(nuevo):
    """Reemplazo fijo que respeta la mayúscula inicial."""
    return lambda m, original: [_conserva(original, nuevo)]


def _reps(*opciones):
    return lambda m, original: [_conserva(original, o) for o in opciones]


# =====================================================================
# 1. Palabras que se escriben SEPARADAS y mucha gente junta
# =====================================================================
SEPARAR = [
    # --- pegados cortos muy frecuentes ---
    ("nose", "no sé", "«No sé» son dos palabras y «sé» del verbo saber lleva tilde."),
    ("ami", "a mí", "«A mí» son dos palabras y «mí» lleva tilde después de preposición."),
    ("ati", "a ti", "«A ti» son dos palabras."),
    ("ala", "a la", "«A la» son dos palabras: la preposición a y el artículo la."),
    ("alas", "a las", "«A las» son dos palabras."),
    ("alos", "a los", "«A los» son dos palabras."),
    ("dela", "de la", "«De la» son dos palabras."),
    ("delas", "de las", "«De las» son dos palabras."),
    ("delos", "de los", "«De los» son dos palabras."),
    ("enla", "en la", "«En la» son dos palabras."),
    ("enel", "en el", "«En el» son dos palabras."),
    ("porla", "por la", "«Por la» son dos palabras."),
    ("porel", "por el", "«Por el» son dos palabras."),
    ("conla", "con la", "«Con la» son dos palabras."),
    ("conel", "con el", "«Con el» son dos palabras."),
    ("delque", "del que", "«Del que» son dos palabras."),
    ("aque", "a que", "«A que» son dos palabras."),
    ("deque", "de que", "«De que» son dos palabras."),
    ("selo", "se lo", "«Se lo» son dos palabras."),
    ("mela", "me la", "«Me la» son dos palabras."),
    ("melo", "me lo", "«Me lo» son dos palabras."),
    ("telo", "te lo", "«Te lo» son dos palabras."),
    ("sepuede", "se puede", "«Se puede» son dos palabras."),
    ("quiensabe", "quién sabe", "«Quién sabe» son dos palabras y «quién» lleva tilde."),
    ("porfin", "por fin", "«Por fin» son dos palabras."),
    ("aveses", "a veces", "«A veces» se escribe separado y «veces» va con c."),
    ("sobrelas", "sobre las", "«Sobre las» son dos palabras."),
    # --- expresiones ---
    ("osea", "o sea", "«O sea» son dos palabras: la conjunción o y el verbo sea."),
    ("aveces", "a veces", "«A veces» se escribe separado: es la preposición a más el sustantivo veces."),
    ("enserio", "en serio", "«En serio» se escribe separado."),
    ("talvez", "tal vez", "«Tal vez» se escribe separado."),
    ("almenos", "al menos", "«Al menos» se escribe separado."),
    ("apartir", "a partir", "«A partir» se escribe separado."),
    ("porsupuesto", "por supuesto", "«Por supuesto» se escribe separado."),
    ("sinembargo", "sin embargo", "«Sin embargo» se escribe separado."),
    ("derrepente", "de repente", "«De repente» se escribe separado y con una sola r."),
    ("derepente", "de repente", "«De repente» se escribe separado."),
    ("amenudo", "a menudo", "«A menudo» se escribe separado."),
    ("esque", "es que", "«Es que» son dos palabras: el verbo es y la conjunción que."),
    ("porfavor", "por favor", "«Por favor» se escribe separado."),
    ("asique", "así que", "«Así que» se escribe separado y así lleva tilde."),
    ("nisiquiera", "ni siquiera", "«Ni siquiera» se escribe separado."),
    ("yaque", "ya que", "«Ya que» se escribe separado."),
    ("paraque", "para que", "«Para que» se escribe separado."),
    ("dedonde", "de donde", "«De donde» se escribe separado."),
    ("acuerdate", "acuérdate", "«Acuérdate» es esdrújula y siempre lleva tilde."),
    ("aparte de eso", "aparte de eso", ""),
    ("sobretodo", "sobre todo", "Cuando significa «principalmente» se escribe separado: sobre todo. "
                                "Junto, «sobretodo» es un abrigo."),
    ("comoquiera", "como quiera", "«Como quiera» se escribe separado cuando es «de la manera que quiera»."),
    ("encuanto", "en cuanto", "«En cuanto» se escribe separado."),
    ("apesar", "a pesar", "«A pesar» se escribe separado."),
    ("enfin", "en fin", "«En fin» se escribe separado."),
    ("porejemplo", "por ejemplo", "«Por ejemplo» se escribe separado."),
    ("decir que", "decir que", ""),
    ("aunqe", "aunque", "Se escribe «aunque»."),
    ("sobremanera", "sobremanera", ""),
    ("todabia", "todavía", "Se escribe «todavía», con v y con tilde en la í."),
    ("enverdad", "en verdad", "«En verdad» se escribe separado."),
    ("aloteiempo", "a lo tiempo", ""),
    ("porlomenos", "por lo menos", "«Por lo menos» se escribe en tres palabras."),
    ("sobreque", "sobre qué", "«Sobre qué» se escribe separado y qué lleva tilde en preguntas."),
    ("adondequiera", "adondequiera", ""),
]

# Palabras que se escriben JUNTAS y mucha gente separa
UNIR = [
    (r"a\s+demás", "además", "«Además» se escribe en una sola palabra."),
    (r"de\s+bajo\s+de", "debajo de", "«Debajo» se escribe en una sola palabra."),
    (r"a\s+penas", "apenas", "«Apenas» se escribe en una sola palabra."),
    (r"con\s+migo", "conmigo", "«Conmigo» se escribe en una sola palabra."),
    (r"con\s+tigo", "contigo", "«Contigo» se escribe en una sola palabra."),
    (r"tam\s+bien", "también", "«También» se escribe en una sola palabra y lleva tilde."),
    (r"tam\s+poco", "tampoco", "«Tampoco» se escribe en una sola palabra."),
    (r"a\s+cerca\s+de", "acerca de", "Cuando significa «sobre», se escribe «acerca de» en una palabra."),
    (r"por\s+venir\s+el\s+futuro", "porvenir", ""),
    (r"en\s+tonces", "entonces", "«Entonces» se escribe en una sola palabra."),
    (r"si\s+quiera", "siquiera", "«Siquiera» se escribe junto cuando significa «al menos»."),
    (r"a\s+si\s+que", "así que", "Se escribe «así que»."),
    (r"de\s+mas\s+iado", "demasiado", ""),
    (r"me\s+nos\s+mal", "menos mal", ""),
    (r"bien\s+venido", "bienvenido", "«Bienvenido» se escribe en una sola palabra."),
    (r"buenas\s+noches", "buenas noches", ""),
]

# =====================================================================
# 2. Palabras que se confunden porque suenan igual
# =====================================================================
CONFUSIONES = [
    # conjunción y / letra i
    ("i_conjuncion", r"(?<=[a-záéíóúñ]\s)(?P<e>i)(?=\s[a-záéíóúñ])", "y",
     "La conjunción se escribe «y»: «pan y agua». La letra i sola no une palabras."),
    # he / e
    ("e_auxiliar", r"(?<=\s)(?P<e>e)\s+(?=\w+(?:ado|ido|cho|sto|to|so)\b)", "he",
     "El verbo haber en primera persona es «he»: «he comido», «he hecho»."),
    # haber / a ver
    ("haber_si", _b(r"(?P<e>haber)\s+(?=si\b)"), "a ver",
     "«A ver» (de mirar o comprobar) son dos palabras. «Haber» es el verbo: «tiene que haber»."),
    ("voy_haber", _b(r"(?:voy|vamos|vas|van)\s+(?P<e>haber)\b"), "a ver",
     "Después de «voy/vamos» va «a ver»: «voy a ver qué pasa». «Haber» es el infinitivo del verbo."),
    ("a_ver_hay", _b(r"(?:puede|pueden|debe|debes|tiene|tienen|tengo|va|van|deber[ií]a|suele)\s+(?:que\s+)?(?P<e>a\s+ver)"), "haber",
     "Aquí va el verbo «haber»: «tiene que haber», «puede haber»."),
    # hecho / echo
    ("ha_echo", _b(r"(?:ha|he|e|has|han|hemos|hab[ií]an?)\s+(?P<e>echo)"), "hecho",
     "El participio del verbo hacer es «hecho», con h. «Echo» es del verbo echar."),
    ("de_echo", _b(r"(?P<e>de\s+echo)\b"), "de hecho",
     "La expresión es «de hecho», con h."),
    ("echo_menos", _b(r"(?P<e>hecho)\s+de\s+menos\b"), "echo",
     "«Echar de menos» va sin h: «te echo de menos»."),
    # hay / ahí / ay
    ("ay_cantidad", _b(r"(?P<e>ay)\s+(?=mucho|mucha|muchos|muchas|poco|poca|pocos|pocas|"
                        r"un\b|una\b|unos\b|unas\b|dos\b|tres\b|gente\b|personas\b|"
                        r"algo\b|alguien\b|varios\b|varias\b|demasiad)"), "hay",
     "«Hay» del verbo haber indica que algo existe: «hay mucha gente». "
     "«¡Ay!» es una queja y «ahí» es un lugar."),
    ("ay_que", _b(r"(?P<e>ay|ahí)\s+que\s+(?=\w+r\b)"), "hay",
     "«Hay que» viene del verbo haber. «Ahí» es lugar y «¡ay!» es una queja."),
    ("hay_lugar", _b(r"(?P<e>hay)\s+(?=est[aá]|estaba|viene|vienen|vamos|voy|mismo)"), "ahí",
     "«Ahí» indica lugar y lleva tilde. «Hay» es del verbo haber."),
    # tuvo / tubo
    ("tubo_que", _b(r"(?P<e>tubo)\s+que\b"), "tuvo",
     "«Tuvo» es del verbo tener. «Tubo» es la pieza hueca."),
    # vaya / valla
    ("valla_a", _b(r"(?P<e>valla)\s+(?=a\b|usted|bien|mal)"), "vaya",
     "«Vaya» es del verbo ir. «Valla» es una cerca y «baya» es un fruto."),
    # sino / si no
    ("si_no_que", _b(r"(?P<e>si\s+no)\s+que\b"), "sino",
     "«Sino» junto cuando contrapone: «no fue Juan, sino Pedro»."),
    # ves / vez
    ("tal_ves", _b(r"(?:tal|una|otra|cada|alguna|esta|la)\s+(?P<e>ves)\b"), "vez",
     "«Vez» se escribe con z. «Ves» es del verbo ver."),
    ("a_veses", _b(r"(?P<e>veses)\b"), "veces",
     "El plural de «vez» es «veces», con c."),
    # haz / has
    ("haz_participio", _b(r"(?P<e>haz)\s+(?=\w+(?:ado|ido|cho|sto|to)\b)"), "has",
     "«Has» con s acompaña al participio: «has hecho». «Haz» es el imperativo de hacer."),
    ("has_imperativo", _b(r"(?P<e>has)\s+(?=caso\b|clic\b|lo\b|el\b|la\b|una\b|un\b)"), "haz",
     "«Haz» es la orden del verbo hacer: «haz caso», «haz clic»."),
    # dequeísmo
    ("dequeismo", r"\b(?:piens|cre[íi]?|crey|cre[eé]|creem|opin|consider|dij|dic|dig|"
                  r"supon|supus|imagin|coment|mencion|asegur|afirm|sospech|pens|resulta|parec)"
                  r"\w*\s+(?P<e>de\s+que)\b", "que",
     "Sobra el «de»: se dice «pienso que», «creo que», «dijo que»."),
    ("queismo_cuenta", _b(r"(?:cuenta|seguro|segura|consciente|convencido)\s+(?P<e>que)\b"), "de que",
     "Aquí falta el «de»: «darse cuenta de que», «estar seguro de que»."),
    # concordancia frecuente
    ("la_problema", _b(r"(?P<e>la|una|esta|otra)\s+(?=problema|tema|idioma|mapa|clima|sistema|programa|planeta)"),
     lambda m, o: [_conserva(o, {"la": "el", "una": "un", "esta": "este", "otra": "otro"}[o.lower()])],
     "Problema, tema, idioma, mapa, clima, sistema y programa son masculinos: «el problema», «un tema».",
     ),
    ("la_agua", _b(r"(?P<e>la|una)\s+(?=agua|águila|alma|aula|área|hambre|arma)\b"),
     lambda m, o: [_conserva(o, "el" if o.lower() == "la" else "un")],
     "Delante de palabras femeninas que empiezan con a tónica se usa «el» o «un»: el agua, un águila."),
    # más / mas
    ("mas_o_menos", _b(r"(?P<e>mas)\s+(?=o\s+menos|de\b|que\b|bien\b|tarde\b|temprano\b|grande\b|vale\b)"), "más",
     "«Más» de cantidad lleva tilde. «Mas» sin tilde solo significa «pero»."),
    ("no_mas", _b(r"(?:no|nada|algo|poco|mucho)\s+(?P<e>mas)\b"), "más",
     "«Más» de cantidad lleva tilde."),
    # pronombres con tilde
    ("el_verbo", _b(r"(?P<e>el)\s+(?=dijo|dice|vino|fue\b|hizo|quiere|tiene|sabe|puede|est[aá]\b|era\b|me\b|le\b|lo\b|nos\b)"), "él",
     "«Él» con tilde es la persona; «el» sin tilde es el artículo: «el libro»."),
    ("tu_verbo", _b(r"(?P<e>tu)\s+(?=eres|tienes|puedes|sabes|quieres|vas\b|est[aá]s|dices|hiciste|fuiste|tambi[eé]n\b)"), "tú",
     "«Tú» con tilde es la persona; «tu» sin tilde indica posesión: «tu casa»."),
    ("a_mi", _b(r"(?:a|para|por|de|en|sin|contra|hacia|sobre)\s+(?P<e>mi)"
                r"(?=\s*[,.;:!?]|\s*$|\s+(?:me\b|no\b|s[ií]\b|ya\b|tambi[eé]n\b))"), "mí",
     "Después de preposición se escribe «mí» con tilde: «para mí», «a mí»."),
    ("no_se", _b(r"(?:no|yo)\s+(?P<e>se)\s+(?=qu[eé]\b|si\b|c[oó]mo\b|cu[aá]ndo\b|d[oó]nde\b|nada\b|mucho\b|bien\b|si\b)"), "sé",
     "«Sé» del verbo saber lleva tilde: «no sé qué»."),
    ("se_que", _b(r"(?<![a-záéíóúñ]\s)(?P<e>se)\s+que\s+(?=\w)"), "sé",
     "«Sé que» lleva tilde porque es el verbo saber."),
    ("de_subjuntivo", _b(r"(?:me|le|te|nos|les)\s+(?P<e>de)\s+(?=un|una|el|la|los|las|m[aá]s)"), "dé",
     "«Dé» del verbo dar lleva tilde para no confundirla con la preposición «de»."),
    ("que_si", _b(r"(?:dijo|dije|dice|dicen|creo|claro|pienso|digo)\s+que\s+(?P<e>si)(?=\s*[.,;!?]|$)"), "sí",
     "«Sí» de afirmación lleva tilde."),
    ("si_afirmacion", _b(r"(?P<e>si)\s*,\s*(?=por supuesto|claro|gracias|señor)"), "sí",
     "«Sí» de afirmación lleva tilde."),
    ("te_bebida", _b(r"(?:un|el|tomar|beber|tomo|tomé)\s+(?P<e>te)(?=[\s,.;:!?]|$)"), "té",
     "«Té» (la bebida) lleva tilde. «Te» sin tilde es el pronombre: «te quiero»."),
    # porque / por qué / porqué
    ("por_que_pregunta", r"¿\s*(?P<e>por\s*que)\b", "por qué",
     "En preguntas se escribe «por qué», separado y con tilde."),
    ("porque_pregunta", r"¿\s*(?P<e>porqu[eé])\b", "por qué",
     "En preguntas se escribe «por qué», separado y con tilde."),
    ("el_porque", _b(r"(?:el|un|su|ese|este)\s+(?P<e>por\s*qu[eé])\b"), "porqué",
     "Cuando es un sustantivo («el motivo») se escribe «porqué», junto y con tilde."),
    # aún / aun
    ("aun_no", _b(r"(?P<e>aun)\s+(?=no\b|est\w*\b|sigue\b|falta\b|queda\b|era\b|hoy\b|tengo\b|tiene\b)"), "aún",
     "«Aún» con tilde significa «todavía». «Aun» sin tilde significa «incluso»."),
    # demás / de más
    ("los_de_mas", _b(r"(?:los|las|lo)\s+(?P<e>de\s+m[aá]s)\b"), "demás",
     "«Los demás» se escribe junto cuando significa «los otros»."),
    # sesión / cesión, cocer / coser y parecidos
    ("sesion_clase", _b(r"(?P<e>seción|sessión|cesión)\s+(?=de\s+(?:clase|fotos|trabajo|terapia))"), "sesión",
     "«Sesión» (reunión o tanda) se escribe con s y con c: s-e-s-i-ó-n."),
    # repeticiones
    ("repetida", _b(r"(?P<e>(?:el|la|los|las|de|que|y|a|en|un|una|lo|se|no)\s+\1)") + "", None,
     "La palabra está repetida.", ),
]

# =====================================================================
# 3. Puntuación y espacios
# =====================================================================
PUNTUACION = [
    ("doble_espacio", r"(?P<e>  +)", " ",
     "Hay más de un espacio seguido."),
    ("espacio_antes_signo", r"(?P<e>\s+(?=[,;:.!?](?:\s|$)))", "",
     "No se deja espacio antes de la coma, el punto ni el punto y coma."),
    ("falta_espacio", r"(?P<e>[,;:](?=[a-záéíóúñ]))", None,
     "Después de la coma y del punto y coma siempre va un espacio."),
    ("coma_antes_pero", r"(?<=[a-záéíóúñ])(?P<e>\s+pero\s)", ", pero ",
     "Antes de «pero» suele ir una coma."),
]

# ---- Construcción de la lista final ----
def _regla_separar(junta, separada, explicacion):
    return Regla(f"separar_{junta}", _b(f"(?P<e>{junta})"), _rep(separada),
                 explicacion, config.CAT_SEPARADAS, 0.95)


def _regla_unir(patron, unida, explicacion):
    return Regla(f"unir_{unida}", _b(f"(?P<e>{patron})"), _rep(unida),
                 explicacion, config.CAT_PEGADAS, 0.9)


def construye_reglas() -> list:
    reglas = []
    for junta, separada, exp in SEPARAR:
        if exp:
            reglas.append(_regla_separar(junta, separada, exp))
    for patron, unida, exp in UNIR:
        if exp:
            reglas.append(_regla_unir(patron, unida, exp))
    for item in CONFUSIONES:
        nombre, patron, rep, exp = item[0], item[1], item[2], item[3]
        if rep is None:
            continue
        reemplazo = rep if callable(rep) else _rep(rep)
        reglas.append(Regla(nombre, patron, reemplazo, exp, config.CAT_CONFUSION, 0.8))
    for nombre, patron, rep, exp in PUNTUACION:
        if rep is None:
            continue
        reglas.append(Regla(nombre, patron, rep, exp, config.CAT_PUNTUACION, 0.7))
    return reglas


REGLAS = construye_reglas()


# ---- Reglas con lógica propia ----
INTERROGATIVOS = {
    "que": "qué", "como": "cómo", "cuando": "cuándo", "donde": "dónde",
    "quien": "quién", "quienes": "quiénes", "cual": "cuál", "cuales": "cuáles",
    "cuanto": "cuánto", "cuanta": "cuánta", "cuantos": "cuántos", "cuantas": "cuántas",
    "adonde": "adónde", "porque": "por qué",
}
_INTERROG_RE = re.compile(_b(r"(?P<e>" + "|".join(INTERROGATIVOS) + r")"), re.IGNORECASE)
_PREGUNTA_RE = re.compile(r"¿[^¿?]*\?|¿[^¿?]*$")


def tildes_en_preguntas(texto: str) -> list:
    """Dentro de ¿...? los interrogativos llevan tilde: ¿que? -> ¿qué?"""
    salida = []
    for pregunta in _PREGUNTA_RE.finditer(texto):
        trozo = pregunta.group()
        for m in _INTERROG_RE.finditer(trozo):
            ini = pregunta.start() + m.start("e")
            fin = pregunta.start() + m.end("e")
            original = texto[ini:fin]
            correcta = _conserva(original, INTERROGATIVOS[original.lower()])
            salida.append(Hallazgo(config.CAT_ACENTO, original, ini, fin, [correcta],
                                   f"Dentro de una pregunta, «{original.lower()}» lleva tilde: "
                                   f"«{correcta.lower()}».", "interrogativo", 0.9))
            break   # solo el primer interrogativo de cada pregunta
    return salida


_REPETIDA_RE = re.compile(_b(r"(?P<p>[a-záéíóúñ]{1,6})\s+(?P=p)"), re.IGNORECASE)


def palabras_repetidas(texto: str) -> list:
    salida = []
    for m in _REPETIDA_RE.finditer(texto):
        palabra = m.group("p")
        salida.append(Hallazgo(config.CAT_GRAMATICA, m.group(), m.start(), m.end(), [palabra],
                               f"La palabra «{palabra}» está repetida.", "repetida", 0.75))
    return salida


_PREGUNTA_SIN_ABRIR = re.compile(r"(?:^|(?<=[.!?\n]))\s*(?P<e>[^¿¡.!?\n]{3,})\?")


def signos_de_apertura(texto: str) -> list:
    """En español las preguntas y exclamaciones abren con ¿ o ¡."""
    salida = []
    for m in _PREGUNTA_SIN_ABRIR.finditer(texto):
        ini = m.start("e")
        trozo = m.group("e").lstrip()
        ini += len(m.group("e")) - len(trozo)
        if not trozo:
            continue
        salida.append(Hallazgo(config.CAT_PUNTUACION, trozo, ini, m.end("e"), ["¿" + trozo],
                               "En español las preguntas se abren con el signo ¿.",
                               "falta_abrir", 0.8))
    return salida


_FALTA_ESPACIO = re.compile(r"(?P<e>[,;](?=[A-Za-záéíóúñÁÉÍÓÚÑ])|\.(?=[A-ZÁÉÍÓÚÑ]))")


def falta_espacio(texto: str) -> list:
    salida = []
    for m in _FALTA_ESPACIO.finditer(texto):
        signo = m.group("e")
        salida.append(Hallazgo(config.CAT_PUNTUACION, signo, m.start("e"), m.end("e"), [signo + " "],
                               f"Después de «{signo}» siempre va un espacio.", "falta_espacio", 0.7))
    return salida


MESES = ("enero febrero marzo abril mayo junio julio agosto septiembre "
         "octubre noviembre diciembre").split()
DIAS = "lunes martes miércoles jueves viernes sábado domingo".split()
_CALENDARIO_RE = re.compile(r"\b(?P<e>" + "|".join(m.capitalize() for m in MESES + DIAS) + r")\b")
_INICIO_ORACION = re.compile(r"(?:^|[.!?¿¡\n]\s*)$")


def meses_y_dias(texto: str) -> list:
    """En español los meses y los días van en minúscula, salvo al empezar la oración."""
    salida = []
    for m in _CALENDARIO_RE.finditer(texto):
        if _INICIO_ORACION.search(texto[:m.start("e")]):
            continue
        original = m.group("e")
        que = "Los meses" if original.lower() in MESES else "Los días de la semana"
        salida.append(Hallazgo(config.CAT_MAYUSCULA, original, m.start("e"), m.end("e"),
                               [original.lower()],
                               f"{que} se escriben con minúscula en español, "
                               "salvo cuando empiezan la oración.", "calendario", 0.6))
    return salida


_MINUSCULA_INICIAL = re.compile(r"(?:[.!?]\s+|\n\s*)(?P<e>[a-záéíóúñ])")


def mayuscula_inicial(texto: str) -> list:
    """Después de un punto, la oración empieza con mayúscula.

    No se revisa la primera letra del texto: al revisar solo las últimas
    palabras escritas, ese trozo casi nunca es el principio de una oración.
    """
    salida = []
    for m in _MINUSCULA_INICIAL.finditer(texto):
        letra = m.group("e")
        salida.append(Hallazgo(config.CAT_MAYUSCULA, letra, m.start("e"), m.end("e"),
                               [letra.upper()],
                               "Toda oración empieza con mayúscula.", "mayuscula_inicial", 0.55))
    return salida


ESPECIALES = [meses_y_dias, mayuscula_inicial, tildes_en_preguntas, palabras_repetidas, signos_de_apertura, falta_espacio]


def revisa(texto: str, reglas: list = None) -> list:
    """Aplica todas las reglas de contexto y devuelve los hallazgos ordenados."""
    reglas = REGLAS if reglas is None else reglas
    salida = []
    for regla in reglas:
        salida.extend(regla.busca(texto))
    for especial in ESPECIALES:
        salida.extend(especial(texto))
    return sorted(salida, key=lambda h: (h.inicio, -h.confianza))
