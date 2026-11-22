"""Ajustes generales del Corrector YAJOL.

Un solo lugar para cambiar rutas, tamaños y límites.
"""
import os

# ---- Rutas ----
PAQUETE_DIR = os.path.dirname(os.path.abspath(__file__))
RAIZ_DIR = os.path.dirname(PAQUETE_DIR)
DATOS_DIR = os.path.join(PAQUETE_DIR, "datos")
RECURSOS_DIR = os.path.join(PAQUETE_DIR, "recursos")
LOGO_PATH = os.path.join(RECURSOS_DIR, "logo_yajol.png")
LOG_PATH = os.path.join(RAIZ_DIR, "corrector.log")

# Archivos de datos
DICCIONARIO_ZIP = os.path.join(DATOS_DIR, "es_MX.zip")
FRECUENCIAS_GZ = os.path.join(DATOS_DIR, "frecuencia.txt.gz")
PALABRAS_EXTRA = os.path.join(DATOS_DIR, "palabras_extra.txt")
NOMBRES_PROPIOS = os.path.join(DATOS_DIR, "nombres.txt")
CONFUSIONES = os.path.join(DATOS_DIR, "confusiones.txt")
USUARIO_TXT = os.path.join(DATOS_DIR, "mis_palabras.txt")

# ---- Revisión ----
PALABRAS_CONTEXTO = 18        # palabras antes del cursor que se revisan
MAX_SUGERENCIAS = 4
MAX_PARTES_PEGADAS = 3        # máximo de palabras que se separan de una palabra pegada
MAX_TARJETAS = 8              # tarjetas visibles en el recuadro de revisión

# ---- Interfaz ----
TAM_ICONO = 64
MARGEN_ICONO = (24, 24)       # margen desde la esquina inferior derecha
AVISO_MS = 4500

# ---- Teclado ----
RETARDO_TECLA = 0.02
RETARDO_COPIA = 0.14
RETARDO_PEGADO = 0.20
INTENTOS_COPIA = 3
ATAJO_MOSTRAR = "<ctrl>+<alt>+i"
ATAJO_REVISAR = "<ctrl>+<alt>+c"

# ---- Gramática opcional (LanguageTool, necesita Java) ----
USAR_LANGUAGETOOL = True      # se usa solo si el paquete y Java están instalados
IDIOMA_LANGUAGETOOL = "es"

# ---- Nombres de categoría ----
CAT_ORTOGRAFIA = "Ortografía"
CAT_ACENTO = "Acentuación"
CAT_PEGADAS = "Palabras juntas"
CAT_SEPARADAS = "Palabras separadas"
CAT_CONFUSION = "Palabra confundida"
CAT_NOMBRE = "Nombre propio"
CAT_MAYUSCULA = "Mayúsculas"
CAT_GRAMATICA = "Gramática"
CAT_PUNTUACION = "Puntuación"
CAT_ESTILO = "Estilo"
