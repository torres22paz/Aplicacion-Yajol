"""Operaciones de texto: normalización, sílabas, distancia entre palabras y parches."""
import re
import unicodedata

# ---- Expresiones base ----
LETRAS = "a-záéíóúüñA-ZÁÉÍÓÚÜÑ"
PALABRA_RE = re.compile(f"[{LETRAS}]+(?:[-'][{LETRAS}]+)*")
ORACION_RE = re.compile(r"[^.!?¿¡\n]+[.!?\n]*")

VOCALES = set("aeiouáéíóúüAEIOUÁÉÍÓÚÜ")
FUERTES = set("aeoáéóAEOÁÉÓ")
DEBILES_TILDE = set("íúÍÚ")
TILDES = set("áéíóúÁÉÍÓÚ")
MAPA_SIN_TILDE = str.maketrans("áéíóúÁÉÍÓÚ", "aeiouAEIOU")

# Letras que suenan igual en español: cambiar una por otra cuenta como medio error
SONIDO_PARECIDO = [
    set("sz"), set("sc"), set("cz"),     # seseo: casa / caza / cocer
    set("bv"),                           # beta / uve
    set("gj"),                           # gente / jinete
    set("yl"),                           # yeísmo parcial
    set("kc"), set("kq"), set("cq"),     # kilo / quilo
    set("mn"),                           # invierno / inbierno
]


def sin_tildes(texto: str) -> str:
    """Quita las tildes conservando la ñ y la ü."""
    salida = []
    for car in texto:
        if car in "ñÑüÜ":
            salida.append(car)
            continue
        descompuesto = unicodedata.normalize("NFD", car)
        salida.append("".join(c for c in descompuesto if unicodedata.category(c) != "Mn"))
    return "".join(salida)


def normaliza(texto: str) -> str:
    """Minúsculas y sin tildes: sirve para comparar dos palabras."""
    return sin_tildes(texto).lower()


def es_misma_con_tilde(palabra: str, candidata: str) -> bool:
    """True si la candidata es la misma palabra pero con otras tildes."""
    return normaliza(candidata) == normaliza(palabra) and candidata.lower() != palabra.lower()


def conserva_forma(original: str, nueva: str) -> str:
    """Aplica a la nueva palabra las mayúsculas del original (casa -> Casa, CASA)."""
    if not original or not nueva:
        return nueva
    if original.isupper() and len(original) > 1:
        return nueva.upper()
    if original[0].isupper():
        return nueva[0].upper() + nueva[1:]
    return nueva


def _coste_cambio(a: str, b: str) -> float:
    if a == b:
        return 0.0
    if a.translate(MAPA_SIN_TILDE) == b.translate(MAPA_SIN_TILDE):
        return 0.3                                   # solo cambia la tilde
    if any({a, b} <= par for par in SONIDO_PARECIDO):
        return 0.5                                   # suenan igual
    return 1.0


def distancia(a: str, b: str) -> float:
    """Coste de convertir a en b. Los cambios que suenan igual cuestan menos."""
    a, b = a.lower(), b.lower()
    previa = [float(j) for j in range(len(b) + 1)]
    prev_prev = list(previa)
    for i, ca in enumerate(a, 1):
        actual = [float(i)]
        for j, cb in enumerate(b, 1):
            borrar = previa[j] + 1
            insertar = actual[j - 1] + 1
            cambiar = previa[j - 1] + _coste_cambio(ca, cb)
            actual.append(min(borrar, insertar, cambiar))
            # transposición (ergo -> egro)
            if i > 1 and j > 1 and a[i - 2] == cb and ca == b[j - 2]:
                actual[j] = min(actual[j], prev_prev[j - 2] + 0.8)
        prev_prev = previa
        previa = actual
    return previa[-1]


# ---- Sílabas y acentuación ----
def nucleos(palabra: str) -> list:
    """Rangos (inicio, fin) de los núcleos vocálicos, es decir, de las sílabas."""
    salida, i, n = [], 0, len(palabra)
    while i < n:
        if palabra[i] in VOCALES:
            inicio = i
            i += 1
            while i < n and palabra[i] in VOCALES and not (
                    (palabra[i - 1] in FUERTES and palabra[i] in FUERTES)
                    or palabra[i - 1] in DEBILES_TILDE or palabra[i] in DEBILES_TILDE):
                i += 1
            salida.append((inicio, i))
        else:
            i += 1
    return salida


def clase_acentual(palabra: str) -> tuple:
    """(clase, sílaba tónica) de una palabra con tilde. Clase None si no se puede deducir."""
    nucs = nucleos(palabra)
    if len(nucs) <= 1:
        return "monosílaba", None
    idx = next((k for k, (s, e) in enumerate(nucs) if any(c in TILDES for c in palabra[s:e])), None)
    if idx is None:
        return None, None
    s, e = nucs[idx]
    clase = {0: "aguda", 1: "llana", 2: "esdrújula"}.get(len(nucs) - 1 - idx, "sobresdrújula")
    return clase, palabra[s:e]


# ---- Fragmentos y parches ----
def fragmento(texto: str, inicio: int, fin: int, radio: int = 45) -> dict:
    """Trozo alrededor del error, cortado en espacios para no partir palabras."""
    izq, der = max(0, inicio - radio), min(len(texto), fin + radio)
    if izq > 0 and (sp := texto.find(" ", izq, inicio)) != -1:
        izq = sp + 1
    if der < len(texto) and (sp := texto.rfind(" ", fin, der)) != -1:
        der = sp
    return {"antes": texto[izq:inicio], "error": texto[inicio:fin], "despues": texto[fin:der],
            "corte_izq": izq > 0, "corte_der": der < len(texto)}


def aplica_cambios(texto: str, cambios: list) -> tuple:
    """cambios: (inicio, fin, reemplazo). Se aplican de atrás hacia adelante; se omiten los solapados."""
    aplicados, ultimo_inicio = [], len(texto)
    for inicio, fin, rep in sorted(cambios, key=lambda c: c[0], reverse=True):
        if inicio < 0 or inicio > fin or fin > ultimo_inicio:
            continue
        texto = texto[:inicio] + rep + texto[fin:]
        aplicados.append((inicio, fin, rep))
        ultimo_inicio = inicio
    return texto, list(reversed(aplicados))


def mensaje_aviso(pares: list, max_lineas: int = 4) -> str:
    """pares: (original, reemplazo, categoría)."""
    if not pares:
        return ""
    lineas = [f"«{o}» → «{r}»  ({c.lower()})" for o, r, c in pares[:max_lineas]]
    if len(pares) > max_lineas:
        lineas.append(f"y {len(pares) - max_lineas} más")
    return "Corregido:\n" + "\n".join(lineas)
