from enum import Enum, auto
from prolog.core.operators import operator_registry


class TokenType(Enum):
    # 基本トークン
    ATOM = auto()
    VARIABLE = auto()
    NUMBER = auto()
    STRING = auto()

    # 区切り文字
    LEFTPAREN = auto()
    RIGHTPAREN = auto()
    LEFTBRACKET = auto()
    RIGHTBRACKET = auto()
    COMMA = auto()
    DOT = auto()
    BAR = auto()

    # 制御構造
    COLONMINUS = auto()  # :-
    UNDERSCORE = auto()  # _

    # 特殊な述語/キーワード
    TRUE = auto()
    FAIL = auto()
    RETRACT = auto()
    ASSERTA = auto()
    ASSERTZ = auto()
    LESSEQUAL = auto()  # `<=' とは別に必要になる場合があるため (例: アトムとして)

    # 演算子トークン（動的生成）
    # これらは operator_registry から自動生成される

    EOF = auto()


# 演算子トークンを動的に追加
def _initialize_operator_tokens():
    """演算子レジストリからTokenTypeを動的に生成"""
    for symbol, op_info in operator_registry._operators.items():
        if op_info.token_type:
            # TokenTypeに動的に追加
            # Enumのメンバーとして追加するために、auto()の代わりに一意の値を割り当てる
            # ここでは、既存のメンバーの数に基づいて値を割り当てる
            new_value = len(TokenType) + 1
            setattr(TokenType, op_info.token_type, new_value)
            # Enumの_member_map_も更新する必要がある
            TokenType._member_map_[op_info.token_type] = TokenType(new_value)
            TokenType._value2member_map_[new_value] = TokenType(new_value)


_initialize_operator_tokens()
