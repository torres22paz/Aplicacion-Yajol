"""Genera Guia.html: las instrucciones del corrector en una página bien presentada.

La página no depende de internet: lleva dentro sus estilos y el logotipo.
Los textos salen de yajol/interfaz/contenido_ayuda.py, los mismos que usa la
ventana de ayuda del programa.
"""
import base64
import html
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from yajol import __version__, config  # noqa: E402
from yajol.interfaz import contenido_ayuda as C  # noqa: E402

ESTILO = """
:root{--azul:#1E3A8A;--azul2:#2563EB;--tinta:#111827;--gris:#4B5563;--linea:#E5E7EB;
--fondo:#F3F4F6;--papel:#FFFFFF;--verde:#166534;--verde-f:#DCFCE7;--rojo:#B91C1C;
--rojo-f:#FEE2E2;--ambar:#92400E;--ambar-f:#FFFBEB;--ambar-b:#FDE68A}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--fondo);color:var(--tinta);
font:16px/1.55 "Segoe UI",system-ui,-apple-system,Roboto,Arial,sans-serif}
header{background:var(--azul);color:#fff}
.ancho{max-width:900px;margin:0 auto;padding:0 20px}
.portada{display:flex;align-items:center;gap:22px;padding:34px 0 30px}
.portada img{width:92px;height:92px;border-radius:50%;background:#fff;flex:none}
.portada h1{margin:0;font-size:32px;line-height:1.15;letter-spacing:-.01em}
.portada p{margin:6px 0 0;color:#C7D2FE;font-size:17px}
.version{display:inline-block;margin-top:10px;padding:2px 10px;border-radius:999px;
background:rgba(255,255,255,.14);color:#E0E7FF;font-size:13px}
nav{background:var(--papel);border-bottom:1px solid var(--linea);position:sticky;top:0;z-index:5}
nav .ancho{display:flex;gap:6px;flex-wrap:wrap;padding-top:10px;padding-bottom:10px}
nav a{color:var(--gris);text-decoration:none;font-weight:600;font-size:14px;
padding:6px 14px;border-radius:999px}
nav a:hover{background:var(--fondo);color:var(--tinta)}
main{padding:28px 0 50px}
section{background:var(--papel);border:1px solid var(--linea);border-radius:14px;
padding:26px 28px;margin-bottom:20px;scroll-margin-top:64px}
h2{margin:0 0 4px;font-size:22px;color:var(--azul)}
.sub{margin:0 0 18px;color:var(--gris)}
.pasos{display:grid;gap:12px}
.paso{display:flex;gap:16px;align-items:flex-start;background:#F9FAFB;
border:1px solid var(--linea);border-radius:12px;padding:16px 18px}
.num{flex:none;width:40px;height:40px;border-radius:50%;background:var(--azul);color:#fff;
font-weight:700;font-size:18px;display:flex;align-items:center;justify-content:center}
.paso h3{margin:0 0 3px;font-size:17px}
.paso p{margin:0;color:var(--gris)}
kbd{display:inline-block;background:#fff;border:1px solid #D1D5DB;border-bottom-width:2px;
border-bottom-color:#9CA3AF;border-radius:6px;padding:1px 9px;font:600 14px "Segoe UI",system-ui,sans-serif;
color:var(--tinta)}
.teclas{margin-top:8px;display:flex;gap:6px;align-items:center;color:var(--gris);font-weight:600}
.aviso{background:var(--ambar-f);border:1px solid var(--ambar-b);border-radius:12px;
padding:14px 18px;color:var(--ambar);margin-top:14px}
.aviso strong{display:block;margin-bottom:4px}
.aviso ul{margin:0;padding-left:20px}
.importante{background:#EEF2FF;border:1px solid #C7D2FE;border-radius:12px;padding:14px 18px;
color:#312E81;margin-top:14px}
table{width:100%;border-collapse:collapse}
td{padding:11px 0;border-bottom:1px solid var(--linea);vertical-align:top}
tr:last-child td{border-bottom:none}
td.cat{width:210px;font-weight:700;color:var(--azul);padding-right:16px}
td.acc{width:270px;padding-right:16px}
.par{display:inline-block;white-space:nowrap;margin:2px 14px 2px 0}
.mal{background:var(--rojo-f);color:var(--rojo);text-decoration:line-through;padding:1px 7px;border-radius:5px}
.bien{background:var(--verde-f);color:var(--verde);font-weight:700;padding:1px 7px;border-radius:5px}
.flecha{color:var(--gris);margin:0 5px}
.raton{color:var(--gris);font-size:15px;margin-top:4px}
.demo{display:flex;gap:26px;align-items:center;flex-wrap:wrap;margin-top:18px;
background:#F9FAFB;border:1px dashed #D1D5DB;border-radius:12px;padding:18px 20px}
.icono{position:relative;width:72px;height:72px;flex:none}
.icono img{width:72px;height:72px;border-radius:50%;background:#fff;
box-shadow:0 2px 8px rgba(17,24,39,.25)}
.icono span{position:absolute;top:-2px;right:-2px;width:26px;height:26px;border-radius:50%;
background:var(--azul2);color:#fff;font-weight:700;border:2px solid #fff;
display:flex;align-items:center;justify-content:center;font-size:15px}
.demo p{margin:0;color:var(--gris);flex:1;min-width:220px}
.tarjeta{background:#fff;border:1px solid #D1D5DB;border-radius:10px;padding:12px 14px;
font-size:14px;min-width:270px;box-shadow:0 2px 8px rgba(17,24,39,.08)}
.tarjeta .c{color:var(--azul);font-weight:700;font-size:13px}
.tarjeta .porque{color:var(--gris);font-size:13px;margin:4px 0 8px}
.tarjeta .cambio{color:var(--verde);font-weight:700}
.tarjeta .boton{background:var(--verde-f);color:var(--verde);font-weight:700;
padding:3px 12px;border-radius:6px;margin-left:6px}
dl{margin:0}
dt{font-weight:700;margin-top:14px}
dt:first-child{margin-top:0}
dd{margin:2px 0 0;color:var(--gris)}
details{margin-top:6px}
summary{cursor:pointer;font-weight:700;color:var(--azul);font-size:18px}
code{background:var(--fondo);border-radius:5px;padding:1px 6px;font:14px Consolas,"Courier New",monospace}
footer{color:var(--gris);font-size:14px;text-align:center;padding-bottom:36px}
@media (max-width:640px){.portada{flex-direction:column;text-align:center;gap:14px}
section{padding:20px 18px}td.cat,td.acc{width:auto;display:block;border-bottom:none;padding-bottom:2px}
td{display:block}}
@media print{nav{display:none}body{background:#fff}section{break-inside:avoid;border-color:#bbb}}
"""

