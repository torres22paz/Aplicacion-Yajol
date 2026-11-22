"""El corrector: junta el diccionario, las reglas de letras y las reglas de contexto."""
import logging
import math

from .. import config
from . import reglas_letras as RL
from . import reglas_texto as RT
from .hallazgo import Hallazgo
from .lexico import Lexico
from .nombres import RevisorNombres
from .texto import (PALABRA_RE, aplica_cambios, conserva_forma, distancia,
                    es_misma_con_tilde, clase_acentual)

log = logging.getLogger("yajol")

PLURAL_CLASE = {"aguda": "agudas", "llana": "llanas",
                "esdrújula": "esdrújulas", "sobresdrújula": "sobresdrújulas"}
REGLA_CLASE = {
    "aguda": "llevan tilde cuando terminan en vocal, n o s",
    "llana": "llevan tilde cuando terminan en consonante distinta de n o s",
    "esdrújula": "siempre llevan tilde",
    "sobresdrújula": "siempre llevan tilde",
}
NUMEROS = {2: "dos", 3: "tres", 4: "cuatro", 5: "cinco"}

# Palabras cortas que pueden quedar sueltas al separar una palabra pegada
FUNCIONALES = {
    "a", "o", "y", "e", "u", "de", "la", "el", "en", "lo", "le", "se", "me", "te", "su", "al",
    "del", "un", "una", "con", "por", "para", "que", "es", "no", "si", "sí", "yo", "tu", "tú",
    "mi", "mí", "nos", "os", "las", "los", "más", "pero", "como", "muy", "ya", "ni", "ha", "he",
    "son", "fue", "ser", "sin", "ver", "da", "dé", "va", "voy", "ir", "así", "qué", "tan",
}
# Trozos que casi nunca son una palabra suelta de verdad
TROZOS_SOSPECHOSOS = {"ab", "ac", "ad", "al", "am", "an", "ar", "as", "ba", "ca", "ce", "co",
                      "da", "des", "di", "do", "ea", "en", "er", "es", "ex", "in", "la", "le",
                      "li", "lo", "ma", "me", "mi", "na", "ne", "no", "pa", "pe", "pi", "po",
                      "re", "sa", "se", "si", "so", "ta", "te", "ti", "to", "tu", "ve", "vi"}


def explica_acento(erronea: str, correcta: str) -> str:
    cabeza = f"Falta la tilde: «{erronea}» se escribe «{correcta}». "
    clase, silaba = clase_acentual(correcta)
    if clase is None:
        return cabeza.strip()
    if clase == "monosílaba":
        return (cabeza + "Las palabras de una sílaba solo llevan tilde para distinguirlas "
                         "de otra igual, como «sí» y «si» o «él» y «el».")
    return (cabeza + f"«{correcta}» es {clase} porque su sílaba fuerte es «{silaba}», "
            f"y las palabras {PLURAL_CLASE[clase]} {REGLA_CLASE[clase]}.")


def explica_pegadas(palabra: str, separada: str) -> str:
    n = separada.count(" ") + 1
    return (f"«{palabra}» está escrito todo junto. Son {NUMEROS.get(n, str(n))} "
            f"palabras distintas: «{separada}».")


def explica_sin_regla(erronea: str, correcta: str) -> str:
    return (f"«{erronea}» no está en el diccionario. La forma correcta es «{correcta}»: "
            f"{RL.diferencia_simple(erronea, correcta)}.")


