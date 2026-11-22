"""Pruebas de lo que se genera para Windows: los .vbs y la guía en HTML."""
import os
import re

import pytest

from yajol import __version__, config
from yajol.interfaz import contenido_ayuda as C

from herramientas import construir, guia


class TestConversionAAscii:
    def test_lo_que_ya_es_ascii_no_cambia(self):
        linea = 'sh.Run q & pyw & q & " -m yajol", 0, False'
        assert construir.a_ascii(linea) == linea

    def test_las_tildes_de_las_cadenas_pasan_a_chrw(self):
        assert construir.a_ascii('x = "Instalación"') == 'x = "Instalaci" & ChrW(243) & "n"'

    def test_una_cadena_que_empieza_con_tilde(self):
        assert construir.a_ascii('x = "Últimas"') == 'x = ChrW(218) & "ltimas"'

    def test_los_signos_especiales_tambien(self):
        salida = construir.a_ascii('Aviso "a → b", 64')
        assert "ChrW(8594)" in salida and salida.endswith(", 64")

    def test_los_comentarios_pierden_la_tilde(self):
        assert construir.a_ascii("' Instalación rápida") == "' Instalacion rapida"

    def test_una_comilla_simple_dentro_de_una_cadena_no_es_comentario(self):
        linea = 'x = "it\'s ok" & y'
        assert construir.a_ascii(linea) == linea

    def test_las_comillas_dobles_escapadas_se_respetan(self):
        linea = 'x = "dijo ""sí"" ayer"'
        salida = construir.a_ascii(linea)
        assert salida == 'x = "dijo ""s" & ChrW(237) & """ ayer"'

    def test_el_resultado_siempre_es_ascii(self):
        for nombre in construir.NOMBRES:
            construir.texto_final(nombre).encode("ascii")


class TestGuionesGenerados:
    @pytest.mark.parametrize("nombre", construir.NOMBRES)
    def test_el_archivo_entregado_coincide_con_su_fuente(self, nombre):
        """Nadie debe editar el .vbs a mano: se genera con herramientas/construir.py."""
        with open(os.path.join(config.RAIZ_DIR, nombre + ".vbs"), "rb") as f:
            entregado = f.read().decode("ascii")
        assert entregado == construir.texto_final(nombre), \
            f"{nombre}.vbs está desactualizado: ejecuta python herramientas/construir.py"

    @pytest.mark.parametrize("nombre", construir.NOMBRES)
    def test_las_comillas_estan_equilibradas(self, nombre):
        for numero, linea in enumerate(construir.texto_final(nombre).split("\r\n"), 1):
            codigo = linea.split("'")[0] if linea.lstrip().startswith("'") else linea
            assert codigo.count('"') % 2 == 0, f"{nombre}.vbs línea {numero}: {linea}"

    @pytest.mark.parametrize("nombre", construir.NOMBRES)
    def test_los_bloques_estan_cerrados(self, nombre):
        texto = construir.texto_final(nombre)
        texto = re.sub(r" _\r\n\s*", " ", texto)          # une las líneas partidas con « _»
        lineas = [ln.strip() for ln in texto.split("\r\n") if not ln.strip().startswith("'")]
        abre_funcion = sum(1 for ln in lineas if re.match(r"(Function|Sub) \w+", ln))
        cierra_funcion = sum(1 for ln in lineas if re.match(r"End (Function|Sub)$", ln))
        assert abre_funcion == cierra_funcion
        abre_si = sum(1 for ln in lineas if re.match(r"If .* Then$", ln))
        cierra_si = sum(1 for ln in lineas if ln == "End If")
        assert abre_si == cierra_si, f"{nombre}.vbs: {abre_si} If de bloque y {cierra_si} End If"
        assert sum(1 for ln in lineas if ln.startswith("For ")) == sum(1 for ln in lineas if ln == "Next")

    @pytest.mark.parametrize("nombre", ["Instalar", "Desinstalar"])
    def test_incluyen_las_funciones_comunes(self, nombre):
        texto = construir.texto_final(nombre)
        assert construir.MARCA_COMUN not in texto
        for funcion in ("LimpiaCarpetaInicio", "LimpiaRegistro", "CierraCorrectorAbierto", "EsVigente"):
            assert f"Function {funcion}" in texto or f"Sub {funcion}" in texto

    def test_ninguna_variable_se_llama_como_una_funcion(self):
        """En VBScript no se distinguen mayúsculas: una variable «carpetaInicio»
        taparía a la función «CarpetaInicio» y el guion fallaría."""
        for nombre in construir.NOMBRES:
            texto = construir.texto_final(nombre)
            funciones = {m.lower() for m in re.findall(r"^(?:Function|Sub) (\w+)", texto, re.M)}
            for declaracion in re.findall(r"^\s*Dim (.+)$", texto, re.M):
                for variable in declaracion.split(","):
                    assert variable.strip().lower() not in funciones, \
                        f"{nombre}.vbs: la variable {variable.strip()} tapa a una función"

    def test_con_option_explicit_todo_esta_declarado_en_el_lanzador(self):
        texto = construir.texto_final("Yajol")
        declaradas = {v.strip().lower() for d in re.findall(r"^Dim (.+)$", texto, re.M) for v in d.split(",")}
        asignadas = {m.lower() for m in re.findall(r"^\s*(?:Set )?(\w+) = ", texto, re.M)}
        assert asignadas <= declaradas, f"sin declarar: {asignadas - declaradas}"

    def test_los_avisos_del_instalador_llevan_tildes(self):
        assert "Instalación" in construir.compone("Instalar")
        assert "ChrW(243)" in construir.texto_final("Instalar")       # la ó

    def test_el_instalador_menciona_el_signo_de_ayuda(self):
        assert "signo ?" in construir.compone("Instalar")


