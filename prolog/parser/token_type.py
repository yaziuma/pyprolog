# prolog/parser/token_type.py
from enum import Enum

class TokenType(Enum):
    # 基本トークン
    ATOM = "ATOM"
    VARIABLE = "VARIABLE" 
    NUMBER = "NUMBER"
    STRING = "STRING"
    
    # 区切り文字
    LEFTPAREN = "LEFTPAREN"
    RIGHTPAREN = "RIGHTPAREN"
    LEFTBRACKET = "LEFTBRACKET"
    RIGHTBRACKET = "RIGHTBRACKET"
    COMMA = "COMMA"
    DOT = "DOT"
    BAR = "BAR"
    
    # 制御構造
    COLONMINUS = "COLONMINUS"  # :-
    UNDERSCORE = "UNDERSCORE"  # _
    
    # 特殊述語
    TRUE = "TRUE"
    FAIL = "FAIL"
    RETRACT = "RETRACT"
    ASSERTA = "ASSERTA"
    ASSERTZ = "ASSERTZ"
    
    EOF = "EOF"

# 演算子トークンを動的に追加する関数
def initialize_operator_tokens():
    """演算子レジストリからTokenTypeを動的に生成"""
    # 遅延インポートで循環参照を回避
    from prolog.core.operators import operator_registry
    
    # 各演算子のトークンタイプを動的に追加
    for symbol, op_info in operator_registry._operators.items():
        if op_info.token_type and not hasattr(TokenType, op_info.token_type):
            # Enumに新しいメンバーを動的に追加
            new_token = op_info.token_type
            setattr(TokenType, new_token, new_token)
            # Enumの内部辞書も更新
            TokenType._member_map_[new_token] = getattr(TokenType, new_token)
            TokenType._value2member_map_[new_token] = getattr(TokenType, new_token)

# モジュール初期化時ではなく、必要時に呼び出す
