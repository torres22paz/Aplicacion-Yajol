"""Pruebas de la parte que habla con Windows: teclado, portapapeles y arranque."""
import os
import sys
import types

import pytest

from yajol import config
from yajol.sistema import inicio, teclado


# ---------------------------------------------------------------
# Teclado y portapapeles: se sustituyen por imitaciones para poder
# probarlos en cualquier sistema, sin tocar el teclado de verdad.
# ---------------------------------------------------------------
class TeclasFalsas:
    shift = "shift"
    ctrl = "ctrl"
    left = "left"


class ControladorFalso:
    def __init__(self):
        self.pulsadas = []
        self.combinaciones = []

    def press(self, tecla):
        self.pulsadas.append(tecla)

    def release(self, tecla):
        pass

    def pressed(self, *modificadores):
        self.combinaciones.append(modificadores)

        class Contexto:
            def __enter__(_): return None
            def __exit__(_, *a): return False
        return Contexto()


class PortapapelesFalso:
    def __init__(self, contenido=""):
        self.contenido = contenido
        self.historial = []
        self.al_copiar = None

    def paste(self):
        return self.contenido

    def copy(self, texto):
        self.contenido = texto
        self.historial.append(texto)
        if self.al_copiar:
            self.al_copiar(texto)


@pytest.fixture
def entorno_falso(monkeypatch):
    """Deja el módulo teclado funcionando sin teclado ni portapapeles reales."""
    controlador = ControladorFalso()
    portapapeles = PortapapelesFalso()
    monkeypatch.setattr(teclado, "_controlador", lambda: controlador)
    monkeypatch.setattr(teclado, "_portapapeles", lambda: portapapeles)
    monkeypatch.setattr(teclado.config, "RETARDO_TECLA", 0)
    monkeypatch.setattr(teclado.config, "RETARDO_COPIA", 0)
    monkeypatch.setattr(teclado.config, "RETARDO_PEGADO", 0)
    falso_pynput = types.ModuleType("pynput.keyboard")
    falso_pynput.Key = TeclasFalsas
    falso_pynput.Controller = lambda: controlador
    monkeypatch.setitem(sys.modules, "pynput", types.ModuleType("pynput"))
    monkeypatch.setitem(sys.modules, "pynput.keyboard", falso_pynput)
    falso_clip = types.ModuleType("pyperclip")
    falso_clip.copy = portapapeles.copy
    falso_clip.paste = portapapeles.paste
    monkeypatch.setitem(sys.modules, "pyperclip", falso_clip)
    return controlador, portapapeles


class TestLeerElTexto:
    def test_usa_la_seleccion_que_ya_habia(self, entorno_falso):
        _, portapapeles = entorno_falso
        portapapeles.al_copiar = lambda t: setattr(portapapeles, "contenido",
                                                   "texto ya seleccionado" if t == "" else t)
        texto, habia = teclado.lee_contexto(5)
        assert texto == "texto ya seleccionado"
        assert habia is True

    def test_si_no_hay_seleccion_toma_las_ultimas_palabras(self, entorno_falso):
        controlador, portapapeles = entorno_falso
        intentos = {"n": 0}

        def responde(t):
            if t != "":
                return
            intentos["n"] += 1
            # la primera copia sale vacía (no había nada seleccionado)
            portapapeles.contenido = "" if intentos["n"] == 1 else "las ultimas palabras"
        portapapeles.al_copiar = responde

        texto, habia = teclado.lee_contexto(7)
        assert texto == "las ultimas palabras"
        assert habia is False
        assert controlador.pulsadas.count(TeclasFalsas.left) == 7

    def test_devuelve_el_portapapeles_como_estaba(self, entorno_falso):
        _, portapapeles = entorno_falso
        portapapeles.contenido = "lo que el usuario tenia copiado"
        portapapeles.al_copiar = lambda t: None
        teclado.lee_contexto(3)
        assert portapapeles.historial[-1] == "lo que el usuario tenia copiado"

    def test_reintenta_cuando_no_llega_nada(self, entorno_falso):
        _, portapapeles = entorno_falso
        portapapeles.al_copiar = lambda t: None
        assert teclado.copia_seleccion(3) == ""