class Corrector:
    """Revisa un texto y devuelve una lista de Hallazgo."""

    def __init__(self, lexico: Lexico = None, usar_languagetool: bool = None):
        self.lexico = lexico if lexico is not None else Lexico()
        self.revisor_nombres = RevisorNombres(self.lexico)
        self.herramienta = None
        self.aviso_gramatica = ""
        self._usar_lt = config.USAR_LANGUAGETOOL if usar_languagetool is None else usar_languagetool

    # ---- Gramática opcional ----
    def carga_gramatica(self) -> str:
        """Enciende LanguageTool si está instalado y hay Java. Devuelve "" si todo bien."""
        if not self._usar_lt:
            return ""
        try:
            import language_tool_python
        except ImportError:
            self.aviso_gramatica = ""      # no está instalado: se usan solo las reglas propias
            return ""
        try:
            self.herramienta = language_tool_python.LanguageTool(config.IDIOMA_LANGUAGETOOL)
            log.info("LanguageTool activo")
            self.aviso_gramatica = ""
        except Exception as exc:
            self.herramienta = None
            self.aviso_gramatica = ("La gramática avanzada necesita Java 17 o superior. "
                                    "El corrector seguirá funcionando con sus reglas propias.")
            log.warning("LanguageTool no disponible: %s", exc)
        return self.aviso_gramatica

    def cierra(self):
        if self.herramienta is not None:
            try:
                self.herramienta.close()
            except Exception:
                pass
            self.herramienta = None

    # ---- Palabras pegadas ----
    def separa_pegadas(self, palabra: str):
        """Si son varias palabras pegadas, devuelve la versión separada; si no, None."""
        n = len(palabra)
        if n < 5 or n > 40 or not palabra.isalpha():
            return None
        baja = palabra.lower()
        mejor = [None] * (n + 1)          # (nº de partes, coste, inicio de la última parte)
        mejor[0] = (0, 0.0, None)
        for i in range(1, n + 1):
            for j in range(max(0, i - 18), i):
                if mejor[j] is None:
                    continue
                partes, coste, _ = mejor[j]
                if partes + 1 > config.MAX_PARTES_PEGADAS:
                    continue
                trozo = baja[j:i]
                valor = self._valor_trozo(trozo)
                if valor is None:
                    continue
                nuevo = (partes + 1, coste + valor)
                if mejor[i] is None or nuevo < mejor[i][:2]:
                    mejor[i] = (nuevo[0], nuevo[1], j)
        if mejor[n] is None or mejor[n][0] < 2:
            return None
        partes, i = [], n
        while i > 0:
            j = mejor[i][2]
            partes.append(baja[j:i])
            i = j
        partes.reverse()
        # al menos una parte debe ser una palabra con cuerpo
        if not any(len(p) >= 3 for p in partes):
            return None
        return conserva_forma(palabra, " ".join(partes))

    def _valor_trozo(self, trozo: str):
        """Coste de usar este trozo como palabra suelta. None si no sirve."""
        if trozo in FUNCIONALES:
            return 0.5
        if len(trozo) < 3:
            return None
        if trozo in TROZOS_SOSPECHOSOS:
            return None
        if not self.lexico.existe(trozo):
            return None
        frec = self.lexico.frecuencia(trozo)
        if frec == 0:
            return None      # un trozo que nadie usa casi nunca es una palabra suelta de verdad
        return 1.0 if frec > 500 else 1.4

    # ---- Ordenar sugerencias ----
    def ordena(self, palabra: str, candidatos: list) -> list:
        """Primero la tilde, luego la más parecida y la más usada."""
        unicas = list(dict.fromkeys(c for c in candidatos if c and c.lower() != palabra.lower()))
        if palabra[:1].islower():
            sin_propios = [c for c in unicas if not c[:1].isupper()]
            unicas = sin_propios or unicas
        ordenadas = sorted(unicas, key=lambda c: self._puntua(palabra, c))
        return [conserva_forma(palabra, c) for c in ordenadas[:config.MAX_SUGERENCIAS]]

    def _puntua(self, palabra: str, candidata: str) -> float:
        """Cuanto más baja, mejor: cerca en letras y usada a menudo."""
        puntos = distancia(palabra, candidata)
        puntos -= 0.35 * math.log10(1 + self.lexico.frecuencia(candidata))
        if es_misma_con_tilde(palabra, candidata):
            puntos -= 0.4
        if " " in candidata:
            puntos += 0.3
        return round(puntos, 3)

    # ---- Ortografía palabra por palabra ----
    def _ortografia(self, texto: str) -> list:
        hallazgos = []
        for m in PALABRA_RE.finditer(texto):
            palabra = m.group()
            if len(palabra) < 2 or palabra.isupper() and len(palabra) <= 4:
                continue                                   # siglas: ONU, INE, SAT
            if self.lexico.existe(palabra):
                continue
            hallazgos.append(self._diagnostica(palabra, m.start(), m.end()))
        return hallazgos

    def _diagnostica(self, palabra: str, inicio: int, fin: int) -> Hallazgo:
        # 1. ¿es un nombre propio conocido mal escrito?
        nombre = self.lexico.forma_del_nombre(palabra)
        if nombre:
            return Hallazgo(config.CAT_NOMBRE, palabra, inicio, fin, [nombre],
                            f"«{nombre}» es un nombre propio: va con mayúscula inicial"
                            + (" y con tilde." if nombre.lower() != palabra.lower() else "."),
                            "nombre_simple", 0.8)
        # 2. ¿encaja alguna regla de letras o le falta una tilde?
        #    Va antes de separar palabras para no partir «kilometro» en «kilo metro».
        por_regla = RL.candidatos(palabra, self.lexico.existe)
        if por_regla:
            correctas = self.ordena(palabra, [c for c, _ in por_regla])
            regla = dict(por_regla).get(correctas[0].lower(), por_regla[0][1])
            if regla == "tilde":
                return Hallazgo(config.CAT_ACENTO, palabra, inicio, fin, correctas,
                                explica_acento(palabra, correctas[0]), regla, 0.8)
            return Hallazgo(config.CAT_ORTOGRAFIA, palabra, inicio, fin, correctas,
                            RL.explica(regla, palabra, correctas[0]), regla, 0.8)
        # 3. ¿son varias palabras pegadas?
        separada = self.separa_pegadas(palabra)
        if separada:
            return Hallazgo(config.CAT_PEGADAS, palabra, inicio, fin, [separada],
                            explica_pegadas(palabra, separada), "pegadas", 0.85)
        # 4. sugerencias del diccionario
        sugeridas = self.ordena(palabra, self.lexico.sugerencias(palabra))
        if not sugeridas:
            return Hallazgo(config.CAT_ORTOGRAFIA, palabra, inicio, fin, [],
                            f"«{palabra}» no está en el diccionario y no encontré una forma parecida. "
                            "Si es un nombre, una sigla o una palabra nueva, puedes añadirla "
                            "con «Aprender palabra».", "desconocida", 0.5)
        mejor = sugeridas[0]
        if es_misma_con_tilde(palabra, mejor):
            return Hallazgo(config.CAT_ACENTO, palabra, inicio, fin, sugeridas,
                            explica_acento(palabra, mejor), "tilde", 0.75)
        if " " in mejor:
            return Hallazgo(config.CAT_PEGADAS, palabra, inicio, fin, sugeridas,
                            explica_pegadas(palabra, mejor), "pegadas", 0.7)
        return Hallazgo(config.CAT_ORTOGRAFIA, palabra, inicio, fin, sugeridas,
                        explica_sin_regla(palabra, mejor), "diccionario", 0.65)

    # ---- Gramática de LanguageTool ----
    def _gramatica(self, texto: str) -> list:
        if self.herramienta is None:
            return []
        hallazgos = []
        try:
            coincidencias = self.herramienta.check(texto)
        except Exception:
            log.exception("Fallo de LanguageTool")
            return []
        for c in coincidencias:
            if c.category in ("TYPOS", "CASING"):
                continue                       # eso ya lo revisan el diccionario y las reglas
            ini, fin = c.offset, c.offset + c.errorLength
            hallazgos.append(Hallazgo(config.CAT_GRAMATICA, texto[ini:fin], ini, fin,
                                      list(c.replacements)[:config.MAX_SUGERENCIAS],
                                      c.message, "languagetool", 0.6))
        return hallazgos

    # ---- Segunda pasada ----
    @staticmethod
    def _mapa_tramos(texto: str, aplicados: list) -> list:
        """Tramos (ini_nuevo, fin_nuevo, desplazamiento) de las partes que no cambiaron."""
        tramos, pos_orig, pos_nuevo = [], 0, 0
        for ini, fin, rep in aplicados:
            largo = ini - pos_orig
            if largo:
                tramos.append((pos_nuevo, pos_nuevo + largo, pos_orig - pos_nuevo))
            pos_nuevo += largo + len(rep)
            pos_orig = fin
        if pos_orig <= len(texto):
            tramos.append((pos_nuevo, pos_nuevo + len(texto) - pos_orig, pos_orig - pos_nuevo))
        return tramos

    def _segunda_pasada(self, texto: str, hallazgos: list) -> list:
        """
        Busca errores de contexto que solo se ven con la ortografía ya arreglada.

        En «dise de que» primero hay que corregir «dise» para darse cuenta
        de que sobra el «de».
        """
        cambios = [(h.inicio, h.fin, h.mejor) for h in hallazgos
                   if h.mejor and h.confianza >= 0.7 and " " not in h.original]
        if not cambios:
            return []
        nuevo, aplicados = aplica_cambios(texto, cambios)
        if nuevo == texto:
            return []
        tramos = self._mapa_tramos(texto, aplicados)
        rescatados = []
        for h in RT.revisa(nuevo):
            tramo = next((t for t in tramos if t[0] <= h.inicio and h.fin <= t[1]), None)
            if tramo is None:
                continue        # cae sobre una palabra ya corregida: se deja para la próxima
            desplazamiento = tramo[2]
            h.inicio += desplazamiento
            h.fin += desplazamiento
            if texto[h.inicio:h.fin] != h.original:
                continue
            h.confianza = max(0.0, h.confianza - 0.05)
            rescatados.append(h)
        return rescatados

    # ---- Entrada principal ----
    def analiza(self, texto: str) -> list:
        """Devuelve los hallazgos del texto, sin solaparse y ordenados por posición."""
        if not texto or not texto.strip():
            return []
        todos = []
        todos += self._ortografia(texto)
        todos += RT.revisa(texto)
        todos += self.revisor_nombres.revisa(texto)
        todos += self._gramatica(texto)
        todos += self._segunda_pasada(texto, todos)
        return self._limpia(todos)

    @staticmethod
    def _limpia(hallazgos: list) -> list:
        """Quita repetidos y solapados; gana el de mayor confianza."""
        ordenados = sorted(hallazgos, key=lambda h: (-h.confianza, h.inicio, -(h.fin - h.inicio)))
        elegidos = []
        for h in ordenados:
            if any(h.solapa(e) for e in elegidos):
                continue
            elegidos.append(h)
        return sorted(elegidos, key=lambda h: h.inicio)

    # ---- Aplicar correcciones ----
    def corrige(self, texto: str, hallazgos: list = None) -> tuple:
        """Aplica la primera sugerencia de cada hallazgo. Devuelve (texto nuevo, cambios)."""
        hallazgos = self.analiza(texto) if hallazgos is None else hallazgos
        cambios = [(h.inicio, h.fin, h.mejor) for h in hallazgos if h.mejor]
        nuevo, aplicados = aplica_cambios(texto, cambios)
        pares = [(texto[i:f], r, next(h.categoria for h in hallazgos if h.inicio == i))
                 for i, f, r in aplicados]
        return nuevo, pares

    def aprende(self, palabra: str) -> bool:
        return self.lexico.aprende(palabra)
