' ============================================================
'  Corrector YAJOL - Instalacion
'  Crea el entorno de Python, instala lo necesario y deja
'  el corrector listo para abrirse solo al encender el equipo.
' ============================================================
Option Explicit

Dim sh, fso, carpeta, q, registro, rc, py, pyw, venv, marca

Set sh  = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
q = Chr(34)
carpeta  = fso.GetParentFolderName(WScript.ScriptFullName)
venv     = carpeta & "\.venv"
py       = venv & "\Scripts\python.exe"
pyw      = venv & "\Scripts\pythonw.exe"
marca    = venv & "\instalado.txt"
registro = carpeta & "\instalacion.log"
sh.CurrentDirectory = carpeta

' ---------- Funciones ----------
Sub Aviso(texto, tipo)
    sh.Popup texto, 0, "Corrector YAJOL", tipo
End Sub

Sub Fallo(texto)
    Dim detalle
    detalle = UltimasLineas(registro, 12)
    Aviso texto & vbCrLf & vbCrLf & _
          "Ultimas lineas del registro:" & vbCrLf & detalle & vbCrLf & vbCrLf & _
          "Registro completo: " & registro, 16
    WScript.Quit 1
End Sub

Function UltimasLineas(ruta, cuantas)
    Dim f, todas, i, salida
    UltimasLineas = "(sin registro)"
    If Not fso.FileExists(ruta) Then Exit Function
    On Error Resume Next
    Set f = fso.OpenTextFile(ruta, 1)
    If Err.Number <> 0 Then Exit Function
    todas = Split(f.ReadAll, vbCrLf)
    f.Close
    On Error GoTo 0
    If Not IsArray(todas) Then Exit Function
    salida = ""
    For i = UBound(todas) To 0 Step -1
        If Trim(todas(i)) <> "" Then
            salida = todas(i) & vbCrLf & salida
            cuantas = cuantas - 1
            If cuantas <= 0 Then Exit For
        End If
    Next
    If salida <> "" Then UltimasLineas = salida
End Function

Sub Apunta(texto)
    Dim f
    On Error Resume Next
    Set f = fso.OpenTextFile(registro, 8, True)
    f.WriteLine texto
    f.Close
    On Error GoTo 0
End Sub

Function Ejecuta(orden)
    Ejecuta = sh.Run("cmd /c " & q & orden & " >> " & q & registro & q & " 2>&1" & q, 0, True)
End Function

Function HayPython(orden)
    HayPython = (sh.Run("cmd /c " & orden & " -c " & q & "import sys" & q & _
                        " >nul 2>&1", 0, True) = 0)
End Function

