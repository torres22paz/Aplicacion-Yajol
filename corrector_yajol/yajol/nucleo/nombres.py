"""Nombres propios: detecta nombres completos en minúscula o sin tilde.

Ejemplo: «omar torres de la paz» → «Omar Torres de la Paz».
"""
import re

from .. import config
from .hallazgo import Hallazgo
from .texto import normaliza

# Partículas que van en minúscula dentro de un nombre completo
PARTICULAS = {"de", "del", "la", "las", "los", "y", "e", "da", "do", "di", "van", "von", "san", "santa"}

# Si antes del nombre va uno de estos, lo más probable es que sea una frase normal
# ("la cruz de la paz") y no el nombre de una persona.
DETERMINANTES = {"el", "la", "los", "las", "un", "una", "unos", "unas", "lo",
                 "mi", "tu", "su", "mis", "tus", "sus", "nuestro", "nuestra",
                 "este", "esta", "estos", "estas", "ese", "esa", "esos", "esas",
                 "aquel", "aquella", "del", "al", "cada", "otro", "otra"}

_TOKEN_RE = re.compile(r"[a-záéíóúüñA-ZÁÉÍÓÚÜÑ]+")


class RevisorNombres:
    def __init__(self, lexico):
        self.lexico = lexico
        # un nombre es "ambiguo" si en minúscula también es una palabra común (paz, flor, león)
        self._ambiguos = {}

    def _es_ambiguo(self, palabra: str) -> bool:
        """True si en minúscula también es una palabra común: paz, flor, león, cruz."""
        clave = palabra.lower()
        if clave not in self._ambiguos:
            dic = self.lexico.hunspell
            self._ambiguos[clave] = bool(dic and dic.lookup(clave))
        return self._ambiguos[clave]

    def _correcto(self, token: str):
        """Devuelve la escritura correcta del nombre, o None si no es un nombre conocido."""
        return self.lexico.forma_del_nombre(token)

    def revisa(self, texto: str) -> list:
        tokens = list(_TOKEN_RE.finditer(texto))
        hallazgos = []
        i = 0
        while i < len(tokens):
            grupo = self._lee_grupo(tokens, i)
            if grupo is None:
                i += 1
                continue
            fin_idx, piezas = grupo
            hallazgo = self._hallazgo(texto, tokens, i, fin_idx, piezas)
            if hallazgo:
                hallazgos.append(hallazgo)
            i = fin_idx + 1
        return hallazgos

    def _lee_grupo(self, tokens, inicio):
        """Lee un nombre completo: nombres y apellidos seguidos, con partículas en medio."""
        piezas = []          # (indice_token, correcto_o_None, es_particula)
        i = inicio
        ultimo_nombre = -1
        while i < len(tokens):
            palabra = tokens[i].group()
            base = normaliza(palabra)
            correcto = self._correcto(palabra)
            if correcto:
                piezas.append((i, correcto, False))
                ultimo_nombre = i
            elif base in PARTICULAS and piezas and ultimo_nombre >= 0:
                piezas.append((i, base, True))
            else:
                break
            # el nombre se corta si hay algo que no sea un espacio entre las dos palabras
            if i + 1 < len(tokens):
                entre = tokens[i].string[tokens[i].end():tokens[i + 1].start()]
                if entre.strip():
                    i += 1
                    break
            i += 1
        # recortar partículas sobrantes al final ("juan de" -> "juan")
        while piezas and piezas[-1][2]:
            piezas.pop()
        if not piezas:
            return None
        return piezas[-1][0], piezas

    def _hallazgo(self, texto, tokens, ini_idx, fin_idx, piezas):
        nombres = [p for p in piezas if not p[2]]
        if not nombres:
            return None
        # un solo nombre: solo se avisa si no es una palabra común y está mal escrito
        if len(nombres) == 1:
            idx, correcto, _ = nombres[0]
            palabra = tokens[idx].group()
            if palabra == correcto:
                return None
            if self._es_ambiguo(palabra) and palabra.islower():
                return None          # "la paz interior" no es un apellido
            if palabra.lower() == correcto.lower() and palabra[:1].isupper():
                return None          # ya va con mayúscula, solo cambiaría una tilde interna
            ini, fin = tokens[idx].span()
            return Hallazgo(config.CAT_NOMBRE, palabra, ini, fin, [correcto],
                            self._explica([palabra], [correcto]), "nombre_simple", 0.7)

        hay_particula = any(p[2] for p in piezas)
        if all(self._es_ambiguo(tokens[i].group()) for i, _, _ in nombres):
            # todas las piezas son también palabras comunes (paz, cruz, torres...):
            # solo se acepta si parece de verdad un nombre completo
            previo = tokens[ini_idx - 1].group().lower() if ini_idx > 0 else ""
            if normaliza(previo) in DETERMINANTES:
                return None
            if not hay_particula and len(nombres) < 3:
                return None

        # nombre completo: se corrige entero
        ini = tokens[ini_idx].start()
        fin = tokens[fin_idx].end()
        original = texto[ini:fin]
        partes_orig, partes_ok = [], []
        for idx, valor, es_particula in piezas:
            palabra = tokens[idx].group()
            partes_orig.append(palabra)
            partes_ok.append(valor.lower() if es_particula else valor)
        if all(p.isupper() for p in partes_orig if len(p) > 1):
            partes_ok = [p.upper() for p in partes_ok]      # respeta el texto en MAYÚSCULAS
        propuesta = self._reconstruye(texto, tokens, piezas, partes_ok)
        if propuesta == original:
            return None
        return Hallazgo(config.CAT_NOMBRE, original, ini, fin, [propuesta],
                        self._explica(partes_orig, partes_ok, hay_particula),
                        "nombre_completo", 0.85)

    @staticmethod
    def _reconstruye(texto, tokens, piezas, partes_ok):
        """Rehace el nombre conservando los espacios originales."""
        salida = []
        for n, (idx, _, _) in enumerate(piezas):
            salida.append(partes_ok[n])
            if n + 1 < len(piezas):
                salida.append(texto[tokens[idx].end():tokens[piezas[n + 1][0]].start()])
        return "".join(salida)

    @staticmethod
    def _explica(originales, correctos, hay_particula=False):
        cambios = [f"«{o}» → «{c}»" for o, c in zip(originales, correctos) if o != c]
        if not cambios:
            return "Los nombres propios se escriben con mayúscula inicial."
        detalle = ", ".join(cambios[:3])
        falta_tilde = any(normaliza(o) == normaliza(c) and o.lower() != c.lower()
                          for o, c in zip(originales, correctos))
        base = ("Los nombres y apellidos se escriben con mayúscula inicial"
                + (" y conservan su tilde" if falta_tilde else "") + f": {detalle}.")
        if hay_particula:
            base += " Las partículas «de», «del», «la» y «y» van en minúscula dentro del nombre."
        return base
