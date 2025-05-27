from enum import Enum, auto
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable

class OperatorType(Enum):
    """演算子の種類"""
    ARITHMETIC = auto()      # 算術演算子 (+, -, *, /, mod, etc.)
    COMPARISON = auto()      # 比較演算子 (=:=, =\=, >, <, etc.)
    LOGICAL = auto()         # 論理演算子 (=, \=, ==, \==)
    STRUCTURAL = auto()      # 構造演算子 (=.., functor, etc.)
    CONTROL = auto()         # 制御演算子 (!, cut)
    IO = auto()             # 入出力演算子 (write, nl, etc.)

class Associativity(Enum):
    """結合性"""
    LEFT = auto()
    RIGHT = auto()
    NON = auto()

@dataclass
class OperatorInfo:
    """演算子情報"""
    symbol: str                    # 演算子記号
    precedence: int               # 優先度 (低い数値 = 高い優先度)
    associativity: Associativity  # 結合性
    operator_type: OperatorType   # 演算子種別
    arity: int                    # アリティ (1=単項, 2=二項)
    evaluator: Optional[Callable] # 評価関数
    token_type: Optional[str]     # 対応するTokenType
    
class OperatorRegistry:
    """演算子レジストリ - 全演算子を一元管理"""
    
    def __init__(self):
        self._operators: Dict[str, OperatorInfo] = {}
        self._precedence_groups: Dict[int, List[OperatorInfo]] = {}
        self._type_groups: Dict[OperatorType, List[OperatorInfo]] = {}
        self._initialize_builtin_operators()
    
    def _initialize_builtin_operators(self):
        """組み込み演算子の初期化"""
        builtin_ops = [
            # 算術演算子 (優先度: ISO Prolog準拠)
            OperatorInfo("**", 200, Associativity.RIGHT, OperatorType.ARITHMETIC, 2, None, "POWER"),
            OperatorInfo("*", 400, Associativity.LEFT, OperatorType.ARITHMETIC, 2, None, "STAR"),
            OperatorInfo("/", 400, Associativity.LEFT, OperatorType.ARITHMETIC, 2, None, "SLASH"),
            OperatorInfo("//", 400, Associativity.LEFT, OperatorType.ARITHMETIC, 2, None, "DIV"),
            OperatorInfo("mod", 400, Associativity.LEFT, OperatorType.ARITHMETIC, 2, None, "MOD"),
            OperatorInfo("+", 500, Associativity.LEFT, OperatorType.ARITHMETIC, 2, None, "PLUS"),
            OperatorInfo("-", 500, Associativity.LEFT, OperatorType.ARITHMETIC, 2, None, "MINUS"),
            
            # 比較演算子
            OperatorInfo("=:=", 700, Associativity.NON, OperatorType.COMPARISON, 2, None, "EQUALCOLONEQUAL"),
            OperatorInfo("=\\=", 700, Associativity.NON, OperatorType.COMPARISON, 2, None, "EQUALSLASHEQUAL"),
            OperatorInfo("<", 700, Associativity.NON, OperatorType.COMPARISON, 2, None, "LESS"),
            OperatorInfo("=<", 700, Associativity.NON, OperatorType.COMPARISON, 2, None, "EQUALLESS"),
            OperatorInfo(">", 700, Associativity.NON, OperatorType.COMPARISON, 2, None, "GREATER"),
            OperatorInfo(">=", 700, Associativity.NON, OperatorType.COMPARISON, 2, None, "GREATEREQUAL"),
            
            # 論理演算子
            OperatorInfo("=", 700, Associativity.NON, OperatorType.LOGICAL, 2, None, "EQUAL"),
            OperatorInfo("\\=", 700, Associativity.NON, OperatorType.LOGICAL, 2, None, "NOTEQUAL"),
            OperatorInfo("==", 700, Associativity.NON, OperatorType.LOGICAL, 2, None, "EQUALEQUAL"),
            OperatorInfo("\\==", 700, Associativity.NON, OperatorType.LOGICAL, 2, None, "NOTEQUALEQUAL"),
            
            # 特殊演算子
            OperatorInfo("is", 700, Associativity.NON, OperatorType.ARITHMETIC, 2, None, "IS"),
            OperatorInfo("!", 200, Associativity.NON, OperatorType.CONTROL, 1, None, "CUT"),
        ]
        
        for op in builtin_ops:
            self.register_operator(op)
    
    def register_operator(self, operator_info: OperatorInfo):
        """演算子を登録"""
        self._operators[operator_info.symbol] = operator_info
        
        # 優先度グループに追加
        if operator_info.precedence not in self._precedence_groups:
            self._precedence_groups[operator_info.precedence] = []
        self._precedence_groups[operator_info.precedence].append(operator_info)
        
        # 種別グループに追加
        if operator_info.operator_type not in self._type_groups:
            self._type_groups[operator_info.operator_type] = []
        self._type_groups[operator_info.operator_type].append(operator_info)
    
    def get_operator(self, symbol: str) -> Optional[OperatorInfo]:
        """演算子情報を取得"""
        return self._operators.get(symbol)
    
    def get_operators_by_type(self, op_type: OperatorType) -> List[OperatorInfo]:
        """指定タイプの演算子一覧を取得"""
        return self._type_groups.get(op_type, [])
    
    def get_operators_by_precedence(self, precedence: int) -> List[OperatorInfo]:
        """指定優先度の演算子一覧を取得"""
        return self._precedence_groups.get(precedence, [])
    
    def is_operator(self, symbol: str) -> bool:
        """指定文字列が演算子かどうか判定"""
        return symbol in self._operators
    
    def get_precedence(self, symbol: str) -> Optional[int]:
        """演算子の優先度を取得"""
        op = self.get_operator(symbol)
        return op.precedence if op else None

# グローバルインスタンス
operator_registry = OperatorRegistry()
