' ============================================================
'  Corrector YAJOL - abre el corrector sin ventana de consola
' ============================================================
Option Explicit

Dim sh, fso, carpeta, q, pyw

Set sh  = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
q = Chr(34)
carpeta = fso.GetParentFolderName(WScript.ScriptFullName)
pyw = carpeta & "\.venv\Scripts\pythonw.exe"
sh.CurrentDirectory = carpeta

If Not fso.FileExists(pyw) Then
    sh.Popup "Todavia falta instalar los componentes." & vbCrLf & vbCrLf & _
             "Abre el archivo Instalar.vbs que esta en esta misma carpeta.", _
             0, "Corrector YAJOL", 48
    WScript.Quit 1
End If

sh.Run q & pyw & q & " -m yajol", 0, False
