# allure-pytest-organizer

自作ツール `organize_files.py`（フォルダ内のファイルを拡張子ごとに振り分ける）を題材にした、
pytest + Allure Report の練習用サンプル。

- `organize_files.py` は自作ツールを無変更でコピーしたもの（`config.ini` / `run_organizer.bat` は含まない）
- テストは `tmp_path` の中だけで動く。実際のフォルダには触らない

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
