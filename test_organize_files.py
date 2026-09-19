"""organize_files.py のテスト（Allure Report 練習用）。

organize_files.py は「フォルダ内のファイルを、拡張子ごとのフォルダに振り分ける」ツール。
  例) memo.txt → txt/memo.txt、photo.png → png/photo.png

実ファイルは一切触らず、pytest の tmp_path（使い捨ての一時フォルダ）の中だけで動かす。

各テストは「準備 → 実行 → 確認」の3ステップで書いてあり、
Allure のレポートでは、その3ステップと日本語タイトル・説明が見える。
"""
import configparser

import allure
import pytest

import organize_files


@pytest.fixture
def target(tmp_path, monkeypatch):
    """整理対象フォルダを、使い捨ての一時フォルダに向けた状態で返す。"""
    config = configparser.ConfigParser()
    config["Settings"] = {"TargetDirectory": str(tmp_path), "LogDirectoryName": "logs"}
    monkeypatch.setattr(organize_files, "load_config", lambda: config)
    return tmp_path


def make_file(directory, name, text="x"):
    path = directory / name
    path.write_text(text, encoding="utf-8")
    return path


@allure.epic("ファイル整理ツール")
@allure.feature("① 拡張子ごとの振り分け")
class TestSortByExtension:
    @allure.story("拡張子と同じ名前のフォルダへ移動する")
    @pytest.mark.parametrize("name, folder", [
        ("memo.txt", "txt"),
        ("photo.png", "png"),
        ("report.xlsx", "xlsx"),
        ("archive.tar.gz", "gz"),
    ])
    def test_moves_into_extension_folder(self, target, name, folder):
        """ファイルが「拡張子と同じ名前のフォルダ」に移り、元の場所からは無くなる。
        `archive.tar.gz` のように拡張子が2つ付くものは、最後の `gz` が使われる。"""
        allure.dynamic.title(f"{name} が {folder}/ フォルダへ移動する")
        with allure.step(f"準備: {name} を置く"):
            make_file(target, name)
        with allure.step("実行: 整理ツールを動かす"):
            organize_files.organize_files()
        with allure.step(f"確認: {folder}/{name} ができ、元の場所からは消えている"):
            assert (target / folder / name).is_file()
            assert not (target / name).exists()

    @allure.story("拡張子が無いファイルは no_extension へ移動する")
    @allure.title("拡張子なしの Makefile が no_extension/ フォルダへ移動する")
    def test_no_extension(self, target):
        """拡張子が無いファイルは、専用の `no_extension` フォルダにまとめられる。"""
        with allure.step("準備: 拡張子なしの Makefile を置く"):
            make_file(target, "Makefile")
        with allure.step("実行: 整理ツールを動かす"):
            organize_files.organize_files()
        with allure.step("確認: no_extension/Makefile ができている"):
            assert (target / "no_extension" / "Makefile").is_file()

    @allure.story("複数のファイルをまとめて振り分ける")
    @allure.title("txt 2つと png 1つを、それぞれのフォルダへ振り分ける")
    def test_multiple_files(self, target):
        """種類の違うファイルが混ざっていても、それぞれ正しいフォルダへ入る。"""
        with allure.step("準備: a.txt, b.txt, c.png を置く"):
            for name in ["a.txt", "b.txt", "c.png"]:
                make_file(target, name)
        with allure.step("実行: 整理ツールを動かす"):
            organize_files.organize_files()
        with allure.step("確認: txt/ に2つ、png/ に1つ入っている"):
            assert sorted(p.name for p in (target / "txt").iterdir()) == ["a.txt", "b.txt"]
            assert [p.name for p in (target / "png").iterdir()] == ["c.png"]


