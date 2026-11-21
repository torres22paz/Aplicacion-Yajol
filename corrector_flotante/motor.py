"""Motor de revisión: diccionarios libres (Hunspell, pyspellchecker, LanguageTool) y explicaciones."""
import difflib
import logging
import os
import re
import unicodedata
from dataclasses import dataclass, field

try:
    from spylls.hunspell import Dictionary as _Hunspell
except Exception:
    _Hunspell = None
try:
    from spellchecker import SpellChecker
except Exception:
    SpellChecker = None

log = logging.getLogger("corrector")

# ---- Ajustes ----
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DICT_DIR = os.path.join(BASE_DIR, "dictionaries")
HUNSPELL_LANGS = ("es_ES", "es_MX")
LANG_LANGTOOL = "es"
CONTEXT_WORDS = 15            # palabras antes del cursor que se revisan
MAX_SUGGESTIONS = 4
MAX_JOINED_PARTS = 3          # cuántas palabras como máximo se separan de una palabra pegada
ICON_SIZE = 34
ICON_OFFSET = (24, 24)        # margen desde la esquina inferior derecha
KEY_DELAY = 0.02
TOAST_MS = 4500
HOTKEY_TOGGLE = "<ctrl>+<alt>+i"

# Palabras frecuentes que el respaldo (pyspellchecker) no trae; solo se usan sin Hunspell
COMMON_VALID = {
    "cómo", "qué", "quién", "quiénes", "dónde", "cuándo", "cuánto", "cuál", "aún",
    "sé", "dé", "sí", "más", "él", "tú", "mí", "té", "sólo",
    "vamos", "estás", "está", "estoy", "estamos", "están", "había", "habría",
}
# Palabras cortas que pueden ir sueltas al separar palabras pegadas (el perro, la casa...)
FUNCTION_WORDS = {"a", "o", "y", "e", "u", "de", "la", "el", "en", "lo", "le", "se", "me", "te",
                  "su", "al", "del", "un", "una", "con", "por", "para", "que", "es", "no", "si",
                  "yo", "tu", "mi", "nos", "os", "las", "los", "mas", "pero", "como", "muy", "ya"}
# Letras que suenan igual: sustituir una por otra cuenta menos como error
SIMILAR_SOUND = [set("kc"), set("cq"), set("sz"), set("bv"), set("gj")]

WORD_RE = re.compile(r"[^\W\d_]+")
CATEGORY_NAMES = {"GRAMMAR": "Gramática", "STYLE": "Estilo"}
JOINED = "Palabras juntas"
ACCENT = "Acentuación"
SPELLING = "Ortografía"


# ---- Texto ----
def sin_acentos(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def es_acento_de(word: str, candidate: str) -> bool:
    """True si candidate es la misma palabra pero con otros acentos."""
    return sin_acentos(candidate).lower() == sin_acentos(word).lower() and candidate.lower() != word.lower()


def _sub_cost(a: str, b: str) -> float:
    if a == b:
        return 0
    return 0.5 if any({a, b} <= pair for pair in SIMILAR_SOUND) else 1


def edit_distance(a: str, b: str) -> float:
    """Costo de pasar de a a b: 1 por letra añadida, quitada o cambiada; 0.5 si suenan igual."""
    a, b = a.lower(), b.lower()
    prev = [float(j) for j in range(len(b) + 1)]
    for i, ca in enumerate(a, 1):
        cur = [float(i)]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + _sub_cost(ca, cb)))
        prev = cur
    return prev[-1]


def snippet_parts(text: str, start: int, end: int, radius: int = 45) -> dict:
    """Fragmento alrededor del error, cortado en espacios para no dejar palabras a medias."""
    left, right = max(0, start - radius), min(len(text), end + radius)
    if left > 0 and (sp := text.find(" ", left, start)) != -1:
        left = sp + 1
    if right < len(text) and (sp := text.rfind(" ", end, right)) != -1:
        right = sp
    return {"before": text[left:start], "wrong": text[start:end], "after": text[end:right],
            "cut_left": left > 0, "cut_right": right < len(text)}


def apply_fixes(text: str, fixes: list) -> tuple:
    """fixes: (inicio, fin, reemplazo). Aplica de atrás hacia adelante; omite solapados."""
    applied, last_start = [], len(text)
    for start, end, rep in sorted(fixes, key=lambda f: f[0], reverse=True):
        if start < 0 or start > end or end > last_start:
            continue
        text = text[:start] + rep + text[end:]
        applied.append((start, end, rep))
        last_start = start
    return text, list(reversed(applied))


def toast_message(pairs: list, max_lines: int = 4) -> str:
    """pairs: (original, reemplazo, categoría)."""
    if not pairs:
        return ""
    lines = [f"«{o}» → «{r}»  ({c.lower()})" for o, r, c in pairs[:max_lines]]
    if len(pairs) > max_lines:
        lines.append(f"y {len(pairs) - max_lines} más")
    return "Corregido:\n" + "\n".join(lines)


