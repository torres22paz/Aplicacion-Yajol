' ============================================================
'  Corrector YAJOL - abre el corrector sin ventana de consola
'  Con el argumento /inicio no muestra ningun aviso.
' ============================================================
Option Explicit

Dim sh, fso, carpeta, q, pyw, silencioso, argumento, i

Set sh  = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
q = Chr(34)
carpeta = fso.GetParentFolderName(WScript.ScriptFullName)
pyw = carpeta & "\.venv\Scripts\pythonw.exe"

silencioso = False
For i = 0 To WScript.Arguments.Count - 1
    argumento = LCase(WScript.Arguments(i))
    If argumento = "/inicio" Or argumento = "--inicio" Then silencioso = True
Next

If Not fso.FileExists(pyw) Or Not fso.FolderExists(carpeta & "\yajol") Then
    If silencioso Then WScript.Quit 0
    If sh.Popup("El corrector todav" & ChrW(237) & "a no est" & ChrW(225) & " instalado en esta carpeta." & vbCrLf & vbCrLf & _
                ChrW(191) & "Lo instalo ahora?", 0, "Corrector YAJOL", 36) = 6 Then
        If fso.FileExists(carpeta & "\Instalar.vbs") Then
            sh.Run "wscript.exe " & q & carpeta & "\Instalar.vbs" & q, 1, False
        End If
    End If
    WScript.Quit 0
End If

sh.CurrentDirectory = carpeta
If silencioso Then
    sh.Run q & pyw & q & " -m yajol --inicio", 0, False
Else
    sh.Run q & pyw & q & " -m yajol", 0, False
End If
