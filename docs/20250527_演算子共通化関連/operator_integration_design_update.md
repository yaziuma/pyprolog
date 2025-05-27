# 演算子統合設計の完全実装更新

## 設計哲学

**演算子統合設計の価値を100%実現し、Prologインタープリターの拡張性と保守性を最大化する**

## Phase 1: 核心システムの完全実装

### 1.1 `prolog/core/operators.py` - 演算子レジストリの強化

```python
# prolog/core/operators.py
from enum import Enum, auto
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable, Any
import logging

logger = logging.getLogger(__name__)

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
    token_type: str              # 対応するTokenType名（必須）
    
    def __post_init__(self):
        """初期化後の検証"""
        if not self.token_type:
            raise ValueError(f"Operator {self.symbol} must have token_type")
        if self.precedence < 1 or self.precedence > 1200:
            raise ValueError(f"Operator precedence must be between 1-1200, got {self.precedence}")

class OperatorRegistry:
    """演算子レジストリ - 全演算子を一元管理"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """シングルトンパターンで実装"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._operators: Dict[str, OperatorInfo] = {}
        self._precedence_groups: Dict[int, List[OperatorInfo]] = {}
        self._type_groups: Dict[OperatorType, List[OperatorInfo]] = {}
        self._token_type_map: Dict[str, str] = {}  # symbol -> token_type
        
        self._initialize_builtin_operators()
        self._initialized = True
        logger.info(f"OperatorRegistry initialized with {len(self._operators)} operators")

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
            OperatorInfo("=:=", 700, Associativity.NON, OperatorType.COMPARISON, 2, None, "ARITH_EQ"),
            OperatorInfo("=\\=", 700, Associativity.NON, OperatorType.COMPARISON, 2, None, "ARITH_NEQ"),
            OperatorInfo("<", 700, Associativity.NON, OperatorType.COMPARISON, 2, None, "LESS"),
            OperatorInfo("=<", 700, Associativity.NON, OperatorType.COMPARISON, 2, None, "LESS_EQ"),
            OperatorInfo(">", 700, Associativity.NON, OperatorType.COMPARISON, 2, None, "GREATER"),
            OperatorInfo(">=", 700, Associativity.NON, OperatorType.COMPARISON, 2, None, "GREATER_EQ"),
            
            # 論理演算子
            OperatorInfo("=", 700, Associativity.NON, OperatorType.LOGICAL, 2, None, "UNIFY"),
            OperatorInfo("\\=", 700, Associativity.NON, OperatorType.LOGICAL, 2, None, "NOT_UNIFY"),
            OperatorInfo("==", 700, Associativity.NON, OperatorType.LOGICAL, 2, None, "IDENTICAL"),
            OperatorInfo("\\==", 700, Associativity.NON, OperatorType.LOGICAL, 2, None, "NOT_IDENTICAL"),
            
            # 特殊演算子
            OperatorInfo("is", 700, Associativity.NON, OperatorType.ARITHMETIC, 2, None, "IS"),
            OperatorInfo("!", 200, Associativity.NON, OperatorType.CONTROL, 0, None, "CUT"),
            
            # IO演算子
            OperatorInfo("write", 0, Associativity.NON, OperatorType.IO, 1, None, "WRITE"),
            OperatorInfo("nl", 0, Associativity.NON, OperatorType.IO, 0, None, "NL"),
            OperatorInfo("tab", 0, Associativity.NON, OperatorType.IO, 1, None, "TAB"),
        ]
        
        for op in builtin_ops:
            self.register_operator(op)

    def register_operator(self, operator_info: OperatorInfo):
        """演算子を登録"""
        logger.debug(f"Registering operator: {operator_info.symbol}")
        
        self._operators[operator_info.symbol] = operator_info
        self._token_type_map[operator_info.symbol] = operator_info.token_type
        
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
    
    def get_token_type(self, symbol: str) -> Optional[str]:
        """演算子のトークンタイプを取得"""
        return self._token_type_map.get(symbol)
    
    def get_all_symbols(self) -> List[str]:
        """全演算子記号を取得（長さ順でソート）"""
        return sorted(self._operators.keys(), key=len, reverse=True)
    
    def add_user_operator(self, symbol: str, precedence: int, associativity: Associativity, 
                         op_type: OperatorType, arity: int, evaluator: Optional[Callable] = None):
        """ユーザー定義演算子を追加"""
        token_type = f"USER_{symbol.upper().replace(' ', '_').replace('/', '_SLASH_').replace('\\', '_BACKSLASH_')}"
        op_info = OperatorInfo(symbol, precedence, associativity, op_type, arity, evaluator, token_type)
        self.register_operator(op_info)
        logger.info(f"Added user operator: {symbol}")

# グローバルインスタンス（シングルトン）
operator_registry = OperatorRegistry()
```

### 1.2 `prolog/parser/token_type.py` - 動的TokenType生成システム

