' ============================================================
'  Corrector YAJOL - Instalacion
'  1. Quita los arranques de versiones anteriores.
'  2. Crea el entorno de Python e instala los componentes.
'  3. Deja el corrector listo para abrirse solo al encender el equipo.
' ============================================================
Option Explicit

Dim sh, fso, carpeta, q, registro, rc, py, pyw, venv, marca
Dim quitados, notaLimpieza, prueba, ordenPython, sello

Set sh  = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
q = Chr(34)
carpeta  = fso.GetParentFolderName(WScript.ScriptFullName)
venv     = carpeta & "\.venv"
py       = venv & "\Scripts\python.exe"
pyw      = venv & "\Scripts\pythonw.exe"
marca    = venv & "\instalado.txt"
registro = carpeta & "\instalacion.log"

' ---------- Funciones comunes ----------
Sub Aviso(texto, tipo)
    sh.Popup texto, 0, "Corrector YAJOL", tipo
End Sub

Function Pregunta(texto)
    ' Devuelve True si la persona responde que si.
    Pregunta = (sh.Popup(texto, 0, "Corrector YAJOL", 36) = 6)
End Function

Function EsNuestro(texto)
    Dim t
    t = LCase(texto)
    EsNuestro = (InStr(t, "yajol") > 0 Or InStr(t, "corrector_flotante") > 0 _
                 Or InStr(t, "corrector flotante") > 0)
End Function