' ---------- 1. Comprobaciones previas ----------
If InStr(LCase(carpeta), ".zip\") > 0 Or Right(LCase(carpeta), 4) = ".zip" Then
    Aviso "Estas abriendo el corrector desde dentro del archivo comprimido." & vbCrLf & vbCrLf & _
          "Haz esto primero:" & vbCrLf & _
          "  1. Cierra esta ventana." & vbCrLf & _
          "  2. Clic derecho sobre " & q & "corrector_yajol.zip" & q & " y elige " & q & "Extraer todo" & q & "." & vbCrLf & _
          "  3. Guarda la carpeta en Documentos o en el Escritorio." & vbCrLf & _
          "  4. Entra en la carpeta extraida y vuelve a abrir Instalar.vbs." & vbCrLf & vbCrLf & _
          "Dentro del ZIP, Windows no deja crear archivos y la instalacion falla.", 48
    WScript.Quit 1
End If

If InStr(LCase(carpeta), "\appdata\local\temp") > 0 Then
    Aviso "La carpeta del corrector esta en los archivos temporales de Windows:" & vbCrLf & vbCrLf & _
          carpeta & vbCrLf & vbCrLf & _
          "Windows borra esa carpeta sola. Muevela a Documentos o al Escritorio " & _
          "y vuelve a abrir Instalar.vbs desde ahi.", 48
    WScript.Quit 1
End If

' La carpeta tiene que dejar escribir
Dim prueba
On Error Resume Next
Err.Clear
Set prueba = fso.CreateTextFile(carpeta & "\prueba_escritura.tmp", True)
If Err.Number <> 0 Then
    Aviso "No tengo permiso para escribir en esta carpeta:" & vbCrLf & vbCrLf & carpeta & vbCrLf & vbCrLf & _
          "Mueve la carpeta a Documentos o al Escritorio y vuelve a intentarlo.", 16
    WScript.Quit 1
End If
prueba.Close
fso.DeleteFile carpeta & "\prueba_escritura.tmp", True
On Error GoTo 0

If Not fso.FileExists(carpeta & "\requirements.txt") Then
    Aviso "Falta el archivo requirements.txt." & vbCrLf & _
          "La carpeta esta incompleta: vuelve a extraer el ZIP entero.", 16
    WScript.Quit 1
End If

' ---------- 2. Ya instalado ----------
If fso.FileExists(marca) And fso.FileExists(pyw) Then
    Aviso "El corrector ya estaba instalado. Lo voy a abrir.", 64
    sh.Run q & carpeta & "\Yajol.vbs" & q, 0, False
    WScript.Quit 0
End If

' ---------- 3. Buscar Python ----------
If fso.FileExists(registro) Then fso.DeleteFile registro, True
Apunta "=== Instalacion del Corrector YAJOL ==="
Apunta "Carpeta: " & carpeta

Dim ordenPython
ordenPython = ""
If HayPython("py -3") Then
    ordenPython = "py -3"
ElseIf HayPython("python") Then
    ordenPython = "python"
ElseIf HayPython("python3") Then
    ordenPython = "python3"
End If

If ordenPython = "" Then
    Aviso "No encontre Python en este equipo." & vbCrLf & vbCrLf & _
          "Instalalo asi:" & vbCrLf & _
          "  1. Entra a python.org/downloads" & vbCrLf & _
          "  2. Descarga la version para Windows." & vbCrLf & _
          "  3. En la primera pantalla del instalador MARCA la casilla" & vbCrLf & _
          "     " & q & "Add python.exe to PATH" & q & "." & vbCrLf & _
          "  4. Termina la instalacion y vuelve a abrir Instalar.vbs.", 48
    WScript.Quit 1
End If
Apunta "Python encontrado con: " & ordenPython

' ---------- 4. Crear el entorno ----------
Aviso "Voy a instalar los componentes." & vbCrLf & _
      "Tarda entre 2 y 5 minutos segun tu internet." & vbCrLf & vbCrLf & _
      "Cuando termine veras otro aviso y aparecera el icono" & vbCrLf & _
      "en la esquina inferior derecha de la pantalla.", 64

If fso.FolderExists(venv) Then fso.DeleteFolder venv, True
Apunta "--- Creando el entorno virtual ---"
rc = Ejecuta(ordenPython & " -m venv " & q & venv & q)
If Not fso.FileExists(py) Then
    Fallo "No se pudo crear el entorno de Python." & vbCrLf & _
          "Suele pasar cuando Python se instalo desde la Microsoft Store." & vbCrLf & _
          "Instalalo desde python.org y marca " & q & "Add python.exe to PATH" & q & "."
End If

' ---------- 5. Instalar las bibliotecas ----------
Apunta "--- Actualizando pip ---"
rc = Ejecuta(q & py & q & " -m pip install --upgrade pip --disable-pip-version-check")

Apunta "--- Instalando los componentes ---"
rc = Ejecuta(q & py & q & " -m pip install --disable-pip-version-check " & _
             "--no-warn-script-location -r " & q & carpeta & "\requirements.txt" & q)
If rc <> 0 Then
    Apunta "--- Segundo intento sin cache ---"
    rc = Ejecuta(q & py & q & " -m pip install --no-cache-dir --disable-pip-version-check " & _
                 "-r " & q & carpeta & "\requirements.txt" & q)
End If
If rc <> 0 Then
    Fallo "Fallo la instalacion de componentes." & vbCrLf & _
          "Suele ser por falta de internet o por el antivirus."
End If

' ---------- 6. Comprobar que todo carga ----------
Apunta "--- Comprobando la instalacion ---"
rc = Ejecuta(q & py & q & " -c " & q & "import PySide6, spylls, pynput, pyperclip" & q)
If rc <> 0 Then
    Fallo "Los componentes se instalaron pero no cargan bien."
End If

Dim sello
Set sello = fso.CreateTextFile(marca, True)
sello.WriteLine "Instalado el " & Now
sello.Close
Apunta "Instalacion terminada correctamente."

' ---------- 7. Arranque automatico ----------
rc = Ejecuta(q & py & q & " " & q & carpeta & "\activar_inicio.py" & q)
If rc <> 0 Then Apunta "Aviso: no se pudo activar el arranque automatico."

Aviso "Listo. El corrector ya esta instalado." & vbCrLf & vbCrLf & _
      "- Se abrira solo cada vez que enciendas el equipo." & vbCrLf & _
      "- Veras el icono en la esquina inferior derecha." & vbCrLf & _
      "- Haz clic en el icono (o pulsa Ctrl+Alt+C) para revisar lo que escribiste." & vbCrLf & _
      "- Con clic derecho en el icono puedes ocultarlo o salir.", 64

sh.Run q & carpeta & "\Yajol.vbs" & q, 0, False
