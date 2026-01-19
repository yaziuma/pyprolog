"""
export_facts/2述語のテスト

事実データのエクスポート機能を検証する
"""

import tempfile
import os
import json
from pyprolog.runtime.interpreter import Runtime


class TestExportFactsPredicate:
    """export_facts/2述語のテストクラス"""

    def setup_method(self):
        """各テストの前にRuntimeを初期化"""
        self.runtime = Runtime()

        # テスト用の事実を追加
        self.runtime.add_rule("person(alice, 28).")
        self.runtime.add_rule("person(bob, 35).")
        self.runtime.add_rule("person(charlie, 42).")
        self.runtime.add_rule("animal(cat, mammal).")
        self.runtime.add_rule("animal(dog, mammal).")
        self.runtime.add_rule("animal(eagle, bird).")

        # ルールも追加（事実と区別されることを確認）
        self.runtime.add_rule("parent(X, Y) :- father(X, Y).")
        self.runtime.add_rule("parent(X, Y) :- mother(X, Y).")

        # 一時ディレクトリ作成
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """各テスト後のクリーンアップ"""
        # 一時ファイルの削除
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_export_facts_csv_basic(self):
        """CSV形式での基本的なエクスポートテスト"""
        output_file = os.path.join(self.temp_dir, "persons.csv")

        # export_facts/2を実行
        solutions = list(
            self.runtime.query(f"export_facts(person/2, '{output_file}').")
        )

        # 1つの解があることを確認
        assert len(solutions) == 1

        # ファイルが作成されていることを確認
        assert os.path.exists(output_file)

        # CSV内容を確認
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()

        # ヘッダーと各行が含まれていることを確認
        lines = content.strip().split("\n")
        assert len(lines) >= 4  # ヘッダー + 3行のデータ

        # 各person事実が含まれていることを確認
        assert "alice" in content
        assert "bob" in content
        assert "charlie" in content
        assert "28" in content
        assert "35" in content
        assert "42" in content

    def test_export_facts_json_basic(self):
        """JSON形式での基本的なエクスポートテスト"""
        output_file = os.path.join(self.temp_dir, "persons.json")

        # export_facts/2をJSON形式で実行
        solutions = list(
            self.runtime.query(f"export_facts(person/2, json('{output_file}')).")
        )

        # 1つの解があることを確認
        assert len(solutions) == 1

        # ファイルが作成されていることを確認
        assert os.path.exists(output_file)

        # JSON内容を確認
        with open(output_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # JSONが配列であることを確認
        assert isinstance(data, list)
        assert len(data) == 3  # 3つのperson事実

        # 各エントリーが適切な構造を持つことを確認
        for item in data:
            assert "functor" in item
            assert "args" in item
            assert item["functor"] == "person"
            assert len(item["args"]) == 2

    def test_export_facts_tsv_basic(self):
        """TSV形式での基本的なエクスポートテスト"""
        output_file = os.path.join(self.temp_dir, "animals.tsv")

        # export_facts/2をTSV形式で実行
        solutions = list(
            self.runtime.query(f"export_facts(animal/2, tsv('{output_file}')).")
        )

        # 1つの解があることを確認
        assert len(solutions) == 1

        # ファイルが作成されていることを確認
        assert os.path.exists(output_file)

        # TSV内容を確認
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()

        # タブ区切りであることを確認
        assert "\t" in content

        # 各animal事実が含まれていることを確認
        assert "cat" in content
        assert "dog" in content
        assert "eagle" in content
        assert "mammal" in content
        assert "bird" in content

    def test_export_facts_only_facts_not_rules(self):
        """事実のみがエクスポートされ、ルールは除外されることのテスト"""
        output_file = os.path.join(self.temp_dir, "all_data.csv")

        # parent述語にはルールしかない
        solutions = list(
            self.runtime.query(f"export_facts(parent/2, '{output_file}').")
        )

        # 解があることを確認（空のファイルでも成功）
        assert len(solutions) == 1

        # ファイルが作成されていることを確認
        assert os.path.exists(output_file)

        # ファイル内容を確認（ヘッダーのみまたは空）
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read().strip()

        # ルール内容は含まれていないことを確認
        assert "father(" not in content
        assert "mother(" not in content
        assert ":-" not in content

    def test_export_facts_nonexistent_predicate(self):
        """存在しない述語を指定した場合のテスト"""
        output_file = os.path.join(self.temp_dir, "nonexistent.csv")

        # 存在しない述語を指定
        solutions = list(
            self.runtime.query(f"export_facts(nonexistent/2, '{output_file}').")
        )

        # 解があることを確認（空のエクスポートでも成功）
        assert len(solutions) == 1

        # ファイルが作成されていることを確認
        assert os.path.exists(output_file)

        # ファイルが空またはヘッダーのみであることを確認
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read().strip()

        # データは含まれていない
        lines = content.split("\n") if content else []
        assert len(lines) <= 1  # ヘッダーのみまたは空

    def test_export_facts_invalid_file_path(self):
        """無効なファイルパスでのテスト"""
        # 存在しないドライブ/ディレクトリへのパス
        if os.name == "nt":
            invalid_path = "Z:\\invalid<>path\\output.csv"
        else:
            invalid_path = "/proc/definitely/invalid/path/output.csv"

        # エラーが発生して失敗することを確認
        solutions = list(
            self.runtime.query(f"export_facts(person/2, '{invalid_path}').")
        )

        # 失敗することを確認（解がない）
        assert len(solutions) == 0

    def test_export_facts_invalid_predicate_format(self):
        """無効な述語指定形式のテスト"""
        output_file = os.path.join(self.temp_dir, "output.csv")

        # アリティなしの述語指定
        solutions = list(self.runtime.query(f"export_facts(person, '{output_file}')."))

        # 失敗することを確認
        assert len(solutions) == 0

        # 負のアリティ
        solutions = list(
            self.runtime.query(f"export_facts(person/(-1), '{output_file}').")
        )

        # 失敗することを確認
        assert len(solutions) == 0

    def test_export_facts_with_japanese_data(self):
        """日本語データを含む事実のエクスポートテスト"""
        # 日本語事実を追加
        self.runtime.add_rule("人(太郎, 30).")
        self.runtime.add_rule("人(花子, 25).")

        output_file = os.path.join(self.temp_dir, "japanese_data.csv")

        # export_facts/2を実行（内部でマッピングされた述語名を使用する可能性）
        solutions = list(self.runtime.query(f"export_facts(人/2, '{output_file}')."))

        # 成功することを確認
        assert len(solutions) == 1

        # ファイルが作成されていることを確認
        assert os.path.exists(output_file)

        # ファイル内容を確認（UTF-8で正しく保存されている）
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()

        # 日本語データが含まれていることを確認
        assert "太郎" in content or "tarou" in content  # マッピングに依存
        assert "花子" in content or "hanako" in content

    def test_export_facts_with_complex_terms(self):
        """複雑な項を含む事実のエクスポートテスト"""
        # リストや複合項を含む事実を追加
        self.runtime.add_rule("data(item1, [a, b, c]).")
        self.runtime.add_rule("data(item2, struct(x, y)).")

        output_file = os.path.join(self.temp_dir, "complex_data.json")

        # JSON形式でエクスポート
        solutions = list(
            self.runtime.query(f"export_facts(data/2, json('{output_file}')).")
        )

        # 成功することを確認
        assert len(solutions) == 1

        # ファイルが作成されていることを確認
        assert os.path.exists(output_file)

        # JSON内容を確認
        with open(output_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # データが正しく構造化されていることを確認
        assert len(data) == 2
        for item in data:
            assert "functor" in item
            assert "args" in item
            assert item["functor"] == "data"

    def test_export_facts_file_overwrite(self):
        """既存ファイルの上書きテスト"""
        output_file = os.path.join(self.temp_dir, "overwrite_test.csv")

        # 既存ファイルを作成
        with open(output_file, "w") as f:
            f.write("existing content")

        # export_facts/2を実行
        solutions = list(
            self.runtime.query(f"export_facts(person/2, '{output_file}').")
        )

        # 成功することを確認
        assert len(solutions) == 1

        # ファイルが上書きされていることを確認
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()

        # 古いコンテンツは残っていない
        assert "existing content" not in content
        # 新しいデータが含まれている
        assert "alice" in content


class TestExportFactsEdgeCases:
    """export_facts述語のエッジケースのテスト"""

    def setup_method(self):
        self.runtime = Runtime()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_export_facts_large_dataset(self):
        """大量データのエクスポートテスト"""
        # 大量の事実を追加
        for i in range(100):
            self.runtime.add_rule(f"data({i}, value_{i}).")

        output_file = os.path.join(self.temp_dir, "large_dataset.csv")

        # エクスポート実行
        solutions = list(self.runtime.query(f"export_facts(data/2, '{output_file}')."))

        # 成功することを確認
        assert len(solutions) == 1
        assert os.path.exists(output_file)

        # ファイルサイズが妥当であることを確認
        file_size = os.path.getsize(output_file)
        assert file_size > 0

    def test_export_facts_unicode_handling(self):
        """Unicode文字の処理テスト"""
        # 様々なUnicode文字を含む事実
        self.runtime.add_rule("unicode('αβγ', 'δεζ').")
        self.runtime.add_rule("unicode('🌟', '🌙').")

        output_file = os.path.join(self.temp_dir, "unicode_test.csv")

        solutions = list(
            self.runtime.query(f"export_facts(unicode/2, '{output_file}').")
        )

        # 成功することを確認
        assert len(solutions) == 1
        assert os.path.exists(output_file)

        # UTF-8エンコーディングで正しく保存されていることを確認
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Unicode文字が含まれていることを確認
        assert "α" in content or "unicode" in content  # 内部表現に依存
