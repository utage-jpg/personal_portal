@echo off
chcp 65001 > nul

echo ================================================
echo  成績グラフ ダッシュボード 起動プロトコル登録
echo  ※ 管理者権限は不要です
echo ================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$vbs = \"$env:USERPROFILE\OneDrive\VScode\【職場】成績グラフ作成\launch_hidden.vbs\";" ^
  "New-Item -Path 'HKCU:\SOFTWARE\Classes\launch-dashboard' -Force | Out-Null;" ^
  "Set-ItemProperty 'HKCU:\SOFTWARE\Classes\launch-dashboard' -Name '(default)' -Value 'URL:Launch Dashboard Protocol';" ^
  "New-ItemProperty 'HKCU:\SOFTWARE\Classes\launch-dashboard' -Name 'URL Protocol' -Value '' -PropertyType String -Force | Out-Null;" ^
  "New-Item -Path 'HKCU:\SOFTWARE\Classes\launch-dashboard\shell\open\command' -Force | Out-Null;" ^
  "Set-ItemProperty 'HKCU:\SOFTWARE\Classes\launch-dashboard\shell\open\command' -Name '(default)' -Value ('\"wscript.exe\" /b /nologo \"' + $vbs + '\"');" ^
  "if (Get-ItemProperty 'HKCU:\SOFTWARE\Classes\launch-dashboard\shell\open\command' -Name '(default)') { Write-Host '登録成功！' } else { Write-Host '登録失敗' }"

echo.
echo ▶ 登録後はブラウザを再起動してから報告ページのボタンをお試しください。
echo.
pause