INSTALACION = [
    ("Extrae el archivo ZIP",
     "Clic derecho sobre <code>corrector_yajol.zip</code> y elige «Extraer todo». "
     "Guarda la carpeta en Documentos o en el Escritorio."),
    ("Abre Instalar.vbs",
     "Entra en la carpeta extraída y haz doble clic en <code>Instalar.vbs</code>. "
     "La instalación tarda entre 2 y 5 minutos y necesita internet."),
    ("Listo",
     "Aparece el icono del pájaro abajo a la derecha y se abre la ventana de ayuda. "
     "Desde ese momento el corrector se abre solo cada vez que enciendes el equipo."),
]

ARCHIVOS = [
    ("Palabras nuevas", "yajol/datos/palabras_extra.txt"),
    ("Nombres y apellidos", "yajol/datos/nombres.txt"),
    ("Mis propias palabras", "yajol/datos/mis_palabras.txt"),
    ("Reglas de letras (s/c/z, b/v…)", "yajol/nucleo/reglas_letras.py"),
    ("Palabras juntas, separadas y confundidas", "yajol/nucleo/reglas_texto.py"),
    ("Textos de esta guía y de la ayuda", "yajol/interfaz/contenido_ayuda.py"),
]


def e(texto: str) -> str:
    return html.escape(texto, quote=False)


def _teclas(teclas: list) -> str:
    return " + ".join(f"<kbd>{e(t)}</kbd>" for t in teclas)


