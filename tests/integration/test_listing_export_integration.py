"""
listing/export機能の統合テスト

listing述語とexport_facts述語の統合動作を検証する
"""

import tempfile
import os
import json
from pyprolog.runtime.interpreter import Runtime
from pyprolog.runtime.io_streams import StringStream


class TestListingExportIntegration:
    """listing/export統合テストクラス"""

    def setup_method(self):
        """各テストの前にRuntimeと知識ベースを準備"""
        self.runtime = Runtime()

        # 包括的な知識ベースを構築
        self.runtime.add_rule("person(alice, 28, engineer).")
        self.runtime.add_rule("person(bob, 35, doctor).")
        self.runtime.add_rule("person(charlie, 42, teacher).")

        self.runtime.add_rule("department(engineering, 50).")
        self.runtime.add_rule("department(medical, 30).")
        self.runtime.add_rule("department(education, 40).")

        self.runtime.add_rule("project(alpha, engineering, active).")
        self.runtime.add_rule("project(beta, medical, completed).")

        # ルール（事実と区別されることを確認）
        self.runtime.add_rule("employee(X) :- person(X, _, _).")
        self.runtime.add_rule("senior(X) :- person(X, Age, _), Age > 30.")
        self.runtime.add_rule(
            "works_on(Person, Project) :- person(Person, _, Dept), project(Project, Dept, active)."
        )

        # 一時ディレクトリ
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """テスト後のクリーンアップ"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_listing_shows_all_predicates(self):
        """listing/0がすべての述語（事実とルール）を表示することを確認"""
        # 出力キャプチャ
        output_buffer = []
        string_stream = StringStream(initial_input="", output_buffer=output_buffer)
        self.runtime.io_manager.set_output_stream(string_stream)

        # listing実行
        solutions = list(self.runtime.query("listing."))
        assert len(solutions) == 1

        output_content = "".join(output_buffer)

        # 事実が含まれることを確認（数値は浮動小数点として表示される）
        assert "person(alice, 28" in output_content
        assert "department(engineering, 50" in output_content
        assert "project(alpha, engineering, active)." in output_content

        # ルールが含まれることを確認
        assert "employee(X) :- person(X, _, _)." in output_content
        assert "senior(X)" in output_content
        assert "works_on(" in output_content
        assert ":-" in output_content

    def test_listing_specific_predicates(self):
        """listing/1で特定の述語のみを表示"""
        # 出力キャプチャ
        output_buffer = []
        string_stream = StringStream(initial_input="", output_buffer=output_buffer)
        self.runtime.io_manager.set_output_stream(string_stream)

        # person/3のみをリスト
        solutions = list(self.runtime.query("listing(person/3)."))
        assert len(solutions) == 1

        output_content = "".join(output_buffer)

        # person/3の事実のみが含まれることを確認（数値は浮動小数点として表示される）
        assert "person(alice, 28" in output_content
        assert "person(bob, 35" in output_content
        assert "person(charlie, 42" in output_content

        # 他の述語は含まれないことを確認
        assert "department(" not in output_content
        assert "project(" not in output_content

    def test_export_facts_only_exports_facts(self):
        """export_facts/2が事実のみをエクスポートし、ルールは除外することを確認"""
        output_file = os.path.join(self.temp_dir, "persons.csv")

        # person/3をエクスポート
        solutions = list(
            self.runtime.query(f"export_facts(person/3, '{output_file}').")
        )
        assert len(solutions) == 1

        # ファイル内容を確認
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()

        # 事実データが含まれることを確認
        assert "alice" in content
        assert "engineer" in content
        assert "bob" in content
        assert "doctor" in content

        # ルールの内容は含まれないことを確認
        assert "employee(" not in content
        assert "senior(" not in content
        assert ":-" not in content

    def test_listing_and_export_consistency(self):
        """listing表示内容とexportの内容に一貫性があることを確認"""
        # listing出力をキャプチャ
        output_buffer = []
        string_stream = StringStream(initial_input="", output_buffer=output_buffer)
        self.runtime.io_manager.set_output_stream(string_stream)

        solutions = list(self.runtime.query("listing(department/2)."))
        assert len(solutions) == 1

        listing_content = "".join(output_buffer)

        # export実行
        export_file = os.path.join(self.temp_dir, "departments.json")
        solutions = list(
            self.runtime.query(f"export_facts(department/2, json('{export_file}')).")
        )
        assert len(solutions) == 1

        # export内容を読み込み
        with open(export_file, "r", encoding="utf-8") as f:
            export_data = json.load(f)

        # 一貫性を確認
        assert len(export_data) == 3  # 3つのdepartment事実

        for item in export_data:
            dept_name = item["args"][0]
            # listing出力にも含まれていることを確認
            assert dept_name in listing_content

    def test_multiple_predicate_export(self):
        """複数の異なる述語の独立したエクスポート"""
        # 複数のエクスポートを実行
        person_file = os.path.join(self.temp_dir, "persons.csv")
        dept_file = os.path.join(self.temp_dir, "departments.csv")
        project_file = os.path.join(self.temp_dir, "projects.json")

        # 各述語を個別にエクスポート
        solutions1 = list(
            self.runtime.query(f"export_facts(person/3, '{person_file}').")
        )
        solutions2 = list(
            self.runtime.query(f"export_facts(department/2, '{dept_file}').")
        )
        solutions3 = list(
            self.runtime.query(f"export_facts(project/3, json('{project_file}')).")
        )

        # 全て成功することを確認
        assert len(solutions1) == 1
        assert len(solutions2) == 1
        assert len(solutions3) == 1

        # 各ファイルが作成されていることを確認
        assert os.path.exists(person_file)
        assert os.path.exists(dept_file)
        assert os.path.exists(project_file)

        # 内容の妥当性を確認
        with open(person_file, "r") as f:
            person_content = f.read()
            assert "alice" in person_content

        with open(dept_file, "r") as f:
            dept_content = f.read()
            assert "engineering" in dept_content

        with open(project_file, "r") as f:
            project_data = json.load(f)
            assert len(project_data) == 2
            assert project_data[0]["functor"] == "project"

    def test_listing_after_dynamic_changes(self):
        """動的な知識ベース変更後のlisting動作"""
        # 初期状態でlisting
        output_buffer1 = []
        string_stream1 = StringStream(initial_input="", output_buffer=output_buffer1)
        self.runtime.io_manager.set_output_stream(string_stream1)

        solutions = list(self.runtime.query("listing(person/3)."))
        assert len(solutions) == 1
        initial_content = "".join(output_buffer1)

        # 新しい事実を動的に追加
        self.runtime.add_rule("person(diana, 29, analyst).")

        # 再度listing
        output_buffer2 = []
        string_stream2 = StringStream(initial_input="", output_buffer=output_buffer2)
        self.runtime.io_manager.set_output_stream(string_stream2)

        solutions = list(self.runtime.query("listing(person/3)."))
        assert len(solutions) == 1
        updated_content = "".join(output_buffer2)

        # 新しい事実が含まれることを確認
        assert "diana" in updated_content
        assert "analyst" in updated_content

        # 更新前よりも内容が増えていることを確認
        assert len(updated_content) > len(initial_content)

    def test_export_after_dynamic_changes(self):
        """動的な知識ベース変更後のexport動作"""
        # 初期状態でexport
        initial_file = os.path.join(self.temp_dir, "initial_persons.json")
        solutions = list(
            self.runtime.query(f"export_facts(person/3, json('{initial_file}')).")
        )
        assert len(solutions) == 1

        with open(initial_file, "r") as f:
            initial_data = json.load(f)
        initial_count = len(initial_data)

        # 新しい事実を追加
        self.runtime.add_rule("person(eve, 31, manager).")

        # 再度export
        updated_file = os.path.join(self.temp_dir, "updated_persons.json")
        solutions = list(
            self.runtime.query(f"export_facts(person/3, json('{updated_file}')).")
        )
        assert len(solutions) == 1

        with open(updated_file, "r") as f:
            updated_data = json.load(f)

        # データが増えていることを確認
        assert len(updated_data) == initial_count + 1

        # 新しいデータが含まれていることを確認
        eve_found = any(
            item["args"][0] == "eve" and item["args"][2] == "manager"
            for item in updated_data
        )
        assert eve_found

    def test_error_recovery_in_mixed_operations(self):
        """エラー発生時の回復動作テスト"""
        # 正常なlisting
        output_buffer = []
        string_stream = StringStream(initial_input="", output_buffer=output_buffer)
        self.runtime.io_manager.set_output_stream(string_stream)

        solutions = list(self.runtime.query("listing(person/3)."))
        assert len(solutions) == 1

        # 無効なexport（失敗するはず）
        invalid_path = "/proc/definitely/invalid/path/file.csv"
        solutions = list(
            self.runtime.query(f"export_facts(person/3, '{invalid_path}').")
        )
        assert len(solutions) == 0  # 失敗

        # 再度正常なlistingが動作することを確認（状態が破損していない）
        output_buffer2 = []
        string_stream2 = StringStream(initial_input="", output_buffer=output_buffer2)
        self.runtime.io_manager.set_output_stream(string_stream2)

        solutions = list(self.runtime.query("listing(department/2)."))
        assert len(solutions) == 1

        content = "".join(output_buffer2)
        assert "engineering" in content

    def test_complex_query_integration(self):
        """複雑なクエリとの統合テスト"""
        # 複雑なクエリの実行
        solutions = list(self.runtime.query("person(X, Age, Job), Age > 30."))
        assert len(solutions) >= 2  # bob と charlie

        # その後でlisting実行
        output_buffer = []
        string_stream = StringStream(initial_input="", output_buffer=output_buffer)
        self.runtime.io_manager.set_output_stream(string_stream)

        solutions = list(self.runtime.query("listing."))
        assert len(solutions) == 1

        # listingが正常に動作することを確認
        content = "".join(output_buffer)
        assert "person(" in content
        assert "department(" in content

    def test_japanese_integration(self):
        """日本語データとの統合テスト"""
        # 日本語の事実を追加
        self.runtime.add_rule("社員(田中, 35, エンジニア).")
        self.runtime.add_rule("社員(佐藤, 28, デザイナー).")

        # listing実行
        output_buffer = []
        string_stream = StringStream(initial_input="", output_buffer=output_buffer)
        self.runtime.io_manager.set_output_stream(string_stream)

        solutions = list(self.runtime.query("listing."))
        assert len(solutions) == 1

        # export実行
        output_file = os.path.join(self.temp_dir, "japanese_employees.json")
        solutions = list(
            self.runtime.query(f"export_facts(社員/3, json('{output_file}')).")
        )

        # 成功することを確認（具体的な内容は内部実装に依存）
        assert len(solutions) == 1
        assert os.path.exists(output_file)


class TestListingExportPerformance:
    """パフォーマンス関連のテスト"""

    def test_large_knowledge_base_listing(self):
        """大規模知識ベースでのlisting性能テスト"""
        runtime = Runtime()

        # 大量の事実を追加
        for i in range(500):
            runtime.add_rule(f"data({i}, value_{i}, type_{i % 10}).")

        # listing実行（タイムアウトしないことを確認）
        output_buffer = []
        string_stream = StringStream(initial_input="", output_buffer=output_buffer)
        runtime.io_manager.set_output_stream(string_stream)

        solutions = list(runtime.query("listing(data/3)."))
        assert len(solutions) == 1

        # 出力内容が妥当であることを確認
        content = "".join(output_buffer)
        assert "data(" in content
        assert len(content) > 1000  # 相応のサイズ

    def test_large_dataset_export(self):
        """大規模データセットのexport性能テスト"""
        runtime = Runtime()

        # 大量の事実を追加
        for i in range(1000):
            runtime.add_rule(f"item({i}, 'name_{i}', {i * 1.5}).")

        # export実行
        temp_dir = tempfile.mkdtemp()
        try:
            output_file = os.path.join(temp_dir, "large_export.csv")

            solutions = list(runtime.query(f"export_facts(item/3, '{output_file}')."))
            assert len(solutions) == 1

            # ファイルが作成され、適切なサイズであることを確認
            assert os.path.exists(output_file)
            file_size = os.path.getsize(output_file)
            assert file_size > 10000  # 相応のファイルサイズ

        finally:
            import shutil

            shutil.rmtree(temp_dir, ignore_errors=True)