```python
# prolog/parser/token_type.py
from enum import Enum
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class TokenType(Enum):
    """動的に拡張可能なトークンタイプ"""
    
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

class TokenTypeManager:
    """TokenTypeの動的管理クラス"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._dynamic_tokens: Dict[str, Any] = {}
        self._initialized = True
    
    def ensure_operator_tokens(self):
        """演算子トークンの動的生成を保証"""
        # 遅延インポートで循環参照回避
        from prolog.core.operators import operator_registry
        
        for symbol, op_info in operator_registry._operators.items():
            token_name = op_info.token_type
            if not hasattr(TokenType, token_name):
                # 動的にトークンタイプを追加
                setattr(TokenType, token_name, token_name)
                self._dynamic_tokens[token_name] = token_name
                
                # Enumの内部構造も更新
                TokenType._member_map_[token_name] = getattr(TokenType, token_name)
                TokenType._value2member_map_[token_name] = getattr(TokenType, token_name)
                
                logger.debug(f"Added dynamic token: {token_name}")
        
        logger.info(f"Ensured {len(self._dynamic_tokens)} dynamic operator tokens")
    
    def get_token_type(self, name: str):
        """トークンタイプを取得（存在しない場合は作成）"""
        if hasattr(TokenType, name):
            return getattr(TokenType, name)
        
        # 動的作成
        setattr(TokenType, name, name)
        self._dynamic_tokens[name] = name
        TokenType._member_map_[name] = getattr(TokenType, name)
        TokenType._value2member_map_[name] = getattr(TokenType, name)
        
        logger.debug(f"Dynamically created token: {name}")
        return getattr(TokenType, name)

# グローバルマネージャー
token_type_manager = TokenTypeManager()

def ensure_operator_tokens():
    """演算子トークンの初期化（外部から呼び出し可能）"""
    token_type_manager.ensure_operator_tokens()
```

### 1.3 `prolog/parser/scanner.py` - 統合設計活用版

```python
# prolog/parser/scanner.py
from prolog.parser.token import Token
from prolog.parser.token_type import TokenType, ensure_operator_tokens
from typing import List, Dict, Callable
import logging

logger = logging.getLogger(__name__)

def default_error_handler(line: int, message: str):
    logger.error(f"[line {line}] Scan error: {message}")

class Scanner:
    """演算子統合設計を活用したスキャナー"""
    
    def __init__(self, source: str, report: Callable[[int, str], None] = default_error_handler):
        self._source = source
        self._tokens: List[Token] = []
        self._start = 0
        self._current = 0
        self._line = 1
        self._report = report
        
        # 演算子トークンの初期化
        ensure_operator_tokens()
        
        self._keywords = {
            "true": TokenType.TRUE,
            "fail": TokenType.FAIL,
            "retract": TokenType.RETRACT,
            "asserta": TokenType.ASSERTA,
            "assertz": TokenType.ASSERTZ,
        }
        
        # 演算子マッピングの動的構築
        self._operator_symbols = self._build_operator_mapping()
        self._sorted_operators = sorted(self._operator_symbols.keys(), key=len, reverse=True)
        
        logger.debug(f"Scanner initialized with {len(self._operator_symbols)} operators")

    def _build_operator_mapping(self) -> Dict[str, TokenType]:
        """operator_registryから演算子マッピングを構築"""
        from prolog.core.operators import operator_registry
        
        mapping = {}
        for symbol, op_info in operator_registry._operators.items():
            token_type = getattr(TokenType, op_info.token_type)
            mapping[symbol] = token_type
        
        return mapping

    def scan_tokens(self) -> List[Token]:
        """トークンスキャンのメインメソッド"""
        logger.debug(f"Scanning source: {len(self._source)} characters")
        
        while not self._is_at_end():
            self._start = self._current
            self._scan_token()
        
        self._tokens.append(Token(TokenType.EOF, "", None, self._line))
        
        logger.debug(f"Scanned {len(self._tokens)} tokens")
        return self._tokens

    def _scan_token(self):
        """個別トークンのスキャン"""
        char = self._advance()
        
        if char.isalpha() or char == "_":
            self._identifier()
        elif char.isdigit():
            self._number()
        elif char == "'":
            self._string()
        elif char == "(":
            self._add_token(TokenType.LEFTPAREN)
        elif char == ")":
            self._add_token(TokenType.RIGHTPAREN)
        elif char == "[":
            self._add_token(TokenType.LEFTBRACKET)
        elif char == "]":
            self._add_token(TokenType.RIGHTBRACKET)
        elif char == ",":
            self._add_token(TokenType.COMMA)
        elif char == ".":
            self._add_token(TokenType.DOT)
        elif char == "|":
            self._add_token(TokenType.BAR)
        elif char == ":":
            if self._match("-"):
                self._add_token(TokenType.COLONMINUS)
            else:
                self._report(self._line, f"Unexpected character: {char}")
        elif char in [" ", "\r", "\t"]:
            pass  # 空白無視
        elif char == "\n":
            self._line += 1
        elif char == "%":
            self._skip_comment()
        else:
            # 演算子チェック（統合設計活用）
            if not self._scan_operator(char):
                self._report(self._line, f"Unexpected character: {char}")

    def _scan_operator(self, start_char: str) -> bool:
        """演算子スキャン（統合設計：最長マッチ優先）"""
        # 現在位置からの文字列を取得
        remaining = self._source[self._current - 1:self._current + 10]
        
        # 最長マッチング
        for operator in self._sorted_operators:
            if remaining.startswith(operator):
                # 追加文字を消費
                for _ in range(len(operator) - 1):
                    self._advance()
                
                token_type = self._operator_symbols[operator]
                self._add_token(token_type, operator)
                logger.debug(f"Scanned operator: {operator}")
                return True
        
        return False

    def _identifier(self):
        """識別子のスキャン"""
        while self._peek().isalnum() or self._peek() == "_":
            self._advance()

        text = self._source[self._start:self._current]
        
        # キーワードチェック
        token_type = self._keywords.get(text)
        
        if token_type is None:
            # 演算子キーワードチェック（統合設計活用）
            if text in self._operator_symbols:
                token_type = self._operator_symbols[text]
            elif text[0].isupper() or text[0] == "_":
                token_type = TokenType.VARIABLE
            else:
                token_type = TokenType.ATOM

        self._add_token(token_type)

    def _number(self):
        """数値のスキャン"""
        while self._peek().isdigit():
            self._advance()
        
        # 小数点処理
        if self._peek() == "." and self._peek_next().isdigit():
            self._advance()  # .を消費
            while self._peek().isdigit():
                self._advance()
        
        value = float(self._source[self._start:self._current])
        self._add_token(TokenType.NUMBER, value)

    def _string(self):
        """文字列のスキャン"""
        while self._peek() != "'" and not self._is_at_end():
            if self._peek() == "\n":
                self._line += 1
            self._advance()
        
        if self._is_at_end():
            self._report(self._line, "Unterminated string")
            return
        
        self._advance()  # 終端'を消費
        value = self._source[self._start + 1:self._current - 1]
        self._add_token(TokenType.STRING, value)

    def _skip_comment(self):
        """コメントをスキップ"""
        while self._peek() != "\n" and not self._is_at_end():
            self._advance()

    # ユーティリティメソッド
    def _match(self, expected: str) -> bool:
        if self._is_at_end() or self._source[self._current] != expected:
            return False
        self._current += 1
        return True

    def _peek(self) -> str:
        return "\0" if self._is_at_end() else self._source[self._current]

    def _peek_next(self) -> str:
        if self._current + 1 >= len(self._source):
            return "\0"
        return self._source[self._current + 1]

    def _is_at_end(self) -> bool:
        return self._current >= len(self._source)

    def _advance(self) -> str:
        self._current += 1
        return self._source[self._current - 1]

    def _add_token(self, token_type: TokenType, literal=None):
        text = self._source[self._start:self._current]
        if literal is None:
            literal = text
        self._tokens.append(Token(token_type, text, literal, self._line))
```

