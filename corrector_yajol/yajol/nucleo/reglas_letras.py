"""Reglas de letras: genera la escritura correcta de una palabra y explica por qué.

La idea es sencilla: cuando una palabra no está en el diccionario se prueban
las confusiones típicas del español (s/c/z, b/v, g/j, ll/y, h, m/n...) y las
tildes que faltan. Si alguna variante sí está en el diccionario, se propone y
se explica con la regla que corresponde.
"""
import re

from .texto import TILDES, VOCALES, normaliza

# ---- Explicaciones por regla ----
R = {
    "c_antes_ei": "Delante de e o i, ese sonido se escribe con c: hacer, cocina, vecino. "
                  "La z casi nunca va delante de e o i (solo en casos como zeta, zigzag o enzima).",
    "z_antes_aou": "Delante de a, o, u ese sonido se escribe con z: zapato, zorro, azúcar.",
    "s_sonido": "Aquí el sonido /s/ se escribe con s.",
    "c_sonido": "Aquí el sonido /s/ se escribe con c.",
    "cc_cion": "Lleva doble c porque existe una palabra de la misma familia con -ct-: "
               "acción va con acto, dirección con directo, redacción con redactor.",
    "imperfecto_b": "Las terminaciones del pretérito imperfecto (-aba, -abas, -ábamos, -aban) "
                    "siempre se escriben con b: cantaba, jugábamos.",
    "mb": "Antes de b siempre se escribe m, nunca n: cambio, hombre, también.",
    "mp": "Antes de p siempre se escribe m, nunca n: campo, siempre, comprar.",
    "nv": "Después de n se escribe v, no b: invierno, enviar, convenio.",
    "b_general": "Esta palabra se escribe con b. En español b y v suenan igual, "
                 "así que conviene memorizar la forma correcta.",
    "v_general": "Esta palabra se escribe con v. En español b y v suenan igual, "
                 "así que conviene memorizar la forma correcta.",
    "bir": "Los verbos terminados en -bir se escriben con b: escribir, recibir, subir. "
           "Solo hervir, servir y vivir son excepción.",
    "ger_gir": "Los verbos terminados en -ger y -gir se escriben con g: proteger, dirigir, elegir. "
               "Solo tejer y crujir son excepción.",
    "aje": "Las palabras terminadas en -aje y -jero se escriben con j: mensaje, garaje, viajero.",
    "j_general": "Esta palabra se escribe con j.",
    "g_general": "Esta palabra se escribe con g.",
    "h_inicial": "Esta palabra lleva h al principio aunque no se pronuncie: hacer, hoy, hombre.",
    "h_sobra": "Esta palabra no lleva h.",
    "h_intervocal": "Esta palabra lleva una h entre vocales aunque no se pronuncie: ahora, ahí, prohibir.",
    "hie_hue": "Las palabras que empiezan con el sonido ie o ue llevan h: hielo, hueso, huevo.",
    "ll_general": "Esta palabra se escribe con ll: calle, llave, pollo.",
    "y_general": "Esta palabra se escribe con y: ayer, mayo, apoyo.",
    "illo": "Los diminutivos y terminaciones -illo, -illa se escriben con ll: cuchillo, mesilla.",
    "k_c": "En español la k casi no se usa: ese sonido se escribe con c delante de a, o, u "
           "y con qu delante de e, i: casa, queso, kilo (excepción).",
    "qu": "Delante de e y de i, el sonido /k/ se escribe qu: queso, quiso.",
    "doble_r": "Entre vocales, el sonido fuerte de la r se escribe rr: perro, carro, corrección.",
    "una_r": "Aquí basta con una r.",
    "x_s": "Esta palabra se escribe con x: examen, éxito, exacto.",
    "tilde": "Falta la tilde.",
    "sobra_tilde": "Esta palabra no lleva tilde.",
    "una_l": "Aquí basta con una l.",
    "j_final": "Al final de palabra ese sonido se escribe con j: reloj, carcaj, boj.",
    "y_i": "La conjunción y y el final de palabra se escriben con y: hay, rey, muy.",
}

