' run_hidden.vbs
' Python スクリプトをコンソールウィンドウなしで実行するラッパー

Dim WshShell, ScriptDir, PythonScript
Set WshShell = CreateObject("WScript.Shell")

ScriptDir    = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\"))
PythonScript = ScriptDir & "reminder.py"

' 0 = ウィンドウ非表示, False = 非同期実行
WshShell.Run "python """ & PythonScript & """", 0, False

Set WshShell = Nothing