## Phase 2: パーサーとインタープリターの統合

### 2.1 `prolog/parser/parser.py` - 統合優先度処理

```python
# prolog/parser/parser.py
from prolog.parser.token import Token
from prolog.parser.token_type import TokenType
from prolog.core.types import Term, Variable, Atom, Number, String, Rule, Fact
from prolog.core.operators import operator_registry, Associativity
from typing import List, Optional, Callable
import logging

logger = logging.getLogger(__name__)

def default_error_handler(token: Token, message: str):
    logger.error(f"Parse error at '{token.lexeme}': {message}")

class Parser:
    """演算子統合設計を活用したパーサー"""
    
    def __init__(self, tokens: List[Token], error_handler: Callable[[Token, str], None] = default_error_handler):
        self._tokens = tokens
        self._current = 0
        self._error_handler = error_handler
        logger.debug(f"Parser initialized with {len(tokens)} tokens")

    def parse(self) -> List[Union[Rule, Fact]]:
        """プログラム全体を解析"""
        rules = []
        
        while not self._is_at_end():
            if self._peek_token_type() == TokenType.EOF:
                break
                
            rule = self._parse_rule()
            if rule:
                rules.append(rule)
                
            if not self._match(TokenType.DOT):
                if not self._is_at_end():
                    self._error(self._peek(), "Expected '.' after rule or fact")
                break
        
        logger.info(f"Parsed {len(rules)} rules/facts")
        return rules

    def _parse_rule(self) -> Optional[Union[Rule, Fact]]:
        """単一ルール/ファクトの解析"""
        head_term = self._parse_term()
        if head_term is None:
            return None

        # Termに変換
        if isinstance(head_term, Atom):
            head_term = Term(head_term, [])

        if self._match(TokenType.COLONMINUS):
            # ルール
            body_terms = []
            while not self._check(TokenType.DOT) and not self._is_at_end():
                term = self._parse_term()
                if term is None:
                    return None
                body_terms.append(term)
                
                if self._match(TokenType.COMMA):
                    continue
                elif self._check(TokenType.DOT):
                    break
                else:
                    self._error(self._peek(), "Expected ',' or '.' in rule body")
                    return None

            if not body_terms:
                self._error(self._peek(), "Rule body cannot be empty")
                return None

            body = self._build_conjunction(body_terms)
            if isinstance(body, Atom):
                body = Term(body, [])
                
            return Rule(head_term, body)
        else:
            # ファクト
            return Fact(head_term)

    def _build_conjunction(self, terms: List) -> Union[Term, Atom]:
        """項リストからコンジャンクションを構築"""
        if len(terms) == 1:
            return terms[0]
        
        result = terms[-1]
        for i in range(len(terms) - 2, -1, -1):
            result = Term(Atom(","), [terms[i], result])
        return result

    def _parse_term(self):
        """項の解析（統合設計：演算子優先度活用）"""
        return self._parse_expression_with_precedence(1200)

    def _parse_expression_with_precedence(self, max_precedence: int):
        """演算子優先度を考慮した式解析（統合設計の核心）"""
        left = self._parse_primary()
        if left is None:
            return None

        while not self._is_at_end():
            token = self._peek()
            if not hasattr(token, "lexeme"):
                break

            symbol = token.lexeme
            
            # 統合設計：operator_registryで演算子判定
            if not operator_registry.is_operator(symbol):
                break

            op_info = operator_registry.get_operator(symbol)
            if not op_info or op_info.precedence > max_precedence:
                break

            self._advance()  # 演算子消費

            # 統合設計：結合性を考慮した優先度計算
            if op_info.associativity == Associativity.LEFT:
                next_max_prec = op_info.precedence - 1
            elif op_info.associativity == Associativity.RIGHT:
                next_max_prec = op_info.precedence
            else:  # NON_ASSOCIATIVE
                next_max_prec = op_info.precedence - 1

            right = self._parse_expression_with_precedence(next_max_prec)
            if right is None:
                self._error(self._peek(), f"Expected right operand for '{symbol}'")
                return None

            left = Term(Atom(symbol), [left, right])

        return left

    def _parse_primary(self):
        """基本要素の解析"""
        if self._match(TokenType.ATOM):
            atom_name = self._previous().lexeme
            if self._match(TokenType.LEFTPAREN):
                # 複合項
                args = []
                if not self._check(TokenType.RIGHTPAREN):
                    while True:
                        arg = self._parse_term()
                        if arg is None:
                            return None
                        args.append(arg)
                        if self._match(TokenType.COMMA):
                            continue
                        break
                self._consume(TokenType.RIGHTPAREN, "Expected ')' after arguments")
                return Term(Atom(atom_name), args)
            else:
                return Atom(atom_name)

        elif self._match(TokenType.NUMBER):
            return Number(self._previous().literal)

        elif self._match(TokenType.VARIABLE):
            return Variable(self._previous().lexeme)

        elif self._match(TokenType.STRING):
            return String(self._previous().literal)

        elif self._match(TokenType.LEFTPAREN):
            expr = self._parse_term()
            if expr is None:
                return None
            self._consume(TokenType.RIGHTPAREN, "Expected ')' after expression")
            return expr

        elif self._match(TokenType.LEFTBRACKET):
            return self._parse_list()

        self._error(self._peek(), "Expected expression")
        return None

    def _parse_list(self):
        """リストの解析"""
        elements = []
        if not self._check(TokenType.RIGHTBRACKET):
            while True:
                elem = self._parse_term()
                if elem is None:
                    return None
                elements.append(elem)
                if self._match(TokenType.COMMA):
                    continue
                break

        tail = None
        if self._match(TokenType.BAR):
            tail = self._parse_term()
            if tail is None:
                return None

        self._consume(TokenType.RIGHTBRACKET, "Expected ']' after list")

        # リストを内部表現に変換
        if tail is None:
            tail = Atom("[]")

        result = tail
        for element in reversed(elements):
            result = Term(Atom("."), [element, result])
        return result

    # ユーティリティメソッド
    def _consume(self, token_type: TokenType, message: str) -> Token:
        if self._check(token_type):
            return self._advance()
        
        self._error(self._peek(), message)
        return Token(token_type, "", None, 0)  # ダミートークン

    def _match(self, *token_types: TokenType) -> bool:
        for token_type in token_types:
            if self._check(token_type):
                self._advance()
                return True
        return False

    def _check(self, token_type: TokenType) -> bool:
        if self._is_at_end():
            return False
        return self._peek_token_type() == token_type

    def _advance(self) -> Token:
        if not self._is_at_end():
            self._current += 1
        return self._previous()

    def _is_at_end(self) -> bool:
        return self._peek_token_type() == TokenType.EOF

    def _peek(self) -> Token:
        return self._tokens[self._current]

    def _previous(self) -> Token:
        return self._tokens[self._current - 1]

    def _peek_token_type(self) -> TokenType:
        token = self._peek()
        return getattr(token, 'token_type', TokenType.EOF)

    def _error(self, token: Token, message: str):
        self._error_handler(token, message)
```