# ---- Explicaciones con reglas del español ----
VOWELS = set("aeiouáéíóúüAEIOUÁÉÍÓÚÜ")
STRONG = set("aeoáéóAEOÁÉÓ")
WEAK_ACCENTED = set("íúÍÚ")
ACCENT_MARKS = set("áéíóúÁÉÍÓÚ")
PLURAL = {"aguda": "agudas", "llana": "llanas", "esdrújula": "esdrújulas", "sobresdrújula": "sobresdrújulas"}
ACCENT_RULE = {
    "aguda": "terminan en vocal, n o s",
    "llana": "terminan en consonante distinta de n o s",
    "esdrújula": "siempre llevan tilde",
    "sobresdrújula": "siempre llevan tilde",
}
NUMBER_WORDS = {2: "dos", 3: "tres", 4: "cuatro"}


def nuclei(word: str) -> list:
    """Rangos (inicio, fin) de los núcleos vocálicos, es decir, de las sílabas."""
    out, i, n = [], 0, len(word)
    while i < n:
        if word[i] in VOWELS:
            start = i
            i += 1
            while i < n and word[i] in VOWELS and not (
                    (word[i - 1] in STRONG and word[i] in STRONG)
                    or word[i - 1] in WEAK_ACCENTED or word[i] in WEAK_ACCENTED):
                i += 1
            out.append((start, i))
        else:
            i += 1
    return out


def stress_class(word: str) -> tuple:
    """(clase, sílaba tónica) de una palabra con tilde. Clase None si no se puede saber."""
    nucs = nuclei(word)
    if len(nucs) <= 1:
        return "monosílaba", None
    idx = next((k for k, (s, e) in enumerate(nucs) if any(c in ACCENT_MARKS for c in word[s:e])), None)
    if idx is None:
        return None, None
    s, e = nucs[idx]
    cls = {0: "aguda", 1: "llana", 2: "esdrújula"}.get(len(nucs) - 1 - idx, "sobresdrújula")
    return cls, word[s:e]


def explain_accent(wrong: str, correct: str) -> str:
    head = f"Falta el acento: «{wrong}» debe escribirse «{correct}». "
    cls, syl = stress_class(correct)
    if cls is None:
        return head.strip()
    if cls == "monosílaba":
        return head + "Las palabras de una sílaba llevan tilde solo para distinguirlas de otra igual (como «sí» y «si»)."
    return (head + f"«{correct}» es {cls} porque su sílaba fuerte es «{syl}». "
            f"Las palabras {PLURAL[cls]} {ACCENT_RULE[cls]}, por eso lleva tilde.")


def explain_spelling(wrong: str, correct: str) -> str:
    # Se comparan las letras sin tildes; la tilde se menciona aparte
    base = sin_acentos(correct)
    diffs = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, wrong.lower(), base.lower()).get_opcodes():
        if tag == "insert":
            diffs.append(f"falta la letra «{base[j1:j2]}»")
        elif tag == "delete":
            diffs.append(f"sobra «{wrong[i1:i2]}»")
        elif tag == "replace":
            diffs.append(f"«{wrong[i1:i2]}» debería ser «{base[j1:j2]}»")
    if base != correct:
        diffs.append("lleva tilde")
    detail = "; ".join(diffs[:3]) or "solo cambian mayúsculas o minúsculas"
    if "k" in wrong.lower() and "k" not in correct.lower() and ("c" in correct.lower() or "qu" in correct.lower()):
        return (f"«{wrong}» no está en el diccionario. En español la «k» casi no se usa: "
                f"la forma correcta es «{correct}» ({detail}).")
    return f"«{wrong}» no está en el diccionario. La forma correcta es «{correct}»: {detail}."


def explain_joined(word: str, joined: str) -> str:
    n = joined.count(" ") + 1
    return (f"«{word}» está escrito todo junto. Debe escribirse en {NUMBER_WORDS.get(n, str(n))} "
            f"palabras separadas: «{joined}».")


def explain_for(word: str, suggestion, category: str) -> str:
    if suggestion is None:
        return (f"«{word}» no está en el diccionario y no encontré una forma parecida. "
                "Si es un nombre propio, una sigla o una palabra nueva, puedes ignorarla.")
    if category == JOINED:
        return explain_joined(word, suggestion)
    if category == ACCENT:
        return explain_accent(word, suggestion)
    return explain_spelling(word, suggestion)


# ---- Corrector ----
@dataclass
class Issue:
    category: str
    original: str
    suggestions: list = field(default_factory=list)
    explanation: str = ""
    start: int = 0
    end: int = 0


def rank_suggestions(word: str, suggestions: list, freq=lambda w: 0) -> list:
    """Orden: acento primero, luego la más parecida y la más usada, y las de varias palabras al final."""
    unique = list(dict.fromkeys(s for s in suggestions if s and s != word))
    if word[:1].islower():  # una palabra en minúscula no se corrige a un nombre propio
        unique = [s for s in unique if not s[:1].isupper()] or unique
    ordered = sorted(unique, key=lambda s: (not es_acento_de(word, s), " " in s,
                                            round(edit_distance(word, s), 2), -freq(s)))
    if word[:1].isupper():
        ordered = [s[:1].upper() + s[1:] for s in ordered]
    return ordered[:MAX_SUGGESTIONS]


