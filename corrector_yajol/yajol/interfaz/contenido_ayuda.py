"""Textos de la ayuda. Los usan la ventana «?» del corrector y la guía en HTML.

Están aquí, separados de las ventanas, para poder cambiarlos sin tocar código.
"""
from .. import config


def teclas(atajo: str) -> list:
    """Convierte "<ctrl>+<alt>+c" en ["Ctrl", "Alt", "C"]."""
    return [parte.strip("<>").capitalize() for parte in atajo.split("+")]


TECLAS_REVISAR = teclas(config.ATAJO_REVISAR)
TECLAS_MOSTRAR = teclas(config.ATAJO_MOSTRAR)

TITULO = "Corrector YAJOL"
LEMA = "Revisa lo que escribes en cualquier programa"

# (título, explicación, teclas opcionales)
PASOS = [
    ("Escribe como siempre",
     "En Word, en el navegador, en WhatsApp Web, en el correo o en cualquier otro programa. "
     "El corrector no estorba: se queda en una esquina.",
     None),
    ("Pulsa el icono del pájaro",
     "El corrector lee las últimas palabras que escribiste. "
     "Si prefieres el teclado, usa el atajo.",
     TECLAS_REVISAR),
    ("Elige la corrección",
     "Aparece una tarjeta por cada error, con la explicación de la regla. "
     "Pulsa la palabra en verde para cambiarla, o «Corregir todo».",
     None),
]

CONSEJOS = [
    "Deja el cursor justo después de lo que escribiste antes de pulsar el icono.",
    "Para revisar solo una parte, selecciónala con el ratón y luego pulsa el icono.",
    "Si marca una palabra que sí es correcta, pulsa «Aprender palabra» y no la vuelve a marcar.",
]

# (categoría, [(mal, bien), ...])
EJEMPLOS = [
    ("Letras s, c y z", [("hazer", "hacer"), ("desision", "decisión"), ("felizes", "felices")]),
    ("Letras b y v", [("escrivir", "escribir"), ("cantava", "cantaba")]),
    ("Letras g, j y h", [("dirijir", "dirigir"), ("ablar", "hablar"), ("aora", "ahora")]),
    ("Tildes", [("ortografia", "ortografía"), ("exito", "éxito")]),
    ("Palabras juntas", [("aveces", "a veces"), ("nose", "no sé"), ("miscompañeros", "mis compañeros")]),
    ("Palabras confundidas", [("haber si vienes", "a ver si vienes"), ("ha echo", "ha hecho")]),
    ("Nombres completos", [("jose hernandez", "José Hernández")]),
    ("Gramática", [("pienso de que", "pienso que"), ("la problema", "el problema")]),
    ("Puntuación", [("Quieres venir?", "¿Quieres venir?")]),
]

# (acción, teclas o None, cómo hacerlo con el ratón)
ATAJOS = [
    ("Revisar lo que escribiste", TECLAS_REVISAR, "Clic en el icono"),
    ("Ocultar o mostrar el icono", TECLAS_MOSTRAR, "Clic derecho → Ocultar icono"),
    ("Mover el icono", None, "Arrástralo con el ratón"),
    ("Ver esta ayuda", None, "Clic en el signo ? del icono"),
    ("Abrir el menú", None, "Clic derecho sobre el icono"),
    ("Cerrar el corrector", None, "Clic derecho → Salir"),
]

# (pregunta, respuesta)
PROBLEMAS = [
    ("No lee lo que escribí",
     "Haz clic dentro del cuadro de texto para dejar ahí el cursor y vuelve a pulsar el icono."),
    ("Marca una palabra que está bien",
     "Pulsa «Aprender palabra» en la tarjeta. Sirve para nombres, siglas y palabras técnicas."),
    ("No veo el icono",
     f"Pulsa {' + '.join(TECLAS_MOSTRAR)} para mostrarlo, o búscalo junto al reloj de Windows."),
    ("No quiero que se abra al encender el equipo",
     "Clic derecho en el icono y desmarca «Iniciar con Windows»."),
    ("Quiero quitarlo del equipo",
     "Abre el archivo Desinstalar.vbs que está en la carpeta del corrector."),
]

PIE = "El corrector se abre solo cada vez que enciendes el equipo."
