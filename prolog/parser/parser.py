from prolog.parser.token import Token
from prolog.parser.token_type import TokenType
from prolog.core.types import Term, Variable, Atom, Number, String, Rule, Fact
from prolog.core.operators import operator_registry, Associativity


# エラーハンドラーのデフォルト実装
def default_error_handler(token, message):
    if hasattr(token, "token_type") and token.token_type == TokenType.EOF:
        print(f"Error at end: {message}")
    else:
        lexeme = getattr(token, "lexeme", str(token))
        print(f"Error at '{lexeme}': {message}")


class Parser:
    def __init__(self, tokens, error_handler=default_error_handler):
        self._tokens = tokens
        self._current = 0
        self._error_handler = error_handler

    def parse(self):
        """プログラム全体を解析し、ルールのリストを返す"""
        rules = []
        while not self._is_at_end():
            if self._peek_token_type() == TokenType.EOF:
                break
            rule = self._parse_rule()
            if rule:
                rules.append(rule)
            if not self._match(TokenType.DOT):
                if not self._is_at_end():
                    self._error(self._peek(), "Expected '.' after rule or fact.")
                break
        return rules

    def _parse_rule(self):
        """単一のルールまたはファクトを解析"""
        parsed_head_candidate = self._parse_term()

        if parsed_head_candidate is None:
            return None

        head_term: Term
        if isinstance(parsed_head_candidate, Atom):
            head_term = Term(parsed_head_candidate, [])
        elif isinstance(parsed_head_candidate, Term):
            head_term = parsed_head_candidate
        else:
            self._error(
                self._previous() if self._current > 0 else self._tokens[0],
                f"Rule or Fact head must be a structure or an atom, not {type(parsed_head_candidate)}.",
            )
            return None

        if self._match(TokenType.COLONMINUS):
            body_terms = []
            while not self._check(TokenType.DOT) and not self._is_at_end():
                term_in_body = self._parse_term()
                if term_in_body is None:
                    return None
                body_terms.append(term_in_body)
                if self._match(TokenType.COMMA):
                    continue
                elif self._check(TokenType.DOT):
                    break
                else:
                    self._error(self._peek(), "Expected ',' or '.' in rule body.")
                    return None

            if not body_terms:
                self._error(self._peek(), "Rule body cannot be empty after ':-'.")
                return None

            if len(body_terms) == 1:
                raw_body = body_terms[0]
            else:
                raw_body = self._build_conjunction(body_terms)

            if raw_body is None:
                self._error(self._peek(), "Failed to construct rule body.")
                return None

            final_body: Term
            if isinstance(raw_body, Atom):
                final_body = Term(raw_body, [])
            elif isinstance(raw_body, Term):
                final_body = raw_body
            else:
                self._error(
                    self._previous() if self._current > 0 else self._tokens[0],
                    f"Rule body goal must be a structure or an atom, not {type(raw_body)}.",
                )
                return None

            return Rule(head_term, final_body)
        else:
            return Fact(head_term)

    def _build_conjunction(self, terms):
        """項のリストからコンジャンクションのTermを構築"""
        if not terms:
            return None

        if len(terms) == 1:
            return terms[0]

        result_conj = terms[-1]
        for i in range(len(terms) - 2, -1, -1):
            arg1 = terms[i]
            arg2 = result_conj
            result_conj = Term(Atom(","), [arg1, arg2])
        return result_conj

    def _parse_term(self):
        """単一の項を解析 (演算子優先順位法を利用)"""
        return self._parse_expression_with_precedence(1200)

    def _parse_expression_with_precedence(self, max_allowed_op_precedence: int):
        """演算子優先度を考慮した式解析"""
        left = self._parse_primary()
        if left is None:
            return None

        while not self._is_at_end():
            peek_token = self._peek()

            if not hasattr(peek_token, "lexeme"):
                break

            current_op_symbol = peek_token.lexeme
            if not operator_registry.is_operator(current_op_symbol):
                break

            op_info = operator_registry.get_operator(current_op_symbol)
            if not op_info:
                self._error(
                    peek_token,
                    f"Internal error: Operator '{current_op_symbol}' recognized but not found in registry.",
                )
                return None

            if op_info.precedence > max_allowed_op_precedence:
                break

            self._advance()  # Consume operator

            if op_info.associativity == Associativity.LEFT:
                next_max_precedence_for_rhs = op_info.precedence - 1
            elif op_info.associativity == Associativity.RIGHT:
                next_max_precedence_for_rhs = op_info.precedence
            else:  # NON_ASSOCIATIVE
                next_max_precedence_for_rhs = op_info.precedence - 1

            right = self._parse_expression_with_precedence(next_max_precedence_for_rhs)
            if right is None:
                self._error(
                    self._peek(),
                    f"Expected right-hand operand for operator '{current_op_symbol}'.",
                )
                return None

            left = Term(Atom(current_op_symbol), [left, right])

        return left

    def _parse_primary(self):
        """最も基本的な要素を解析"""
        if self._match(TokenType.ATOM):
            atom_name = self._previous().lexeme
            if self._match(TokenType.LEFTPAREN):
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
                self._consume(TokenType.RIGHTPAREN, "Expected ')' after arguments.")
                return Term(Atom(atom_name), args)
            else:
                return Atom(atom_name)

        elif self._match(TokenType.NUMBER):
            literal = self._previous().literal
            if not isinstance(literal, (int, float)):
                self._error(
                    self._previous(),
                    "Internal error: Number literal is not int or float.",
                )
                return None
            return Number(literal)

        elif self._match(TokenType.VARIABLE):
            return Variable(self._previous().lexeme)

        elif self._match(TokenType.STRING):
            literal = self._previous().literal
            if not isinstance(literal, str):
                self._error(
                    self._previous(), "Internal error: String literal is not str."
                )
                return None
            return String(literal)

        elif self._match(TokenType.LEFTPAREN):
            expr = self._parse_term()
            if expr is None:
                return None
            self._consume(TokenType.RIGHTPAREN, "Expected ')' after expression.")
            return expr

        elif self._match(TokenType.LEFTBRACKET):
            elements = []
            if not self._check(TokenType.RIGHTBRACKET):
                while True:
                    el = self._parse_term()
                    if el is None:
                        return None
                    elements.append(el)
                    if self._match(TokenType.COMMA):
                        continue
                    break

            tail = None
            if self._match(TokenType.BAR):
                tail = self._parse_term()
                if tail is None:
                    return None

            self._consume(TokenType.RIGHTBRACKET, "Expected ']' after list elements.")

            if tail is None:
                current_list_term = Atom("[]")
            else:
                current_list_term = tail

            for element in reversed(elements):
                current_list_term = Term(Atom("."), [element, current_list_term])
            return current_list_term

        self._error(self._peek(), "Expected expression.")
        return None

    def _consume(self, token_type: TokenType, message: str) -> Token:
        if self._check(token_type):
            return self._advance()
        self._error(self._peek(), message)
        # ダミーのTokenを返す（エラー回復のため）
        return Token(
            token_type, "", None, self._peek().line if not self._is_at_end() else 0
        )

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
        """Tokenの型を安全に取得"""
        token = self._peek()
        if hasattr(token, "token_type"):
            return token.token_type
        elif hasattr(token, "type"):
            return token.token_type
        else:
            # フォールバック
            return TokenType.EOF

    def _error(self, token: Token, message: str) -> None:
        self._error_handler(token, message)


class ParseError(RuntimeError):
    pass
