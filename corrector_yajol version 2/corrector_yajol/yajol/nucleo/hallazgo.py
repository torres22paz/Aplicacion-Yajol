"""Estructura común para todo lo que el corrector encuentra."""
from dataclasses import dataclass, field


@dataclass
class Hallazgo:
    """Un posible error localizado en el texto."""
    categoria: str
    original: str
    inicio: int
    fin: int
    sugerencias: list = field(default_factory=list)
    explicacion: str = ""
    regla: str = ""
    confianza: float = 0.5        # 0 a 1; las de regla propia son más altas

    @property
    def mejor(self):
        return self.sugerencias[0] if self.sugerencias else None

    def solapa(self, otro) -> bool:
        return self.inicio < otro.fin and otro.inicio < self.fin
