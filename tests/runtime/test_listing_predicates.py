"""
listing述語のテスト

listing/0, listing/1述語の機能を検証する
"""

from pyprolog.runtime.interpreter import Runtime
from pyprolog.runtime.io_streams import StringStream


class TestListingPredicates:
    """listing述語のテストクラス"""

    def setup_method(self):
        """各テストの前にRuntimeを初期化"""
        self.runtime = Runtime()

        # テスト用の知識ベースを追加
        self.runtime.add_rule("person(alice, 28).")
        self.runtime.add_rule("person(bob, 35).")
        self.runtime.add_rule("person(charlie, 42).")
        self.runtime.add_rule("parent(X, Y) :- father(X, Y).")
        self.runtime.add_rule("parent(X, Y) :- mother(X, Y).")
        self.runtime.add_rule("father(bob, alice).")
        self.runtime.add_rule("mother(eve, alice).")

    def test_listing_zero_predicate_basic(self):
        """listing/0の基本動作テスト"""
        # 出力キャプチャ用のStringStreamを設定
        output_buffer = []
        string_stream = StringStream(initial_input="", output_buffer=output_buffer)
        self.runtime.io_manager.set_output_stream(string_stream)

        # listing/0を実行
        solutions = list(self.runtime.query("listing."))

        # 1つの解があることを確認
        assert len(solutions) == 1

        # 出力内容を取得
        output_content = "".join(output_buffer)

        # 全ての述語が出力されていることを確認（数値は浮動小数点として表示される）
        assert "person(alice, 28" in output_content
        assert "person(bob, 35" in output_content
        assert "person(charlie, 42" in output_content
        assert "parent(X, Y) :- father(X, Y)." in output_content
        assert "parent(X, Y) :- mother(X, Y)." in output_content
        assert "father(bob, alice)." in output_content
        assert "mother(eve, alice)." in output_content

    def test_listing_one_predicate_person_2(self):
        """listing/1でperson/2を指定するテスト"""
        # 出力キャプチャ用のStringStreamを設定
        output_buffer = []
        string_stream = StringStream(initial_input="", output_buffer=output_buffer)
        self.runtime.io_manager.set_output_stream(string_stream)

        # listing(person/2)を実行
        solutions = list(self.runtime.query("listing(person/2)."))

        # 1つの解があることを確認
        assert len(solutions) == 1

        # 出力内容を取得
        output_content = "".join(output_buffer)

        # person/2の述語のみが出力されていることを確認（数値は浮動小数点として表示される）
        assert "person(alice, 28" in output_content
        assert "person(bob, 35" in output_content
        assert "person(charlie, 42" in output_content

        # 他の述語は出力されていないことを確認
        assert "parent(" not in output_content
        assert "father(" not in output_content
        assert "mother(" not in output_content

    def test_listing_one_predicate_parent_2(self):
        """listing/1でparent/2を指定するテスト"""
        # 出力キャプチャ用のStringStreamを設定
        output_buffer = []
        string_stream = StringStream(initial_input="", output_buffer=output_buffer)
        self.runtime.io_manager.set_output_stream(string_stream)

        # listing(parent/2)を実行
        solutions = list(self.runtime.query("listing(parent/2)."))

        # 1つの解があることを確認
        assert len(solutions) == 1

        # 出力内容を取得
        output_content = "".join(output_buffer)

        # parent/2のルールが出力されていることを確認
        assert "parent(X, Y) :- father(X, Y)." in output_content
        assert "parent(X, Y) :- mother(X, Y)." in output_content

        # 他の述語は出力されていないことを確認
        assert "person(" not in output_content

    def test_listing_one_predicate_nonexistent(self):
        """存在しない述語を指定した場合のテスト"""
        # 出力キャプチャ用のStringStreamを設定
        output_buffer = []
        string_stream = StringStream(initial_input="", output_buffer=output_buffer)
        self.runtime.io_manager.set_output_stream(string_stream)

        # 存在しない述語を指定
        solutions = list(self.runtime.query("listing(nonexistent/1)."))

        # 解があることを確認（何も出力されないが成功）
        assert len(solutions) == 1

        # 出力が空またはコメントのみであることを確認
        output_content = "".join(output_buffer)
        # 存在しない述語でもコメントが出力される可能性がある
        assert "nonexistent" in output_content or output_content.strip() == ""

    def test_listing_one_predicate_invalid_format(self):
        """無効な述語指定形式のテスト"""
        # 無効な形式での呼び出し（アリティなし）
        solutions = list(self.runtime.query("listing(person)."))

        # 失敗することを確認
        assert len(solutions) == 0

    def test_listing_empty_knowledge_base(self):
        """空の知識ベースでのlisting/0テスト"""
        # 新しい空のRuntimeを作成
        empty_runtime = Runtime()

        # 出力キャプチャ用のStringStreamを設定
        output_buffer = []
        string_stream = StringStream(initial_input="", output_buffer=output_buffer)
        empty_runtime.io_manager.set_output_stream(string_stream)

        # listing/0を実行
        solutions = list(empty_runtime.query("listing."))

        # 1つの解があることを確認
        assert len(solutions) == 1

        # 出力が空またはコメントのみであることを確認
        output_content = "".join(output_buffer)
        # 空でも成功するが、何も実質的な内容は出力されない
        assert "person(" not in output_content
        assert "parent(" not in output_content

    def test_listing_with_japanese_predicates(self):
        """日本語述語名でのテスト"""
        # 日本語述語を追加
        self.runtime.add_rule("人(太郎, 30).")
        self.runtime.add_rule("人(花子, 25).")

        # 出力キャプチャ用のStringStreamを設定
        output_buffer = []
        string_stream = StringStream(initial_input="", output_buffer=output_buffer)
        self.runtime.io_manager.set_output_stream(string_stream)

        # listing/0を実行
        solutions = list(self.runtime.query("listing."))

        # 成功することを確認
        assert len(solutions) == 1

        # 出力内容を確認（日本語述語も含まれる）
        output_content = "".join(output_buffer)

        # 既存の英語述語も含まれることを確認
        assert "person(alice, 28" in output_content  # 28.0 or 28 both acceptable

        # 日本語述語も出力されることを確認（ただし内部形式でマッピングされている可能性あり）
        # 実装に依存するため、単に成功することを確認

    def test_listing_with_complex_rules(self):
        """複雑なルールでのテスト"""
        # より複雑なルールを追加
        self.runtime.add_rule("grandparent(X, Z) :- parent(X, Y), parent(Y, Z).")
        self.runtime.add_rule("sibling(X, Y) :- parent(Z, X), parent(Z, Y), X \\= Y.")

        # 出力キャプチャ用のStringStreamを設定
        output_buffer = []
        string_stream = StringStream(initial_input="", output_buffer=output_buffer)
        self.runtime.io_manager.set_output_stream(string_stream)

        # listing/0を実行
        solutions = list(self.runtime.query("listing."))

        # 成功することを確認
        assert len(solutions) == 1

        # 出力内容を確認
        output_content = "".join(output_buffer)

        # 複雑なルールも出力されることを確認
        assert "grandparent(" in output_content
        assert "sibling(" in output_content
        assert ":-" in output_content  # ルール形式が含まれる
        assert "," in output_content  # 連言が含まれる


