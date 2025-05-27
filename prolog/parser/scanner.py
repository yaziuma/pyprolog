from prolog.parser.token import Token
from prolog.parser.token_type import TokenType
from prolog.core.operators import operator_registry


# エラーハンドラーのデフォルト実装（必要に応じてカスタマイズ可能）
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
        self._keywords = {
            "true": TokenType.TRUE,
            "fail": TokenType.FAIL,
            "retract": TokenType.RETRACT,
            "asserta": TokenType.ASSERTA,
            "assertz": TokenType.ASSERTZ,
            # "is" は演算子として処理されるため、キーワードからは削除
            # "nl", "tab", "write" も演算子として処理
        }
        self._operator_symbols = self._build_operator_symbol_map()
        # 演算子シンボルを長さの降順でソートし、最長マッチを優先
        self._sorted_operator_symbols = sorted(
            self._operator_symbols.keys(), key=len, reverse=True
        )

    def _build_operator_symbol_map(self):
        """演算子記号からTokenTypeへのマッピングを構築"""
        symbol_map = {}
        for symbol, op_info in operator_registry._operators.items():
            if op_info.token_type:
                # TokenTypeを名前から取得
                try:
                    token_type_member = getattr(TokenType, op_info.token_type)
                    symbol_map[symbol] = token_type_member
                except AttributeError:
                    # TokenType に存在しない場合はエラーログなどを出すか、無視する
                    # ここでは、初期化時にエラーが発生する可能性があるため、
                    # _initialize_operator_tokens が呼ばれた後であることを期待
                    pass  # またはエラー処理
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
            # アトム、変数、またはキーワード（is, nl, tab, writeなど）
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
                self._report(
                    self._line, f"Unexpected character: {char}"
                )  # ':' 単独はエラー
        elif char in [" ", "\r", "\t"]:
            # 空白文字は無視
            pass
        elif char == "\n":
            self._line += 1
        elif char == "%":  # コメント
            while self._peek() != "\n" and not self._is_at_end():
                self._advance()
        else:
            # 演算子かどうかをチェック
            if not self._scan_operator(char):
                self._report(self._line, f"Unexpected character: {char}")

    def _scan_operator(self, start_char):
        """演算子の字句解析（長いものから優先してマッチング）"""
        # 現在位置から可能な演算子を探索
        # start_char を含めて、ソースの残りの部分と比較
        current_segment = (
            start_char
            + self._source[
                self._current : self._current
                + max(len(s) for s in self._sorted_operator_symbols if s)
                - 1
                if self._sorted_operator_symbols
                else 0
            ]
        )

        for symbol in self._sorted_operator_symbols:
            if current_segment.startswith(symbol):
                # マッチした場合、文字を消費
                # start_char は既に _advance() で消費済み
                # symbol の残りの長さを消費
                for _ in range(len(symbol) - 1):
                    self._advance()

                token_type = self._operator_symbols[symbol]
                self._add_token(token_type, symbol)  # 演算子の字句を保存
                return True
        return False

    def _identifier(self):
        while self._peek().isalnum() or self._peek() == "_":
            self._advance()

        text = self._source[self._start : self._current]

        # キーワードかどうかをチェック
        token_type = self._keywords.get(text)

        if token_type is None:
            # 演算子キーワード（例: 'mod'）もここで識別される可能性がある
            # OperatorRegistry に登録されているシンボルと一致するか確認
            op_info = operator_registry.get_operator(text)
            if op_info and op_info.token_type:
                try:
                    token_type = getattr(TokenType, op_info.token_type)
                except AttributeError:
                    # TokenType に動的に追加されていない場合はアトムとして扱う
                    token_type = TokenType.ATOM
            elif text[0].isupper() or text[0] == "_":
                token_type = TokenType.VARIABLE
            else:
                token_type = TokenType.ATOM

        self._add_token(token_type)

    def _number(self):
        while self._peek().isdigit():
            self._advance()
        if self._peek() == "." and self._peek_next().isdigit():
            self._advance()  # Consume the "."
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
        self._advance()  # The closing '.
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
            TokenType.LEFTPAREN,
            TokenType.RIGHTPAREN,
            TokenType.LEFTBRACKET,
            TokenType.RIGHTBRACKET,
            TokenType.COMMA,
            TokenType.DOT,
            TokenType.BAR,
            TokenType.COLONMINUS,
            TokenType.UNDERSCORE,
            TokenType.EOF,
        ]:
            literal = text  # ATOM, VARIABLE, STRING, NUMBER などの場合に字句を保存
        self._tokens.append(
            Token(type, literal if literal is not None else text, literal, self._line)
        )
