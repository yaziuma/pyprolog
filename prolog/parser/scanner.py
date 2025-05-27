# prolog/parser/scanner.py
from prolog.parser.token import Token
from prolog.parser.token_type import TokenType, initialize_operator_tokens

def default_error_handler(line, message):
    print(f"[line {line}] Error: {message}")

class Scanner:
    def __init__(self, source, report=default_error_handler):
        self._source = source
        self._tokens = []
        self._start = 0
        self._current = 0
        self._line = 1
        self._report = report
        
        # 演算子トークンの動的初期化
        initialize_operator_tokens()
        
        self._keywords = {
            "true": TokenType.TRUE,
            "fail": TokenType.FAIL,
            "retract": TokenType.RETRACT,
            "asserta": TokenType.ASSERTA,
            "assertz": TokenType.ASSERTZ,
        }
        
        # 演算子マッピングを operator_registry から構築
        self._operator_symbols = self._build_operator_symbol_map()
        self._sorted_operator_symbols = sorted(
            self._operator_symbols.keys(), key=len, reverse=True
        )

    def _build_operator_symbol_map(self):
        """演算子レジストリからTokenTypeへのマッピングを構築"""
        from prolog.core.operators import operator_registry
        
        symbol_map = {}
        for symbol, op_info in operator_registry._operators.items():
            if op_info.token_type:
                # 動的に追加されたTokenTypeを取得
                if hasattr(TokenType, op_info.token_type):
                    token_type = getattr(TokenType, op_info.token_type)
                    symbol_map[symbol] = token_type
        return symbol_map

    def scan_tokens(self):
        while not self._is_at_end():
            self._start = self._current
            self._scan_token()
        self._tokens.append(Token(TokenType.EOF, "", None, self._line))
        return self._tokens

    def _scan_token(self):
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
            pass
        elif char == "\n":
            self._line += 1
        elif char == "%":
            while self._peek() != "\n" and not self._is_at_end():
                self._advance()
        else:
            if not self._scan_operator(char):
                self._report(self._line, f"Unexpected character: {char}")

    def _scan_operator(self, start_char):
        """演算子の字句解析（統合設計通り：長いものから優先してマッチング）"""
        current_segment = (
            start_char + self._source[self._current:self._current + 10]
        )

        for symbol in self._sorted_operator_symbols:
            if current_segment.startswith(symbol):
                # 文字を消費
                for _ in range(len(symbol) - 1):
                    self._advance()
                
                token_type = self._operator_symbols[symbol]
                self._add_token(token_type, symbol)
                return True
        return False

    def _identifier(self):
        while self._peek().isalnum() or self._peek() == "_":
            self._advance()

        text = self._source[self._start : self._current]
        token_type = self._keywords.get(text)

        if token_type is None:
            # 演算子キーワード（統合設計活用）
            from prolog.core.operators import operator_registry
            op_info = operator_registry.get_operator(text)
            if op_info and op_info.token_type:
                if hasattr(TokenType, op_info.token_type):
                    token_type = getattr(TokenType, op_info.token_type)
                else:
                    token_type = TokenType.ATOM
            elif text[0].isupper() or text[0] == "_":
                token_type = TokenType.VARIABLE
            else:
                token_type = TokenType.ATOM

        self._add_token(token_type)

    # 残りのメソッドは既存のまま...
    def _number(self):
        while self._peek().isdigit():
            self._advance()
        if self._peek() == "." and self._peek_next().isdigit():
            self._advance()
            while self._peek().isdigit():
                self._advance()
        self._add_token(
            TokenType.NUMBER, float(self._source[self._start : self._current])
        )

    def _string(self):
        while self._peek() != "'" and not self._is_at_end():
            if self._peek() == "\n":
                self._line += 1
            self._advance()
        if self._is_at_end():
            self._report(self._line, "Unterminated string.")
            return
        self._advance()
        value = self._source[self._start + 1 : self._current - 1]
        self._add_token(TokenType.STRING, value)

    def _match(self, expected):
        if self._is_at_end():
            return False
        if self._source[self._current] != expected:
            return False
        self._current += 1
        return True

    def _peek(self):
        if self._is_at_end():
            return "\0"
        return self._source[self._current]

    def _peek_next(self):
        if self._current + 1 >= len(self._source):
            return "\0"
        return self._source[self._current + 1]

    def _is_at_end(self):
        return self._current >= len(self._source)

    def _advance(self):
        self._current += 1
        return self._source[self._current - 1]

    def _add_token(self, type, literal=None):
        text = self._source[self._start : self._current]
        if literal is None and type not in [
            TokenType.LEFTPAREN, TokenType.RIGHTPAREN, TokenType.LEFTBRACKET,
            TokenType.RIGHTBRACKET, TokenType.COMMA, TokenType.DOT, TokenType.BAR,
            TokenType.COLONMINUS, TokenType.UNDERSCORE, TokenType.EOF,
        ]:
            literal = text
        self._tokens.append(
            Token(type, literal if literal is not None else text, literal, self._line)
        )
