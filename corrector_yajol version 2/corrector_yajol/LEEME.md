# Corrector YAJOL 2.0

Corrector ortográfico flotante para Windows. Revisa lo que escribes en
**cualquier programa**: Word, el navegador, WhatsApp Web, el correo, el bloc
de notas o el editor de código.

---

## Instalación (una sola vez)

1. **Extrae el ZIP.** Clic derecho sobre `corrector_yajol.zip` → *Extraer todo*.
   Guarda la carpeta en **Documentos** o en el **Escritorio**.

   > Esto es lo más importante. Si abres el instalador sin extraer el ZIP,
   > Windows no deja crear archivos y la instalación falla. Esa era la causa
   > del error que te aparecía.

2. Entra en la carpeta extraída y haz doble clic en **`Instalar.vbs`**.

3. Espera entre 2 y 5 minutos. Cuando termine verás un aviso y aparecerá el
   icono en la esquina inferior derecha de la pantalla.

Si no tienes Python, el instalador te lo dirá con las instrucciones exactas.
Descárgalo de [python.org](https://www.python.org/downloads/) y marca la
casilla **«Add python.exe to PATH»** en la primera pantalla.

---

## Cómo se usa

| Acción | Cómo |
|---|---|
| Revisar lo que acabas de escribir | Clic en el icono, o **Ctrl + Alt + C** |
| Revisar solo un trozo | Selecciónalo y pulsa el icono |
| Ocultar o mostrar el icono | **Ctrl + Alt + I** |
| Mover el icono | Arrástralo con el ratón |
| Opciones | Clic derecho sobre el icono |
| Salir | Clic derecho → *Salir* |

El corrector arranca solo cada vez que enciendes el equipo. Para quitarlo,
clic derecho en el icono de la bandeja → desmarca **«Iniciar con Windows»**,
o abre `Desinstalar.vbs`.

---

## Qué corrige

**Ortografía por reglas del español** — además de decirte la palabra correcta,
te explica la regla:

- **s / c / z** — *hazer → hacer*, *desision → decisión*, *felizes → felices*, *rason → razón*
- **b / v** — *escrivir → escribir*, *cantava → cantaba*, *obserbar → observar*
- **m antes de p y b** — *canbio → cambio*, *inposible → imposible*, *tanvien → también*
- **g / j** — *dirijir → dirigir*, *mensage → mensaje*, *relog → reloj*
- **h** — *ablar → hablar*, *ielo → hielo*, *aora → ahora*, *proivir → prohibir*
- **ll / y** — *cuchiyo → cuchillo*, *desarroyo → desarrollo*
- **x / cs** — *ecselente → excelente*, *exepcion → excepción*
- **Tildes** — *ortografia → ortografía*, *matematicas → matemáticas*, *exito → éxito*
- **Varios errores a la vez** — *corecion → corrección*, *tanvien → también*

**Palabras juntas y separadas**

- Juntas que van separadas: *osea → o sea*, *aveces → a veces*, *nose → no sé*,
  *ala → a la*, *talvez → tal vez*, *enserio → en serio*, *porfavor → por favor*
- Pegadas sin querer: *miscompañeros → mis compañeros*, *megustan → me gustan*
- Separadas que van juntas: *a demás → además*, *con migo → conmigo*, *tam bien → también*

**Nombres propios y nombres completos**

- *omar torres de la paz* → **Omar Torres de la Paz**
- *jose hernandez garcia* → **José Hernández García**
- *maria del carmen lopez* → **María del Carmen López**
- Respeta las partículas: *de*, *del*, *la*, *y* van en minúscula.
- No confunde apellidos con palabras comunes: *«la paz interior»* se queda igual.

**Palabras que suenan igual**

- *haber / a ver*, *hecho / echo*, *hay / ahí / ay*, *tuvo / tubo*, *vaya / valla*
- *has / haz*, *ves / vez*, *sino / si no*, *porque / por qué / porqué*
- *mas / más*, *tu / tú*, *el / él*, *mi / mí*, *se / sé*, *de / dé*, *te / té*, *aun / aún*

**Gramática y puntuación**

- Dequeísmo: *pienso de que → pienso que*. Queísmo: *me di cuenta que → cuenta de que*
- Concordancia: *la problema → el problema*, *la agua → el agua*
- Palabras repetidas: *el el perro → el perro*
- Signos de apertura: *Quieres venir?* → *¿Quieres venir?*
- Tildes en preguntas: *¿como estas?* → *¿cómo estas?*
- Espacios dobles, espacio después de coma y punto
- Meses y días en minúscula (*Enero → enero*)
- Mayúscula después de punto

---

## Palabras que no conoce

Si marca un nombre, una sigla o una palabra técnica que sí es correcta, pulsa
**«Aprender palabra»** en la tarjeta. Se guarda en
`yajol/datos/mis_palabras.txt` y no vuelve a marcarla.

También puedes editar ese archivo a mano: una palabra por línea.

---

## Añadir más palabras y más reglas

| Quiero añadir… | Archivo |
|---|---|
| Palabras nuevas | `yajol/datos/palabras_extra.txt` |
| Nombres y apellidos | `yajol/datos/nombres.txt` |
| Mis propias palabras | `yajol/datos/mis_palabras.txt` |
| Reglas de letras (s/c/z, b/v…) | `yajol/nucleo/reglas_letras.py`, lista `CAMBIOS` |
| Palabras juntas/separadas | `yajol/nucleo/reglas_texto.py`, listas `SEPARAR` y `UNIR` |
| Palabras que se confunden | `yajol/nucleo/reglas_texto.py`, lista `CONFUSIONES` |

Cada lista es una línea por regla, con su explicación en español. No hace
falta tocar nada más.

---

## Gramática avanzada (opcional)

El corrector trae sus propias reglas y **no necesita Java**. Si además quieres
la gramática completa de LanguageTool:

```
.venv\Scripts\python -m pip install -r requirements-gramatica.txt
```

Requiere Java 17 o superior y descarga unos 250 MB la primera vez. Si Java no
está instalado, el corrector avisa y sigue funcionando con sus reglas.

---

## Organización de las carpetas

```
corrector_yajol/
├── Instalar.vbs              Instala todo y activa el arranque automático
├── Yajol.vbs                 Abre el corrector sin ventana de consola
├── Desinstalar.vbs           Quita el arranque automático y los componentes
├── activar_inicio.py         Enciende o apaga el arranque con Windows
├── requirements.txt          Componentes necesarios
├── requirements-gramatica.txt  Componentes opcionales (LanguageTool)
│
├── yajol/
│   ├── __main__.py           Punto de entrada (python -m yajol)
│   ├── app.py                Une todo: icono, corrector y teclado
│   ├── config.py             Ajustes en un solo lugar
│   │
│   ├── nucleo/               Motor de corrección
│   │   ├── corrector.py      Junta el diccionario con las reglas
│   │   ├── lexico.py         Diccionario, listas propias y frecuencias
│   │   ├── reglas_letras.py  s/c/z, b/v, g/j, h, ll/y, tildes
│   │   ├── reglas_texto.py   Reglas que necesitan ver la frase
│   │   ├── nombres.py        Nombres completos
│   │   ├── texto.py          Sílabas, distancias y parches
│   │   └── hallazgo.py       Estructura de un error encontrado
│   │
│   ├── interfaz/             Ventanas
│   │   ├── icono.py          Icono flotante
│   │   ├── popup.py          Tarjetas con las sugerencias
│   │   ├── aviso.py          Aviso breve tras corregir
│   │   └── estilos.py        Colores
│   │
│   ├── sistema/              Integración con Windows
│   │   ├── teclado.py        Lee y escribe en el programa de enfrente
│   │   └── inicio.py         Arranque automático
│   │
│   ├── datos/                Diccionarios y listas
│   └── recursos/             Logotipo
│
└── tests/                    Pruebas unitarias (351 pruebas)
```

---

## Pruebas

```
.venv\Scripts\python -m pytest
```

Cubren el texto, el diccionario, las reglas de letras, las reglas de contexto,
los nombres, el corrector completo, las ventanas, el teclado y el arranque de
Windows. Incluyen una batería de textos bien escritos para comprobar que el
corrector **no marca errores donde no los hay**.

---

## Si algo falla

| Síntoma | Qué hacer |
|---|---|
| «Falló la instalación de componentes» | Extrae el ZIP a Documentos y vuelve a abrir `Instalar.vbs`. Revisa `instalacion.log`. |
| No encuentra Python | Instálalo desde python.org marcando *Add python.exe to PATH*. |
| No aparece el icono | Abre `Yajol.vbs`. Si no sale nada, mira `corrector.log`. |
| No lee lo que escribí | Deja el cursor en el cuadro de texto antes de pulsar el icono. |
| Marca palabras correctas | Pulsa *Aprender palabra*. |

Los dos registros, `instalacion.log` y `corrector.log`, están en la misma
carpeta del corrector y dicen exactamente qué pasó.

---

## Qué cambió respecto de la versión anterior

- **Se arregló el error de instalación**: ahora detecta que estás abriendo el
  programa desde dentro del ZIP o desde la carpeta temporal y te dice qué hacer.
- **Se arregló el texto ilegible** («FallÃ³ la instalaciÃ³n»): los archivos de
  Windows se guardan en el formato que Windows espera.
- **Arranca solo con Windows**, con un interruptor en el menú del icono.
- **Ya no necesita Java.** LanguageTool pasó a ser opcional.
- **Pesa la tercera parte**: 0.9 MB en vez de 2.5 MB, y la instalación bajó de
  unos 300 MB a unos 90 MB.
- **Motor de reglas nuevo** con s/c/z, b/v, g/j, h, ll/y y explicaciones.
- **Nombres completos**, palabras confundidas, puntuación y mayúsculas.
- **Carpetas reorganizadas** en módulos pequeños con una sola responsabilidad.
- **351 pruebas unitarias** donde antes había una sola batería.
