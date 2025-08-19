"""
テスト: PyPrologのネストされた述語における例外伝播の検証

修正前の問題:
- 直接述語: runtime.query("get_char(X).") → 例外が正常に伝播される
- ネスト述語: runtime.query("start_diagnosis.") → 例外がキャッチされ、[]が返される

修正後の期待動作:
- すべての場合で例外が正常に伝播される
"""

import pytest
from pyprolog.runtime.interpreter import Runtime
from pyprolog.runtime.io_manager import IOManager


class PrologInputRequiredException(Exception):
    """カスタム例外：インタラクティブ入力が必要"""

    def __init__(self, input_type: str, variable: str):
        self.input_type = input_type
        self.variable = variable
        super().__init__(f"Input required: {input_type} for {variable}")


class InteractiveIOManager(IOManager):
    """カスタムIOManager：入力要求時に例外を発生させる"""

    def __init__(self):
        super().__init__()

    def read_char_from_current(self) -> str:
        """文字入力時に例外を発生"""
        raise PrologInputRequiredException(input_type="char", variable="X")

    def read_line_from_current(self) -> str:
        """行入力時に例外を発生"""
        raise PrologInputRequiredException(input_type="line", variable="X")


def test_direct_get_char_exception():
    """直接get_char述語での例外伝播テスト"""
    runtime = Runtime()
    runtime.io_manager = InteractiveIOManager()

    with pytest.raises(PrologInputRequiredException) as excinfo:
        runtime.query("get_char(X).")

    assert "Input required: char for X" in str(excinfo.value)
    assert excinfo.value.input_type == "char"
    assert excinfo.value.variable == "X"


def test_nested_predicate_exception():
    """ネストされた述語での例外伝播テスト"""
    # Prologプログラムを定義
    prolog_code = """
    start_diagnosis :- 
        write('Starting diagnosis'), nl,
        ask_question(1).

    ask_question(ID) :-
        write('Enter input: '),
        get_char(Input).
    """

    runtime = Runtime()
    runtime.io_manager = InteractiveIOManager()

    # ルールを追加
    assert runtime.add_rule(prolog_code), "Prologプログラムの読み込み失敗"

    # 修正後は例外が正常に伝播されるはず
    with pytest.raises(PrologInputRequiredException) as excinfo:
        runtime.query("start_diagnosis.")

    assert "Input required: char for X" in str(excinfo.value)
    assert excinfo.value.input_type == "char"


def test_deeper_nesting_exception():
    """より深いネストでの例外伝播テスト"""
    prolog_code = """
    level1 :- level2.
    level2 :- level3.
    level3 :- get_char(X).
    """

    runtime = Runtime()
    runtime.io_manager = InteractiveIOManager()

    assert runtime.add_rule(prolog_code), "Prologプログラムの読み込み失敗"

    # 深いネストでも例外が正常に伝播されるはず
    with pytest.raises(PrologInputRequiredException) as excinfo:
        runtime.query("level1.")

    assert "Input required: char for X" in str(excinfo.value)
    assert excinfo.value.input_type == "char"


def test_direct_read_line_exception():
    """直接read_line述語での例外伝播テスト"""
    runtime = Runtime()
    runtime.io_manager = InteractiveIOManager()

    with pytest.raises(PrologInputRequiredException) as excinfo:
        runtime.query("read_line(X).")

    assert "Input required: line for X" in str(excinfo.value)
    assert excinfo.value.input_type == "line"
    assert excinfo.value.variable == "X"


def test_nested_read_line_exception():
    """ネストされたread_line述語での例外伝播テスト"""
    prolog_code = """
    start_input :- 
        write('Starting input'), nl,
        ask_for_line(1).

    ask_for_line(ID) :-
        write('Enter line: '),
        read_line(Input).
    """

    runtime = Runtime()
    runtime.io_manager = InteractiveIOManager()

    assert runtime.add_rule(prolog_code), "Prologプログラムの読み込み失敗"

    with pytest.raises(PrologInputRequiredException) as excinfo:
        runtime.query("start_input.")

    assert "Input required: line for X" in str(excinfo.value)
    assert excinfo.value.input_type == "line"


def test_mixed_io_operations():
    """get_charとread_lineの混合テスト"""
    prolog_code = """
    mixed_input :- 
        write('First get char'), nl,
        get_char(C),
        write('Then read line'), nl,
        read_line(L).
    """

    runtime = Runtime()
    runtime.io_manager = InteractiveIOManager()

    assert runtime.add_rule(prolog_code), "Prologプログラムの読み込み失敗"

    # get_charで先に例外が発生するはず
    with pytest.raises(PrologInputRequiredException) as excinfo:
        runtime.query("mixed_input.")

    assert excinfo.value.input_type == "char"
