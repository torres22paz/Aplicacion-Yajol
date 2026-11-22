"""Arranque automático con Windows.

Se crea un acceso directo en la carpeta Inicio del usuario. No hace falta
ser administrador y se puede quitar desde el menú del corrector o desde el
Administrador de tareas, pestaña «Inicio».

Este módulo también limpia los arranques que dejaron las versiones
anteriores (el antiguo «Corrector flotante»), que eran los que mostraban
un error cada vez que se encendía el equipo.
"""
import logging
import os
import subprocess
import sys

from .. import config

log = logging.getLogger("yajol")

NOMBRE_ACCESO = "Corrector YAJOL.lnk"
NOMBRE_RESPALDO = "Corrector YAJOL.vbs"
ARGUMENTO_INICIO = "--inicio"

# Con cualquiera de estas marcas, una entrada de arranque es de este programa
MARCAS_PROPIAS = ("yajol", "corrector_flotante", "corrector flotante")
EXTENSIONES_GUION = (".vbs", ".bat", ".cmd", ".js")
CLAVES_RUN = (r"Software\Microsoft\Windows\CurrentVersion\Run",
              r"Software\Microsoft\Windows\CurrentVersion\RunOnce")

# Respaldo por si no se puede crear el acceso directo: un guion que comprueba
# que todo sigue en su sitio y, si no, termina sin mostrar nada.
PLANTILLA_VBS = """' Arranque del Corrector YAJOL. Si la carpeta ya no existe, no hace nada.
On Error Resume Next
Dim sh, fso, pyw, carpeta
Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
carpeta = "{carpeta}"
pyw = carpeta & "\\.venv\\Scripts\\pythonw.exe"
If fso.FileExists(pyw) And fso.FolderExists(carpeta & "\\yajol") Then
    sh.CurrentDirectory = carpeta
    sh.Run Chr(34) & pyw & Chr(34) & " -m yajol {argumento}", 0, False
End If
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


def pythonw_del_entorno() -> str:
    """El pythonw.exe del entorno propio del corrector."""
    return os.path.join(config.RAIZ_DIR, ".venv", "Scripts", "pythonw.exe")


# ---------------------------------------------------------------
# PowerShell: crear y leer accesos directos
# ---------------------------------------------------------------
SIN_CONSOLA = 0x08000000        # CREATE_NO_WINDOW: que no parpadee ninguna ventana negra


def _ejecuta(orden: list, tiempo: int = 30, comprobar: bool = True) -> bytes:
    """Ejecuta un programa de Windows sin abrir ventana y devuelve su salida."""
    resultado = subprocess.run(orden, check=comprobar, timeout=tiempo,
                               creationflags=SIN_CONSOLA, stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    return resultado.stdout


def _powershell(orden: str, tiempo: int = 30) -> str:
    """Ejecuta una orden de PowerShell y devuelve lo que escribe."""
    completa = "[Console]::OutputEncoding=[Text.Encoding]::UTF8;" + orden
    crudo = _ejecuta(["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy",
                      "Bypass", "-Command", completa], tiempo)
    return crudo.decode("utf-8", errors="replace")


def _ps(texto: str) -> str:
    """Escapa un texto para ponerlo entre comillas simples de PowerShell."""
    return texto.replace("'", "''")


def _crea_acceso_directo(destino: str, objetivo: str, argumentos: str,
                         carpeta_trabajo: str, icono: str = "") -> bool:
    """Crea un .lnk con PowerShell. Devuelve True si lo consiguió."""
    orden = (
        f"$s = (New-Object -ComObject WScript.Shell).CreateShortcut('{_ps(destino)}');"
        f"$s.TargetPath = '{_ps(objetivo)}';"
        f"$s.Arguments = '{_ps(argumentos)}';"
        f"$s.WorkingDirectory = '{_ps(carpeta_trabajo)}';"
        + (f"$s.IconLocation = '{_ps(icono)}';" if icono else "")
        + "$s.Description = 'Corrector ortografico YAJOL';"
        "$s.Save()"
    )
    try:
        _powershell(orden)
        return os.path.exists(destino)
    except Exception:
        log.exception("No se pudo crear el acceso directo con PowerShell")
        return False


def _lee_accesos_directos(carpeta: str) -> dict:
    """{nombre.lnk: "destino argumentos carpeta"} de los accesos directos de una carpeta."""
    orden = (
        "$w = New-Object -ComObject WScript.Shell;"
        f"Get-ChildItem -LiteralPath '{_ps(carpeta)}' -Filter *.lnk | ForEach-Object {{"
        "$s = $w.CreateShortcut($_.FullName);"
        "Write-Output ($_.Name + [char]9 + $s.TargetPath + ' ' + $s.Arguments + ' ' "
        "+ $s.WorkingDirectory) }"
    )
    salida = {}
    try:
        for linea in _powershell(orden).splitlines():
            if "\t" in linea:
                nombre, destino = linea.split("\t", 1)
                salida[nombre.strip()] = destino.strip()
    except Exception:
        log.exception("No se pudieron leer los accesos directos de %s", carpeta)
    return salida


def _crea_respaldo_vbs() -> bool:
    """Si PowerShell falla, se deja un guion en la carpeta Inicio."""
    try:
        os.makedirs(carpeta_inicio(), exist_ok=True)
        # VBScript lee ANSI: cp1252 evita que Windows muestre texto ilegible
        with open(ruta_respaldo(), "w", encoding="cp1252", errors="replace",
                  newline="\r\n") as f:
            f.write(PLANTILLA_VBS.format(carpeta=config.RAIZ_DIR, argumento=ARGUMENTO_INICIO))
        return True
    except Exception:
        log.exception("No se pudo crear el arranque de respaldo")
        return False


# ---------------------------------------------------------------
# Limpieza de arranques antiguos
# ---------------------------------------------------------------
def _igual_ruta(texto: str, ruta: str) -> bool:
    return os.path.normcase(ruta).rstrip("\\/").lower() in os.path.normcase(texto).lower()


def es_entrada_antigua(nombre: str, destino: str, raiz_actual: str = None) -> bool:
    """
    Decide si una entrada de arranque es un resto que hay que quitar.

    nombre:  nombre del acceso directo, del valor del Registro o de la tarea.
    destino: a dónde apunta (ruta, argumentos, contenido del guion...).

    Es antigua si es de este programa (por el nombre o por el destino) y no es
    el acceso directo vigente que apunta a la carpeta actual.
    """
    raiz_actual = raiz_actual if raiz_actual is not None else config.RAIZ_DIR
    todo = f"{nombre} {destino}".lower()
    if not any(marca in todo for marca in MARCAS_PROPIAS):
        return False                         # no es nuestro: no se toca
    vigente = (nombre.lower() in (NOMBRE_ACCESO.lower(), NOMBRE_RESPALDO.lower())
               and _igual_ruta(destino, raiz_actual)
               and "corrector_flotante" not in destino.lower()
               and ARGUMENTO_INICIO in destino)
    return not vigente


def _texto_crudo(ruta: str, limite: int = 20000) -> str:
    """Las rutas que hay escritas dentro de un acceso directo, sin necesidad de abrirlo."""
    try:
        with open(ruta, "rb") as f:
            crudo = f.read(limite)
    except OSError:
        return ""
    texto = crudo.replace(b"\x00", b"").decode("latin-1", errors="replace")
    return "".join(c if 32 <= ord(c) < 127 else " " for c in texto)


def _entradas_carpeta_inicio() -> dict:
    """{ruta_completa: descripción} de lo que hay en la carpeta Inicio."""
    carpeta = carpeta_inicio()
    salida = {}
    if not os.path.isdir(carpeta):
        return salida
    accesos = _lee_accesos_directos(carpeta) if es_windows() else {}
    for nombre in os.listdir(carpeta):
        ruta = os.path.join(carpeta, nombre)
        if not os.path.isfile(ruta):
            continue
        extension = os.path.splitext(nombre)[1].lower()
        if extension == ".lnk":
            # destino leído con PowerShell y, además, lo que se lee dentro del
            # propio archivo: así funciona aunque PowerShell esté bloqueado
            salida[ruta] = (accesos.get(nombre, "") + " " + _texto_crudo(ruta)).strip()
        elif extension in EXTENSIONES_GUION:
            try:
                with open(ruta, encoding="cp1252", errors="replace") as f:
                    salida[ruta] = f.read(4000)
            except OSError:
                salida[ruta] = ""
    return salida


def _entradas_registro() -> list:
    """[(clave, nombre, valor)] de los programas que el Registro abre al iniciar sesión."""
    salida = []
    try:
        import winreg
    except ImportError:
        return salida
    for clave in CLAVES_RUN:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, clave) as k:
                indice = 0
                while True:
                    try:
                        nombre, valor, _ = winreg.EnumValue(k, indice)
                    except OSError:
                        break
                    salida.append((clave, nombre, str(valor)))
                    indice += 1
        except OSError:
            continue
    return salida


def _borra_registro(clave: str, nombre: str) -> bool:
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, clave, 0, winreg.KEY_SET_VALUE) as k:
            winreg.DeleteValue(k, nombre)
        return True
    except Exception:
        log.exception("No se pudo borrar %s del Registro", nombre)
        return False


def _tareas_programadas() -> list:
    """[(nombre, texto de la fila)] de las tareas programadas del usuario."""
    try:
        crudo = _ejecuta(["schtasks", "/query", "/fo", "csv", "/nh", "/v"], 40, comprobar=False)
    except Exception:
        return []
    import csv
    import io
    salida = []
    texto = crudo.decode("mbcs" if es_windows() else "utf-8", errors="replace")
    for fila in csv.reader(io.StringIO(texto)):
        if len(fila) > 1 and fila[1].startswith("\\"):
            salida.append((fila[1], " ".join(fila)))
    return salida


def _borra_tarea(nombre: str) -> bool:
    try:
        _ejecuta(["schtasks", "/delete", "/tn", nombre, "/f"], 20)
        return True
    except Exception:
        log.warning("No se pudo borrar la tarea programada %s", nombre)
        return False


def limpia_antiguos(incluir_tareas: bool = True) -> list:
    """
    Quita los arranques que dejaron versiones anteriores o carpetas que ya no existen.

    Revisa la carpeta Inicio, el Registro (Run) y las tareas programadas.
    Solo toca lo que es de este programa. Devuelve la lista de lo que quitó.
    """
    quitados = []
    if not es_windows():
        return quitados
    for ruta, destino in _entradas_carpeta_inicio().items():
        nombre = os.path.basename(ruta)
        if es_entrada_antigua(nombre, destino):
            try:
                os.remove(ruta)
                quitados.append(f"Inicio: {nombre}")
            except OSError:
                log.exception("No se pudo borrar %s", ruta)
    for clave, nombre, valor in _entradas_registro():
        if es_entrada_antigua(nombre, valor) and _borra_registro(clave, nombre):
            quitados.append(f"Registro: {nombre}")
    if incluir_tareas:
        for nombre, fila in _tareas_programadas():
            if es_entrada_antigua(nombre, fila) and _borra_tarea(nombre):
                quitados.append(f"Tarea: {nombre}")
    for quitado in quitados:
        log.info("Arranque antiguo eliminado -> %s", quitado)
    return quitados


# ---------------------------------------------------------------
# Activar, desactivar y reparar
# ---------------------------------------------------------------
def activar() -> bool:
    """Hace que el corrector se abra solo al encender el equipo."""
    if not es_windows():
        return False
    if not os.path.isdir(carpeta_inicio()):
        log.error("No existe la carpeta Inicio: %s", carpeta_inicio())
        return False
    objetivo = pythonw_del_entorno()
    if not os.path.exists(objetivo):
        objetivo = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    if not os.path.exists(objetivo):
        objetivo = sys.executable
    # El acceso directo abre pythonw directamente y en modo silencioso:
    # al encender el equipo nunca se muestran ventanas de error.
    if _crea_acceso_directo(ruta_acceso(), objetivo, f"-m yajol {ARGUMENTO_INICIO}",
                            config.RAIZ_DIR, config.ICONO_PATH):
        if os.path.exists(ruta_respaldo()):
            try:
                os.remove(ruta_respaldo())
            except OSError:
                pass
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


def repara(incluir_tareas: bool = False) -> dict:
    """
    Deja el arranque en buen estado. Se llama cada vez que abre el corrector.

    1. Quita los arranques de versiones anteriores y los que apuntan a una
       carpeta que ya no es esta (por ejemplo, si la carpeta se movió).
    2. Si el arranque estaba activado y se quitó algo, lo vuelve a crear
       apuntando a esta carpeta.
    """
    informe = {"quitados": [], "activo": False}
    if not es_windows():
        return informe
    estaba = esta_activado()
    informe["quitados"] = limpia_antiguos(incluir_tareas=incluir_tareas)
    if (estaba or informe["quitados"]) and not esta_activado():
        informe["activo"] = activar()
    else:
        informe["activo"] = esta_activado()
    return informe
