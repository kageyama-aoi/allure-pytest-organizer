"""organize_files.py のテスト（Allure Report 練習用）。

実ファイルは一切触らず、pytest の tmp_path 配下だけで動かす。
"""
import configparser

import allure
import pytest

import organize_files


@pytest.fixture
def target(tmp_path, monkeypatch):
    """整理対象フォルダを tmp_path に向けた状態で返す。"""
    config = configparser.ConfigParser()
    config["Settings"] = {"TargetDirectory": str(tmp_path), "LogDirectoryName": "logs"}
    monkeypatch.setattr(organize_files, "load_config", lambda: config)
    return tmp_path


def make_file(directory, name, text="x"):
    path = directory / name
    path.write_text(text, encoding="utf-8")
    return path


@allure.epic("ファイル整理ツール")
@allure.feature("拡張子ごとの振り分け")
class TestSortByExtension:
    @allure.story("拡張子と同名のフォルダへ移動する")
    @pytest.mark.parametrize("name, folder", [
        ("memo.txt", "txt"),
        ("photo.png", "png"),
        ("report.xlsx", "xlsx"),
        ("archive.tar.gz", "gz"),
    ])
    def test_moves_into_extension_folder(self, target, name, folder):
        with allure.step(f"{name} を用意する"):
            make_file(target, name)
        with allure.step("整理を実行する"):
            organize_files.organize_files()
        with allure.step(f"{folder}/ に移動し、元の場所から消えている"):
            assert (target / folder / name).is_file()
            assert not (target / name).exists()

    @allure.story("拡張子なしは no_extension へ移動する")
    def test_no_extension(self, target):
        make_file(target, "Makefile")
        organize_files.organize_files()
        assert (target / "no_extension" / "Makefile").is_file()

    @allure.story("複数ファイルをまとめて振り分ける")
    def test_multiple_files(self, target):
        for name in ["a.txt", "b.txt", "c.png"]:
            make_file(target, name)
        organize_files.organize_files()
        assert sorted(p.name for p in (target / "txt").iterdir()) == ["a.txt", "b.txt"]
        assert [p.name for p in (target / "png").iterdir()] == ["c.png"]


@allure.epic("ファイル整理ツール")
@allure.feature("同名ファイルの衝突回避")
class TestNameCollision:
    @allure.story("同名があれば連番を付ける")
    def test_adds_counter_when_name_exists(self, target):
        (target / "txt").mkdir()
        make_file(target / "txt", "memo.txt", "old")
        make_file(target, "memo.txt", "new")

        organize_files.organize_files()

        assert (target / "txt" / "memo.txt").read_text(encoding="utf-8") == "old"
        assert (target / "txt" / "memo_2.txt").read_text(encoding="utf-8") == "new"

    @allure.story("連番も埋まっていれば次の番号を使う")
    def test_skips_used_counters(self, target):
        (target / "txt").mkdir()
        make_file(target / "txt", "memo.txt")
        make_file(target / "txt", "memo_2.txt")
        make_file(target, "memo.txt", "new")

        organize_files.organize_files()

        assert (target / "txt" / "memo_3.txt").read_text(encoding="utf-8") == "new"


@allure.epic("ファイル整理ツール")
@allure.feature("対象外の扱い")
class TestSkipped:
    @allure.story("既存のフォルダは移動しない")
    def test_directories_are_left_alone(self, target):
        (target / "keep_me").mkdir()
        organize_files.organize_files()
        assert (target / "keep_me").is_dir()

    @allure.story("ログ用フォルダが作られる")
    def test_log_directory_is_created(self, target):
        organize_files.organize_files()
        assert (target / "logs").is_dir()

    @allure.story("存在しないフォルダでは何もせず終了する")
    @pytest.mark.xfail(
        strict=True,
        raises=FileNotFoundError,
        reason="既知のバグ: setup_logging が is_dir() 確認より先に mkdir するため落ちる",
    )
    def test_missing_target_directory(self, tmp_path, monkeypatch):
        missing = tmp_path / "nothing"
        config = configparser.ConfigParser()
        config["Settings"] = {"TargetDirectory": str(missing), "LogDirectoryName": "logs"}
        monkeypatch.setattr(organize_files, "load_config", lambda: config)

        organize_files.organize_files()  # 本来は例外にならず「見つかりません」ログで終了したい


@allure.epic("ファイル整理ツール")
@allure.feature("設定ファイル")
class TestConfig:
    @allure.story("config.ini が無ければ FileNotFoundError")
    def test_load_config_missing(self, tmp_path, monkeypatch):
        # __file__ の親を空の tmp_path に差し替え、config.ini が無い状態にする
        monkeypatch.setattr(organize_files, "__file__", str(tmp_path / "organize_files.py"))
        with pytest.raises(FileNotFoundError):
            organize_files.load_config()

    @allure.story("設定が読めなければメッセージを出して終了する")
    def test_organize_files_handles_bad_config(self, monkeypatch, capsys):
        def boom():
            raise FileNotFoundError("config.ini")

        monkeypatch.setattr(organize_files, "load_config", boom)
        organize_files.organize_files()
        assert "設定ファイルの読み込みに失敗しました" in capsys.readouterr().out