# ---- Cambios de una letra por otra ----
# (patrón, reemplazo, regla). El patrón se busca en cualquier posición.
CAMBIOS = [
    # seseo: s / c / z
    (r"z(?=[ei])", "c", "c_antes_ei"),
    (r"s(?=[ei])", "c", "c_antes_ei"),
    (r"c(?=[ei])", "s", "s_sonido"),
    (r"s(?=[aou])", "z", "z_antes_aou"),
    (r"z(?=[aou])", "s", "s_sonido"),
    (r"c(?=[aou])", "z", "z_antes_aou"),
    (r"s(?=[ei])", "z", "z_antes_aou"),
    (r"x", "s", "s_sonido"),
    (r"s", "x", "x_s"),
    (r"cs", "x", "x_s"),
    (r"cs", "xc", "x_s"),
    (r"s(?=[ec])", "xc", "x_s"),
    (r"x(?=[ei])", "xc", "x_s"),
    # b / v
    (r"b", "v", "v_general"),
    (r"v", "b", "b_general"),
    # g / j
    (r"j(?=[ei])", "g", "ger_gir"),
    (r"g(?=[ei])", "j", "j_general"),
    (r"g(?=[ei])", "gu", "g_general"),
    (r"gu(?=[ei])", "g", "g_general"),
    (r"j(?=[aou])", "g", "g_general"),
    (r"j(?=u[ei])", "gu", "g_general"),
    # ll / y
    (r"ll", "y", "y_general"),
    (r"y", "ll", "ll_general"),
    (r"i(?=\b)", "y", "y_i"),
    # k / qu / c
    (r"k(?=[ei])", "qu", "k_c"),
    (r"k(?=[aou])", "c", "k_c"),
    (r"qu(?=[ei])", "c", "k_c"),
    (r"c(?=[ei])", "qu", "qu"),
    # m / n
    (r"n(?=[bv])", "m", "mb"),
    (r"n(?=p)", "m", "mp"),
    (r"m(?=[bv])", "n", "nv"),
    # dobles
    (r"rr", "r", "una_r"),
    (r"r", "rr", "doble_r"),
    (r"cc", "c", "c_sonido"),
    (r"c(?=i[óo]n)", "cc", "cc_cion"),
    (r"ll", "l", "una_l"),
    (r"g$", "j", "j_final"),
    (r"j$", "g", "g_general"),
    (r"l(?=[aeiou])", "ll", "ll_general"),
    # h
    (r"^h", "", "h_sobra"),
    (r"h", "", "h_sobra"),
]

# Cambios que añaden una letra en vez de sustituirla
INSERCIONES = [
    ("^", "h", "h_inicial"),
]
# La h también aparece entre vocales: ahora, ahí, búho, prohibir
H_INTERVOCAL = re.compile(r"(?<=[aeiouáéíóú])(?=[aeiouáéíóú])")

SIN_TILDE = "aeiou"
CON_TILDE = "áéíóú"
MAPA_TILDE = dict(zip(SIN_TILDE, CON_TILDE))
MAPA_QUITA = dict(zip(CON_TILDE, SIN_TILDE))

MAX_VARIANTES = 400


def _afina_regla(regla: str, correcta: str, erronea: str) -> str:
    """Ajusta la explicación a la palabra concreta cuando hay una regla más precisa."""
    baja = correcta.lower()
    if regla in ("b_general", "v_general"):
        if re.search(r"[áa]ba(?:s|mos|is|n)?$", baja) or baja.endswith("aba"):
            return "imperfecto_b"
        if baja.endswith("bir"):
            return "bir"
        if re.search(r"mb", baja) and re.search(r"nv|nb", erronea.lower()):
            return "mb"
        if re.search(r"nv", baja):
            return "nv"
    if regla in ("j_general", "g_general", "ger_gir"):
        if baja.endswith(("aje", "ajes", "jero", "jera")):
            return "aje"
        if re.search(r"g(er|ir)$", baja):
            return "ger_gir"
    if regla in ("ll_general", "y_general") and re.search(r"ill[oa]s?$", baja):
        return "illo"
    if regla == "h_inicial" and re.match(r"h(ie|ue)", baja):
        return "hie_hue"
    return regla


def variantes_tilde(palabra: str) -> list:
    """Versiones de la palabra con una tilde puesta o quitada."""
    salida = []
    for i, car in enumerate(palabra):
        bajo = car.lower()
        if bajo in MAPA_TILDE:
            nueva = MAPA_TILDE[bajo]
            salida.append(palabra[:i] + (nueva.upper() if car.isupper() else nueva) + palabra[i + 1:])
        elif bajo in MAPA_QUITA:
            nueva = MAPA_QUITA[bajo]
            salida.append(palabra[:i] + (nueva.upper() if car.isupper() else nueva) + palabra[i + 1:])
    return salida


