"""Genera los archivos que Windows abre con doble clic.

    python herramientas/construir.py

- Instalar.vbs, Yajol.vbs y Desinstalar.vbs a partir de herramientas/guiones/*.vbs.txt
- Guia.html a partir de los textos de la ayuda

Los .vbs finales solo contienen caracteres ASCII: las tildes y los signos de
los avisos se escriben con ChrW(código). Así Windows los muestra bien en
cualquier equipo, tenga la configuración regional que tenga. (Guardar un .vbs
en UTF-8 era la causa del texto ilegible «FallÃ³ la instalaciÃ³n» de la
primera versión.)
"""
import os
import sys
import unicodedata

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
GUIONES = os.path.join(AQUI, "guiones")
MARCA_COMUN = "'@COMUN@"
NOMBRES = ("Instalar", "Yajol", "Desinstalar")


def lee(nombre: str) -> str:
    with open(os.path.join(GUIONES, nombre), encoding="utf-8") as f:
        return f.read()


def compone(nombre: str) -> str:
    """Texto final del guion, con las funciones comunes incluidas."""
    texto = lee(nombre + ".vbs.txt")
    if MARCA_COMUN in texto:
        texto = texto.replace(MARCA_COMUN, lee("comun.vbs.txt").rstrip("\n"))
    return texto


def _sin_tildes(texto: str) -> str:
    """Para los comentarios: quita tildes y signos que no sean ASCII."""
    plano = unicodedata.normalize("NFKD", texto)
    return plano.encode("ascii", "ignore").decode("ascii")


def _cadena_ascii(contenido: str) -> str:
    """Convierte el interior de una cadena de VBScript en una expresión solo ASCII.

    'Instalación' -> "Instalaci" & ChrW(243) & "n"
    """
    if all(ord(c) < 128 for c in contenido):
        return '"' + contenido + '"'
    trozos, actual = [], ""
    for car in contenido:
        if ord(car) < 128:
            actual += car
        else:
            if actual:
                trozos.append('"' + actual + '"')
                actual = ""
            trozos.append(f"ChrW({ord(car)})")
    if actual:
        trozos.append('"' + actual + '"')
    return " & ".join(trozos)


def a_ascii(linea: str) -> str:
    """Pasa una línea de VBScript a ASCII puro sin cambiar lo que hace."""
    salida, i, n = [], 0, len(linea)
    while i < n:
        car = linea[i]
        if car == '"':                      # cadena: hasta la comilla de cierre ("" es una comilla)
            j = i + 1
            while j < n:
                if linea[j] == '"':
                    if j + 1 < n and linea[j + 1] == '"':
                        j += 2
                        continue
                    break
                j += 1
            salida.append(_cadena_ascii(linea[i + 1:j]))
            i = j + 1
        elif car == "'":                    # comentario: hasta el final de la línea
            salida.append(_sin_tildes(linea[i:]))
            break
        else:
            salida.append(car)
            i += 1
    return "".join(salida)


def texto_final(nombre: str) -> str:
    lineas = compone(nombre).replace("\r\n", "\n").split("\n")
    return "\r\n".join(a_ascii(linea) for linea in lineas)


def escribe_vbs(nombre: str, destino_dir: str = RAIZ) -> str:
    ruta = os.path.join(destino_dir, nombre + ".vbs")
    with open(ruta, "wb") as f:
        f.write(texto_final(nombre).encode("ascii"))
    return ruta


def main() -> int:
    for nombre in NOMBRES:
        print("escrito:", os.path.relpath(escribe_vbs(nombre), RAIZ))
    sys.path.insert(0, RAIZ)
    try:
        from herramientas import guia
    except ImportError:
        import guia
    print("escrito:", os.path.relpath(guia.escribe(), RAIZ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
