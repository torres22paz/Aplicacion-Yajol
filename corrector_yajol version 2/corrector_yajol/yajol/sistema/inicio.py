"""Arranque automático con Windows.

Se crea un acceso directo en la carpeta Inicio del usuario. No hace falta
ser administrador y se puede quitar desde el menú del corrector o desde el
Administrador de tareas, pestaña «Inicio».
"""
import logging
import os
import subprocess
import sys

from .. import config

log = logging.getLogger("yajol")

NOMBRE_ACCESO = "Corrector YAJOL.lnk"
NOMBRE_RESPALDO = "Corrector YAJOL.vbs"
LANZADOR = os.path.join(config.RAIZ_DIR, "Yajol.vbs")

PLANTILLA_VBS = """' Arranque del Corrector YAJOL (copia de respaldo del acceso directo).
Set sh = CreateObject("WScript.Shell")
sh.Run Chr(34) & "{lanzador}" & Chr(34), 0, False
"""


def es_windows() -> bool:
    return os.name == "nt"


def carpeta_inicio() -> str:
    """Carpeta Inicio del usuario (shell:startup)."""
    base = os.environ.get("APPDATA", "")
    return os.path.join(base, "Microsoft", "Windows", "Start Menu", "Programs", "Startup")


def ruta_acceso() -> str:
    return os.path.join(carpeta_inicio(), NOMBRE_ACCESO)


def ruta_respaldo() -> str:
    return os.path.join(carpeta_inicio(), NOMBRE_RESPALDO)


def esta_activado() -> bool:
    return os.path.exists(ruta_acceso()) or os.path.exists(ruta_respaldo())


def _crea_acceso_directo(destino: str, objetivo: str, argumentos: str,
                         carpeta_trabajo: str, icono: str = "") -> bool:
    """Crea un .lnk con PowerShell. Devuelve True si lo consiguió."""
    orden = (
        "$s = (New-Object -ComObject WScript.Shell).CreateShortcut('{destino}');"
        "$s.TargetPath = '{objetivo}';"
        "$s.Arguments = '{argumentos}';"
        "$s.WorkingDirectory = '{trabajo}';"
        "{icono}"
        "$s.Description = 'Corrector ortografico YAJOL';"
        "$s.Save()"
    ).format(destino=destino.replace("'", "''"),
             objetivo=objetivo.replace("'", "''"),
             argumentos=argumentos.replace("'", "''"),
             trabajo=carpeta_trabajo.replace("'", "''"),
             icono=f"$s.IconLocation = '{icono}';" if icono else "")
    try:
        sin_ventana = subprocess.STARTUPINFO()
        sin_ventana.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", orden],
                       check=True, timeout=30, startupinfo=sin_ventana,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return os.path.exists(destino)
    except Exception:
        log.exception("No se pudo crear el acceso directo con PowerShell")
        return False


def _crea_respaldo_vbs() -> bool:
    """Si PowerShell falla, se deja un .vbs en la carpeta Inicio."""
    try:
        os.makedirs(carpeta_inicio(), exist_ok=True)
        # VBScript lee ANSI: cp1252 evita que Windows muestre texto ilegible
        with open(ruta_respaldo(), "w", encoding="cp1252", errors="replace",
                  newline="\r\n") as f:
            f.write(PLANTILLA_VBS.format(lanzador=LANZADOR))
        return True
    except Exception:
        log.exception("No se pudo crear el arranque de respaldo")
        return False


def activar() -> bool:
    """Hace que el corrector se abra solo al encender el equipo."""
    if not es_windows():
        return False
    if not os.path.isdir(carpeta_inicio()):
        log.error("No existe la carpeta Inicio: %s", carpeta_inicio())
        return False
    if os.path.exists(LANZADOR):
        objetivo, argumentos = "wscript.exe", f'"{LANZADOR}"'
        trabajo = config.RAIZ_DIR
    else:
        # sin lanzador: se usa el pythonw del entorno actual
        objetivo = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
        if not os.path.exists(objetivo):
            objetivo = sys.executable
        argumentos = '-m yajol'
        trabajo = config.RAIZ_DIR
    if _crea_acceso_directo(ruta_acceso(), objetivo, argumentos, trabajo, config.LOGO_PATH):
        log.info("Arranque automático activado")
        return True
    return _crea_respaldo_vbs()


def desactivar() -> bool:
    """Quita el arranque automático."""
    quitado = False
    for ruta in (ruta_acceso(), ruta_respaldo()):
        if os.path.exists(ruta):
            try:
                os.remove(ruta)
                quitado = True
            except OSError:
                log.exception("No se pudo borrar %s", ruta)
    return quitado


def alterna() -> bool:
    """Enciende o apaga el arranque automático. Devuelve el estado final."""
    if esta_activado():
        desactivar()
        return False
    return activar()