def variantes_letras(palabra: str) -> dict:
    """{variante: regla} aplicando una confusión de letras a la vez y a todas las posiciones."""
    baja = palabra.lower()
    salida = {}
    for patron, reemplazo, regla in CAMBIOS:
        compilado = re.compile(patron)
        posiciones = [m.span() for m in compilado.finditer(baja)]
        if not posiciones:
            continue
        # una posición a la vez
        for ini, fin in posiciones[:6]:
            nueva = baja[:ini] + reemplazo + baja[fin:]
            if nueva != baja:
                salida.setdefault(nueva, regla)
        # todas las posiciones de golpe
        if len(posiciones) > 1:
            nueva = compilado.sub(reemplazo, baja)
            if nueva != baja:
                salida.setdefault(nueva, regla)
        if len(salida) > MAX_VARIANTES:
            break
    for patron, letra, regla in INSERCIONES:
        nueva = re.sub(patron, letra, baja, count=1)
        if nueva != baja:
            salida.setdefault(nueva, regla)
    for m in H_INTERVOCAL.finditer(baja):
        salida.setdefault(baja[:m.start()] + "h" + baja[m.start():], "h_intervocal")
    return salida


def candidatos(palabra: str, existe) -> list:
    """
    Busca la forma correcta probando las confusiones típicas.

    `existe` es una función que dice si una palabra está en el diccionario.
    Devuelve una lista de (palabra_correcta, regla) ordenada por cercanía.
    """
    encontrados = {}

    def prueba(variante, regla):
        if variante and variante != palabra.lower() and existe(variante):
            encontrados.setdefault(variante, regla)

    # 1. solo tildes
    for v in variantes_tilde(palabra.lower()):
        prueba(v, "tilde")
    # 2. una confusión de letras
    letras = variantes_letras(palabra)
    for v, regla in letras.items():
        prueba(v, regla)
    # 3. letras + tilde (lapizes -> lapices -> lápices)
    if not encontrados:
        for v, regla in list(letras.items())[:150]:
            for t in variantes_tilde(v):
                prueba(t, regla)
    # 4. dos confusiones de letras (canvio -> cambio; tanvien -> tambien)
    dobles = {}
    if not encontrados:
        for v in list(letras)[:60]:
            for v2, regla2 in variantes_letras(v).items():
                dobles.setdefault(v2, regla2)
                prueba(v2, regla2)
    # 5. dos confusiones + tilde (corecion -> correccion -> corrección)
    if not encontrados:
        for v, regla in list(dobles.items())[:400]:
            for t in variantes_tilde(v):
                prueba(t, regla)

    # las formas con tilde de lo encontrado también valen (lapices / lápices)
    for v, regla in list(encontrados.items()):
        for t in variantes_tilde(v):
            if t != v and existe(t):
                encontrados.setdefault(t, regla if regla != "tilde" else "tilde")

    orden = sorted(encontrados.items(), key=lambda kv: (len(kv[0]) != len(palabra), kv[0]))
    return [(p, _afina_regla(r, p, palabra)) for p, r in orden]


def explica(regla: str, erronea: str, correcta: str) -> str:
    """Texto que se le muestra al usuario."""
    detalle = R.get(regla, "")
    if regla == "tilde":
        return f"«{erronea}» lleva tilde: se escribe «{correcta}»."
    if regla == "sobra_tilde":
        return f"«{erronea}» no lleva tilde: se escribe «{correcta}»."
    cabeza = f"Se escribe «{correcta}», no «{erronea}». "
    return (cabeza + detalle).strip()


# ---- Diagnóstico de la diferencia entre dos palabras ----
def diferencia_simple(erronea: str, correcta: str) -> str:
    """Describe en pocas palabras qué cambió, para las correcciones sin regla propia."""
    import difflib
    a, b = erronea.lower(), correcta.lower()
    partes = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b).get_opcodes():
        if tag == "insert":
            partes.append(f"falta «{b[j1:j2]}»")
        elif tag == "delete":
            partes.append(f"sobra «{a[i1:i2]}»")
        elif tag == "replace":
            partes.append(f"«{a[i1:i2]}» debería ser «{b[j1:j2]}»")
    return "; ".join(partes[:3]) or "solo cambian mayúsculas o minúsculas"


def solo_cambia_tilde(a: str, b: str) -> bool:
    return normaliza(a) == normaliza(b) and a.lower() != b.lower()


def tiene_tilde(palabra: str) -> bool:
    return any(c in TILDES for c in palabra)


def es_vocal(car: str) -> bool:
    return car in VOCALES