class TestEscribirElTexto:
    def test_pega_el_texto_corregido(self, entorno_falso):
        controlador, portapapeles = entorno_falso
        portapapeles.contenido = "lo de antes"
        teclado.reemplaza_seleccion("texto corregido")
        assert "texto corregido" in portapapeles.historial
        assert portapapeles.historial[-1] == "lo de antes"
        assert (TeclasFalsas.ctrl,) in controlador.combinaciones

    def test_selecciona_hacia_atras(self, entorno_falso):
        controlador, _ = entorno_falso
        teclado.selecciona_atras(4)
        assert controlador.pulsadas.count(TeclasFalsas.left) == 4
        assert (TeclasFalsas.shift, TeclasFalsas.ctrl) in controlador.combinaciones


class TestDisponibilidad:
    def test_dice_si_puede_usar_el_teclado(self, entorno_falso):
        assert teclado.disponible() is True


# ---------------------------------------------------------------
# Arranque automático
# ---------------------------------------------------------------
class TestArranqueAutomatico:
    def test_sabe_si_esta_en_windows(self):
        assert inicio.es_windows() == (os.name == "nt")

    def test_la_carpeta_inicio_es_la_de_windows(self, monkeypatch):
        monkeypatch.setenv("APPDATA", os.path.join("C:", "Users", "ana", "AppData", "Roaming"))
        ruta = inicio.carpeta_inicio()
        assert ruta.endswith(os.path.join("Programs", "Startup"))

    def test_el_acceso_directo_se_llama_igual_siempre(self, monkeypatch):
        monkeypatch.setenv("APPDATA", "X")
        assert inicio.ruta_acceso().endswith("Corrector YAJOL.lnk")
        assert inicio.ruta_respaldo().endswith("Corrector YAJOL.vbs")

    def test_detecta_que_ya_esta_activado(self, monkeypatch, tmp_path):
        monkeypatch.setattr(inicio, "carpeta_inicio", lambda: str(tmp_path))
        monkeypatch.setattr(inicio, "ruta_acceso", lambda: str(tmp_path / "Corrector YAJOL.lnk"))
        monkeypatch.setattr(inicio, "ruta_respaldo", lambda: str(tmp_path / "Corrector YAJOL.vbs"))
        assert not inicio.esta_activado()
        (tmp_path / "Corrector YAJOL.lnk").write_text("x")
        assert inicio.esta_activado()

    def test_desactivar_borra_los_dos_archivos(self, monkeypatch, tmp_path):
        monkeypatch.setattr(inicio, "ruta_acceso", lambda: str(tmp_path / "a.lnk"))
        monkeypatch.setattr(inicio, "ruta_respaldo", lambda: str(tmp_path / "b.vbs"))
        (tmp_path / "a.lnk").write_text("x")
        (tmp_path / "b.vbs").write_text("x")
        assert inicio.desactivar()
        assert not (tmp_path / "a.lnk").exists()
        assert not (tmp_path / "b.vbs").exists()

    def test_desactivar_sin_nada_no_falla(self, monkeypatch, tmp_path):
        monkeypatch.setattr(inicio, "ruta_acceso", lambda: str(tmp_path / "no.lnk"))
        monkeypatch.setattr(inicio, "ruta_respaldo", lambda: str(tmp_path / "no.vbs"))
        assert inicio.desactivar() is False

    def test_el_respaldo_comprueba_que_la_carpeta_existe(self, monkeypatch, tmp_path):
        monkeypatch.setattr(inicio, "carpeta_inicio", lambda: str(tmp_path))
        monkeypatch.setattr(inicio, "ruta_respaldo", lambda: str(tmp_path / "r.vbs"))
        assert inicio._crea_respaldo_vbs()
        contenido = (tmp_path / "r.vbs").read_text(encoding="cp1252", errors="replace")
        assert "pythonw.exe" in contenido and "--inicio" in contenido
        assert "FileExists" in contenido, "si la carpeta ya no existe no debe mostrar nada"
        assert "On Error Resume Next" in contenido

    def test_fuera_de_windows_no_activa_nada(self, monkeypatch):
        monkeypatch.setattr(inicio, "es_windows", lambda: False)
        assert inicio.activar() is False

    def test_alterna_apaga_lo_que_estaba_encendido(self, monkeypatch):
        estado = {"activo": True}
        monkeypatch.setattr(inicio, "esta_activado", lambda: estado["activo"])
        monkeypatch.setattr(inicio, "desactivar", lambda: estado.update(activo=False) or True)
        monkeypatch.setattr(inicio, "activar", lambda: True)
        assert inicio.alterna() is False


