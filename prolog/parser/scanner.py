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

    def __init__(
        self, source: str, report: Callable[[int, str], None] = default_error_handler
    ):
        self._source = source
        self._tokens: List[Token] = []
        self._start = 0
        self._current = 0
        self._line = 1
        self._report = report

        # 演算子トークンの初期化をキーワード定義より前に移動
        ensure_operator_tokens()

        self._keywords = {
            "true": TokenType.TRUE,
            "fail": TokenType.FAIL,
            "retract": TokenType.RETRACT,
            "asserta": TokenType.ASSERTA,
            "assertz": TokenType.ASSERTZ,
            "write": TokenType.ATOM, # 'write' をATOMとして扱う
            "nl": TokenType.ATOM,    # 'nl' もATOMとして扱う
            # "is": TokenType.OPERATOR_XFX_700, # 'is' は operator_registry 経由で処理
            # "cut": TokenType.CUT, # '!' は _scan_token で直接 TokenType.CUT を生成
            #  'functor', 'arg', '=..' などもここに追加可能だが、これらは通常のアトムとして扱われる
        }

        # 演算子マッピングの動的構築
        self._operator_symbols = self._build_operator_mapping()
        self._sorted_operators = sorted(
            self._operator_symbols.keys(), key=len, reverse=True
        )

        logger.debug(
            f"Scanner initialized with {len(self._operator_symbols)} operators"
        )

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
            # else: # ':' 単独の場合、演算子としてスキャンさせる
            elif not self._scan_operator(char):
                 self._report(self._line, f"Unexpected character: {char}")
        elif char == "!": # '!' を CUT トークンとして処理
            self._add_token(TokenType.CUT)
        elif char in [" ", "\r", "\t"]:
            pass  # 空白無視
        elif char == "\n":
            self._line += 1
        elif char == "%":
            self._skip_comment()
        elif char == '-': # Handle potential negative numbers or operators starting with '-'
            if self._peek().isdigit():
                self._number() # self._start is at '-', _current is at the first digit. _number handles it.
            else: # Operator starting with '-'
                  # _current is already advanced past '-', so _scan_operator which looks at current-1 is fine.
                if not self._scan_operator(char): # Pass char for context/logging if needed
                    self._report(self._line, f"Unexpected operator or character sequence starting with: {char}")
        else:
            # Default: Other characters, likely operators or unexpected.
            # _current is already advanced past char, so _scan_operator which looks at current-1 is fine.
            if not self._scan_operator(char): # Pass char for context/logging if needed
                self._report(self._line, f"Unexpected character: {char}")

    def _scan_operator(self, start_char: str) -> bool:
        """演算子スキャン（統合設計：最長マッチ優先）"""
        # 現在位置からの文字列を取得
        remaining = self._source[self._current - 1 : self._current + 10]

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

        text = self._source[self._start : self._current]

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

        value = float(self._source[self._start : self._current])
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
        value = self._source[self._start + 1 : self._current - 1]
        # Change to tokenize single-quoted literals as STRING - reverting a change made during previous type checking
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
        text = self._source[self._start : self._current]
        if literal is None:
            literal = text
        self._tokens.append(Token(token_type, text, literal, self._line))