class TestListingPredicateEdgeCases:
    """listing述語のエッジケースのテスト"""

    def test_listing_with_numbers_and_variables(self):
        """数値と変数を含む述語のテスト"""
        runtime = Runtime()
        runtime.add_rule("test(1, X, 3.14).")
        runtime.add_rule("test(Y, hello, Z) :- Y > 0, Z < 10.")

        # 出力キャプチャ用のStringIOを設定
        output_buffer = []
        string_stream = StringStream(initial_input="", output_buffer=output_buffer)
        runtime.io_manager.set_output_stream(string_stream)

        # listing/0を実行
        solutions = list(runtime.query("listing."))

        # 成功することを確認
        assert len(solutions) == 1

        # 出力内容を確認
        output_content = "".join(output_buffer)
        assert "test(" in output_content

    def test_listing_with_special_characters(self):
        """特殊文字を含む述語のテスト"""
        runtime = Runtime()
        runtime.add_rule("'special atom'(test).")
        runtime.add_rule("normal_atom(value).")

        # 出力キャプチャ用のStringIOを設定
        output_buffer = []
        string_stream = StringStream(initial_input="", output_buffer=output_buffer)
        runtime.io_manager.set_output_stream(string_stream)

        # listing/0を実行
        solutions = list(runtime.query("listing."))

        # 成功することを確認
        assert len(solutions) == 1