class TestArchivosDeWindows:
    """Los .vbs tienen que ser legibles por Windows (ANSI), no UTF-8."""

    @pytest.mark.parametrize("nombre", ["Instalar.vbs", "Yajol.vbs", "Desinstalar.vbs"])
    def test_el_lanzador_existe(self, nombre):
        assert os.path.exists(os.path.join(config.RAIZ_DIR, nombre)), f"falta {nombre}"

    @pytest.mark.parametrize("nombre", ["Instalar.vbs", "Yajol.vbs", "Desinstalar.vbs"])
    def test_se_lee_bien_en_ansi(self, nombre):
        ruta = os.path.join(config.RAIZ_DIR, nombre)
        crudo = open(ruta, "rb").read()
        # sin caracteres fuera de ASCII no hay forma de que salga texto ilegible
        assert all(b < 128 for b in crudo), f"{nombre} tiene caracteres que Windows puede romper"

    @pytest.mark.parametrize("nombre", ["Instalar.vbs", "Yajol.vbs", "Desinstalar.vbs"])
    def test_usa_saltos_de_linea_de_windows(self, nombre):
        crudo = open(os.path.join(config.RAIZ_DIR, nombre), "rb").read()
        assert b"\r\n" in crudo

    def test_el_instalador_avisa_si_se_abre_desde_el_zip(self):
        texto = open(os.path.join(config.RAIZ_DIR, "Instalar.vbs"), encoding="cp1252").read()
        assert ".zip" in texto.lower()
        assert "Extraer todo" in texto

    def test_el_instalador_limpia_antes_de_cualquier_otra_cosa(self):
        texto = open(os.path.join(config.RAIZ_DIR, "Instalar.vbs"), encoding="ascii").read()
        limpieza = texto.index("quitados = LimpiaCarpetaInicio() + LimpiaRegistro()")
        assert limpieza < texto.index("Extraer todo"), \
            "aunque se abra desde el ZIP, primero hay que quitar el arranque antiguo"

    def test_el_lanzador_es_silencioso_al_encender_el_equipo(self):
        texto = open(os.path.join(config.RAIZ_DIR, "Yajol.vbs"), encoding="ascii").read()
        assert "/inicio" in texto
        assert "If silencioso Then WScript.Quit 0" in texto

    def test_desinstalar_no_cierra_otros_programas_de_python(self):
        texto = open(os.path.join(config.RAIZ_DIR, "Desinstalar.vbs"), encoding="ascii").read()
        assert "taskkill" not in texto.lower()
        assert "-m yajol" in texto

    def test_el_instalador_revisa_la_carpeta_temporal(self):
        texto = open(os.path.join(config.RAIZ_DIR, "Instalar.vbs"), encoding="cp1252").read()
        assert "temp" in texto.lower()

    def test_el_instalador_busca_python_de_varias_formas(self):
        texto = open(os.path.join(config.RAIZ_DIR, "Instalar.vbs"), encoding="cp1252").read()
        assert "py -3" in texto and "python" in texto

    def test_requirements_no_pide_java(self):
        texto = open(os.path.join(config.RAIZ_DIR, "requirements.txt"), encoding="utf-8").read()
        assert "language-tool" not in texto, "LanguageTool necesita Java: va en el archivo opcional"

    def test_requirements_trae_lo_imprescindible(self):
        texto = open(os.path.join(config.RAIZ_DIR, "requirements.txt"), encoding="utf-8").read()
        for paquete in ("PySide6", "spylls", "pynput", "pyperclip"):
            assert paquete in texto


