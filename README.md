# allure-pytest-organizer

自作ツール `organize_files.py`（フォルダ内のファイルを拡張子ごとに振り分ける）を題材にした、
pytest + Allure Report の練習用サンプル。

- `organize_files.py` は自作ツールを無変更でコピーしたもの（`config.ini` / `run_organizer.bat` は含まない）
- テストは `tmp_path` の中だけで動く。実際のフォルダには触らない

なぜこの構成にしたか（使っている仕組みと理由）は [docs/仕組み解説.md](docs/仕組み解説.md) にまとめています。

## 何をテストしているか

`organize_files.py` は、フォルダ内のファイルを拡張子ごとのフォルダに振り分けるツールです。

```
memo.txt   →  txt/memo.txt
photo.png  →  png/photo.png
Makefile   →  no_extension/Makefile
```

テストは次の4グループ・13件です。

| グループ | 確かめていること |
|---|---|
| ① 拡張子ごとの振り分け | 正しいフォルダに移る（拡張子なし・複数ファイルも） |
| ② 同じ名前のファイルがあるとき | 上書きせず `memo_2.txt` のように連番を付ける |
| ③ 対象外・準備まわり | 既存フォルダは動かさない／ログ用フォルダを作る／存在しないフォルダ指定（既知のバグ） |
| ④ 設定ファイル | `config.ini` が無いときの挙動 |

## レポートの見方

公開ページ: https://kageyama-aoi.github.io/allure-pytest-organizer/

- テスト一覧は「ファイル整理ツール → ①〜④のグループ → 確認している内容」の順に並びます
  （`allurerc.mjs` の `groupBy` で、テストコードに書いた日本語の分類を使う設定にしています）。
- テストを1つ開くと、日本語タイトル・説明・「準備 → 実行 → 確認」の3ステップが見えます。
- 成功・失敗の件数は、トップの集計に出ます。
- 1件だけ skipped と表示されるのは、失敗ではなく「既知のバグを記録しているテスト」です（下の「結果」を参照）。

## 実行手順（ローカル）

```powershell
pip install -r requirements.txt
python -m pytest --alluredir=allure-results
npx -y allure@3 generate allure-results -o allure-report   # Node があれば Java 不要
npx -y allure@3 open allure-report                         # ブラウザで開く
```

## 結果（2026-09-19 時点）

12 passed / 1 xfailed

`xfail` は元コードの既知バグ：対象フォルダが存在しないと、`setup_logging` が `is_dir()` 確認より先に
`mkdir` するため `FileNotFoundError` で落ちる。直したら `strict=True` により XPASS で失敗になるので、
`test_organize_files.py` の `xfail` を外す合図になる。

## 次のステップ

GitHub Actions で `allure-report/` を GitHub Pages に公開する。