def category_for(word: str, top) -> str:
    if top is None:
        return SPELLING
    if " " in top and " " not in word:
        return JOINED
    return ACCENT if es_acento_de(word, top) else SPELLING


def load_frequencies(path: str = os.path.join(DICT_DIR, "frecuencia_es.txt")) -> dict:
    """Palabras más usadas en español (lista libre FrequencyWords). Vacío si no existe."""
    freq = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                parts = line.split()
                if len(parts) == 2 and parts[1].isdigit():
                    freq.setdefault(parts[0].lower(), int(parts[1]))
    return freq


def load_hunspell(dict_dir: str = DICT_DIR, langs=HUNSPELL_LANGS) -> list:
    if _Hunspell is None:
        return []
    loaded = []
    for lang in langs:
        base = os.path.join(dict_dir, lang)
        if os.path.exists(base + ".dic") and os.path.exists(base + ".aff"):
            try:
                loaded.append(_Hunspell.from_files(base))
                log.info("Diccionario cargado: %s", lang)
            except Exception:
                log.exception("No se pudo cargar %s", lang)
    return loaded


class Corrector:
    def __init__(self, dict_dir: str = DICT_DIR, hunspell=None):
        self.hunspell = hunspell if hunspell is not None else load_hunspell(dict_dir)
        self.pyspell = SpellChecker(language="es") if SpellChecker else None
        self.freq_map = load_frequencies()
        self.tool = None
        self.tool_error = ""

    def load_grammar(self) -> str:
        """Inicia LanguageTool (necesita Java). Devuelve un aviso si no se pudo."""
        try:
            import language_tool_python
            self.tool = language_tool_python.LanguageTool(LANG_LANGTOOL)
            self.tool_error = ""
            log.info("LanguageTool listo")
        except Exception as exc:
            self.tool = None
            self.tool_error = f"Gramática no disponible: instala Java 17 o superior. ({exc})"
            log.warning(self.tool_error)
        return self.tool_error

    def close(self):
        if self.tool:
            self.tool.close()

    def is_correct(self, word: str) -> bool:
        if word.lower() in COMMON_VALID:
            return True
        if self.hunspell:
            return any(d.lookup(word) or d.lookup(word.lower()) for d in self.hunspell)
        if self.pyspell:
            return not self.pyspell.unknown([word.lower()])
        return True

    def suggest(self, word: str) -> list:
        sugg = []
        for d in self.hunspell:
            sugg += list(d.suggest(word))[:8]
        if self.pyspell:
            sugg += list(self.pyspell.candidates(word.lower()) or [])
        return sugg

    def freq(self, word: str) -> int:
        return self.freq_map.get(word.lower(), 0)

    def _valid_part(self, part: str) -> bool:
        return (len(part) >= 3 or part.lower() in FUNCTION_WORDS) and self.is_correct(part)

    def split_joined(self, word: str):
        """Si la palabra es varias palabras pegadas, devuelve la versión separada; si no, None."""
        n = len(word)
        if n < 4 or n > 40:
            return None
        best = [None] * (n + 1)   # best[i] = (número de partes, inicio de la última parte)
        best[0] = (0, None)
        for i in range(1, n + 1):
            for j in range(max(0, i - 20), i):
                if best[j] is None or best[j][0] + 1 > MAX_JOINED_PARTS:
                    continue
                if not self._valid_part(word[j:i]):
                    continue
                if best[i] is None or best[j][0] + 1 < best[i][0]:
                    best[i] = (best[j][0] + 1, j)
        if best[n] is None or best[n][0] < 2:
            return None
        parts, i = [], n
        while i > 0:
            j = best[i][1]
            parts.append(word[j:i])
            i = j
        return " ".join(reversed(parts))

    def _spelling_issues(self, text: str) -> list:
        issues = []
        for m in WORD_RE.finditer(text):
            word = m.group()
            if self.is_correct(word):
                continue
            joined = self.split_joined(word)
            if joined:
                issues.append(Issue(JOINED, word, [joined], explain_for(word, joined, JOINED),
                                    m.start(), m.end()))
                continue
            sugg = rank_suggestions(word, self.suggest(word), self.freq)
            top = sugg[0] if sugg else None
            cat = category_for(word, top)
            issues.append(Issue(cat, word, sugg, explain_for(word, top, cat), m.start(), m.end()))
        return issues

    def _grammar_issues(self, text: str, spans: list) -> list:
        issues = []
        for match in self.tool.check(text):
            if match.category == "TYPOS":
                continue  # la ortografía la revisa Hunspell, que es más precisa
            start, end = match.offset, match.offset + match.errorLength
            if any(start < b and a < end for a, b in spans):
                continue
            issues.append(Issue(CATEGORY_NAMES.get(match.category, "Gramática"), text[start:end],
                                list(match.replacements)[:MAX_SUGGESTIONS], match.message, start, end))
        return issues

    def analyze(self, text: str) -> list:
        if not text or not text.strip():
            return []
        issues = self._spelling_issues(text)
        if self.tool:
            issues += self._grammar_issues(text, [(i.start, i.end) for i in issues])
        return sorted(issues, key=lambda i: i.start)
