"""
統一入力システム対応入出力述語

IOPredicate基底クラスを継承した入出力述語の具象実装
"""

from typing import Optional
from pyprolog.core.types import PrologType, Atom, Number
from pyprolog.runtime.io_predicate import IOPredicate


class GetCharPredicate(IOPredicate):
    """get_char/1述語 - 統一入力システム対応版"""
    
    def _get_expected_arg_count(self) -> int:
        return 1
    
    def _get_predicate_name(self) -> str:
        return "get_char"
    
    def _get_input_type(self) -> str:
        return "char"
    
    def _convert_to_prolog_term(self, input_value: Optional[str]) -> PrologType:
        """
        文字入力のPrologターム変換
        
        変換ルール:
        - EOF (None or "") → Atom("end_of_file")
        - 数字文字 → Number
        - その他文字 → Atom
        - 複数文字の場合は最初の文字のみ使用
        """
        if input_value is None or input_value == "":
            return self._handle_eof()
        
        # 最初の文字のみ使用
        char = input_value[0] if len(input_value) > 0 else ""
        
        if char.isdigit():
            return Number(int(char))
        else:
            return Atom(char)
    
    def _get_prompt(self) -> str:
        return "文字を入力してください: "


class ReadLinePredicate(IOPredicate):
    """read_line/1述語 - 統一入力システム対応版"""
    
    def _get_expected_arg_count(self) -> int:
        return 1
    
    def _get_predicate_name(self) -> str:
        return "read_line"
    
    def _get_input_type(self) -> str:
        return "line"
    
    def _convert_to_prolog_term(self, input_value: Optional[str]) -> PrologType:
        """
        行入力のPrologターム変換
        
        変換ルール:
        - EOF (None) → Atom("end_of_file")  
        - 数値変換可能 → Number
        - その他 → Atom
        """
        if input_value is None:
            return self._handle_eof()
        
        # 数値変換試行
        number_term = self._try_convert_to_number(input_value)
        return number_term if number_term else Atom(input_value)
    
    def _get_prompt(self) -> str:
        return "行を入力してください: "


class PeekCharPredicate(IOPredicate):
    """peek_char/1述語 - 統一入力システム対応版（非破壊的読み取り）"""
    
    def _get_expected_arg_count(self) -> int:
        return 1
    
    def _get_predicate_name(self) -> str:
        return "peek_char"
    
    def _get_input_type(self) -> str:
        return "peek_char"
    
    def _convert_to_prolog_term(self, input_value: Optional[str]) -> PrologType:
        """覗き見文字のPrologターム変換"""
        if input_value is None or input_value == "":
            return self._handle_eof()
        
        # peek_charは通常最初の文字を返す
        char = input_value[0] if len(input_value) > 0 else ""
        return Atom(char)
    
    def _get_additional_request_params(self):
        """非破壊的読み取りフラグ"""
        return {"non_destructive": True}
    
    def _get_prompt(self) -> str:
        return "peek_char: "