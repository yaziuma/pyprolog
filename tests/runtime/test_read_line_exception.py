"""
テスト: read_line述語での例外伝播確認

PyPrologの修正後、read_line述語でも例外が正常に伝播することを確認するテスト
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


def test_direct_read_line():
    """直接read_line述語のテスト"""
    runtime = Runtime()
    runtime.io_manager = InteractiveIOManager()
    
    with pytest.raises(PrologInputRequiredException) as excinfo:
        runtime.query("read_line(X).")
    
    assert "Input required: line for X" in str(excinfo.value)
    assert excinfo.value.input_type == "line"
    assert excinfo.value.variable == "X"


def test_nested_read_line():
    """ネストされたread_line述語のテスト"""
    prolog_code = """
    start_input :- 
        write('Starting input'), nl,
        ask_for_line(1).

    ask_for_line(ID) :-
        write('Enter line: '),
        read_line(Input),
        write('Got: '), write(Input).
    """
    
    runtime = Runtime()
    runtime.io_manager = InteractiveIOManager()
    
    # ルールを追加
    assert runtime.add_rule(prolog_code), "Prologプログラムの読み込み失敗"
    
    # 修正後は例外が正常に伝播されるはず
    with pytest.raises(PrologInputRequiredException) as excinfo:
        runtime.query("start_input.")
    
    assert "Input required: line for X" in str(excinfo.value)
    assert excinfo.value.input_type == "line"


def test_mixed_io_get_char_then_read_line():
    """混合IOテスト: get_char → read_line"""
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


def test_mixed_io_read_line_then_get_char():
    """混合IOテスト: read_line → get_char"""
    prolog_code = """
    mixed_input_reverse :- 
        write('First read line'), nl,
        read_line(L),
        write('Then get char'), nl,
        get_char(C).
    """
    
    runtime = Runtime()
    runtime.io_manager = InteractiveIOManager()
    
    assert runtime.add_rule(prolog_code), "Prologプログラムの読み込み失敗"
    
    # read_lineで先に例外が発生するはず
    with pytest.raises(PrologInputRequiredException) as excinfo:
        runtime.query("mixed_input_reverse.")
    
    assert excinfo.value.input_type == "line"


def test_deeply_nested_read_line():
    """深くネストされたread_line述語のテスト"""
    prolog_code = """
    deep_level1 :- deep_level2.
    deep_level2 :- deep_level3.
    deep_level3 :- deep_level4.
    deep_level4 :- read_line(Line).
    """
    
    runtime = Runtime()
    runtime.io_manager = InteractiveIOManager()
    
    assert runtime.add_rule(prolog_code), "Prologプログラムの読み込み失敗"
    
    # 深いネストでも例外が正常に伝播されるはず
    with pytest.raises(PrologInputRequiredException) as excinfo:
        runtime.query("deep_level1.")
    
    assert excinfo.value.input_type == "line"