## Phase 3: 統合実行エンジンの実装

### 3.1 `prolog/runtime/interpreter.py` - 統合評価システム

```python
# prolog/runtime/interpreter.py
from prolog.core.types import Term, Variable, Number, Rule, Fact, Atom, String
from prolog.core.binding_environment import BindingEnvironment
from prolog.parser.scanner import Scanner
from prolog.parser.parser import Parser
from prolog.runtime.math_interpreter import MathInterpreter
from prolog.runtime.logic_interpreter import LogicInterpreter
from prolog.core.operators import operator_registry, OperatorType, OperatorInfo
from prolog.core.errors import PrologError
from typing import List, Iterator, Dict, Any, Union
import logging

logger = logging.getLogger(__name__)

class Runtime:
    """演算子統合設計を活用した統合実行エンジン"""
    
    def __init__(self, rules: List[Union[Rule, Fact]] = None):
        self.rules = rules if rules is not None else []
        self.math_interpreter = MathInterpreter()
        self.logic_interpreter = LogicInterpreter(self.rules, self)
        
        # 統合設計：演算子評価システムの構築
        self._operator_evaluators = self._build_unified_evaluator_system()
        
        logger.info(f"Runtime initialized with {len(self.rules)} rules and {len(self._operator_evaluators)} operator evaluators")

    def _build_unified_evaluator_system(self) -> Dict[str, callable]:
        """統合設計：演算子評価システムの構築"""
        evaluators = {}
        
        # 算術演算子の統合
        arithmetic_ops = operator_registry.get_operators_by_type(OperatorType.ARITHMETIC)
        for op_info in arithmetic_ops:
            if op_info.symbol == "is":
                evaluators[op_info.symbol] = self._create_is_evaluator()
            else:
                evaluators[op_info.symbol] = self._create_arithmetic_evaluator(op_info)
        
        # 比較演算子の統合
        comparison_ops = operator_registry.get_operators_by_type(OperatorType.COMPARISON)
        for op_info in comparison_ops:
            evaluators[op_info.symbol] = self._create_comparison_evaluator(op_info)
        
        # 論理演算子の統合
        logical_ops = operator_registry.get_operators_by_type(OperatorType.LOGICAL)
        for op_info in logical_ops:
            if op_info.symbol == "=":
                evaluators[op_info.symbol] = self._create_unification_evaluator()
            else:
                evaluators[op_info.symbol] = self._create_logical_evaluator(op_info)
        
        # 制御演算子の統合
        control_ops = operator_registry.get_operators_by_type(OperatorType.CONTROL)
        for op_info in control_ops:
            evaluators[op_info.symbol] = self._create_control_evaluator(op_info)
        
        # IO演算子の統合
        io_ops = operator_registry.get_operators_by_type(OperatorType.IO)
        for op_info in io_ops:
            evaluators[op_info.symbol] = self._create_io_evaluator(op_info)
        
        logger.debug(f"Built {len(evaluators)} unified operator evaluators")
        return evaluators

    def _create_arithmetic_evaluator(self, op_info: OperatorInfo):
        """算術演算子評価器の生成"""
        def evaluator(args: List, env: BindingEnvironment) -> bool:
            if len(args) != op_info.arity:
                raise PrologError(f"Operator {op_info.symbol} expects {op_info.arity} arguments, got {len(args)}")
            
            if op_info.arity == 2:
                left_val = self.math_interpreter.evaluate(args[0], env)
                right_val = self.math_interpreter.evaluate(args[1], env)
                result = self.math_interpreter.evaluate_binary_op(op_info.symbol, left_val, right_val)
                return True  # 算術演算は常に成功（エラーでない限り）
            
            raise NotImplementedError(f"Unary arithmetic operator {op_info.symbol} not implemented")
        
        return evaluator

    def _create_comparison_evaluator(self, op_info: OperatorInfo):
        """比較演算子評価器の生成"""
        def evaluator(args: List, env: BindingEnvironment) -> bool:
            if len(args) != 2:
                raise PrologError(f"Comparison operator {op_info.symbol} requires 2 arguments")
            
            left_val = self.math_interpreter.evaluate(args[0], env)
            right_val = self.math_interpreter.evaluate(args[1], env)
            return self.math_interpreter.evaluate_comparison_op(op_info.symbol, left_val, right_val)
        
        return evaluator

    def _create_is_evaluator(self):
        """'is' 演算子専用評価器"""
        def evaluator(args: List, env: BindingEnvironment) -> Iterator[BindingEnvironment]:
            if len(args) != 2:
                raise PrologError("'is' operator requires exactly 2 arguments")
            
            result_term, expression = args[0], args[1]
            
            try:
                value = self.math_interpreter.evaluate(expression, env)
                result_number = Number(value)
                
                # 単一化を試行
                unified, new_env = self.logic_interpreter.unify(result_term, result_number, env)
                if unified:
                    yield new_env
                    
            except Exception as e:
                logger.debug(f"'is' evaluation failed: {e}")
                # 失敗時は何も yield しない
        
        return evaluator

    def _create_unification_evaluator(self):
        """単一化演算子評価器"""
        def evaluator(args: List, env: BindingEnvironment) -> Iterator[BindingEnvironment]:
            if len(args) != 2:
                raise PrologError("Unification operator requires exactly 2 arguments")
            
            unified, new_env = self.logic_interpreter.unify(args[0], args[1], env)
            if unified:
                yield new_env
        
        return evaluator

    def _create_logical_evaluator(self, op_info: OperatorInfo):
        """論理演算子評価器の生成"""
        def evaluator(args: List, env: BindingEnvironment) -> bool:
            if len(args) != 2:
                raise PrologError(f"Logical operator {op_info.symbol} requires 2 arguments")
            
            # 論理演算子の実装（例：==, \==）
            if op_info.symbol == "==":
                # 厳密同一性チェック
                left_deref = self.logic_interpreter.dereference(args[0], env)
                right_deref = self.logic_interpreter.dereference(args[1], env)
                return left_deref == right_deref
            elif op_info.symbol == "\\==":
                # 厳密非同一性チェック
                left_deref = self.logic_interpreter.dereference(args[0], env)
                right_deref = self.logic_interpreter.dereference(args[1], env)
                return left_deref != right_deref
            
            raise NotImplementedError(f"Logical operator {op_info.symbol} not implemented")
        
        return evaluator

    def _create_control_evaluator(self, op_info: OperatorInfo):
        """制御演算子評価器の生成"""
        def evaluator(args: List, env: BindingEnvironment) -> Iterator[BindingEnvironment]:
            if op_info.symbol == "!":
                # カット：現在の環境で成功し、バックトラックを防ぐ
                yield env
                # カット信号をどう処理するかは実装依存
                # ここでは単純に成功として扱う
            else:
                raise NotImplementedError(f"Control operator {op_info.symbol} not implemented")
        
        return evaluator

    def _create_io_evaluator(self, op_info: OperatorInfo):
        """IO演算子評価器の生成"""
        def evaluator(args: List, env: BindingEnvironment) -> Iterator[BindingEnvironment]:
            if op_info.symbol == "write":
                if len(args) != 1:
                    raise PrologError("write/1 requires exactly 1 argument")
                
                # 引数を文字列として出力
                arg_deref = self.logic_interpreter.dereference(args[0], env)
                print(str(arg_deref), end='')
                yield env
                
            elif op_info.symbol == "nl":
                if len(args) != 0:
                    raise PrologError("nl/0 requires no arguments")
                print()
                yield env
                
            elif op_info.symbol == "tab":
                if len(args) > 1:
                    raise PrologError("tab requires 0 or 1 arguments")
                
                if len(args) == 1:
                    # 引数指定の場合
                    count_term = self.logic_interpreter.dereference(args[0], env)
                    if isinstance(count_term, Number):
                        print(' ' * int(count_term.value), end='')
                    else:
                        print('\t', end='')
                else:
                    print('\t', end='')
                yield env
            else:
                raise NotImplementedError(f"IO operator {op_info.symbol} not implemented")
        
        return evaluator

    def execute(self, goal: Term, env: BindingEnvironment) -> Iterator[BindingEnvironment]:
        """統合設計：統一されたゴール実行"""
        logger.debug(f"Executing goal: {goal}")
        
        if isinstance(goal, Term):
            functor_name = goal.functor.name if hasattr(goal.functor, 'name') else str(goal.functor)
            
            # 統合設計：operator_registry で演算子判定
            op_info = operator_registry.get_operator(functor_name)
            
            if op_info and functor_name in self._operator_evaluators:
                # 演算子として評価
                evaluator = self._operator_evaluators[functor_name]
                
                try:
                    # 演算子タイプに応じた評価
                    if op_info.operator_type in [OperatorType.ARITHMETIC, OperatorType.COMPARISON, OperatorType.LOGICAL]:
                        if functor_name in ["=", "is"]:
                            # ジェネレータ型評価器
                            yield from evaluator(goal.args, env)
                        else:
                            # ブール型評価器
                            success = evaluator(goal.args, env)
                            if success:
                                yield env
                    else:
                        # 制御・IO演算子（ジェネレータ型）
                        yield from evaluator(goal.args, env)
                        
                except Exception as e:
                    logger.debug(f"Operator evaluation failed: {e}")
                    # 演算子評価失敗時は通常の述語として処理を続行
                    yield from self.logic_interpreter.solve_goal(goal, env)
            else:
                # 通常の述語として処理
                yield from self.logic_interpreter.solve_goal(goal, env)
        else:
            # Termでない場合（通常はありえない）
            yield from self.logic_interpreter.solve_goal(goal, env)

    def query(self, query_string: str) -> List[Dict[Variable, Any]]:
        """クエリ実行（既存API互換性維持）"""
        logger.debug(f"Executing query: {query_string}")
        
        try:
            # 統合設計：Scanner と Parser を使用
            tokens = Scanner(query_string).scan_tokens()
            
            if not query_string.strip().endswith("."):
                query_string += "."
                tokens = Scanner(query_string).scan_tokens()
            
            parsed_structures = Parser(tokens).parse()
            
            if not parsed_structures:
                logger.warning("Query parsing failed")
                return []

            # ゴール抽出
            if isinstance(parsed_structures[0], Fact):
                query_goal = parsed_structures[0].head
            elif isinstance(parsed_structures[0], Rule):
                query_goal = parsed_structures[0].head
            else:
                logger.error(f"Unexpected parsed structure: {type(parsed_structures[0])}")
                return []

            # 統合実行エンジンで実行
            solutions = []
            initial_env = BindingEnvironment()

            for env in self.execute(query_goal, initial_env):
                result = {}
                query_vars = self._extract_variables(query_goal)

                for var_name in query_vars:
                    var_obj = Variable(var_name)
                    value = env.get_value(var_name)
                    if value is not None:
                        result[var_obj] = self.logic_interpreter.dereference(value, env)

                if result or not query_vars:
                    solutions.append(result)

            logger.debug(f"Query completed with {len(solutions)} solutions")
            return solutions

        except Exception as e:
            logger.error(f"Query execution error: {e}", exc_info=True)
            return []

    def _extract_variables(self, term) -> List[str]:
        """項から変数名を抽出"""
        variables = set()
        
        def extract_recursive(current_term):
            if isinstance(current_term, Variable):
                variables.add(current_term.name)
            elif isinstance(current_term, Term):
                for arg in current_term.args:
                    extract_recursive(arg)
        
        extract_recursive(term)
        return list(variables)

    def add_rule(self, rule_string: str) -> bool:
        """動的ルール追加"""
        try:
            if not rule_string.strip().endswith("."):
                rule_string += "."
            
            tokens = Scanner(rule_string).scan_tokens()
            parsed_rules = Parser(tokens).parse()
            
            if parsed_rules:
                self.rules.extend(parsed_rules)
                self.logic_interpreter.rules = self.rules
                logger.info(f"Added {len(parsed_rules)} rule(s)")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to add rule: {e}")
            return False

    def consult(self, filename: str) -> bool:
        """ファイルからルールを読み込み"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tokens = Scanner(source).scan_tokens()
            new_rules = Parser(tokens).parse()
            
            self.rules.extend(new_rules)
            self.logic_interpreter.rules = self.rules
            
            logger.info(f"Consulted {len(new_rules)} rules from {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to consult {filename}: {e}")
            return False
```

