# reminder.py
# 職場報告管理 リマインダースクリプト
# Windowsタスクスケジューラから毎日12:30に実行される

import re
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

# ── パス設定 ──
BASE_DIR  = Path(__file__).parent.parent
DATA_JS   = BASE_DIR / "data.js"
INDEX_HTML = BASE_DIR / "index.html"

# ── data.js を読み込んで JSON として解析 ──
def load_data():
    try:
        text = DATA_JS.read_text(encoding='utf-8')
        # "const APP_DATA = { ... };" の中身を抽出
        m = re.search(r'const APP_DATA\s*=\s*(\{.*\})\s*;', text, re.DOTALL)
        if not m:
            return None
        return json.loads(m.group(1))
    except Exception as e:
        print(f"[ERROR] data.js 読み込みエラー: {e}", file=sys.stderr)
        return None

# ── Windows トースト通知（PowerShell 経由）──
def notify(title, body):
    title = title.replace('"', "'").replace('\n', ' ')[:200]
    body  = body.replace('"', "'").replace('\n', ' ')[:300]
    ps = f'''
Add-Type -AssemblyName System.Windows.Forms
$icon  = [System.Drawing.SystemIcons]::Warning
$tray  = New-Object System.Windows.Forms.NotifyIcon
$tray.Icon              = $icon
$tray.BalloonTipIcon    = "Warning"
$tray.BalloonTipTitle   = "{title}"
$tray.BalloonTipText    = "{body}"
$tray.Visible           = $True
$tray.ShowBalloonTip(12000)
Start-Sleep -Seconds 14
$tray.Dispose()
'''
    subprocess.Popen(
        ['powershell', '-WindowStyle', 'Hidden', '-NonInteractive', '-Command', ps],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

# ── 期日差分（日数）──
def day_diff(deadline_str):
    if not deadline_str:
        return None
    try:
        dl = date.fromisoformat(deadline_str[:10])
        return (dl - date.today()).days
    except:
        return None

# ── タスクの状態 ──
def task_state(t):
    if t.get('status') == '完了':
        return 'done'
    if t.get('urgent') and not t.get('deadline'):
        return 'urgent'
    diff = day_diff(t.get('deadline'))
    if diff is None:
        return 'urgent'
    if diff < 0:
        return 'overdue'
    if diff <= 7:
        return 'soon'
    return 'normal'

# ── メイン処理 ──
def run():
    data = load_data()
    if not data:
        notify("【職場報告管理】エラー", "data.js が読み込めませんでした。ファイルを確認してください。")
        return

    today = date.today()
    tasks = data.get('tasks', [])

    # リマインダー対象を収集
    overdue_list = []  # 期限切れ
    urgent_list  = []  # 期日未設定・早急
    today_list   = []  # 本日期限
    day3_list    = []  # 3日以内
    day7_list    = []  # 7日以内（3日超）

    for t in tasks:
        if t.get('status') == '完了':
            continue

        state = task_state(t)
        title = t.get('title', '不明なタスク')
        diff  = day_diff(t.get('deadline'))

        if state == 'overdue':
            overdue_list.append((title, abs(diff)))
        elif state == 'urgent':
            urgent_list.append(title)
        elif diff == 0:
            today_list.append(title)
        elif diff is not None and diff <= 3:
            day3_list.append((title, diff))
        elif diff is not None and diff <= 7:
            day7_list.append((title, diff))

    # ── 通知を送信 ──

    # 1. 期限切れ（最優先・毎日通知）
    if overdue_list:
        lines = [f"・{t}（{d}日超過）" for t, d in overdue_list]
        notify(
            f"🔴【期限切れ】{len(overdue_list)}件 — 職場報告管理",
            '\n'.join(lines[:4]) + ('...' if len(lines) > 4 else '')
        )

    # 2. 早急対応
    if urgent_list:
        lines = [f"・{t}" for t in urgent_list]
        notify(
            f"🚨【早急対応】{len(urgent_list)}件 — 職場報告管理",
            '\n'.join(lines[:4])
        )

    # 3. 本日期限
    if today_list:
        lines = [f"・{t}" for t in today_list]
        notify(
            f"🔔【本日期限】{len(today_list)}件 — 職場報告管理",
            '\n'.join(lines[:4])
        )

    # 4. 3日以内
    if day3_list:
        lines = [f"・{t}（残り{d}日）" for t, d in day3_list]
        notify(
            f"⚠️【3日以内に期限】{len(day3_list)}件 — 職場報告管理",
            '\n'.join(lines[:4])
        )

    # 5. 7日以内（3日超）— 日曜のみ通知（週1）
    if day7_list and today.weekday() == 6:  # 日曜
        lines = [f"・{t}（残り{d}日）" for t, d in day7_list]
        notify(
            f"📅【今週中に期限】{len(day7_list)}件 — 職場報告管理",
            '\n'.join(lines[:4])
        )

    # 何もなければ無音（通知しない）
    total = len(overdue_list) + len(urgent_list) + len(today_list) + len(day3_list)
    if total == 0:
        print(f"[{today}] リマインダー対象なし")
    else:
        print(f"[{today}] 通知送信: 期限切れ{len(overdue_list)} 早急{len(urgent_list)} 本日{len(today_list)} 3日以内{len(day3_list)}")

if __name__ == '__main__':
    run()
