' ============================================================
'  Corrector YAJOL - quitar del equipo
' ============================================================
Option Explicit

Dim sh, fso, carpeta, venv, respuesta, inicio, archivo

Set sh  = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
carpeta = fso.GetParentFolderName(WScript.ScriptFullName)
venv = carpeta & "\.venv"
inicio = sh.ExpandEnvironmentStrings("%APPDATA%") & _
         "\Microsoft\Windows\Start Menu\Programs\Startup"

respuesta = sh.Popup("Voy a quitar el arranque automatico y los componentes instalados." & vbCrLf & _
                     "Tus palabras aprendidas no se borran." & vbCrLf & vbCrLf & _
                     "Continuo?", 0, "Corrector YAJOL", 36)
If respuesta <> 6 Then WScript.Quit 0

' Cerrar el corrector si esta abierto
sh.Run "cmd /c taskkill /f /im pythonw.exe >nul 2>&1", 0, True

For Each archivo In Array("Corrector YAJOL.lnk", "Corrector YAJOL.vbs")
    If fso.FileExists(inicio & "\" & archivo) Then fso.DeleteFile inicio & "\" & archivo, True
Next

If fso.FolderExists(venv) Then fso.DeleteFolder venv, True

sh.Popup "Listo. El corrector ya no se abrira al encender el equipo." & vbCrLf & _
         "Puedes borrar esta carpeta si ya no la necesitas.", 0, "Corrector YAJOL", 64