### 3.2 `prolog/runtime/math_interpreter.py` - 統合設計対応版

```python
# prolog/runtime/math_interpreter.py
from prolog.core.types import Term, Variable, Number, Atom, String, PrologType
from prolog.core.binding_environment import BindingEnvironment
from prolog.core.errors import PrologError
from prolog.core.operators import operator_registry, OperatorType
from typing import Union
import logging

logger = logging.getLogger(__name__)

class MathInterpreter:
    """統合設計を活用した数学的評価エンジン"""
    
    def __init__(self):
        logger.debug("MathInterpreter initialized")

    def evaluate(self, expression: PrologType, env: BindingEnvironment) -> Union[int, float]:
        """統合設計：演算子レジストリを活用した式評価"""
        
        if isinstance(expression, Number):
            return expression.value
            
        if isinstance(expression, Variable):
            value = env.get_value(expression.name)
            if value is None:
                raise PrologError(f"Variable {expression.name} is not instantiated")
            
            # 再帰的評価
            return self.evaluate(value, env)
            
        if isinstance(expression, Atom):
            # アトムを数値として解釈を試行
            try:
                return float(expression.name)
            except ValueError:
                raise PrologError(f"Cannot evaluate atom '{expression.name}' as number")
        
        if isinstance(expression, Term):
            functor_name = expression.functor.name
            
            # 統合設計：operator_registry で演算子判定
            op_info = operator_registry.get_operator(functor_name)
            
            if op_info and op_info.operator_type == OperatorType.ARITHMETIC:
                if op_info.arity == 2 and len(expression.args) == 2:
                    left_val = self.evaluate(expression.args[0], env)
                    right_val = self.evaluate(expression.args[1], env)
                    return self.evaluate_binary_op(functor_name, left_val, right_val)
                elif op_info.arity == 1 and len(expression.args) == 1:
                    operand_val = self.evaluate(expression.args[0], env)
                    return self.evaluate_unary_op(functor_name, operand_val)
                else:
                    raise PrologError(f"Arity mismatch for operator {functor_name}: expected {op_info.arity}, got {len(expression.args)}")
            else:
                # 関数として評価（例：abs/1, max/2 など）
                return self._evaluate_function(functor_name, expression.args, env)
        
        raise PrologError(f"Cannot evaluate expression: {expression}")

    def evaluate_binary_op(self, op_symbol: str, left_val: Union[int, float], right_val: Union[int, float]) -> Union[int, float]:
        """統合設計：バイナリ演算子の評価"""
        
        if not isinstance(left_val, (int, float)) or not isinstance(right_val, (int, float)):
            raise PrologError(f"Arithmetic operation requires numeric arguments: {left_val}, {right_val}")

        # 統合設計：operator_registry から演算子情報を取得
        op_info = operator_registry.get_operator(op_symbol)
        if not op_info:
            raise PrologError(f"Unknown arithmetic operator: {op_symbol}")

        try:
            if op_symbol == "+":
                return left_val + right_val
            elif op_symbol == "-":
                return left_val - right_val
            elif op_symbol == "*":
                return left_val * right_val
            elif op_symbol == "/":
                if right_val == 0:
                    raise PrologError("Division by zero")
                return left_val / right_val
            elif op_symbol == "//":
                if right_val == 0:
                    raise PrologError("Integer division by zero")
                return int(left_val // right_val)
            elif op_symbol == "**":
                return left_val ** right_val
            elif op_symbol == "mod":
                if right_val == 0:
                    raise PrologError("Modulo by zero")
                return left_val % right_val
            else:
                raise PrologError(f"Unsupported binary arithmetic operator: {op_symbol}")
                
        except Exception as e:
            raise PrologError(f"Arithmetic error in {op_symbol}: {e}")

    def evaluate_unary_op(self, op_symbol: str, operand_val: Union[int, float]) -> Union[int, float]:
        """単項演算子の評価"""
        
        if not isinstance(operand_val, (int, float)):
            raise PrologError(f"Unary arithmetic operation requires numeric argument: {operand_val}")

        if op_symbol == "-":
            return -operand_val
        elif op_symbol == "+":
            return operand_val
        elif op_symbol == "abs":
            return abs(operand_val)
        else:
            raise PrologError(f"Unknown unary arithmetic operator: {op_symbol}")

    def evaluate_comparison_op(self, op_symbol: str, left_val: Union[int, float], right_val: Union[int, float]) -> bool:
        """統合設計：比較演算子の評価"""
        
        if not isinstance(left_val, (int, float)) or not isinstance(right_val, (int, float)):
            raise PrologError(f"Comparison requires numeric arguments: {left_val}, {right_val}")

        # 統合設計：operator_registry から演算子情報を取得
        op_info = operator_registry.get_operator(op_symbol)
        if not op_info or op_info.operator_type != OperatorType.COMPARISON:
            raise PrologError(f"Unknown comparison operator: {op_symbol}")

        if op_symbol == "=:=":
            return left_val == right_val
        elif op_symbol == "=\\=":
            return left_val != right_val
        elif op_symbol == "<":
            return left_val < right_val
        elif op_symbol == "=<":
            return left_val <= right_val
        elif op_symbol == ">":
            return left_val > right_val
        elif op_symbol == ">=":
            return left_val >= right_val
        else:
            raise PrologError(f"Unsupported comparison operator: {op_symbol}")

    def _evaluate_function(self, func_name: str, args: List[PrologType], env: BindingEnvironment) -> Union[int, float]:
        """数学関数の評価（拡張可能）"""
        
        if func_name == "abs" and len(args) == 1:
            val = self.evaluate(args[0], env)
            return abs(val)
        elif func_name == "max" and len(args) == 2:
            val1 = self.evaluate(args[0], env)
            val2 = self.evaluate(args[1], env)
            return max(val1, val2)
        elif func_name == "min" and len(args) == 2:
            val1 = self.evaluate(args[0], env)
            val2 = self.evaluate(args[1], env)
            return min(val1, val2)
        else:
            raise PrologError(f"Unknown mathematical function: {func_name}/{len(args)}")
```