def _logo() -> str:
    with open(config.LOGO_PATH, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode("ascii")


def genera() -> str:
    logo = _logo()
    partes = []
    a = partes.append
    a("<!DOCTYPE html>\n<html lang=\"es\">\n<head>\n<meta charset=\"utf-8\">")
    a("<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">")
    a(f"<title>{e(C.TITULO)} — Guía</title>\n<style>{ESTILO}</style>\n</head>\n<body>")
    a("<header><div class=\"ancho portada\">")
    a(f"<img src=\"{logo}\" alt=\"Logotipo de YAJOL\">")
    a(f"<div><h1>{e(C.TITULO)}</h1><p>{e(C.LEMA)}</p>"
      f"<span class=\"version\">Versión {e(__version__)} · Windows</span></div>")
    a("</div></header>")
    a("<nav><div class=\"ancho\">"
      "<a href=\"#instalar\">Instalación</a><a href=\"#usar\">Cómo se usa</a>"
      "<a href=\"#corrige\">Qué corrige</a><a href=\"#atajos\">Atajos</a>"
      "<a href=\"#falla\">Si algo falla</a><a href=\"#ampliar\">Ampliarlo</a>"
      "</div></nav>")
    a("<main class=\"ancho\">")

    # ---- Instalación ----
    a("<section id=\"instalar\"><h2>Instalación</h2>"
      "<p class=\"sub\">Se hace una sola vez.</p><div class=\"pasos\">")
    for n, (titulo, texto) in enumerate(INSTALACION, 1):
        a(f"<div class=\"paso\"><div class=\"num\">{n}</div><div><h3>{e(titulo)}</h3>"
          f"<p>{texto}</p></div></div>")
    a("</div><div class=\"importante\"><strong>Lo más importante:</strong> extrae el ZIP antes de "
      "instalar. Si abres el instalador desde dentro del archivo comprimido, Windows no permite "
      "instalar nada. El instalador también quita el arranque de la versión anterior, "
      "que era el que mostraba un error al encender el equipo.</div></section>")

    # ---- Cómo se usa ----
    a("<section id=\"usar\"><h2>Cómo se usa</h2>"
      "<p class=\"sub\">Tres pasos, en cualquier programa.</p><div class=\"pasos\">")
    for n, (titulo, texto, teclas) in enumerate(C.PASOS, 1):
        extra = f"<div class=\"teclas\">{_teclas(teclas)}</div>" if teclas else ""
        a(f"<div class=\"paso\"><div class=\"num\">{n}</div><div><h3>{e(titulo)}</h3>"
          f"<p>{e(texto)}</p>{extra}</div></div>")
    a("</div>")
    a("<div class=\"demo\"><div class=\"icono\">"
      f"<img src=\"{logo}\" alt=\"\"><span>?</span></div>"
      "<p><strong>Este es el icono.</strong> Púlsalo para revisar. El signo <strong>?</strong> "
      "de su esquina abre la ayuda siempre que necesites recordar cómo funciona.</p>"
      "<div class=\"tarjeta\"><div class=\"c\">Ortografía</div>"
      "<div>quiero <span class=\"mal\">hazer</span> la tarea</div>"
      "<div class=\"porque\"><strong>Por qué:</strong> delante de e o i, ese sonido se escribe con c.</div>"
      "<div><span class=\"cambio\">Cambiar por:</span><span class=\"boton\">hacer</span></div></div>"
      "</div>")
    a("<div class=\"aviso\"><strong>Consejos</strong><ul>")
    for consejo in C.CONSEJOS:
        a(f"<li>{e(consejo)}</li>")
    a("</ul></div></section>")

    # ---- Qué corrige ----
    a("<section id=\"corrige\"><h2>Qué corrige</h2>"
      "<p class=\"sub\">Cada corrección viene con la regla de ortografía que la explica.</p><table>")
    for categoria, pares in C.EJEMPLOS:
        celdas = "".join(
            f"<span class=\"par\"><span class=\"mal\">{e(mal)}</span>"
            f"<span class=\"flecha\">→</span><span class=\"bien\">{e(bien)}</span></span>"
            for mal, bien in pares)
        a(f"<tr><td class=\"cat\">{e(categoria)}</td><td>{celdas}</td></tr>")
    a("</table></section>")

    # ---- Atajos ----
    a("<section id=\"atajos\"><h2>Atajos</h2>"
      "<p class=\"sub\">Con el teclado o con el ratón.</p><table>")
    for accion, teclas, raton in C.ATAJOS:
        t = f"<div>{_teclas(teclas)}</div>" if teclas else ""
        a(f"<tr><td class=\"acc\">{e(accion)}</td><td>{t}<div class=\"raton\">{e(raton)}</div></td></tr>")
    a("</table></section>")

    # ---- Si algo falla ----
    a("<section id=\"falla\"><h2>Si algo falla</h2>"
      "<p class=\"sub\">Las dudas más comunes.</p><dl>")
    for pregunta, respuesta in C.PROBLEMAS:
        a(f"<dt>{e(pregunta)}</dt><dd>{e(respuesta)}</dd>")
    a("<dt>La instalación falló</dt><dd>Comprueba que extrajiste el ZIP y que hay internet, y vuelve a "
      "abrir <code>Instalar.vbs</code>. El archivo <code>instalacion.log</code> de la carpeta dice "
      "exactamente qué pasó.</dd>")
    a("<dt>Aparece un error al encender el equipo</dt><dd>Abre <code>Instalar.vbs</code> una vez: "
      "quita los arranques de versiones anteriores y repara el de esta. Al encender el equipo, "
      "esta versión nunca muestra ventanas de error; si algo falla lo anota en "
      "<code>corrector.log</code>.</dd>")
    a("</dl></section>")

    # ---- Ampliarlo ----
    a("<section id=\"ampliar\"><details><summary>Añadir palabras y reglas</summary>"
      "<p class=\"sub\" style=\"margin-top:10px\">Cada archivo lleva una palabra o una regla por línea.</p><table>")
    for que, donde in ARCHIVOS:
        a(f"<tr><td class=\"acc\">{e(que)}</td><td><code>{e(donde)}</code></td></tr>")
    a("</table><p class=\"sub\" style=\"margin:14px 0 0\">Gramática avanzada opcional (necesita Java 17): "
      "<code>.venv\\Scripts\\python -m pip install -r requirements-gramatica.txt</code></p>"
      "</details></section>")

    a("</main>")
    a(f"<footer>{e(C.TITULO)} {e(__version__)} · Para volver a ver esta guía, pulsa el signo ? del icono "
      "y luego «Guía completa».</footer>")
    a("</body>\n</html>\n")
    return "\n".join(partes)


def escribe(ruta: str = None) -> str:
    ruta = ruta or config.GUIA_PATH
    with open(ruta, "w", encoding="utf-8", newline="\n") as f:
        f.write(genera())
    return ruta


if __name__ == "__main__":
    print(escribe())
