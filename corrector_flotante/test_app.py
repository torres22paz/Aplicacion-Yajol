"""Pruebas del corrector. Ejecutar con: python -m pytest"""
import gc
import os
import sys
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pytest  # noqa: E402
from PySide6.QtCore import QEvent, QPoint, Qt  # noqa: E402
from PySide6.QtGui import QMouseEvent  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

import main  # noqa: E402
import motor  # noqa: E402
from motor import (Corrector, apply_fixes, edit_distance, explain_accent,  # noqa: E402
                   explain_spelling, rank_suggestions, snippet_parts, stress_class, toast_message)
from ventanas import FloatingIcon, SuggestionPopup, snippet_html  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def qt_session():
    app = QApplication.instance() or QApplication([])
    yield app
    for w in app.topLevelWidgets():
        w.close()
        w.deleteLater()
    app.processEvents()
    gc.collect()


@pytest.fixture(scope="module")
def corrector():
    c = Corrector()
    assert c.hunspell, "Debe cargar los diccionarios Hunspell de la carpeta dictionaries"
    return c


# ---- Texto y correcciones ----
def test_snippet_no_corta_palabras_y_marca_el_error():
    words = " ".join(f"palabra{i}" for i in range(40))
    text = f"{words} ERROR {words}"
    s = text.index("ERROR")
    p = snippet_parts(text, s, s + 5)
    assert p["wrong"] == "ERROR" and p["cut_left"] and p["cut_right"]
    assert p["before"].split()[-1].startswith("palabra") and p["after"].split()[0].startswith("palabra")


def test_snippet_html_escapa_el_texto_del_usuario():
    text = "<b>Hola</b> cancion"
    s = text.index("cancion")
    out = snippet_html(text, s, s + 7)
    assert "&lt;b&gt;" in out and "<b>" not in out and "<span" in out


def test_apply_fixes_aplica_sin_correr_posiciones_y_omite_solapados():
    new, applied = apply_fixes("dificil y cancion", [(0, 7, "difícil"), (10, 17, "canción")])
    assert new == "difícil y canción" and len(applied) == 2
    new, applied = apply_fixes("abcdef", [(0, 4, "X"), (2, 6, "Y")])
    assert new == "abY" and applied == [(2, 6, "Y")]
    assert apply_fixes("hola", [(-1, 2, "x"), (3, 1, "y")]) == ("hola", [])


def test_toast_resume_y_limita_lineas():
    msg = toast_message([(f"a{i}", f"b{i}", "Ortografía") for i in range(6)], max_lines=4)
    assert msg.count("→") == 4 and "y 2 más" in msg and toast_message([]) == ""


def test_orden_de_sugerencias_acento_primero_y_mayusculas():
    assert rank_suggestions("cancion", ["canto", "canción", "canción"])[0] == "canción"
    assert rank_suggestions("Dificil", ["difícil"]) == ["Difícil"]
    # una palabra en minúscula no se corrige a un nombre propio
    assert "Cancino" not in rank_suggestions("cancion", ["Cancino", "canción"])


def test_distancia_da_menos_costo_a_letras_que_suenan_igual():
    assert edit_distance("kome", "come") == 0.5          # k suena como c
    assert edit_distance("kome", "tome") == 1.0
    assert edit_distance("futas", "frutas") == 1.0


# ---- Explicaciones con reglas del español ----
def test_clases_de_acentuacion():
    assert stress_class("canción") == ("aguda", "ió")
    assert stress_class("difícil") == ("llana", "í")
    assert stress_class("lápiz") == ("llana", "á")
    assert stress_class("teléfono") == ("esdrújula", "é")
    assert stress_class("sí") == ("monosílaba", None)


def test_explicaciones_de_tilde_citan_la_regla():
    assert "es llana" in explain_accent("dificil", "difícil")
    assert "consonante distinta de n o s" in explain_accent("dificil", "difícil")
    assert "vocal, n o s" in explain_accent("cancion", "canción")
    assert "siempre llevan tilde" in explain_accent("silaba", "sílaba")