Function EsVigente(nombre, destino, carpetaTrabajo)
    ' El acceso directo bueno: el de esta version, que apunta a una carpeta que existe.
    Dim n, d
    n = LCase(nombre)
    d = LCase(destino)
    EsVigente = False
    If n <> "corrector yajol.lnk" And n <> "corrector yajol.vbs" Then Exit Function
    If InStr(d, "--inicio") = 0 Then Exit Function
    If InStr(d, "corrector_flotante") > 0 Then Exit Function
    If InStr(d, ".zip\") > 0 Or InStr(d, "\appdata\local\temp") > 0 Then Exit Function
    If n = "corrector yajol.lnk" Then
        If carpetaTrabajo = "" Then Exit Function
        If Not fso.FolderExists(carpetaTrabajo & "\yajol") Then Exit Function
    End If
    EsVigente = True
End Function

Function CarpetaInicio()
    ' Carpeta Inicio del usuario (shell:startup).
    Dim c
    c = ""
    On Error Resume Next
    c = sh.SpecialFolders("Startup")
    On Error GoTo 0
    If c = "" Then
        c = sh.Environment("PROCESS")("APPDATA") & "\Microsoft\Windows\Start Menu\Programs\Startup"
    End If
    CarpetaInicio = c
End Function

Function LimpiaCarpetaInicio()
    ' Quita de la carpeta Inicio los accesos de versiones anteriores. Devuelve cuantos quito.
    Dim rutaInicio, archivo, ext, destino, trabajo, acceso, f, lista, ruta, cuenta
    cuenta = 0
    lista = ""
    rutaInicio = CarpetaInicio()
    On Error Resume Next
    If rutaInicio <> "" And fso.FolderExists(rutaInicio) Then
        For Each archivo In fso.GetFolder(rutaInicio).Files
            ext = LCase(fso.GetExtensionName(archivo.Name))
            destino = ""
            trabajo = ""
            If ext = "lnk" Then
                ' cada dato se lee por separado: si uno falla, los demas se conservan
                Set acceso = sh.CreateShortcut(archivo.Path)
                destino = destino & acceso.TargetPath & " "
                destino = destino & acceso.Arguments & " "
                trabajo = acceso.WorkingDirectory
                destino = destino & trabajo & " "
                ' y ademas se busca dentro del propio archivo, por si lo anterior no dio nada
                Set f = fso.OpenTextFile(archivo.Path, 1)
                destino = destino & Replace(f.ReadAll, Chr(0), "")
                f.Close
            ElseIf ext = "vbs" Or ext = "bat" Or ext = "cmd" Then
                Set f = fso.OpenTextFile(archivo.Path, 1)
                destino = f.ReadAll
                f.Close
            End If
            If ext = "lnk" Or ext = "vbs" Or ext = "bat" Or ext = "cmd" Then
                If EsNuestro(archivo.Name & " " & destino) Then
                    If Not EsVigente(archivo.Name, destino, trabajo) Then
                        lista = lista & archivo.Path & "|"
                    End If
                End If
            End If
            Err.Clear
        Next
        For Each ruta In Split(lista, "|")
            If ruta <> "" Then
                Err.Clear
                fso.DeleteFile ruta, True
                If Err.Number = 0 Then cuenta = cuenta + 1
            End If
        Next
    End If
    On Error GoTo 0
    LimpiaCarpetaInicio = cuenta
End Function

Function LimpiaRegistro()
    ' Quita del Registro (Run) los arranques de versiones anteriores. Devuelve cuantos quito.
    Dim clave, temporal, f, linea, corte, nombre, dato, cuenta
    cuenta = 0
    On Error Resume Next
    temporal = fso.GetSpecialFolder(2) & "\yajol_run.txt"
    For Each clave In Array("HKCU\Software\Microsoft\Windows\CurrentVersion\Run", _
                            "HKCU\Software\Microsoft\Windows\CurrentVersion\RunOnce")
        If fso.FileExists(temporal) Then fso.DeleteFile temporal, True
        sh.Run "cmd /c reg query " & q & clave & q & " > " & q & temporal & q & " 2>nul", 0, True
        If fso.FileExists(temporal) Then
            Set f = fso.OpenTextFile(temporal, 1)
            Do While Not f.AtEndOfStream
                linea = f.ReadLine
                corte = InStr(linea, "    REG_")
                If Left(linea, 4) = "    " And corte > 0 Then
                    nombre = Trim(Left(linea, corte - 1))
                    dato = Mid(linea, corte)
                    If nombre <> "" And EsNuestro(nombre & " " & dato) Then
                        If sh.Run("cmd /c reg delete " & q & clave & q & " /v " & q & nombre & q & _
                                  " /f >nul 2>&1", 0, True) = 0 Then cuenta = cuenta + 1
                    End If
                End If
            Loop
            f.Close
            fso.DeleteFile temporal, True
        End If
        Err.Clear
    Next
    On Error GoTo 0
    LimpiaRegistro = cuenta
End Function

Sub CierraCorrectorAbierto()
    ' Cierra solo el corrector (esta version o la anterior), no otros programas de Python.
    Dim wmi, proceso, orden
    On Error Resume Next
    Set wmi = GetObject("winmgmts:\\.\root\cimv2")
    For Each proceso In wmi.ExecQuery("SELECT * FROM Win32_Process WHERE Name = 'pythonw.exe'")
        orden = ""
        orden = LCase(proceso.CommandLine & "")
        If InStr(orden, "-m yajol") > 0 Or InStr(orden, "corrector_flotante") > 0 Then
            proceso.Terminate
        End If
        Err.Clear
    Next
    On Error GoTo 0
End Sub

Sub Fallo(texto)
    Dim detalle
    detalle = UltimasLineas(registro, 10)
    Aviso texto & vbCrLf & vbCrLf & _
          ChrW(218) & "ltimas l" & ChrW(237) & "neas del registro:" & vbCrLf & detalle & vbCrLf & _
          "Registro completo: " & registro, 16
    WScript.Quit 1
End Sub

Function UltimasLineas(ruta, cuantas)
    Dim f, todas, i, salida
    UltimasLineas = "(sin registro)" & vbCrLf
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
            salida = Left(todas(i), 110) & vbCrLf & salida
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

' ---------- 1. Quitar los arranques antiguos ----------
' Se hace siempre y antes que nada: el arranque de la version anterior es
' el que mostraba un error cada vez que se encendia el equipo.
quitados = LimpiaCarpetaInicio() + LimpiaRegistro()
notaLimpieza = ""
If quitados > 0 Then
    notaLimpieza = vbCrLf & vbCrLf & _
        "Adem" & ChrW(225) & "s quit" & ChrW(233) & " el arranque de la versi" & ChrW(243) & "n anterior: era el que mostraba " & _
        "el error cada vez que encend" & ChrW(237) & "as el equipo."
End If

' ---------- 2. Comprobaciones previas ----------
If InStr(LCase(carpeta), ".zip\") > 0 Or Right(LCase(carpeta), 4) = ".zip" _
   Or InStr(LCase(carpeta), "\appdata\local\temp") > 0 Then
    Aviso "Est" & ChrW(225) & "s abriendo el instalador desde dentro del archivo comprimido." & vbCrLf & vbCrLf & _
          "Haz esto:" & vbCrLf & vbCrLf & _
          "   1.  Cierra esta ventana." & vbCrLf & _
          "   2.  Clic derecho sobre corrector_yajol.zip  " & ChrW(8594) & "  Extraer todo." & vbCrLf & _
          "   3.  Guarda la carpeta en Documentos o en el Escritorio." & vbCrLf & _
          "   4.  Entra en esa carpeta y abre Instalar.vbs." & vbCrLf & vbCrLf & _
          "Dentro del ZIP, Windows no permite instalar nada." & notaLimpieza, 48
    WScript.Quit 1
End If

sh.CurrentDirectory = carpeta

' La carpeta tiene que dejar escribir
On Error Resume Next
Err.Clear
Set prueba = fso.CreateTextFile(carpeta & "\prueba_escritura.tmp", True)
If Err.Number <> 0 Then
    On Error GoTo 0
    Aviso "No tengo permiso para escribir en esta carpeta:" & vbCrLf & vbCrLf & carpeta & vbCrLf & vbCrLf & _
          "Mueve la carpeta a Documentos o al Escritorio y vuelve a intentarlo.", 16
    WScript.Quit 1
End If
prueba.Close
fso.DeleteFile carpeta & "\prueba_escritura.tmp", True
On Error GoTo 0

If Not fso.FileExists(carpeta & "\requirements.txt") Or Not fso.FolderExists(carpeta & "\yajol") Then
    Aviso "La carpeta est" & ChrW(225) & " incompleta." & vbCrLf & vbCrLf & _
          "Vuelve a extraer el archivo ZIP completo y abre Instalar.vbs desde la carpeta extra" & ChrW(237) & "da.", 16
    WScript.Quit 1
End If

CierraCorrectorAbierto

' ---------- 3. Ya estaba instalado: solo se repara y se abre ----------
If fso.FileExists(marca) And fso.FileExists(pyw) Then
    Apunta "=== Reparaci" & ChrW(243) & "n del " & Now & " ==="
    rc = Ejecuta(q & py & q & " " & q & carpeta & "\activar_inicio.py" & q)
    Aviso "El corrector ya estaba instalado. Revis" & ChrW(233) & " el arranque y lo voy a abrir." & notaLimpieza & vbCrLf & vbCrLf & _
          "Para recordar c" & ChrW(243) & "mo funciona, pulsa el signo ? del icono.", 64
    sh.Run q & pyw & q & " -m yajol", 0, False
    WScript.Quit 0
End If

' ---------- 4. Buscar Python ----------
On Error Resume Next
If fso.FileExists(registro) Then fso.DeleteFile registro, True
On Error GoTo 0
Apunta "=== Instalaci" & ChrW(243) & "n del Corrector YAJOL, " & Now & " ==="
Apunta "Carpeta: " & carpeta
Apunta "Arranques antiguos eliminados: " & quitados

ordenPython = ""
If HayPython("py -3") Then
    ordenPython = "py -3"
ElseIf HayPython("python") Then
    ordenPython = "python"
ElseIf HayPython("python3") Then
    ordenPython = "python3"
End If

If ordenPython = "" Then
    Aviso "Falta Python en este equipo." & vbCrLf & vbCrLf & _
          "Inst" & ChrW(225) & "lalo as" & ChrW(237) & ":" & vbCrLf & vbCrLf & _
          "   1.  Entra a  python.org/downloads" & vbCrLf & _
          "   2.  Descarga la versi" & ChrW(243) & "n para Windows y " & ChrW(225) & "brela." & vbCrLf & _
          "   3.  En la primera pantalla marca la casilla" & vbCrLf & _
          "        " & ChrW(171) & "Add python.exe to PATH" & ChrW(187) & "." & vbCrLf & _
          "   4.  Al terminar, vuelve a abrir Instalar.vbs." & notaLimpieza, 48
    WScript.Quit 1
End If
Apunta "Python encontrado con: " & ordenPython

' ---------- 5. Crear el entorno ----------
Aviso "Voy a instalar el corrector." & vbCrLf & vbCrLf & _
      "Tarda entre 2 y 5 minutos y necesita internet." & vbCrLf & _
      "Mientras tanto no ver" & ChrW(225) & "s nada en pantalla: es normal." & vbCrLf & vbCrLf & _
      "Al terminar se abrir" & ChrW(225) & " una ventana que explica c" & ChrW(243) & "mo se usa.", 64

On Error Resume Next
If fso.FolderExists(venv) Then fso.DeleteFolder venv, True
On Error GoTo 0
Apunta "--- Creando el entorno virtual ---"
rc = Ejecuta(ordenPython & " -m venv " & q & venv & q)
If Not fso.FileExists(py) Then
    Fallo "No se pudo crear el entorno de Python." & vbCrLf & vbCrLf & _
          "Suele pasar cuando Python se instal" & ChrW(243) & " desde la Microsoft Store." & vbCrLf & _
          "Inst" & ChrW(225) & "lalo desde python.org y marca " & ChrW(171) & "Add python.exe to PATH" & ChrW(187) & "."
End If

' ---------- 6. Instalar los componentes ----------
Apunta "--- Actualizando pip ---"
rc = Ejecuta(q & py & q & " -m pip install --upgrade pip --disable-pip-version-check")

Apunta "--- Instalando los componentes ---"
rc = Ejecuta(q & py & q & " -m pip install --disable-pip-version-check " & _
             "--no-warn-script-location -r " & q & carpeta & "\requirements.txt" & q)
If rc <> 0 Then
    Apunta "--- Segundo intento sin cach" & ChrW(233) & " ---"
    rc = Ejecuta(q & py & q & " -m pip install --no-cache-dir --disable-pip-version-check " & _
                 "-r " & q & carpeta & "\requirements.txt" & q)
End If
If rc <> 0 Then
    Fallo "No se pudieron descargar los componentes." & vbCrLf & vbCrLf & _
          "Revisa que haya internet y vuelve a abrir Instalar.vbs." & vbCrLf & _
          "Si sigue igual, puede ser el antivirus."
End If

Apunta "--- Comprobando la instalaci" & ChrW(243) & "n ---"
rc = Ejecuta(q & py & q & " -c " & q & "import PySide6, spylls, pynput, pyperclip" & q)
If rc <> 0 Then
    Fallo "Los componentes se instalaron pero no cargan bien."
End If

Set sello = fso.CreateTextFile(marca, True)
sello.WriteLine "Instalado el " & Now
sello.Close
Apunta "Instalaci" & ChrW(243) & "n terminada correctamente."

' ---------- 7. Arranque automatico ----------
rc = Ejecuta(q & py & q & " " & q & carpeta & "\activar_inicio.py" & q)
If rc <> 0 Then Apunta "Aviso: no se pudo activar el arranque autom" & ChrW(225) & "tico."

Aviso "Listo. El corrector ya est" & ChrW(225) & " instalado." & vbCrLf & vbCrLf & _
      "   " & ChrW(8226) & "  Se abre solo cada vez que enciendes el equipo." & vbCrLf & _
      "   " & ChrW(8226) & "  El icono del p" & ChrW(225) & "jaro aparece abajo a la derecha." & vbCrLf & _
      "   " & ChrW(8226) & "  Pulsa el icono para revisar lo que escribiste." & vbCrLf & _
      "   " & ChrW(8226) & "  Pulsa el signo ? del icono para ver la ayuda." & notaLimpieza, 64

sh.Run q & pyw & q & " -m yajol", 0, False