class TestDatos:
    @pytest.mark.parametrize("ruta", [
        config.DICCIONARIO_ZIP, config.FRECUENCIAS_GZ,
        config.PALABRAS_EXTRA, config.NOMBRES_PROPIOS, config.LOGO_PATH,
    ])
    def test_los_archivos_de_datos_estan(self, ruta):
        assert os.path.exists(ruta), f"falta {ruta}"

    def test_la_aplicacion_no_pesa_mucho(self):
        total = sum(os.path.getsize(os.path.join(raiz, f))
                    for raiz, _, archivos in os.walk(config.RAIZ_DIR)
                    for f in archivos
                    if "__pycache__" not in raiz and ".venv" not in raiz and ".git" not in raiz)
        assert total < 2 * 1024 * 1024, f"la carpeta pesa {total / 1024:.0f} KB"

    def test_hay_icono_para_el_acceso_directo(self):
        with open(config.ICONO_PATH, "rb") as f:
            assert f.read(4) == b"\x00\x00\x01\x00", "debe ser un archivo .ico de verdad"


# ---------------------------------------------------------------
# Limpieza de los arranques de versiones anteriores
# ---------------------------------------------------------------
RAIZ = r"C:\Users\Omar\Documents\corrector_yajol"


class TestEntradasAntiguas:
    @pytest.mark.parametrize("nombre,destino", [
        # el arranque de la primera versión, que apuntaba dentro del ZIP
        ("iniciar.lnk", r'C:\Windows\System32\wscript.exe "C:\Users\OmarAle\AppData\Local\Temp\7de3'
                        r'_corrector yajol.zip\corrector_flotante\iniciar.vbs"'),
        ("Corrector flotante.lnk", r"C:\algo\pythonw.exe main.py"),
        ("CorrectorFlotante", r"pythonw C:\x\corrector_flotante\main.py"),
        # el de la versión 2.0, que abría Yajol.vbs con wscript
        ("Corrector YAJOL.lnk", RAIZ + r'\Yajol.vbs " ' + RAIZ),
        # el de otra carpeta (la carpeta se movió o se instaló dos veces)
        ("Corrector YAJOL.lnk", r"D:\otra\corrector_yajol\.venv\Scripts\pythonw.exe -m yajol --inicio D:\otra"),
        ("viejo.bat", r"start pythonw C:\cosas\corrector_flotante\main.py"),
    ])
    def test_lo_antiguo_se_reconoce(self, nombre, destino):
        assert inicio.es_entrada_antigua(nombre, destino, RAIZ)

    def test_el_acceso_vigente_se_respeta(self):
        destino = RAIZ + r"\.venv\Scripts\pythonw.exe -m yajol --inicio " + RAIZ
        assert not inicio.es_entrada_antigua("Corrector YAJOL.lnk", destino, RAIZ)

    def test_el_respaldo_vigente_se_respeta(self):
        contenido = inicio.PLANTILLA_VBS.format(carpeta=RAIZ, argumento="--inicio")
        assert not inicio.es_entrada_antigua("Corrector YAJOL.vbs", contenido, RAIZ)

    @pytest.mark.parametrize("nombre,destino", [
        ("OneDrive.lnk", r"C:\Program Files\Microsoft OneDrive\OneDrive.exe /background"),
        ("Spotify", r"C:\Users\Omar\AppData\Roaming\Spotify\Spotify.exe"),
        ("Corrector ortografico de otra marca.lnk", r"C:\Program Files\Otro\otro.exe"),
        ("comedor.lnk", r"C:\Users\Omar\PycharmProjects\comedor\pythonw.exe app.py"),
    ])
    def test_los_programas_ajenos_no_se_tocan(self, nombre, destino):
        assert not inicio.es_entrada_antigua(nombre, destino, RAIZ)

    def test_lee_las_rutas_de_dentro_de_un_acceso_directo(self, tmp_path):
        acceso = tmp_path / "iniciar.lnk"
        ruta = r"C:\Temp\x.zip\corrector_flotante\iniciar.vbs"
        acceso.write_bytes(b"L\x00\x00\x00\x01\x14\x02\x00" + ruta.encode("utf-16-le") + b"\x00\x00")
        assert "corrector_flotante" in inicio._texto_crudo(str(acceso))

    def test_un_archivo_que_no_existe_no_rompe_nada(self, tmp_path):
        assert inicio._texto_crudo(str(tmp_path / "no_esta.lnk")) == ""


