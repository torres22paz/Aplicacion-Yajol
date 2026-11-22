' Lanzador del corrector: no abre ventanas de consola.
' La primera vez instala lo necesario. Cualquier fallo muestra un aviso con el motivo.
Option Explicit

Dim sh, fso, dir, q, pyExe, pyw, marca, logf, rc, cmdline

Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
q = Chr(34)
dir = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = dir
pyExe = dir & "\.venv\Scripts\python.exe"
pyw = dir & "\.venv\Scripts\pythonw.exe"
marca = dir & "\.venv\listo"
logf = dir & "\instalacion.log"

Sub Fallo(texto)
    sh.Popup texto & vbCrLf & vbCrLf & "Detalle en: " & logf, 0, "Corrector flotante", 16
    WScript.Quit 1
End Sub

If Not fso.FileExists(marca) Then
    sh.Popup "Primera vez: instalando componentes. Tarda entre 5 y 10 minutos." & vbCrLf & _
             "Cuando termine aparecerá el icono en la esquina inferior derecha.", 8, "Corrector flotante", 64

    ' Crear el entorno virtual: primero con "python", luego con el lanzador "py"
    rc = sh.Run("cmd /c python -m venv .venv >> " & q & logf & q & " 2>&1", 0, True)
    If rc <> 0 Or Not fso.FileExists(pyExe) Then
        rc = sh.Run("cmd /c py -3 -m venv .venv >> " & q & logf & q & " 2>&1", 0, True)
    End If
    If Not fso.FileExists(pyExe) Then
        Fallo "No se encontró Python. Instálalo desde python.org y marca ""Add python.exe to PATH""."
    End If

    ' Instalar dependencias. La instrucción va envuelta en comillas para que cmd no las altere.
    cmdline = "cmd /c " & q & q & pyExe & q & " -m pip install -r requirements.txt >> " & q & logf & q & " 2>&1" & q
    rc = sh.Run(cmdline, 0, True)
    If rc <> 0 Then Fallo "Falló la instalación de componentes."

    fso.CreateTextFile(marca, True).Close
End If

If Not fso.FileExists(pyw) Then Fallo "Falta el entorno de Python. Borra la carpeta .venv y vuelve a abrir este archivo."

sh.Run q & pyw & q & " " & q & dir & "\main.py" & q, 0, False
