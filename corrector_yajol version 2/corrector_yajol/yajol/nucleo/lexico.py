"""Léxico: diccionario Hunspell comprimido, listas propias, nombres y frecuencias."""
import gzip
import logging
import os

from .. import config
from .texto import normaliza

try:
    from spylls.hunspell import Dictionary as _Hunspell
except Exception:                                    # pragma: no cover - sin spylls
    _Hunspell = None

log = logging.getLogger("yajol")

AUTO = object()   # "cárgalo tú": distinto de None, que significa "sin diccionario"


def _lee_lista(ruta: str) -> list:
    """Lee un archivo de una palabra por línea. Ignora vacías y las que empiezan con #."""
    if not os.path.exists(ruta):
        return []
    with open(ruta, encoding="utf-8") as f:
        return [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]


def carga_frecuencias(ruta: str = None) -> dict:
    """Palabras más usadas del español (lista libre FrequencyWords), comprimida en gzip."""
    ruta = ruta or config.FRECUENCIAS_GZ
    frec = {}
    if not os.path.exists(ruta):
        return frec
    abrir = gzip.open if ruta.endswith(".gz") else open
    with abrir(ruta, "rt", encoding="utf-8") as f:
        for linea in f:
            partes = linea.split()
            if len(partes) == 2 and partes[1].isdigit():
                frec.setdefault(partes[0].lower(), int(partes[1]))
    return frec


def carga_hunspell(ruta: str = None):
    """Carga el diccionario es_MX desde el ZIP. Devuelve None si no se puede."""
    ruta = ruta or config.DICCIONARIO_ZIP
    if _Hunspell is None or not os.path.exists(ruta):
        log.warning("Diccionario Hunspell no disponible (%s)", ruta)
        return None
    try:
        dic = _Hunspell.from_zip(ruta)
        log.info("Diccionario cargado: %s", os.path.basename(ruta))
        return dic
    except Exception:
        log.exception("No se pudo abrir %s", ruta)
        return None


class Lexico:
    """Decide si una palabra existe y propone alternativas parecidas."""

    def __init__(self, hunspell=AUTO, extra=None, nombres=None, frecuencias=None,
                 usuario_path: str = None):
        self.hunspell = carga_hunspell() if hunspell is AUTO else hunspell
        self.extra = {normaliza(p) for p in (extra if extra is not None else _lee_lista(config.PALABRAS_EXTRA))}
        self.frecuencias = carga_frecuencias() if frecuencias is None else frecuencias
        self.usuario_path = usuario_path if usuario_path is not None else config.USUARIO_TXT
        self.usuario = {normaliza(p) for p in _lee_lista(self.usuario_path)}

        crudos = nombres if nombres is not None else _lee_lista(config.NOMBRES_PROPIOS)
        # nombres.txt guarda la forma correcta con mayúscula y tildes: "José", "Hernández"
        self.nombres = {}
        for n in crudos:
            self.nombres.setdefault(normaliza(n), n)

        self._cache_correcta = {}
        self._cache_sugerencias = {}

    # ---- Consulta ----
    def existe(self, palabra: str) -> bool:
        """True si la palabra está en alguna de las listas conocidas."""
        if not palabra:
            return True
        clave = palabra.lower()
        if clave in self._cache_correcta:
            return self._cache_correcta[clave]
        resultado = self._busca(palabra)
        if len(self._cache_correcta) < 20000:
            self._cache_correcta[clave] = resultado
        return resultado

    def _busca(self, palabra: str) -> bool:
        base = normaliza(palabra)
        if base in self.extra or base in self.usuario:
            return True
        if base in self.nombres:
            # un nombre propio solo vale si va con tilde y mayúscula correctas
            return palabra == self.nombres[base]
        if self.hunspell is None:
            # sin diccionario no se inventan errores
            return True
        if self.hunspell.lookup(palabra):
            return True
        if palabra.isupper() or palabra[0].isupper():
            return bool(self.hunspell.lookup(palabra.lower())
                        or self.hunspell.lookup(palabra.capitalize()))
        return False

    def es_nombre_propio(self, palabra: str) -> bool:
        return normaliza(palabra) in self.nombres

    def forma_del_nombre(self, palabra: str):
        """Devuelve la escritura correcta de un nombre propio conocido, o None."""
        return self.nombres.get(normaliza(palabra))

    def frecuencia(self, palabra: str) -> int:
        return self.frecuencias.get(palabra.lower(), 0)

    def sugerencias(self, palabra: str, limite: int = 10) -> list:
        """Candidatos del diccionario para una palabra mal escrita."""
        clave = palabra.lower()
        if clave in self._cache_sugerencias:
            return self._cache_sugerencias[clave]
        salida = []
        nombre = self.forma_del_nombre(palabra)
        if nombre:
            salida.append(nombre)
        if self.hunspell is not None:
            try:
                for s in self.hunspell.suggest(palabra):
                    salida.append(s)
                    if len(salida) >= limite:
                        break
            except Exception:
                log.exception("Fallo al sugerir para %r", palabra)
        unicas = list(dict.fromkeys(salida))
        if len(self._cache_sugerencias) < 5000:
            self._cache_sugerencias[clave] = unicas
        return unicas

    # ---- Palabras del usuario ----
    def aprende(self, palabra: str) -> bool:
        """Añade una palabra a la lista personal para no volver a marcarla."""
        palabra = palabra.strip()
        if not palabra:
            return False
        base = normaliza(palabra)
        if base in self.usuario:
            return False
        self.usuario.add(base)
        self._cache_correcta.pop(palabra.lower(), None)
        try:
            os.makedirs(os.path.dirname(self.usuario_path), exist_ok=True)
            with open(self.usuario_path, "a", encoding="utf-8") as f:
                f.write(palabra + "\n")
        except OSError:
            log.exception("No se pudo guardar %r en la lista personal", palabra)
            return False
        return True

    @property
    def total_palabras(self) -> int:
        propias = len(self.extra) + len(self.nombres) + len(self.usuario)
        return propias + (len(self.hunspell.dic.words) if self.hunspell else 0)