@pytest.fixture
def windows_falso(monkeypatch, tmp_path):
    """Una carpeta Inicio y un Registro de mentira, para probar la limpieza completa."""
    carpeta = tmp_path / "Startup"
    carpeta.mkdir()
    monkeypatch.setattr(inicio.config, "RAIZ_DIR", RAIZ)
    monkeypatch.setattr(inicio, "es_windows", lambda: True)
    monkeypatch.setattr(inicio, "carpeta_inicio", lambda: str(carpeta))
    monkeypatch.setattr(inicio, "ruta_acceso", lambda: str(carpeta / inicio.NOMBRE_ACCESO))
    monkeypatch.setattr(inicio, "ruta_respaldo", lambda: str(carpeta / inicio.NOMBRE_RESPALDO))
    pythonw = tmp_path / "pythonw.exe"
    pythonw.write_text("")
    monkeypatch.setattr(inicio, "pythonw_del_entorno", lambda: str(pythonw))
    accesos = {}
    monkeypatch.setattr(inicio, "_lee_accesos_directos", lambda c: dict(accesos))
    registro = [("Run", "CorrectorFlotante", r"pythonw C:\x\corrector_flotante\main.py"),
                ("Run", "OneDrive", r"C:\onedrive.exe /background")]
    borrados = []
    monkeypatch.setattr(inicio, "_entradas_registro", lambda: list(registro))
    monkeypatch.setattr(inicio, "_borra_registro", lambda c, n: borrados.append(n) or True)
    tareas = [("\\Corrector flotante al inicio", "equipo \\Corrector flotante al inicio pythonw main.py"),
              ("\\Microsoft\\Windows\\Defrag", "equipo defrag.exe")]
    tareas_borradas = []
    monkeypatch.setattr(inicio, "_tareas_programadas", lambda: list(tareas))
    monkeypatch.setattr(inicio, "_borra_tarea", lambda n: tareas_borradas.append(n) or True)

    def crea_acceso(destino, objetivo, argumentos, trabajo, icono=""):
        with open(destino, "w") as f:
            f.write("acceso")
        accesos[os.path.basename(destino)] = f"{objetivo} {argumentos} {trabajo}"
        return True
    monkeypatch.setattr(inicio, "_crea_acceso_directo", crea_acceso)
    return {"carpeta": carpeta, "accesos": accesos, "borrados": borrados,
            "tareas_borradas": tareas_borradas}


