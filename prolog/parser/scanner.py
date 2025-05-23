from .token import Token
from .token_type import TokenType
from prolog.core.errors import ScannerError  # 修正: 正しいパスからインポート
from prolog.util.logger import logger

logger.debug("scanner.py loaded")


def default_error_handler(line, message):
    print(f"Line[{line}] Error: {message}")
    raise ScannerError("Scanner error")


class Scanner:
    def __init__(self, source, report=default_error_handler):
        logger.debug(
            f"Scanner initialized with source: {source[:50]}{'...' if len(source) > 50 else ''}"
        )
        self._source = source
        self._tokens = []
        self._start = 0
        self._current = 0
        self._line = 1
        self._report = report
        self._keywords = self._initialize_keywords()

    def _initialize_keywords(self):
        keywords = {
            "fail": TokenType.FAIL,
            "write": TokenType.WRITE,
            "nl": TokenType.NL,
            "tab": TokenType.TAB,
            "is": TokenType.IS,
            "retract": TokenType.RETRACT,
            "asserta": TokenType.ASSERTA,
            "assertz": TokenType.ASSERTZ,
            "true": TokenType.TRUE,
            "mod": TokenType.MOD,
            "div": TokenType.DIV,
        }
        return keywords

    def _add_token(self, token_type):
        self._add_token_with_literal(token_type, None)

    def _add_token_with_literal(self, token_type, literal, lex=None):
        lexeme = self._source[self._start : self._current] if lex is None else lex
        # logger.debug(f"Adding token: type={token_type}, lexeme='{lexeme}', literal={literal}, line={self._line}") # Potentially too verbose
        self._tokens.append(Token(token_type, lexeme, literal, self._line))

    def _is_at_end(self):
        return self._current >= len(self._source)

    def _advance(self):
        self._current += 1
        return self._source[self._current - 1]

    def _make_token(self, token_type, literal, line):
        lexeme = self._source[self._start : self._current]
        return Token(token_type, lexeme, literal, line)

    def _is_next(self, expected):
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

    def _is_digit(self, c):
        return c >= "0" and c <= "9"

    def _is_alphanumeric(self, c):
        return (
            (c >= "a" and c <= "z")
            or (c >= "A" and c <= "Z")
            or (c >= "0" and c <= "9")
            or (c == "_")
        )

    def _is_lowercase_alpha(self, c):
        return c >= "a" and c <= "z"

    def _is_uppercase_alpha(self, c):
        return c >= "A" and c <= "Z"

    def _is_whitespace(self, c):
        return c == " " or c == "\r" or c == "\t"

    def _str_to_number(self, strnum):
        try:
            return float(strnum)
        except Exception:
            self._report(self._line, f'"{strnum}" is not a number.')

    def _is_keyword(self):
        value = self._source[self._start : self._current]
        token_type = self._keywords.get(value, TokenType.ATOM)
        return token_type

    def _process_atom(self):
        while self._is_alphanumeric(self._peek()):
            self._advance()

        token_type = self._is_keyword()
        self._add_token(token_type)

    def _process_variable(self):
        while self._is_alphanumeric(self._peek()):
            self._advance()

        self._add_token(TokenType.VARIABLE)

    def _process_number(self):
        while self._is_digit(self._peek()):
            self._advance()

        if self._peek() == "." and self._is_digit(self._peek_next()):
            self._advance()
            while self._is_digit(self._peek()):
                self._advance()

        value = self._str_to_number(self._source[self._start : self._current])
        self._add_token_with_literal(TokenType.NUMBER, value)

    def _process_string_literal(self):
        while self._peek() != "'" and not self._is_at_end():
            if self._peek() == "\n":
                self._line += 1
            self._advance()

        if self._is_at_end():
            self._report(self._line, "Unterminated string")

        self._advance()

        literal = self._source[self._start + 1 : self._current - 1]
        self._add_token_with_literal(TokenType.ATOM, literal, literal)

    def _scan_token(self):
        c = self._advance()

        if self._is_whitespace(c):
            pass
        elif c == "\n":
            self._line += 1
        elif c == "%":
            while not self._peek() == "\n" and not self._is_at_end():
                self._advance()
        elif c == "/" and self._is_next("*"):
            while not self._is_at_end():
                c = self._advance()
                if c == "*" and self._is_next("/"):
                    break
                if self._is_at_end():
                    self._report(self._line, "Unterminated comment")
        elif c == "'":
            self._process_string_literal()
        elif self._is_lowercase_alpha(c):
            self._process_atom()
        elif c == "_":
            if not self._is_alphanumeric(self._peek_next()):
                self._add_token(TokenType.UNDERSCORE)
            else:
                self._process_variable()
        elif self._is_uppercase_alpha(c):
            self._process_variable()
        elif c == "-" and self._is_digit(self._peek()):
            # TODO: refactor this logic to unary operator
            self._process_number()
        elif self._is_digit(c):
            self._process_number()
        elif c == "[":
            self._add_token(TokenType.LEFTBRACKET)
        elif c == "]":
            self._add_token(TokenType.RIGHTBRACKET)
        elif c == "|":
            self._add_token(TokenType.BAR)
        elif c == "!":
            self._add_token(TokenType.CUT)
        elif c == "(":
            self._add_token(TokenType.LEFTPAREN)
        elif c == ")":
            self._add_token(TokenType.RIGHTPAREN)
        elif c == "*":
            self._add_token(TokenType.STAR)
        elif c == "/":
            self._add_token(TokenType.SLASH)
        elif c == "+":
            self._add_token(TokenType.PLUS)
        elif c == "-":
            self._add_token(TokenType.MINUS)
        elif c == "=":
            if self._is_next("="): # ==
                self._add_token(TokenType.EQUALEQUAL)
            elif self._is_next(":"): # =:=
                if self._is_next("="):
                    self._add_token(TokenType.EQUALCOLONEQUAL) # TokenType.EQUAL_ARITH or similar
                else:
                    # Rollback _is_next for ':'
                    self._current -=1
                    self._report(self._line, f"Expected `=` after `=:` for `=:=` operator, found `{self._peek()}`")
            elif self._is_next("\\"): # =\=
                if self._is_next("="):
                    self._add_token(TokenType.EQUALSLASHEQUAL) # TokenType.NOT_EQUAL_ARITH or similar
                else:
                    # Rollback _is_next for '\'
                    self._current -=1
                    self._report(self._line, f"Expected `=` after `=\\` for `=\=` operator, found `{self._peek()}`")
            elif self._is_next("<"): # =<
                self._add_token(TokenType.EQUALLESS)
            # Note: EQUALSLASH for =/= might need to be distinct from =\=
            # For now, assuming EQUALSLASH was intended for =/=
            elif self._is_next("/"): # =/=
                 if self._is_next("="): # Check for =/=
                    self._add_token(TokenType.EQUALSLASH) # Or a more specific =/= token
                 else:
                    # Rollback _is_next for '/'
                    self._current -=1
                    self._add_token(TokenType.EQUAL) # Fallback to just = if not =/=
            else:  # 単独の = 演算子
                self._add_token(TokenType.EQUAL)
        elif c == "<":
            if self._is_next("="): # <=
                self._add_token(TokenType.LESSEQUAL)
            else:
                self._add_token(TokenType.LESS)
        elif c == ">":
            if self._is_next("="): # >=
                self._add_token(TokenType.GREATEREQUAL)
            else:
                self._add_token(TokenType.GREATER)
        elif c == ":":
            if self._is_next("-"): # :-
                self._add_token(TokenType.COLONMINUS)
            # Removed the 'else' that reported "Expected - but found :",
            # as a single ':' might be part of another operator like '=:'
            # or could be an error if it's truly standalone and not expected.
            # If a standalone ':' is an error, it should be caught after all valid multi-char ops are checked.
            # For now, let it fall through to "Unexpected character" if not part of a known sequence.
            else: # A single ':' is not a standard token on its own usually.
                 self._report(self._line, f"Unexpected character after colon: {self._peek()}")

        elif c == ".":
            self._add_token(TokenType.DOT)
        elif c == ",":
            self._add_token(TokenType.COMMA)
        else:
            self._report(self._line, f"Unexpected character: {c}")

    def tokenize(self):
        logger.debug("Scanner.tokenize called")
        while self._is_at_end() is not True:
            self._start = self._current
            self._scan_token()

        self._add_token(TokenType.EOF)
        logger.debug(
            f"Scanner.tokenize returning (first 5): {self._tokens[:5]}{'...' if len(self._tokens) > 5 else ''}"
        )
        return self._tokens