## Phase 4: テスト適応と設計検証

### 4.1 テスト構造の再設計

```python
# tests/test_operator_integration/test_unified_operators.py
"""演算子統合設計の包括的テスト"""

import pytest
from prolog.runtime.interpreter import Runtime
from prolog.core.operators import operator_registry, OperatorType, Associativity
from prolog.core.types import Variable, Atom, Number, Term
from prolog.parser.scanner import Scanner
from prolog.parser.parser import Parser
import logging

# テスト用ログ設定
logging.basicConfig(level=logging.DEBUG)

class TestOperatorIntegration:
    """演算子統合設計の統合テスト"""

    def test_operator_registry_completeness(self):
        """演算子レジストリの完全性テスト"""
        # 必須演算子の存在確認
        required_operators = [
            ("+", OperatorType.ARITHMETIC),
            ("-", OperatorType.ARITHMETIC),
            ("*", OperatorType.ARITHMETIC),
            ("/", OperatorType.ARITHMETIC),
            ("=:=", OperatorType.COMPARISON),
            ("=", OperatorType.LOGICAL),
            ("is", OperatorType.ARITHMETIC),
            ("!", OperatorType.CONTROL),
        ]
        
        for symbol, expected_type in required_operators:
            op_info = operator_registry.get_operator(symbol)
            assert op_info is not None, f"Operator {symbol} not found in registry"
            assert op_info.operator_type == expected_type, f"Operator {symbol} has wrong type"

    def test_dynamic_token_generation(self):
        """動的TokenType生成のテスト"""
        source = "X is 2 + 3 * 4."
        tokens = Scanner(source).scan_tokens()
        
        # 演算子トークンが正しく生成されていることを確認
        token_types = [token.token_type for token in tokens]
        assert any("IS" in str(tt) for tt in token_types), "IS token not generated"
        assert any("PLUS" in str(tt) for tt in token_types), "PLUS token not generated"
        assert any("STAR" in str(tt) for tt in token_types), "STAR token not generated"

    def test_operator_precedence_parsing(self):
        """演算子優先度の正しい解析テスト"""
        source = "test(X) :- X is 2 + 3 * 4."
        tokens = Scanner(source).scan_tokens()
        rules = Parser(tokens).parse()
        
        assert len(rules) == 1
        rule = rules[0]
        
        # 'is' の右辺が正しい構造になっているかチェック
        # 2 + (3 * 4) として解析されるべき
        is_term = rule.body
        assert isinstance(is_term, Term)
        assert is_term.functor.name == "is"
        
        right_side = is_term.args[1]  # 'is' の右辺
        assert isinstance(right_side, Term)
        assert right_side.functor.name == "+"
        
        # 左辺は 2、右辺は (3 * 4)
        left_operand = right_side.args[0]
        right_operand = right_side.args[1]
        
        assert isinstance(left_operand, Number)
        assert left_operand.value == 2
        
        assert isinstance(right_operand, Term)
        assert right_operand.functor.name == "*"

    def test_unified_arithmetic_evaluation(self):
        """統合算術評価システムのテスト"""
        source = """
        calc(X, Y, Z) :- Z is X + Y * 2.
        """
        tokens = Scanner(source).scan_tokens()
        rules = Parser(tokens).parse()
        runtime = Runtime(rules)
        
        solutions = runtime.query("calc(5, 3, Result).")
        assert len(solutions) == 1
        
        result_var = Variable("Result")
        assert result_var in solutions[0]
        # 5 + (3 * 2) = 11
        assert float(str(solutions[0][result_var])) == 11.0

    def test_unified_comparison_evaluation(self):
        """統合比較評価システムのテスト"""
        source = """
        compare_test(X, Y) :- X =:= Y + 1.
        """
        tokens = Scanner(source).scan_tokens()
        rules = Parser(tokens).parse()
        runtime = Runtime(rules)
        
        # 成功ケース: 5 =:= 4 + 1
        solutions_success = runtime.query("compare_test(5, 4).")
        assert len(solutions_success) == 1
        
        # 失敗ケース: 5 =:= 3 + 1
        solutions_fail = runtime.query("compare_test(5, 3).")
        assert len(solutions_fail) == 0

    def test_unified_unification_evaluation(self):
        """統合単一化評価システムのテスト"""
        source = """
        unify_test(X, Y) :- X = Y.
        """
        tokens = Scanner(source).scan_tokens()
        rules = Parser(tokens).parse()
        runtime = Runtime(rules)
        
        solutions = runtime.query("unify_test(hello, X).")
        assert len(solutions) == 1
        
        x_var = Variable("X")
        assert x_var in solutions[0]
        assert str(solutions[0][x_var]) == "hello"

    def test_io_operator_integration(self):
        """IO演算子統合テスト"""
        source = """
        test_io(X) :- write(X), nl.
        """
        tokens = Scanner(source).scan_tokens()
        rules = Parser(tokens).parse()
        runtime = Runtime(rules)
        
        # 出力をキャプチャして検証
        import io
        import sys
        from contextlib import redirect_stdout
        
        f = io.StringIO()
        with redirect_stdout(f):
            solutions = runtime.query("test_io(hello).")
        
        output = f.getvalue()
        assert "hello" in output
        assert len(solutions) == 1

    def test_operator_extensibility(self):
        """演算子拡張性のテスト"""
        # 新しい演算子を動的に追加
        operator_registry.add_user_operator(
            "**", 200, Associativity.RIGHT, OperatorType.ARITHMETIC, 2
        )
        
        # 追加された演算子が使用可能か確認
        op_info = operator_registry.get_operator("**")
        assert op_info is not None
        assert op_info.precedence == 200
        assert op_info.associativity == Associativity.RIGHT

class TestBackwardCompatibility:
    """既存テストとの互換性テスト"""

    def test_basic_queries_still_work(self):
        """基本的なクエリが引き続き動作することを確認"""
        source = """
        location(computer, office).
        location(knife, kitchen).
        """
        tokens = Scanner(source).scan_tokens()
        rules = Parser(tokens).parse()
        runtime = Runtime(rules)
        
        solutions = runtime.query("location(computer, X).")
        assert len(solutions) == 1
        
        x_var = Variable("X")
        assert x_var in solutions[0]
        assert str(solutions[0][x_var]) == "office"

    def test_arithmetic_queries_enhanced(self):
        """算術クエリが統合設計で強化されていることを確認"""
        source = """
        calc(X) :- X is (2 + 3) * (4 - 1).