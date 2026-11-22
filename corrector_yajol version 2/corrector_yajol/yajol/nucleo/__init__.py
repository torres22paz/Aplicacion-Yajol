"""Motor de corrección: léxico, reglas y diagnóstico."""
from .corrector import Corrector
from .hallazgo import Hallazgo
from .lexico import Lexico

__all__ = ["Corrector", "Hallazgo", "Lexico"]
