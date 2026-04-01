import logging
from collections.abc import Callable

from pyprolog.parser.token import Token
from pyprolog.parser.token_type import TokenType, ensure_operator_tokens
from pyprolog.util import VariableMapper
from pyprolog.util.functor_mapper import FunctorMapper

logger = logging.getLogger(__name__)


def default_error_handler(line: int, message: str):
    logger.error("[line %d] Scan error: %s", line, message)


class Scanner:
    """演算子統合設計を活用したスキャナー"""

    def __init__(
        self,
        source: str,
        report: Callable[[int, str], None] = default_error_handler,
        variable_mapper: VariableMapper | None = None,
        functor_mapper: FunctorMapper | None = None,
    ):
        self._source = source
        self._tokens: list[Token] = []
        self._start = 0
        self._current = 0
        self._line = 1
        self._report = report
        self._variable_mapper = variable_mapper
        self._functor_mapper = functor_mapper
        ensure_operator_tokens()
        self._keywords = {
            "true": TokenType.TRUE,
            "fail": TokenType.FAIL,
            "retract": TokenType.RETRACT,
            "asserta": TokenType.ASSERTA,
            "assertz": TokenType.ASSERTZ,
            "write": TokenType.ATOM,
            "nl": TokenType.ATOM,
        }
        self._operator_symbols = self._build_operator_mapping()
        self._sorted_operators = sorted(
            self._operator_symbols.keys(), key=len, reverse=True
        )
        logger.debug(
            "Scanner initialized with %r operators", len(self._operator_symbols)
        )

    def _build_operator_mapping(self) -> dict[str, TokenType]:
        """operator_registryから演算子マッピングを構築"""
        from pyprolog.core.operators import operator_registry

        mapping = {}
        for symbol, op_info in operator_registry._operators.items():
            token_type = getattr(TokenType, op_info.token_type)
            mapping[symbol] = token_type
        return mapping

    def scan_tokens(self) -> list[Token]:
        """トークンスキャンのメインメソッド"""
        logger.debug("Scanning source: %d characters", len(self._source))
        while not self._is_at_end():
            self._start = self._current
            self._scan_token()
        self._tokens.append(Token(TokenType.EOF, "", None, self._line))
        logger.debug("Scanned %d tokens", len(self._tokens))
        return self._tokens

    def _scan_token(self):
        """個別トークンのスキャン"""
        char = self._advance()
        if char.isalpha() or char == "_":
            self._identifier()
        elif char.isdigit():
            self._number()
        elif char in {"'", '"'}:
            self._string(char)
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
            elif not self._scan_operator(char):
                self._report(self._line, f"Unexpected character: {char}")
        elif char == "!":
            if self._match("="):
                self._add_token(self._operator_symbols["!="], "!=")
            else:
                self._add_token(TokenType.CUT)
        elif char in [" ", "\r", "\t"]:
            pass
        elif char == "\n":
            self._line += 1
        elif char == "%":
            self._skip_comment()
        elif char == "-":
            if self._peek().isdigit():
                self._number()
            elif not self._scan_operator(char):
                self._report(
                    self._line,
                    f"Unexpected operator or character sequence starting with: {char}",
                )
        elif not self._scan_operator(char):
            self._report(self._line, f"Unexpected character: {char}")

    def _scan_operator(self, start_char: str) -> bool:
        """演算子スキャン（統合設計：最長マッチ優先）"""
        remaining = self._source[self._current - 1 : self._current + 10]
        for operator in self._sorted_operators:
            if remaining.startswith(operator):
                for _ in range(len(operator) - 1):
                    self._advance()
                token_type = self._operator_symbols[operator]
                self._add_token(token_type, operator)
                logger.debug("Scanned operator: %s", operator)
                return True
        return False

    def _identifier(self):
        """識別子のスキャン（Unicode対応版）"""
        while not self._is_at_end() and (
            self._peek().isalnum()
            or self._peek() == "_"
            or (self._peek() and ord(self._peek()) > 127)
            or self._is_valid_identifier_char(self._peek())
        ):
            self._advance()
        text = self._source[self._start : self._current]
        literal_override = None
        token_type = self._keywords.get(text)
        if token_type is None:
            if text in self._operator_symbols:
                token_type = self._operator_symbols[text]
            elif self._functor_mapper and self._functor_mapper.needs_mapping(text):
                token_type = TokenType.ATOM
                literal_override = self._functor_mapper.map_non_ascii_to_english(text)
                logger.debug(
                    "Mapped non-ASCII functor '%r' to '%r'", text, literal_override
                )
            elif self._variable_mapper and self._variable_mapper.is_japanese_variable(
                text
            ):
                token_type = TokenType.VARIABLE
                literal_override = self._variable_mapper.map_japanese_to_english(text)
                logger.debug(
                    "Mapped Japanese variable '%r' to '%r'", text, literal_override
                )
            elif text[0].isupper() or text[0] == "_":
                token_type = TokenType.VARIABLE
            else:
                token_type = TokenType.ATOM
        if literal_override is not None:
            self._add_token(token_type, literal_override=literal_override)
        else:
            self._add_token(token_type)

    def _is_valid_identifier_char(self, char: str) -> bool:
        """識別子として有効な文字かチェック"""
        if not char:
            return False
        invalid_chars = set("()[]{}.,;:!|\"'`~@#$%^&*+-=<>?/\\")
        return char not in invalid_chars and (not char.isspace())

    def _number(self):
        """数値のスキャン"""
        while self._peek().isdigit():
            self._advance()
        if self._peek() == "." and self._peek_next().isdigit():
            self._advance()
            while self._peek().isdigit():
                self._advance()
        value = float(self._source[self._start : self._current])
        self._add_token(TokenType.NUMBER, value)

    def _string(self, quote_char: str):
        """文字列のスキャン"""
        while self._peek() != quote_char and (not self._is_at_end()):
            if self._peek() == "\n":
                self._line += 1
            self._advance()
        if self._is_at_end():
            self._report(self._line, "Unterminated string")
            return
        self._advance()
        value = self._source[self._start + 1 : self._current - 1]
        self._add_token(TokenType.STRING, value)

    def _skip_comment(self):
        """コメントをスキップ"""
        while self._peek() != "\n" and (not self._is_at_end()):
            self._advance()

    def _match(self, expected: str) -> bool:
        if self._is_at_end() or self._source[self._current] != expected:
            return False
        self._current += 1
        return True

    def _peek(self) -> str:
        return "\x00" if self._is_at_end() else self._source[self._current]

    def _peek_next(self) -> str:
        if self._current + 1 >= len(self._source):
            return "\x00"
        return self._source[self._current + 1]

    def _is_at_end(self) -> bool:
        return self._current >= len(self._source)

    def _advance(self) -> str:
        self._current += 1
        return self._source[self._current - 1]

    def _add_token(self, token_type: TokenType, literal_override=None):
        text = self._source[self._start : self._current]
        literal_to_store = literal_override if literal_override is not None else text
        self._tokens.append(Token(token_type, text, literal_to_store, self._line))