@allure.epic("ファイル整理ツール")
@allure.feature("② 同じ名前のファイルがあるとき")
class TestNameCollision:
    @allure.story("上書きせず、連番を付けて残す")
    @allure.title("移動先に同名ファイルがあれば、memo_2.txt と連番を付けて残す")
    def test_adds_counter_when_name_exists(self, target):
        """既にある memo.txt を上書きして消してしまわないことを確かめる。"""
        with allure.step("準備: txt/ に古い memo.txt、直下に新しい memo.txt を置く"):
            (target / "txt").mkdir()
            make_file(target / "txt", "memo.txt", "old")
            make_file(target, "memo.txt", "new")
        with allure.step("実行: 整理ツールを動かす"):
            organize_files.organize_files()
        with allure.step("確認: 古い方はそのまま、新しい方は memo_2.txt になっている"):
            assert (target / "txt" / "memo.txt").read_text(encoding="utf-8") == "old"
            assert (target / "txt" / "memo_2.txt").read_text(encoding="utf-8") == "new"

    @allure.story("上書きせず、連番を付けて残す")
    @allure.title("memo_2.txt も使用済みなら、次の memo_3.txt を使う")
    def test_skips_used_counters(self, target):
        """連番が既に埋まっていても、空いている次の番号まで進む。"""
        with allure.step("準備: txt/ に memo.txt と memo_2.txt、直下に新しい memo.txt を置く"):
            (target / "txt").mkdir()
            make_file(target / "txt", "memo.txt")
            make_file(target / "txt", "memo_2.txt")
            make_file(target, "memo.txt", "new")
        with allure.step("実行: 整理ツールを動かす"):
            organize_files.organize_files()
        with allure.step("確認: 新しい方は memo_3.txt になっている"):
            assert (target / "txt" / "memo_3.txt").read_text(encoding="utf-8") == "new"


@allure.epic("ファイル整理ツール")
@allure.feature("③ 対象外・準備まわり")
class TestSkipped:
    @allure.story("フォルダは動かさない")
    @allure.title("もともとあるフォルダは、移動せずそのまま残す")
    def test_directories_are_left_alone(self, target):
        """整理の対象は「ファイル」だけ。既存のフォルダは触らない。"""
        with allure.step("準備: keep_me フォルダを作る"):
            (target / "keep_me").mkdir()
        with allure.step("実行: 整理ツールを動かす"):
            organize_files.organize_files()
        with allure.step("確認: keep_me フォルダがそのまま残っている"):
            assert (target / "keep_me").is_dir()

    @allure.story("ログを残す")
    @allure.title("実行すると logs フォルダができる")
    def test_log_directory_is_created(self, target):
        """実行の記録を残すための logs フォルダが作られる。"""
        with allure.step("実行: 整理ツールを動かす"):
            organize_files.organize_files()
        with allure.step("確認: logs フォルダができている"):
            assert (target / "logs").is_dir()

    @allure.story("設定ミスへの対応")
    @allure.title("【既知のバグ】存在しないフォルダを指定すると、想定外のエラーで落ちる")
    @pytest.mark.xfail(
        strict=True,
        raises=FileNotFoundError,
        reason="既知のバグ: setup_logging が is_dir() 確認より先に mkdir するため落ちる",
    )
    def test_missing_target_directory(self, tmp_path, monkeypatch):
        """本来は「フォルダが見つかりません」とログに出して静かに終わってほしい。
        現状のツールは、その前にログ用フォルダを作ろうとして FileNotFoundError で落ちる。
        直るまでは「失敗が想定どおり」として記録している（レポートでは skipped 扱い）。"""
        missing = tmp_path / "nothing"
        config = configparser.ConfigParser()
        config["Settings"] = {"TargetDirectory": str(missing), "LogDirectoryName": "logs"}
        monkeypatch.setattr(organize_files, "load_config", lambda: config)

        with allure.step("実行: 存在しないフォルダを対象にして整理ツールを動かす"):
            organize_files.organize_files()


@allure.epic("ファイル整理ツール")
@allure.feature("④ 設定ファイル（config.ini）")
class TestConfig:
    @allure.story("設定ファイルが無いとき")
    @allure.title("config.ini が無ければ FileNotFoundError になる")
    def test_load_config_missing(self, tmp_path, monkeypatch):
        """設定ファイルが見つからないことを、エラーではっきり知らせる。"""
        with allure.step("準備: config.ini が存在しない場所にツールがある状態にする"):
            monkeypatch.setattr(organize_files, "__file__", str(tmp_path / "organize_files.py"))
        with allure.step("確認: 設定を読むと FileNotFoundError になる"):
            with pytest.raises(FileNotFoundError):
                organize_files.load_config()

    @allure.story("設定ファイルが無いとき")
    @allure.title("設定が読めないときは、メッセージを出して終了する")
    def test_organize_files_handles_bad_config(self, monkeypatch, capsys):
        """設定エラーのとき、落ちずに「設定ファイルの読み込みに失敗しました」と表示して終わる。"""
        def boom():
            raise FileNotFoundError("config.ini")

        with allure.step("準備: 設定の読み込みが失敗する状態にする"):
            monkeypatch.setattr(organize_files, "load_config", boom)
        with allure.step("実行: 整理ツールを動かす"):
            organize_files.organize_files()
        with allure.step("確認: 失敗を知らせるメッセージが表示されている"):
            assert "設定ファイルの読み込みに失敗しました" in capsys.readouterr().out
