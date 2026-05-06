# 冨澤用ポータル — Claude Code 操作ガイド

## プロジェクト概要

職場タスク・お知らせを管理する個人用ポータル。
- `index.html` : メインページ（今日やること＋タスク一覧プルダウン＋カレンダー）
- `today.html` : 今日やること専用ページ
- `data.js`    : タスク・お知らせデータ（ここを編集して内容を管理）
- `未処理/`    : 処理前の連絡文（PDF・msg）を入れるフォルダ
- `処理済み/`  : 処理完了した連絡文を移動するフォルダ

---

## 「タスクの反映をお願いします」と言われたときの手順

**ユーザーがこのフレーズを言ったら、以下を自動で実行する。確認なしで進めてよい。**

### Step 1 — 未処理フォルダのファイルを確認

```
未処理/ フォルダ内のファイルを一覧表示する
```

### Step 2 — 各ファイルの内容を読み取る

- **PDF** → `Read` ツールで読み取り（連絡番号・タイトル・期限・対応内容を抽出）
- **msg（Outlook メール）** → バイナリのため、以下の Python で日本語テキストを抽出する：

```python
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

with open(r'ファイルパス', 'rb') as f:
    data = f.read()

results = []
i = 0
while i < len(data) - 3:
    b1, b2 = data[i], data[i+1]
    if (b2 == 0x30 and 0x40 <= b1 <= 0xFF) or \
       (b2 == 0x4E and b1 >= 0x00) or \
       (0x4E <= b2 <= 0x9F):
        start = i
        text_bytes = []
        while i < len(data) - 1:
            bb1, bb2 = data[i], data[i+1]
            if (bb2 == 0x00 and (bb1 == 0x09 or bb1 == 0x0A or bb1 == 0x0D or 0x20 <= bb1 <= 0x7E)) or \
               (bb2 == 0x30 and 0x00 <= bb1 <= 0xFF) or \
               (0x4E <= bb2 <= 0x9F) or \
               (bb2 == 0xFF and 0x01 <= bb1 <= 0xEF):
                text_bytes += [bb1, bb2]
                i += 2
            else:
                break
        if len(text_bytes) >= 20:
            try:
                t = bytes(text_bytes).decode('utf-16-le', errors='replace').strip()
                cjk = sum(1 for c in t if '぀' <= c <= '鿿')
                if cjk >= 4:
                    results.append(t)
            except:
                pass
    else:
        i += 1

seen = set()
for r in results:
    r2 = re.sub(r'\s+', ' ', r).strip()
    if r2 and r2 not in seen and len(r2) > 8:
        seen.add(r2)
        print(r2[:400])
```

### Step 3 — data.js にタスクを追加

`data.js` の `tasks` 配列の末尾に追記する。

**タスクオブジェクトの形式：**
```json
{
  "id": "t###",
  "title": "タスクタイトル",
  "source": "連絡No.2026-XXX または メール差出人",
  "category": "報告 | 対応 | 確認 | 連絡 | その他",
  "deadline": "YYYY-MM-DD または YYYY-MM-DDTHH:MM:SS または null",
  "status": "未対応",
  "urgent": false,
  "notes": "対応内容の詳細（\\nで改行）",
  "sourceFile": "元ファイル名.pdf",
  "addedDate": "YYYY-MM-DD（今日の日付）"
}
```

**注意事項：**
- `id` は既存の最大番号の次（例：t012 の次は t013）
- `status` は常に `"未対応"` で追加（完了状態は localStorage で管理）
- `deadline` が時刻も必要な場合は ISO 形式（`2026-04-28T13:15:00`）
- 期限が明示されていない緊急案件は `"deadline": null, "urgent": true`
- 1つの連絡文から複数のタスクが発生する場合は別々のオブジェクトに分割
- `// 最終更新:` の日付を今日の日付に更新する

### Step 4 — お知らせとして追加すべき場合

タスク（期限付き対応）ではなく情報共有・制度説明の場合は、`notices` 配列に追加する：

```json
{
  "id": "n###",
  "title": "お知らせタイトル",
  "source": "連絡No.2026-XXX",
  "date": "YYYY-MM-DD（連絡の日付）",
  "content": "内容（\\nで改行）",
  "sourceFile": "元ファイル名.pdf",
  "addedDate": "YYYY-MM-DD（今日の日付）"
}
```

### Step 5 — ファイルを処理済みフォルダへ移動

```bash
mv "未処理/ファイル名" "処理済み/ファイル名"
```

すべてのファイルを移動し、`未処理/` フォルダが空になったことを確認する。

### Step 6 — 完了報告

追加したタスクの一覧（件名・期限・カテゴリ）をユーザーに報告する。

---

### Step 4-B — イベントとして追加すべき場合

打合せ・会議・ミーティング・研修・説明会など「参加・出席するもの」は `events` 配列に追加する：

```json
{
  "id": "e###",
  "title": "イベント名（例：教務職Webミーティング 第5回）",
  "date": "YYYY-MM-DDTHH:MM:SS（開始日時）",
  "endTime": "HH:MM または null（終了時刻のみ・同日）",
  "location": "Teams / 会議室名 / null",
  "source": "連絡No.2026-XXX",
  "notes": "議題・持参資料など（\\nで改行）または null",
  "sourceFile": "元ファイル名.pdf",
  "addedDate": "YYYY-MM-DD（今日の日付）"
}
```

**注意事項：**
- `id` は既存の最大番号の次（例：e001 の次は e002）
- `date` は開始日時（時刻不明の場合は日付のみ `YYYY-MM-DD`）
- イベントに完了状態はなし（カレンダーにシアンドットで表示）

---

## タスク・イベント・お知らせの判定基準

| 判定 | 条件 | 追加先 |
|------|------|--------|
| タスク（報告） | 「報告してください」「ポータルに入力」等 | tasks |
| タスク（対応） | 「配付してください」「登録してください」等 | tasks |
| タスク（緊急） | 「早急に」「至急」または期限が設定されていない対応依頼 | tasks（urgent: true） |
| イベント | 打合せ・会議・ミーティング・研修・説明会など参加するもの | events |
| お知らせ | 情報共有・制度説明・周知事項のみ | notices |

---

## その他の操作

### 手動でタスクを追加したいとき
ポータルの「タスク一覧」プルダウンを開き、「追加」ボタンから登録（localStorage に保存される）。
永続化したい場合は data.js への追記を依頼する。

### タスクを削除したいとき
手動追加タスク → ポータル上の「削除」ボタン
data.js タスク → Claude Code に「〇〇のタスクを削除して」と依頼する。
