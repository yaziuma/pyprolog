from enum import Enum, auto


class TokenType(Enum):
    ATOM = (auto(),)
    VARIABLE = (auto(),)
    NUMBER = (auto(),)
    LEFTPAREN = (auto(),)
    RIGHTPAREN = (auto(),)
    COLONMINUS = (auto(),)
    COMMA = (auto(),)
    DOT = (auto(),)
    UNDERSCORE = (auto(),)
    SINGLEQUOTE = (auto(),)
    FAIL = (auto(),)
    WRITE = (auto(),)
    NL = (auto(),)
    TAB = (auto(),)
    IS = (auto(),)
    PLUS = (auto(),)
    MINUS = (auto(),)
    SLASH = (auto(),)
    STAR = (auto(),)
    GREATER = (auto(),)
    LESS = (auto(),)
    GREATEREQUAL = (auto(),)
    EQUALLESS = (auto(),)
    EQUALEQUAL = (auto(),)
    EQUALSLASH = (auto(),)
    RETRACT = (auto(),)
    ASSERTA = (auto(),)
    ASSERTZ = (auto(),)
    CUT = (auto(),)
    LEFTBRACKET = (auto(),)
    RIGHTBRACKET = (auto(),)
    BAR = (auto(),)
    TRUE = (auto(),)  # true アトム用
    EQUAL = (auto(),)  # = 演算子用
    MOD = (auto(),)  # mod 演算子用
    DIV = (auto(),)  # // または div 演算子用
    EOF = auto()