class TestGuiaHtml:
    @pytest.fixture(scope="class")
    def pagina(self):
        return guia.genera()

    def test_la_guia_entregada_esta_al_dia(self, pagina):
        with open(config.GUIA_PATH, encoding="utf-8") as f:
            assert f.read() == pagina, "ejecuta python herramientas/construir.py"

    def test_no_depende_de_internet(self, pagina):
        externos = re.findall(r'(?:src|href)="(https?://[^"]+)"', pagina)
        assert externos == [], f"recursos externos: {externos}"
        assert "<script" not in pagina

    def test_lleva_el_logotipo_dentro(self, pagina):
        assert "data:image/png;base64," in pagina

    def test_tiene_todas_las_secciones(self, pagina):
        for ancla in ("instalar", "usar", "corrige", "atajos", "falla", "ampliar"):
            assert f'id="{ancla}"' in pagina and f'href="#{ancla}"' in pagina

    def test_usa_los_mismos_textos_que_la_ayuda(self, pagina):
        for titulo, _, _ in C.PASOS:
            assert titulo in pagina
        for categoria, _ in C.EJEMPLOS:
            assert categoria in pagina

    def test_explica_el_signo_de_interrogacion(self, pagina):
        assert "signo <strong>?</strong>" in pagina

    def test_explica_el_error_al_encender_el_equipo(self, pagina):
        assert "error al encender el equipo" in pagina

    def test_indica_la_version(self, pagina):
        assert f"Versión {__version__}" in pagina

    def test_los_enlaces_no_son_azules(self, pagina):
        estilo = pagina[pagina.index("<style>"):pagina.index("</style>")]
        assert re.search(r"nav a\{color:var\(--gris\);text-decoration:none", estilo)
        cuerpo = pagina[pagina.index("<main"):]
        assert "<a " not in cuerpo, "fuera del menú no hay enlaces"

    def test_el_html_esta_bien_cerrado(self, pagina):
        for etiqueta in ("section", "table", "div", "details", "main", "header", "nav", "dl"):
            assert pagina.count(f"<{etiqueta}") == pagina.count(f"</{etiqueta}>"), etiqueta

    def test_esta_en_espanol_y_en_utf8(self, pagina):
        assert '<html lang="es">' in pagina and '<meta charset="utf-8">' in pagina