class TestLimpiezaCompleta:
    def _siembra(self, w):
        (w["carpeta"] / "iniciar.lnk").write_text("x")
        w["accesos"]["iniciar.lnk"] = r"wscript.exe C:\Temp\a.zip\corrector_flotante\iniciar.vbs"
        (w["carpeta"] / "OtroPrograma.lnk").write_text("x")
        w["accesos"]["OtroPrograma.lnk"] = r"C:\Windows\notepad.exe"
        (w["carpeta"] / "viejo.bat").write_text(r"start pythonw C:\c\corrector_flotante\main.py")
        (w["carpeta"] / "ajeno.vbs").write_text("WScript.Echo 1")

    def test_quita_lo_antiguo_de_los_tres_sitios(self, windows_falso):
        self._siembra(windows_falso)
        quitados = inicio.limpia_antiguos()
        quedan = sorted(os.listdir(windows_falso["carpeta"]))
        assert quedan == ["OtroPrograma.lnk", "ajeno.vbs"]
        assert windows_falso["borrados"] == ["CorrectorFlotante"]
        assert windows_falso["tareas_borradas"] == ["\\Corrector flotante al inicio"]
        assert len(quitados) == 4

    def test_sin_nada_antiguo_no_quita_nada(self, windows_falso, monkeypatch):
        monkeypatch.setattr(inicio, "_entradas_registro", lambda: [])
        monkeypatch.setattr(inicio, "_tareas_programadas", lambda: [])
        (windows_falso["carpeta"] / "OtroPrograma.lnk").write_text("x")
        assert inicio.limpia_antiguos() == []
        assert os.listdir(windows_falso["carpeta"]) == ["OtroPrograma.lnk"]

    def test_fuera_de_windows_no_hace_nada(self, monkeypatch):
        monkeypatch.setattr(inicio, "es_windows", lambda: False)
        assert inicio.limpia_antiguos() == []
        assert inicio.repara() == {"quitados": [], "activo": False}

    def test_activar_abre_pythonw_en_modo_silencioso(self, windows_falso):
        assert inicio.activar()
        destino = windows_falso["accesos"][inicio.NOMBRE_ACCESO]
        assert "pythonw.exe" in destino and "-m yajol --inicio" in destino
        assert "wscript" not in destino.lower(), "así no depende de ningún guion al encender"

    def test_lo_que_crea_activar_no_se_considera_antiguo(self, windows_falso, monkeypatch):
        monkeypatch.setattr(inicio, "_entradas_registro", lambda: [])
        monkeypatch.setattr(inicio, "_tareas_programadas", lambda: [])
        inicio.activar()
        assert inicio.limpia_antiguos() == []
        assert inicio.esta_activado()

    def test_reparar_sustituye_el_arranque_antiguo_por_el_nuevo(self, windows_falso):
        self._siembra(windows_falso)
        informe = inicio.repara(incluir_tareas=True)
        assert informe["activo"] is True
        assert len(informe["quitados"]) == 4
        assert inicio.NOMBRE_ACCESO in os.listdir(windows_falso["carpeta"])
        assert "iniciar.lnk" not in os.listdir(windows_falso["carpeta"])

    def test_reparar_rehace_el_acceso_si_la_carpeta_se_movio(self, windows_falso, monkeypatch):
        monkeypatch.setattr(inicio, "_entradas_registro", lambda: [])
        (windows_falso["carpeta"] / inicio.NOMBRE_ACCESO).write_text("x")
        windows_falso["accesos"][inicio.NOMBRE_ACCESO] = \
            r"D:\antes\corrector_yajol\.venv\Scripts\pythonw.exe -m yajol --inicio D:\antes\corrector_yajol"
        informe = inicio.repara()
        assert informe["activo"] is True
        assert RAIZ in windows_falso["accesos"][inicio.NOMBRE_ACCESO]

    def test_reparar_no_activa_lo_que_el_usuario_apago(self, windows_falso, monkeypatch):
        monkeypatch.setattr(inicio, "_entradas_registro", lambda: [])
        informe = inicio.repara()
        assert informe == {"quitados": [], "activo": False}
        assert os.listdir(windows_falso["carpeta"]) == []

    def test_reparar_no_rehace_lo_que_ya_esta_bien(self, windows_falso, monkeypatch):
        monkeypatch.setattr(inicio, "_entradas_registro", lambda: [])
        inicio.activar()
        creados = []
        monkeypatch.setattr(inicio, "activar", lambda: creados.append(1) or True)
        assert inicio.repara()["activo"] is True
        assert creados == []