def test_explicaciones_ortograficas():
    assert "falta la letra «i»" in explain_spelling("dificl", "difícil")
    assert "lleva tilde" in explain_spelling("dificl", "difícil")
    assert "sobra" in explain_spelling("hholaa", "hola")
    assert "casi no se usa" in explain_spelling("kome", "come")


# ---- Corrector con diccionarios libres ----
def test_texto_correcto_no_genera_errores(corrector):
    assert corrector.analyze("Hola, ¿cómo estás hoy? Vamos a la casa.") == []
    assert corrector.analyze("   ") == []


def test_falta_de_acento_con_motivo_y_sugerencia(corrector):
    by = {i.original: i for i in corrector.analyze("La cancion es dificil")}
    assert by["cancion"].category == "Acentuación"
    assert by["cancion"].suggestions[0] == "canción"
    assert "vocal, n o s" in by["cancion"].explanation
    assert by["dificil"].suggestions[0] == "difícil" and "llana" in by["dificil"].explanation


def test_ejemplo_del_usuario_cada_error_con_motivo_y_sugerencia(corrector):
    issues = corrector.analyze("El perro kome futas te sombr")
    by = {i.original: i for i in issues}
    assert set(by) == {"kome", "futas", "sombr"}
    assert by["kome"].suggestions[0] == "come" and "casi no se usa" in by["kome"].explanation
    assert by["futas"].suggestions[0] == "frutas" and "falta la letra «r»" in by["futas"].explanation
    assert by["sombr"].suggestions[0] == "sombra" and "falta la letra «a»" in by["sombr"].explanation


def test_palabras_pegadas_se_detectan_y_se_separan(corrector):
    by = {i.original: i for i in corrector.analyze("Me gusta elperro y lacasa")}
    assert by["elperro"].category == "Palabras juntas"
    assert by["elperro"].suggestions == ["el perro"]
    assert "dos palabras" in by["elperro"].explanation
    assert by["lacasa"].suggestions == ["la casa"]
    assert corrector.analyze("comefrutas")[0].suggestions == ["come frutas"]


def test_una_falta_de_letra_no_se_confunde_con_palabras_pegadas(corrector):
    issue = next(i for i in corrector.analyze("Compre futas") if i.original == "futas")
    assert issue.category == "Ortografía"


def test_posiciones_y_orden(corrector):
    text = "xqzvw y cancion"
    issues = corrector.analyze(text)
    assert [i.start for i in issues] == sorted(i.start for i in issues)
    cancion = next(i for i in issues if i.original == "cancion")
    assert text[cancion.start:cancion.end] == "cancion"


def test_palabra_desconocida_no_inventa_sugerencia(corrector):
    issue = next(i for i in corrector.analyze("Esto es xqzvw") if i.original == "xqzvw")
    assert issue.category == "Ortografía" and "no encontré una forma parecida" in issue.explanation


def test_languagetool_aporta_gramatica_y_estilo_sin_duplicar_ortografia(corrector):
    class M:
        def __init__(self, off, n, cat, reps, msg="msg"):
            self.offset, self.errorLength, self.category = off, n, cat
            self.replacements, self.message = reps, msg

    class Tool:
        def __init__(self, matches):
            self.matches = matches

        def check(self, _):
            return self.matches

    corrector.tool = Tool([M(6, 5, "GRAMMAR", ["van"], "Concordancia."),
                           M(0, 5, "TYPOS", ["Ellos"]),           # ignorado: lo revisa Hunspell
                           M(11, 4, "STYLE", ["bien"], "Estilo.")])
    try:
        issues = corrector.analyze("Ellos vamos al cine")
    finally:
        corrector.tool = None
    assert {i.category for i in issues} == {"Gramática", "Estilo"}
    gram = next(i for i in issues if i.category == "Gramática")
    assert gram.explanation == "Concordancia." and gram.suggestions == ["van"]


def test_sin_hunspell_usa_respaldo():
    c = Corrector(hunspell=[])
    assert [i.original for i in c.analyze("Hola cancion")] == ["cancion"]


