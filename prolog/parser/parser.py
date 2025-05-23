from .token_type import TokenType
from .token import Token
from prolog.core.types import Variable, Term, Rule, Conjunction, TRUE_TERM as TRUE
from prolog.runtime.builtins import Fail, Write, Nl, Tab, Retract, AssertA, AssertZ, Cut
from .types import Arithmetic, Logic, Number, Dot, Bar
from .expression import BinaryExpression, PrimaryExpression
from prolog.util.logger import logger


logger.debug("parser.py loaded (new version)")


def default_error_handler(line, message):
    print(f"Line[{line}] Error: {message}")
    raise Exception("Parser error")


def is_single_param_buildin(token_type):
    st = set([TokenType.RETRACT, TokenType.ASSERTA, TokenType.ASSERTZ])
    if token_type in st:
        return True
    return False


class Parser:
    def __init__(self, tokens, report=default_error_handler):
        logger.debug(
            f"Parser initialized with tokens (first 5): {tokens[:5]}{'...' if len(tokens) > 5 else ''}"
        )
        self._current = 0
        self._is_done = False
        self._scope = {}
        self._tokens = tokens
        self._report = report

    def _peek(self):
        logger.debug(
            f"Parser._peek: current={self._current}, tokens_length={len(self._tokens)}"
        )
        if self._current >= len(self._tokens):
            logger.error(
                f"Parser._peek: Index out of range! current={self._current}, tokens_length={len(self._tokens)}"
            )
            # エラーを直接投げるのではなく、EOFトークンを返す
            return Token(TokenType.EOF, "EOF", None, -1)
        return self._tokens[self._current]

    def _peek_next(self):
        return self._tokens[self._current + 1]

    def _is_at_end(self):
        # 現在のトークンがEOFトークンであるか、インデックスが最大値を超えているかをチェック
        return (
            self._current < len(self._tokens)
            and self._peek().token_type == TokenType.EOF
        ) or self._current >= len(self._tokens)

    def _previous(self):
        return self._tokens[self._current - 1]

    def _advance(self):
        logger.debug(
            f"Parser._advance: before: current={self._current}, tokens_length={len(self._tokens)}"
        )
        self._current += 1
        logger.debug(
            f"Parser._advance: after: current={self._current}, tokens_length={len(self._tokens)}"
        )
        if (
            self._current < len(self._tokens) and self._is_at_end()
        ):  # This check is after incrementing current
            self._is_done = True  # Assuming _is_done is a class member: self._is_done
        elif self._current >= len(
            self._tokens
        ):  # Also handle case where current goes out of bounds
            self._is_done = True
        return self._previous()

    def _token_matches(self, token_type):
        match_result = False
        # Ensure _peek() is safe, especially if it can return a dummy EOF token that might not have token_type
        # The current _peek() returns a Token object even for EOF, so .token_type should be safe.
        peeked_token = self._peek()

        if isinstance(token_type, list):
            match_result = peeked_token.token_type in token_type
        else:
            match_result = peeked_token.token_type == token_type
        logger.debug(
            f"Parser._token_matches: current_token={peeked_token}, expected={token_type}, result={match_result}"
        )
        return match_result

    def _next_token_matches(self, token_type):
        if self._current + 1 >= len(self._tokens):
            return False  # Next token does not exist, so it cannot match

        next_token = self._tokens[self._current + 1]  # Effectively self._peek_next()
        if isinstance(token_type, list):
            return next_token.token_type in token_type
        return next_token.token_type == token_type

    def _is_type(self, token, token_type):
        return token.token_type == token_type

    def _create_variable(self, name, has_arithmetic_exp=None):
        variable = self._scope.get(name, None)
        if variable is None:
            if has_arithmetic_exp is None:
                variable = Variable(name)
            else:
                variable = Arithmetic(name, has_arithmetic_exp)
            self._scope[name] = variable
        elif isinstance(variable, Variable) and has_arithmetic_exp is not None:
            variable = Arithmetic(name, has_arithmetic_exp)
        return variable

    def _parse_primary(self):
        token = self._peek()

        if self._is_type(token, TokenType.NUMBER):
            self._advance()
            number_value = token.literal
            return PrimaryExpression(Number(number_value))
        elif self._is_type(token, TokenType.VARIABLE):
            self._advance()
            return PrimaryExpression(self._create_variable(token.lexeme))
        elif self._is_type(token, TokenType.LEFTPAREN):
            self._advance()
            expr = self._parse_expression()

            prev_token = self._advance()  # consume ')'
            if prev_token.token_type != TokenType.RIGHTPAREN:
                self._report(
                    self._peek().line, f'Expected ")" after expression: {expr}'
                )
            return expr

        self._report(self._peek().line, f"Expected number or variable but got: {token}")

    def _parse_equality(self):
        expr = self._parse_comperison()

        while self._token_matches([TokenType.EQUALEQUAL, TokenType.EQUALSLASH]):
            self._advance()
            operator = self._previous().lexeme
            right = self._parse_comperison()
            expr = BinaryExpression(expr, operator, right)
        return expr

    def _parse_comperison(self):
        expr = self._parse_addition()

        while self._token_matches(
            [
                TokenType.GREATER,
                TokenType.GREATEREQUAL,
                TokenType.LESS,
                TokenType.EQUALLESS,
            ]
        ):
            self._advance()
            operator = self._previous().lexeme
            right = self._parse_addition()
            expr = BinaryExpression(expr, operator, right)
        return expr

    def _parse_addition(self):
        expr = self._parse_multiplication()

        while self._token_matches([TokenType.MINUS, TokenType.PLUS]):
            self._advance()
            operator = self._previous().lexeme
            right = self._parse_multiplication()
            expr = BinaryExpression(expr, operator, right)
        return expr

    def _parse_multiplication(self):
        expr = self._parse_primary()

        while self._token_matches([TokenType.SLASH, TokenType.STAR]):
            self._advance()
            operator = self._previous().lexeme
            right = self._parse_primary()
            expr = BinaryExpression(expr, operator, right)
        return expr

    def _parse_expression(self):
        return self._parse_equality()

    def _parse_arithmetic(self, token):
        self._advance()  # consume IS

        return self._create_variable(token.lexeme, self._parse_expression())

    def _parse_logic(self):
        return Logic(self._parse_equality())

    def _parse_atom(self):
        token = self._advance()  # Consume the token

        if self._is_type(token, TokenType.TRUE):
            return TRUE()
        if self._is_type(token, TokenType.FAIL):
            return Fail()
        if self._is_type(token, TokenType.CUT):  # Assuming CUT token is for '!'
            return Cut()

        if (
            not self._is_type(token, TokenType.ATOM)
            and not self._is_type(token, TokenType.VARIABLE)
            and not self._is_type(token, TokenType.UNDERSCORE)
            and not self._is_type(token, TokenType.NUMBER)
            and not self._is_type(token, TokenType.WRITE)
            and not self._is_type(token, TokenType.NL)
            and not self._is_type(token, TokenType.TAB)
            and not self._is_type(token, TokenType.RETRACT)
            and not self._is_type(token, TokenType.ASSERTA)
            and not self._is_type(token, TokenType.ASSERTZ)
        ):
            self._report(
                token.line,
                f"Bad atom name or unexpected token: {token.lexeme} of type {token.token_type}",
            )
            return None

        if (
            self._is_type(token, TokenType.ATOM)
            or self._is_type(token, TokenType.VARIABLE)
            or self._is_type(token, TokenType.UNDERSCORE)
            or self._is_type(token, TokenType.NUMBER)
            or self._is_type(token, TokenType.WRITE)
            or self._is_type(token, TokenType.NL)
            or self._is_type(token, TokenType.TAB)
            or self._is_type(token, TokenType.RETRACT)
            or self._is_type(token, TokenType.ASSERTA)
            or self._is_type(token, TokenType.ASSERTZ)
        ):
            return token

        self._report(token.line, f"Unhandled token in _parse_atom: {token.lexeme}")
        return None

    def _parse_buildin_single_arg(self, predicate, args):
        if len(args) != 1:
            self._report(
                self._peek().line, f"{predicate} requires exactly one argument"
            )
        if predicate == "retract":
            return Retract(args[0])
        if predicate == "asserta":
            return AssertA(args[0])
        if predicate == "assertz":
            return AssertZ(args[0])

    def _parse_list(self):
        logger.debug(
            f"Parser._parse_list entered. Current token: {self._peek()}, index: {self._current}"
        )
        dot_list = []
        dot_tail = None
        self._advance()  # consume '['
        logger.debug(
            f"Parser._parse_list after consuming '[': next token: {self._peek()}, index: {self._current}"
        )

        if self._token_matches(TokenType.RIGHTBRACKET):
            logger.debug("Parser._parse_list: detected empty list pattern")
            self._advance()  # consume ']'
            result = Dot.from_list([])
            logger.debug(
                f"Parser._parse_list: parsed empty list with Dot.from_list([]): {result}, type: {type(result)}"
            )
            logger.debug(
                f"Parser._parse_list: finished parsing list: result: {result}, type: {type(result)}"
            )
            return result

        while not self._token_matches(TokenType.RIGHTBRACKET):
            if self._token_matches(TokenType.BAR):
                self._advance()  # consume '|'
                dot_tail = self._parse_term()
                if not self._token_matches(TokenType.RIGHTBRACKET):
                    self._report(
                        self._peek().line,
                        f"Expected ']' after | Tail in list, but got {self._peek()}",
                    )
                break

            list_element = None
            if self._token_matches(TokenType.LEFTBRACKET):
                list_element = self._parse_list()
            else:
                list_element = self._parse_term()
            dot_list.append(list_element)

            if self._token_matches(TokenType.COMMA):
                self._advance()  # consume ','
                if self._token_matches(TokenType.RIGHTBRACKET):
                    self._report(
                        self._peek().line, "Unexpected ']' after comma in list."
                    )
            elif not self._token_matches(
                TokenType.RIGHTBRACKET
            ) and not self._token_matches(TokenType.BAR):
                self._report(
                    self._peek().line,
                    f"Expected ',' or '|' or ']' in list element sequence, but got {self._peek()}",
                )

        if not self._token_matches(TokenType.RIGHTBRACKET):
            self._report(
                self._peek().line,
                f"List not properly closed. Expected ']', got {self._peek()}",
            )

        self._advance()  # consume right bracket

        if dot_tail is None:
            result = Dot.from_list(dot_list)
            logger.debug(
                f"Parser._parse_list: parsed proper list: {result}, type: {type(result)}"
            )
            logger.debug(
                f"Parser._parse_list: finished parsing list: result: {result}, type: {type(result)}"
            )
            return result
        else:
            result = Bar(Dot.from_list(dot_list), dot_tail)
            logger.debug(
                f"Parser._parse_list: parsed list with tail: {result}, type: {type(result)}"
            )
            logger.debug(
                f"Parser._parse_list: finished parsing list: result: {result}, type: {type(result)}"
            )
            return result

    def _parse_term(self):
        logger.debug(
            f"Parser._parse_term entered. Current token: {self._peek()}, index: {self._current}"
        )
        if self._token_matches(TokenType.LEFTPAREN):
            self._advance()
            args = []
            while not self._token_matches(TokenType.RIGHTPAREN):
                args.append(self._parse_term())
                if not self._token_matches(TokenType.COMMA) and not self._token_matches(
                    TokenType.RIGHTPAREN
                ):
                    self._report(
                        self._peek().line,
                        f"Expecter , or ) in term but got {self._peek()}",
                    )
                if self._token_matches(TokenType.COMMA):
                    self._advance()

            self._advance()
            result = Conjunction(args)
            logger.debug(
                f"Parser._parse_term: parsed conjunction in parens: {result}, type: {type(result)}"
            )
            return result

        if self._next_token_matches(
            [
                TokenType.EQUALEQUAL,
                TokenType.EQUALSLASH,
                TokenType.EQUALLESS,
                TokenType.LESS,
                TokenType.GREATEREQUAL,
                TokenType.GREATER,
            ]
        ):
            result = self._parse_logic()
            logger.debug(
                f"Parser._parse_term: parsed logic expression: {result}, type: {type(result)}"
            )
            return result

        if self._token_matches(TokenType.LEFTBRACKET):
            result = self._parse_list()
            logger.debug(
                f"Parser._parse_term: parsed list: {result}, type: {type(result)}"
            )
            return result

        atom_or_builtin_obj = self._parse_atom()
        logger.debug(
            f"Parser._parse_term after _parse_atom: atom_or_builtin_obj={atom_or_builtin_obj}, type={type(atom_or_builtin_obj)}, next token: {self._peek()}"
        )

        if isinstance(atom_or_builtin_obj, (TRUE, Fail, Cut)):
            if self._token_matches(TokenType.LEFTPAREN):
                self._report(
                    self._peek().line,
                    f"Special term '{type(atom_or_builtin_obj).__name__}' cannot be used as a functor.",
                )
                return None
            return atom_or_builtin_obj

        if atom_or_builtin_obj is None:
            logger.debug("Parser._parse_term: _parse_atom returned None, propagating.")
            return None

        token = atom_or_builtin_obj
        if token is None:
            self._report(
                self._peek().line,
                "Internal parser error: token became None unexpectedly.",
            )
            return None

        # predicate = token.lexeme if hasattr(token, 'lexeme') and token.token_type in [TokenType.ATOM, TokenType.VARIABLE, TokenType.WRITE, TokenType.RETRACT, TokenType.ASSERTA, TokenType.ASSERTZ] else None # F841 Removed

        lhs_term = None
        if self._is_type(token, TokenType.VARIABLE) or self._is_type(
            token, TokenType.UNDERSCORE
        ):
            if self._is_type(token, TokenType.UNDERSCORE):
                lhs_term = Variable("_")
            elif self._peek().token_type == TokenType.IS:
                lhs_term = self._parse_arithmetic(token)
            else:
                lhs_term = self._create_variable(token.lexeme)
        elif self._is_type(token, TokenType.NL):
            lhs_term = Nl()
        elif self._is_type(token, TokenType.TAB):
            lhs_term = Tab()
        elif self._is_type(token, TokenType.NUMBER):
            lhs_term = Number(token.literal)
        elif (
            self._is_type(token, TokenType.ATOM)
            or self._is_type(token, TokenType.WRITE)
            or is_single_param_buildin(token.token_type)
        ):
            current_predicate_name = token.lexeme

            if not self._token_matches(TokenType.LEFTPAREN):
                if self._is_type(token, TokenType.NL):
                    lhs_term = Nl()
                elif self._is_type(token, TokenType.TAB):
                    lhs_term = Tab()
                else:
                    lhs_term = Term(current_predicate_name)
            else:
                self._advance()
                args = []
                while not self._token_matches(TokenType.RIGHTPAREN):
                    parsed_arg = self._parse_term()
                    if parsed_arg is None:
                        return None
                    args.append(parsed_arg)
                    if not self._token_matches(
                        TokenType.COMMA
                    ) and not self._token_matches(TokenType.RIGHTPAREN):
                        self._report(
                            self._peek().line,
                            f"Expected , or ) in term arguments for {current_predicate_name}, but got {self._peek()}",
                        )
                        return None
                    if self._token_matches(TokenType.COMMA):
                        self._advance()
                self._advance()

                if is_single_param_buildin(token.token_type):
                    lhs_term = self._parse_buildin_single_arg(
                        current_predicate_name, args
                    )
                elif self._is_type(token, TokenType.WRITE):
                    lhs_term = Write(*args)
                else:
                    lhs_term = Term(current_predicate_name, *args)
        else:
            self._report(
                token.line,
                f"Parser._parse_term: Unhandled token type {token.token_type} ({token.lexeme if hasattr(token, 'lexeme') else 'N/A'}) for LHS parsing.",
            )
            return None

        if lhs_term is None:
            self._report(
                self._peek().line,
                f"Parser._parse_term: Could not determine LHS from token {token}",
            )
            return None

        logger.debug(
            f"Parser._parse_term: Parsed LHS: {lhs_term}, type: {type(lhs_term)}"
        )

        if self._token_matches(TokenType.EQUAL):
            self._advance()
            rhs_term = self._parse_term()
            if rhs_term is None:
                self._report(
                    self._peek().line,
                    "Missing or invalid right-hand side for '=' operator.",
                )
                return None

            equality_term = Term("=", lhs_term, rhs_term)
            logger.debug(
                f"Parser._parse_term: Parsed equality term: {equality_term}, type: {type(equality_term)}"
            )
            return equality_term

        logger.debug(
            f"Parser._parse_term: Parsed term (no '=' found after LHS): {lhs_term}, type: {type(lhs_term)}"
        )
        return lhs_term

    def _parse_rule(self):
        logger.debug(
            f"Parser._parse_rule entered. Current token: {self._peek()}, index: {self._current}"
        )
        head = self._parse_term()
        logger.debug(
            f"Parser._parse_rule after parsing head: head={head}, type={type(head)}, next token: {self._peek()}"
        )

        if self._token_matches(TokenType.DOT):
            self._advance()
            result = Rule(head, TRUE())
            logger.debug(
                f"Parser._parse_rule: parsed fact: {result}, type: {type(result)}"
            )
            return result

        if not self._token_matches(TokenType.COLONMINUS):
            self._report(
                self._peek().line, f"Expected :- in rule but got {self._peek()}"
            )

        self._advance()
        args = []
        while not self._token_matches(TokenType.DOT):
            args.append(self._parse_term())
            if not self._token_matches(TokenType.COMMA) and not self._token_matches(
                TokenType.DOT
            ):
                self._report(
                    self._peek().line,
                    f"Expected , or . in term but got {self._peek()}",
                )

            if self._token_matches(TokenType.COMMA):
                self._advance()

        self._advance()
        body = None
        if len(args) == 1:
            body = args[0]
        else:
            body = Conjunction(args)

        result = Rule(head, body)
        logger.debug(f"Parser._parse_rule: parsed rule: {result}, type: {type(result)}")
        return result

    def _all_vars(self, terms):
        variables = []
        for term in terms:
            if isinstance(term, Term):
                for arg in term.args:
                    if isinstance(arg, Variable):
                        if arg not in variables:
                            variables.append(arg)
        return variables

    def _parse_query(self):
        logger.debug(
            f"Parser._parse_query entered. Current token: {self._peek()}, index: {self._current}"
        )
        head_term = self._parse_term()
        logger.debug(
            f"Parser._parse_query: parsed head_term: {head_term}, current token: {self._peek()}, index: {self._current}"
        )

        # 明示的なピリオドで終わるクエリを処理
        if self._token_matches(TokenType.DOT):
            logger.debug("Parser._parse_query: detected single term query with DOT")
            self._advance()  # 消費 '.'
            return head_term

        # クエリとしてのルール定義は許可されない
        if self._token_matches(TokenType.COLONMINUS):
            self._report(self._peek().line, "Cannot use rule as a query")
            return None

        # EOF または最後のトークンに達した場合、暗黙のDOTとして扱う
        if (
            self._is_at_end() or self._current >= len(self._tokens) - 1
        ):  # Fixed: len(self._tokens) -1
            logger.debug(
                f"Parser._parse_query: implicit DOT at end of query, returning single term: {head_term}"
            )
            return head_term

        # ここから複合クエリ（コンジャンクション）の処理
        args = [head_term]

        # コンマで区切られた複数の項を処理
        while self._token_matches(TokenType.COMMA):
            self._advance()  # コンマを消費
            if self._token_matches(TokenType.DOT):  # 例: p(X),. のような不正なケース
                self._report(
                    self._peek().line,
                    "Unexpected '.' after comma in query conjunction.",
                )
                return None

            term_in_conj = self._parse_term()
            if term_in_conj is None:
                logger.error("Parser._parse_query: Failed to parse term in conjunction")
                return None
            args.append(term_in_conj)

        # 最後のピリオドを処理（存在する場合）
        if self._token_matches(TokenType.DOT):
            self._advance()  # 消費 '.'
        elif not self._is_at_end():
            # 明示的なDOTがなく、まだEOFに達していない場合
            logger.warning(
                f"Parser._parse_query: Expected '.' at end of query, got: {self._peek()}"
            )
            # Consider if an error should be reported or if it's an implicit DOT
            # For now, let's assume if it's not EOF and not DOT, it's a syntax issue if more tokens follow.
            # If no more tokens follow (covered by _is_at_end()), it's treated as implicit DOT.

        # 変数を収集してクエリルールを作成
        query_head_vars = self._all_vars(args)
        if query_head_vars:
            query_rule_head = Term("##", *query_head_vars)
        else:
            query_rule_head = Term("##")

        result = Rule(query_rule_head, Conjunction(args))
        logger.debug(f"Parser._parse_query: returning query as rule: {result}")
        return result

    def parse_rules(self):
        logger.debug("Parser.parse_rules (public) called")
        rules = []
        while not self._is_done and self._peek().token_type != TokenType.EOF:
            self._scope = {}
            rule = self._parse_rule()
            if rule:
                rules.append(rule)
            elif not self._is_done and self._peek().token_type != TokenType.EOF:
                logger.warning(
                    f"Parser.parse_rules: _parse_rule returned None. Next token: {self._peek()}. Stopping."
                )
                break
        logger.debug(
            f"Parser.parse_rules (public) returning: {rules}, count: {len(rules)}"
        )
        return rules

    def parse_terms(self):
        logger.debug("Parser.parse_terms (public) called")
        self._scope = {}
        if self._is_done or self._peek().token_type == TokenType.EOF:
            logger.debug(
                "Parser.parse_terms (public): No tokens or EOF. Returning None."
            )
            return None

        term = self._parse_term()
        logger.debug(f"Parser.parse_terms (public) returning: {term}")
        return term

    def parse_query(self):
        logger.debug("Parser.parse_query (public) called")
        self._scope = {}
        if self._is_done or self._peek().token_type == TokenType.EOF:
            logger.debug(
                "Parser.parse_query (public): No tokens or EOF. Returning None."
            )
            return None

        query = self._parse_query()
        logger.debug(f"Parser.parse_query (public) returning: {query}")
        return query
