# parser.py の完全修正版

from .token_type import TokenType

# from .token import Token # Unused import
from prolog.core.types import (
    Variable,
    Term,
    Rule,
    Conjunction,
    TRUE_TERM,
    Fail,
    EMPTY_LIST_ATOM, # Added for list parsing
)  # Removed TRUEClass, CUTClass
from prolog.runtime.builtins import Write, Nl, Tab, Retract, AssertA, AssertZ

# Cut は prolog.core.types から、Cutクラスをインポート
from prolog.core.types import Cut  # This is the Cut class from core.types
from .types import Arithmetic, Number  # Removed Logic

# from .expression import BinaryExpression, PrimaryExpression # Unused imports
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
    def __init__(self, tokens, error_handler=None):
        self._tokens = tokens
        self._current = 0
        self._error_handler = error_handler or default_error_handler
        self._variable_cache = {}

    def _create_variable(self, name):
        if name not in self._variable_cache:
            self._variable_cache[name] = Variable(name)
        return self._variable_cache[name]

    def _report(self, line, message):
        self._error_handler(line, message)

    def _advance(self):
        if not self._is_at_end():
            self._current += 1
        return self._previous()

    def _is_at_end(self):
        return self._peek().token_type == TokenType.EOF

    def _peek(self):
        return self._tokens[self._current]

    def _previous(self):
        return self._tokens[self._current - 1]

    def _token_matches(self, token_type):
        if self._is_at_end():
            return False
        return self._peek().token_type == token_type

    def _is_type(self, token, token_type):
        if token is None:
            return False
        return token.token_type == token_type

    def _expect(self, token_type, message):
        if self._token_matches(token_type):
            return self._advance()
        token_for_line = self._peek() if not self._is_at_end() else self._previous()
        line = getattr(token_for_line, 'line', -1)
        self._report(line, message)
        raise Exception(message)

    def _parse_list(self):
        logger.debug(f"Parser._parse_list entered. Current token: {self._peek()}")
        # _parse_term peeks for LEFTBRACKET, then calls _parse_list.
        # _parse_list should start by consuming LEFTBRACKET.
        self._advance() # Consume '[' (LEFTBRACKET)

        if self._token_matches(TokenType.RIGHTBRACKET): # Corrected: RIGHTBRACKET
            self._advance()  # Consume ']'
            logger.debug("Parser._parse_list: Parsed empty list.")
            return EMPTY_LIST_ATOM

        elements = []
        while True:
            if self._is_at_end():
                self._report(self._previous().line, "Unexpected EOF in list.")
                return None # Or raise
            
            term = self._parse_term()
            if term is None:
                return None
            elements.append(term)

            if self._token_matches(TokenType.COMMA):
                self._advance()  # Consume ','
                if self._token_matches(TokenType.RIGHTBRACKET): # Corrected: RIGHTBRACKET, Case like [a,]
                    self._report(self._peek().line, "Unexpected ']' after comma in list, expected term.")
                    return None # Or raise
                if self._token_matches(TokenType.BAR): # Case like [a,|]
                     self._report(self._peek().line, "Unexpected '|' after comma in list.")
                     return None # Or raise
                if self._is_at_end(): # Case like [a, EOF
                    self._report(self._previous().line, "Unexpected EOF after comma in list.")
                    return None # Or raise
            elif self._token_matches(TokenType.BAR):
                self._advance()  # Consume '|'
                if self._is_at_end():
                    self._report(self._previous().line, "Unexpected EOF after '|' in list.")
                    return None # Or raise
                tail = self._parse_term()
                if tail is None:
                    return None
                self._expect(TokenType.RIGHTBRACKET, "Expected ']' after tail in list.") # Corrected: RIGHTBRACKET
                
                current_list = tail
                for element in reversed(elements):
                    current_list = Term('.', [element, current_list])
                logger.debug(f"Parser._parse_list: Parsed list with tail: {current_list}")
                return current_list
            elif self._token_matches(TokenType.RIGHTBRACKET): # Corrected: RIGHTBRACKET
                self._advance()  # Consume ']'
                current_list = EMPTY_LIST_ATOM
                for element in reversed(elements):
                    current_list = Term('.', [element, current_list])
                logger.debug(f"Parser._parse_list: Parsed proper list: {current_list}")
                return current_list
            else:
                self._report(self._peek().line, f"Expected ',', '|', or ']' in list, but got {self._peek().token_type}.")
                return None # Or raise

    def _parse_atom(self):
        # This method is called when _parse_term has determined the upcoming token
        # is NOT a LEFT_BRACKET. It's for parsing simple elements like atoms, numbers, vars.
        peeked_token = self._peek()

        if self._is_type(peeked_token, TokenType.TRUE):
            self._advance()
            return TRUE_TERM
        if self._is_type(peeked_token, TokenType.FAIL):
            self._advance()
            return Fail()
        if self._is_type(peeked_token, TokenType.CUT):
            self._advance()
            return Cut()

        token = self._advance() # Consume the actual token

        # These token types are returned directly as they are,
        # _parse_term will then convert them to Variable, Number, or use lexeme for Term.
        valid_simple_tokens = [
            TokenType.ATOM, TokenType.VARIABLE, TokenType.UNDERSCORE,
            TokenType.NUMBER, TokenType.WRITE, TokenType.NL, TokenType.TAB,
            TokenType.RETRACT, TokenType.ASSERTA, TokenType.ASSERTZ
        ]
        if token.token_type in valid_simple_tokens:
            return token
        
        self._report(
            token.line,
            f"Expected an atom, variable, number, or special constant, but got: {token.lexeme} of type {token.token_type}",
        )
        return None


    def _parse_term(self):
        logger.debug(
            f"Parser._parse_term entered. Current token: {self._peek()}, index: {self._current}"
        )

        # Check for list start first: '['
        if self._token_matches(TokenType.LEFTBRACKET): # Use LEFTBRACKET
            return self._parse_list()

        # If not a list, proceed to parse atom, variable, number, or special constants
        atom_or_builtin_obj = self._parse_atom() # _parse_atom now returns Token or special instance
        
        logger.debug(
            f"Parser._parse_term after _parse_atom: atom_or_builtin_obj={atom_or_builtin_obj}, type={type(atom_or_builtin_obj)}, next token: {self._peek()}"
        )

        # Handle special constants like true, fail, !
        if atom_or_builtin_obj is TRUE_TERM or isinstance(atom_or_builtin_obj, (Fail, Cut)):
            # These cannot be functors
            if self._token_matches(TokenType.LEFTPAREN):
                self._report(
                    self._peek().line,
                    f"Special term '{type(atom_or_builtin_obj).__name__}' cannot be used as a functor.",
                )
                return None # Or raise
            return atom_or_builtin_obj

        if atom_or_builtin_obj is None: # Error from _parse_atom
            logger.debug("Parser._parse_term: _parse_atom returned None, propagating.")
            return None

        # At this point, atom_or_builtin_obj is a Token object (e.g., ATOM, VARIABLE, NUMBER, etc.)
        token = atom_or_builtin_obj
        
        lhs_term = None # This will hold the parsed Term, Variable, Number, etc.

        # Convert Token to specific AST node (Variable, Number, or prepare for Term)
        if self._is_type(token, TokenType.VARIABLE) or self._is_type(token, TokenType.UNDERSCORE):
            if self._is_type(token, TokenType.UNDERSCORE):
                lhs_term = Variable("_")
            elif self._peek().token_type == TokenType.IS: # Arithmetic expression: Var is Expr
                lhs_term = self._parse_arithmetic(token) # _parse_arithmetic consumes 'is' and expr
            else: # Simple variable
                lhs_term = self._create_variable(token.lexeme)
        elif self._is_type(token, TokenType.NL):
            lhs_term = Nl()
        elif self._is_type(token, TokenType.TAB):
            lhs_term = Tab()
        elif self._is_type(token, TokenType.NUMBER):
            lhs_term = Number(token.literal)
        elif ( # ATOM or built-in predicate name that can be a functor
            self._is_type(token, TokenType.ATOM) or
            self._is_type(token, TokenType.WRITE) or
            is_single_param_buildin(token.token_type) # retract, asserta, assertz
        ):
            current_predicate_name = token.lexeme
            if not self._token_matches(TokenType.LEFTPAREN): # Simple atom or 0-arity builtin (if any)
                # Note: NL and TAB are handled above. Write, Retract, etc., expect args.
                # So this path is mainly for simple atoms like 'foo'.
                lhs_term = Term(current_predicate_name)
            else: # Functor: pred(...) or builtin_pred(...)
                self._advance()  # Consume '('
                args = []
                if self._token_matches(TokenType.RIGHTPAREN): # pred() case
                    self._advance() # Consume ')'
                    # For some builtins like write(), this might be valid (prints newline or similar)
                    # For user-defined predicates, arity 0 with () is usually same as without.
                else:
                    while True:
                        parsed_arg = self._parse_term()
                        if parsed_arg is None: return None
                        args.append(parsed_arg)
                        if self._token_matches(TokenType.RIGHTPAREN):
                            self._advance()
                            break
                        self._expect(TokenType.COMMA, "Expected ',' or ')' in arguments.")
                        if self._token_matches(TokenType.RIGHTPAREN):
                            self._report(self._peek().line, "Unexpected ')' after comma in arguments.")
                            return None # Or raise

                # Construct Term or specific Builtin class instance
                if is_single_param_buildin(token.token_type):
                    lhs_term = self._parse_buildin_single_arg(current_predicate_name, args)
                elif self._is_type(token, TokenType.WRITE):
                    lhs_term = Write(*args)
                else: # User-defined predicate or other functor
                    lhs_term = Term(current_predicate_name, *args)
        else:
            # This case should ideally not be reached if _parse_atom and list parsing are exhaustive
            lexeme = getattr(token, "lexeme", "N/A")
            token_type_val = getattr(token, "token_type", "Unknown") # Renamed to avoid clash
            line = getattr(token, "line", -1)
            self._report(line, f"Parser._parse_term: Unhandled token type {token_type_val} ({lexeme}) for term construction.")
            return None

        if lhs_term is None:
            self._report(self._peek().line, f"Parser._parse_term: Failed to construct term from token {token}")
            return None
        
        logger.debug(f"Parser._parse_term: Parsed LHS: {lhs_term}, type: {type(lhs_term)}")

        # Check for '=' operator (unification)
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
            result = Rule(head, TRUE_TERM)  # TRUE_TERMを使用
            logger.debug(
                f"Parser._parse_rule: parsed fact: {result}, type: {type(result)}"
            )
            return result

        if not self._token_matches(TokenType.COLONMINUS):
            self._report(
                self._peek().line, f"Expected :- in rule but got {self._peek()}"
            )
            return None  # エラー時はNoneを返す

        self._advance()
        args = []
        while not self._token_matches(TokenType.DOT):
            term_arg = self._parse_term()
            if term_arg is None:  # _parse_termがエラーでNoneを返した場合
                return None
            args.append(term_arg)

            if not self._token_matches(TokenType.COMMA) and not self._token_matches(
                TokenType.DOT
            ):
                self._report(
                    self._peek().line,
                    f"Expected , or . in term but got {self._peek()}",
                )
                return None  # エラー時はNoneを返す

            if self._token_matches(TokenType.COMMA):
                self._advance()
            elif self._token_matches(
                TokenType.DOT
            ):  # ドットが見つかったらループを抜ける
                break
            else:  # カンマでもドットでもない場合（実際には上のチェックで捕捉されるはず）
                self._report(
                    self._peek().line,
                    f"Unexpected token in rule body: {self._peek()}",
                )
                return None

        if not self._token_matches(TokenType.DOT):
            self._report(
                self._peek().line,
                f"Rule body must end with a dot. Found: {self._peek()}",
            )
            return None

        self._advance()  # Consume the dot
        body = None
        if len(args) == 1:
            body = args[0]
        elif len(args) > 1:
            body = Conjunction(args)
        else:  # argsが空の場合（例： `p :- .` のような不正なケース）
            self._report(
                self._peek().line,  # or self._previous().line if more appropriate
                "Rule body cannot be empty after ':-'.",
            )
            return None

        result = Rule(head, body)
        logger.debug(f"Parser._parse_rule: parsed rule: {result}, type: {type(result)}")
        return result

    def _parse_buildin_single_arg(self, predicate_name, args):
        if len(args) != 1:
            self._report(
                self._peek().line,
                f"Built-in {predicate_name} expects 1 argument, got {len(args)}",
            )
        if predicate_name == "retract":
            return Retract(args[0])
        elif predicate_name == "asserta":
            return AssertA(args[0])
        elif predicate_name == "assertz":
            return AssertZ(args[0])
        else:
            self._report(
                self._peek().line, f"Unknown single-argument built-in: {predicate_name}"
            )
            return None  # 不明なビルトイン

    def _parse_primary_arithmetic_expr(self):
        """Parses a primary arithmetic expression (Number, Variable, or parenthesized expression)."""
        if self._token_matches(TokenType.NUMBER):
            token = self._advance()
            return Number(token.literal)
        elif self._token_matches(TokenType.VARIABLE):
            token = self._advance()
            return self._create_variable(token.lexeme)
        elif self._token_matches(TokenType.LEFTPAREN):
            self._advance()  # Consume '('
            expr = self._parse_additive_expr() # Start parsing the inner expression
            if not self._token_matches(TokenType.RIGHTPAREN):
                self._report(self._peek().line, "Expected ')' after expression.")
                return None
            self._advance()  # Consume ')'
            return expr
        else:
            self._report(self._peek().line, f"Unexpected token in arithmetic expression: {self._peek().lexeme}")
            return None

    def _parse_multiplicative_expr(self):
        """Parses multiplicative expressions (*, /)."""
        expr = self._parse_primary_arithmetic_expr()
        if expr is None: return None

        while self._token_matches(TokenType.STAR) or self._token_matches(TokenType.SLASH):
            operator_token = self._advance()
            op_type = operator_token.token_type
            
            right = self._parse_primary_arithmetic_expr()
            if right is None: return None
            
            # Assuming Arithmetic can handle operator type or we need a more complex structure
            # For now, let's assume Arithmetic stores operator as string and two operands
            # This might require changes to the Arithmetic class in prolog.parser.types
            op_str = "*" if op_type == TokenType.STAR else "/"
            expr = Term(op_str, expr, right) # Using Term for now, ideally Arithmetic class handles this
        return expr

    def _parse_additive_expr(self):
        """Parses additive expressions (+, -)."""
        expr = self._parse_multiplicative_expr()
        if expr is None: return None

        while self._token_matches(TokenType.PLUS) or self._token_matches(TokenType.MINUS):
            operator_token = self._advance()
            op_type = operator_token.token_type

            right = self._parse_multiplicative_expr()
            if right is None: return None

            op_str = "+" if op_type == TokenType.PLUS else "-"
            expr = Term(op_str, expr, right) # Using Term for now
        return expr

    def _parse_arithmetic(self, variable_token):
        """Parses an 'is' expression: Variable is ArithmeticExpression."""
        variable = self._create_variable(variable_token.lexeme)
        if not self._token_matches(TokenType.IS):
            # This check should ideally be done before calling _parse_arithmetic
            self._report(self._peek().line, "Expected 'is' operator.")
            return None
        
        self._advance()  # Consume 'is'

        expression_rhs = self._parse_additive_expr() # Start with highest precedence
        
        if expression_rhs is None:
            # _parse_additive_expr should have reported the error
            return None

        return Arithmetic(variable, expression_rhs)

    def parse(self):
        statements = []
        self._variable_cache = {}  # 各文のパース前にキャッシュをリセット
        while not self._is_at_end():
            try:
                stmt = self._parse_rule()
                if stmt:  # stmtがNoneでない場合のみ追加
                    statements.append(stmt)
                else:
                    # _parse_ruleがNoneを返した場合、エラーが発生しているはずなので、
                    # エラーリカバリを試みるか、パースを中止する
                    # ここでは単純に次のトークンに進んでリカバリを試みる（より高度なリカバリが必要な場合もある）
                    logger.warning(
                        "Parser.parse: _parse_rule returned None, attempting to recover by advancing."
                    )
                    if not self._is_at_end():  # EOFでなければ進む
                        # エラー箇所に応じて、どこまでスキップするかを決める必要がある
                        # 例えば、次のドット(.)やEOFまでスキップするなど
                        # ここでは単純に1トークン進めるが、これでは不十分な場合が多い
                        # self._advance() # この行は慎重に。無限ループの可能性も。
                        # より安全なのは、エラーが発生したらパースを中止するか、
                        # 次の明確な区切り（例：次の '.'）までスキップする戦略。
                        # 今回はエラーハンドラが例外を投げる設定なので、実際にはここまで来ない想定。
                        # もし例外を投げないエラーハンドラを使う場合は、ここでの処理が重要になる。
                        pass  # default_error_handlerが例外を投げるので、ここは実行されないはず

            except Exception as e:
                logger.error(f"Parser.parse: Exception during parsing: {e}")
                # エラーが発生した場合、通常はパースを中止するか、
                # エラーリカバリを試みる。
                # default_error_handler が例外を投げるので、ループはここで終了する。
                # もし例外をキャッチして継続したい場合は、ここでエラー処理を行う。
                break  # エラーが発生したらパースを中止

        return statements
