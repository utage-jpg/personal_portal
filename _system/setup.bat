@echo off
chcp 65001 > nul

echo ================================================
echo  職場報告管理 リマインダー セットアップ
echo  ※ 管理者権限は不要です
echo ================================================
echo.

set "VBS=%~dp0run_hidden.vbs"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$vbs = '%VBS%';" ^
  "$action   = New-ScheduledTaskAction -Execute 'wscript.exe' -Argument ('/b /nologo """ + $vbs + """');" ^
  "$trigger  = New-ScheduledTaskTrigger -Daily -At '12:30';" ^
  "$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Hours 1) -StartWhenAvailable;" ^
  "$principal = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited;" ^
  "Unregister-ScheduledTask -TaskName 'WorkplaceReportReminder' -Confirm:$false -ErrorAction SilentlyContinue;" ^
  "Register-ScheduledTask -TaskName 'WorkplaceReportReminder' -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null;" ^
  "$task = Get-ScheduledTask -TaskName 'WorkplaceReportReminder' -ErrorAction SilentlyContinue;" ^
  "if ($task) { $i = Get-ScheduledTaskInfo 'WorkplaceReportReminder'; Write-Host '登録成功！次回実行:' $i.NextRunTime } else { Write-Host '登録失敗' }"

echo.
echo ▶ 動作テスト（すぐに通知が来るか確認）:
echo   python "%~dp0reminder.py"
echo.
pause