class TestOrdenesDeWindows:
    """Las órdenes que se mandan a Windows, revisadas sin ejecutarlas."""

    def _captura(self, monkeypatch):
        ordenes = []

        def falso(orden, tiempo=30, comprobar=True):
            ordenes.append(orden)
            return b"iniciar.lnk\tC:\\w\\wscript.exe C:\\t\\corrector_flotante\\iniciar.vbs \r\n"
        monkeypatch.setattr(inicio, "_ejecuta", falso)
        return ordenes

    def test_crear_el_acceso_usa_powershell_sin_perfil(self, monkeypatch, tmp_path):
        ordenes = self._captura(monkeypatch)
        inicio._crea_acceso_directo(str(tmp_path / "a.lnk"), r"C:\p\pythonw.exe",
                                    "-m yajol --inicio", r"C:\app", r"C:\app\y.ico")
        orden = ordenes[0]
        assert orden[0] == "powershell" and "-NoProfile" in orden and "-NonInteractive" in orden
        guion = orden[-1]
        for trozo in ("CreateShortcut(", "$s.TargetPath = 'C:\\p\\pythonw.exe'",
                      "$s.Arguments = '-m yajol --inicio'", "$s.WorkingDirectory = 'C:\\app'",
                      "$s.IconLocation = 'C:\\app\\y.ico'", "$s.Save()"):
            assert trozo in guion, trozo

    def test_las_comillas_simples_de_las_rutas_se_escapan(self, monkeypatch, tmp_path):
        ordenes = self._captura(monkeypatch)
        inicio._crea_acceso_directo(str(tmp_path / "a.lnk"), r"C:\Users\D'Angelo\pythonw.exe",
                                    "-m yajol --inicio", r"C:\Users\D'Angelo\app")
        assert "D''Angelo" in ordenes[0][-1]

    def test_la_orden_no_lleva_comillas_dobles(self, monkeypatch, tmp_path):
        """Las comillas dobles se pierden al pasar la orden a PowerShell."""
        ordenes = self._captura(monkeypatch)
        inicio._crea_acceso_directo(str(tmp_path / "a.lnk"), "x", "-m yajol --inicio", "y")
        inicio._lee_accesos_directos(r"C:\Inicio")
        for orden in ordenes:
            assert '"' not in orden[-1]

    def test_lee_el_destino_de_cada_acceso(self, monkeypatch):
        self._captura(monkeypatch)
        accesos = inicio._lee_accesos_directos(r"C:\Inicio")
        assert "corrector_flotante" in accesos["iniciar.lnk"]

    def test_si_powershell_falla_no_se_rompe_nada(self, monkeypatch):
        def falla(*a, **k):
            raise OSError("powershell bloqueado")
        monkeypatch.setattr(inicio, "_ejecuta", falla)
        assert inicio._lee_accesos_directos(r"C:\Inicio") == {}
        assert inicio._crea_acceso_directo("a.lnk", "x", "y", "z") is False
        assert inicio._tareas_programadas() == []
        assert inicio._borra_tarea("\\tarea") is False

    def test_las_tareas_programadas_se_leen_del_csv(self, monkeypatch):
        csv = (b'"PC","\\Corrector flotante","N/A","Listo","pythonw main.py"\r\n'
               b'"PC","\\Microsoft\\Windows\\Defrag","N/A","Listo","defrag.exe"\r\n')
        monkeypatch.setattr(inicio, "_ejecuta", lambda *a, **k: csv)
        monkeypatch.setattr(inicio, "es_windows", lambda: False)     # para decodificar en utf-8
        tareas = inicio._tareas_programadas()
        assert [nombre for nombre, _ in tareas] == ["\\Corrector flotante", "\\Microsoft\\Windows\\Defrag"]
        assert inicio.es_entrada_antigua(*tareas[0]) and not inicio.es_entrada_antigua(*tareas[1])


class TestSoltarModificadores:
    def test_suelta_ctrl_alt_y_mayus(self, entorno_falso, monkeypatch):
        controlador, _ = entorno_falso
        sueltas = []
        monkeypatch.setattr(controlador, "release", sueltas.append)
        TeclasFalsas.alt = "alt"
        try:
            teclado.suelta_modificadores(0)
        finally:
            del TeclasFalsas.alt
        assert {"alt", "ctrl", "shift"} <= set(sueltas)

    def test_con_el_atajo_se_sueltan_antes_de_copiar(self, entorno_falso, monkeypatch):
        orden = []
        monkeypatch.setattr(teclado, "suelta_modificadores", lambda *a: orden.append("soltar"))
        monkeypatch.setattr(teclado, "copia_seleccion", lambda *a: orden.append("copiar") or "texto")
        teclado.lee_contexto(3, desde_atajo=True)
        assert orden[:2] == ["soltar", "copiar"]

    def test_con_el_raton_no_hace_falta(self, entorno_falso, monkeypatch):
        llamadas = []
        monkeypatch.setattr(teclado, "suelta_modificadores", lambda *a: llamadas.append(1))
        monkeypatch.setattr(teclado, "copia_seleccion", lambda *a: "texto")
        teclado.lee_contexto(3)
        assert llamadas == []