def test_grammar_falla_con_mensaje_si_no_hay_java(monkeypatch, corrector):
    import types
    fake = types.ModuleType("language_tool_python")

    def boom(*a, **k):
        raise RuntimeError("Java no encontrado")

    fake.LanguageTool = boom
    monkeypatch.setitem(sys.modules, "language_tool_python", fake)
    msg = corrector.load_grammar()
    assert "Java" in msg and corrector.tool is None


# ---- Interfaz ----
def _issues(text):
    out = []
    if "cancion" in text:
        a = text.index("cancion")
        out.append(motor.Issue("Acentuación", "cancion", ["canción"], "Falta el acento.", a, a + 7))
    if "xqzvw" in text:
        b = text.index("xqzvw")
        out.append(motor.Issue("Ortografía", "xqzvw", ["xqzv"], "No existe.", b, b + 5))
    return out


def test_popup_muestra_tarjetas_y_boton_corregir_todo(qt_session):
    p = SuggestionPopup()
    text = "La cancion es xqzvw"
    p.show_issues(text, _issues(text), QPoint(0, 0))
    assert p.title.text().startswith("Se encontraron 2")
    assert p.all_btn.text() == "Corregir todo (2)" and not p.all_btn.isHidden()
    p.close()


def test_popup_sin_errores(qt_session):
    p = SuggestionPopup()
    p.show_issues("texto bien escrito", [], QPoint(0, 0))
    assert "Sin errores" in p.title.text() and p.all_btn.isHidden()
    p.close()


def test_click_en_sugerencia_y_corregir_todo_emiten_senales(qt_session):
    p = SuggestionPopup()
    chosen, all_ = [], []
    p.fix_chosen.connect(lambda i, r: chosen.append((i.original, r)))
    p.fix_all_requested.connect(lambda lst: all_.append(len(lst)))
    text = "La cancion es xqzvw"
    p.show_issues(text, _issues(text), QPoint(0, 0))
    next(b for b in p.findChildren(type(p.all_btn)) if b.text() == "canción").click()
    assert chosen == [("cancion", "canción")]
    p.show_issues(text, _issues(text), QPoint(0, 0))
    p.all_btn.click()
    assert all_ == [2]
    p.close()


def test_icono_click_izquierdo_emite_clicked(qt_session):
    icon = FloatingIcon()
    icon.show()
    hits = []
    icon.clicked.connect(lambda: hits.append(1))
    c = QPoint(icon.width() // 2, icon.height() // 2)
    icon.mousePressEvent(QMouseEvent(QEvent.MouseButtonPress, c, c, Qt.LeftButton, Qt.LeftButton, Qt.NoModifier))
    icon.mouseReleaseEvent(QMouseEvent(QEvent.MouseButtonRelease, c, c, Qt.LeftButton, Qt.NoButton, Qt.NoModifier))
    assert hits == [1]
    icon.close()


# ---- Aplicación completa (teclado simulado) ----
def test_app_arranca_corrige_y_oculta_el_icono(qt_session, monkeypatch):
    replaced = {}
    monkeypatch.setattr(main, "read_context", lambda n: "La cancion es dificil")
    monkeypatch.setattr(main, "replace_selection", lambda t: replaced.setdefault("text", t))

    app = main.CorrectorApp(qt_session)
    assert app.icon.isVisible()
    deadline = time.time() + 60
    while app.corrector is None and time.time() < deadline:
        qt_session.processEvents()
        time.sleep(0.05)
    assert app.corrector is not None, "El corrector debe cargar en segundo plano"

    issues = app.corrector.analyze("La cancion es dificil")
    app.show_result("La cancion es dificil", issues)
    assert app.popup.isVisible()

    app.fix_all(issues)
    assert replaced["text"] == "La canción es difícil"

    app.toggle_icon()
    assert not app.icon.isVisible()
    app.toggle_icon()
    assert app.icon.isVisible()
    app._close()
    app.icon.close()
    app.popup.close()
