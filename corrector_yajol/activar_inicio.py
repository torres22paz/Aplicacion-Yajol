"""Deja en buen estado el arranque automático con Windows.

Lo usa Instalar.vbs. También se puede ejecutar a mano:
    .venv\\Scripts\\python activar_inicio.py           -> limpia lo antiguo y lo activa
    .venv\\Scripts\\python activar_inicio.py limpiar   -> solo quita arranques antiguos
    .venv\\Scripts\\python activar_inicio.py quitar    -> lo desactiva
"""
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from yajol import config  # noqa: E402
from yajol.sistema import inicio  # noqa: E402


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    try:
        logging.basicConfig(filename=config.LOG_PATH, level=logging.INFO, encoding="utf-8",
                            format="%(asctime)s %(levelname)s %(message)s")
    except Exception:
        pass
    orden = argv[0].lower() if argv else "activar"

    if orden in ("quitar", "off", "desactivar"):
        inicio.desactivar()
        print("Arranque automatico desactivado")
        return 0

    quitados = inicio.limpia_antiguos()
    for quitado in quitados:
        print("Arranque antiguo eliminado:", quitado.encode("ascii", "replace").decode("ascii"))
    if orden == "limpiar":
        return 0

    if inicio.activar():
        print("Arranque automatico activado")
        return 0
    print("No se pudo activar el arranque automatico")
    return 1


if __name__ == "__main__":
    sys.exit(main())
