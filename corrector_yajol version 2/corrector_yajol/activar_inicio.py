"""Activa o desactiva el arranque automático con Windows.

Lo usa Instalar.vbs. También se puede ejecutar a mano:
    .venv\\Scripts\\python activar_inicio.py          -> lo activa
    .venv\\Scripts\\python activar_inicio.py quitar   -> lo quita
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from yajol.sistema import inicio  # noqa: E402


def main() -> int:
    quitar = len(sys.argv) > 1 and sys.argv[1].lower() in ("quitar", "off", "desactivar")
    if quitar:
        inicio.desactivar()
        print("Arranque automatico desactivado")
        return 0
    if inicio.activar():
        print("Arranque automatico activado")
        return 0
    print("No se pudo activar el arranque automatico")
    return 1


if __name__ == "__main__":
    sys.exit(main())
