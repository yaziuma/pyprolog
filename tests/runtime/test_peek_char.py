# tests/runtime/test_peek_char.py
import pytest
from pyprolog.runtime.io_streams import StringStream
from pyprolog.runtime.unified_input_system import StreamInputHandler
from pyprolog.runtime.interpreter import Runtime
from pyprolog.core.types import Variable, Atom


class TestStringStreamPeekOperations:
    """StringStreamのpeek機能テスト"""

    def test_peek_char_basic(self):
        """基本的なpeek_char動作"""
        stream = StringStream("hello")

        # 最初の文字をpeek
        assert stream.peek_char() == "h"

        # 位置が変わらないことを確認
        assert stream.peek_char() == "h"

        # 実際に読み取った後
        assert stream.read_char() == "h"
        assert stream.peek_char() == "e"

    def test_peek_char_at_eof(self):
        """EOF時のpeek_char動作"""
        stream = StringStream("a")

        # 文字を読み取り
        assert stream.read_char() == "a"

        # EOF時のpeek
        assert stream.peek_char() == ""
        assert stream.at_end_of_stream() is True

    def test_peek_char_empty_stream(self):
        """空ストリームでのpeek"""
        stream = StringStream("")

        assert stream.peek_char() == ""
        assert stream.at_end_of_stream() is True

    def test_peek_char_multibyte(self):
        """マルチバイト文字のpeek"""
        stream = StringStream("こんにちは")
        assert stream.peek_char() == "こ"
        assert stream.read_char() == "こ"
        assert stream.peek_char() == "ん"

    def test_at_end_of_stream_progression(self):
        """at_end_of_streamの状態変化"""
        stream = StringStream("ab")

        assert stream.at_end_of_stream() is False

        # 1文字ずつ読み取りながら確認
        assert stream.peek_char() == "a"
        assert stream.at_end_of_stream() is False
        stream.read_char()

        assert stream.peek_char() == "b"
        assert stream.at_end_of_stream() is False
        stream.read_char()

        assert stream.at_end_of_stream() is True

    def test_supports_peek_operations(self):
        """peek操作サポート確認"""
        stream = StringStream("test")
        assert stream.supports_peek_operations() is True

    def test_get_stream_status(self):
        """ストリーム状態情報の取得"""
        stream = StringStream("hello")
        status = stream.get_stream_status()

        assert status.at_eof is False
        assert status.has_data_available is True
        assert status.supports_peek is True
        assert status.stream_type == "StringStream"
        assert status.has_errors is False


class TestPeekCharPredicate:
    """PeekCharPredicate述語のテスト"""

    def test_peek_char_unification_success(self):
        """peek_char/1の成功ケース"""
        runtime = Runtime()
        runtime.io_manager.set_input_handler(StreamInputHandler(StringStream("abc")))

        solutions = runtime.query("peek_char(X)")

        assert len(solutions) == 1
        assert solutions[0][Variable("X")] == Atom("a")

        # 再度実行しても同じ結果
        solutions2 = runtime.query("peek_char(Y)")
        assert solutions2[0][Variable("Y")] == Atom("a")

    def test_peek_char_unification_failure(self):
        """peek_char/1の失敗ケース"""
        runtime = Runtime()
        runtime.io_manager.set_input_handler(StreamInputHandler(StringStream("abc")))

        solutions = runtime.query("peek_char(z)")  # 'a'と'z'は一致しない

        assert len(solutions) == 0

    def test_peek_char_eof(self):
        """EOF時のpeek_char/1"""
        runtime = Runtime()
        runtime.io_manager.set_input_handler(StreamInputHandler(StringStream("")))

        solutions = runtime.query("peek_char(X)")

        assert len(solutions) == 1
        assert solutions[0][Variable("X")] == Atom("end_of_file")

    def test_peek_char_mixed_operations(self):
        """peek_charとget_charの混在操作"""
        runtime = Runtime()
        stream = StringStream("abcde")
        runtime.io_manager.set_input_handler(StreamInputHandler(stream))

        # peek -> get -> peek -> get のパターン
        peek1 = runtime.query("peek_char(X1)")  # 'a'
        get1 = runtime.query("get_char(Y1)")  # 'a' (消費)
        peek2 = runtime.query("peek_char(X2)")  # 'b'
        get2 = runtime.query("get_char(Y2)")  # 'b' (消費)

        assert peek1[0][Variable("X1")] == Atom("a")
        assert get1[0][Variable("Y1")] == Atom("a")
        assert peek2[0][Variable("X2")] == Atom("b")
        assert get2[0][Variable("Y2")] == Atom("b")


class TestAtEndOfStreamPredicate:
    """AtEndOfStreamPredicate述語のテスト"""

    def test_at_end_of_stream_false(self):
        """データがある場合の動作"""
        runtime = Runtime()
        runtime.io_manager.set_input_handler(StreamInputHandler(StringStream("data")))

        solutions = runtime.query("at_end_of_stream")

        assert len(solutions) == 0  # 失敗

    def test_at_end_of_stream_true(self):
        """EOFの場合の動作"""
        runtime = Runtime()
        runtime.io_manager.set_input_handler(StreamInputHandler(StringStream("")))

        solutions = runtime.query("at_end_of_stream")

        assert len(solutions) == 1  # 成功

    def test_at_end_of_stream_progression(self):
        """読み取り進行中のEOF状態変化"""
        runtime = Runtime()
        stream = StringStream("a")
        runtime.io_manager.set_input_handler(StreamInputHandler(stream))

        # データがあるときは失敗
        solutions1 = runtime.query("at_end_of_stream")
        assert len(solutions1) == 0

        # 文字を読み取り
        runtime.query("get_char(X)")

        # EOF到達後は成功
        solutions2 = runtime.query("at_end_of_stream")
        assert len(solutions2) == 1


class TestConditionalReading:
    """条件付き読み取りパターンのテスト"""

    def test_conditional_reading(self):
        """条件付き読み取りパターン"""
        runtime = Runtime()

        # 数字判定ルールを追加
        runtime.add_rule("""
        read_if_digit(Char) :-
            peek_char(Next),
            Next >= '0',
            Next =< '9',
            get_char(Char).
        """)

        # テストケース1: 数字がある場合
        runtime.io_manager.set_input_handler(StreamInputHandler(StringStream("5abc")))
        solutions = runtime.query("read_if_digit(X)")
        assert len(solutions) == 1
        # Check if get_char returns a character - could be Atom or Number depending on implementation
        result = solutions[0][Variable("X")]
        assert result == Atom("5") or result == 5 or str(result) == "5"

        # テストケース2: 数字がない場合
        runtime.io_manager.set_input_handler(StreamInputHandler(StringStream("abc")))
        solutions = runtime.query("read_if_digit(Y)")
        assert len(solutions) == 0


@pytest.mark.timeout(1)
def test_basic_functionality():
    """基本機能の動作確認"""
    runtime = Runtime()
    stream = StringStream("hello")
    runtime.io_manager.set_input_handler(StreamInputHandler(stream))

    # peek_char使用
    peek_result = runtime.query("peek_char(X)")
    assert peek_result[0][Variable("X")] == Atom("h")

    # EOF確認
    eof_result = runtime.query("at_end_of_stream")
    assert len(eof_result) == 0  # False（まだデータあり）
