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

    def test_el_respaldo_vbs_apunta_al_lanzador(self, monkeypatch, tmp_path):
        monkeypatch.setattr(inicio, "carpeta_inicio", lambda: str(tmp_path))
        monkeypatch.setattr(inicio, "ruta_respaldo", lambda: str(tmp_path / "r.vbs"))
        assert inicio._crea_respaldo_vbs()
        contenido = (tmp_path / "r.vbs").read_text(encoding="cp1252", errors="replace")
        assert "Yajol.vbs" in contenido and "WScript.Shell" in contenido

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
