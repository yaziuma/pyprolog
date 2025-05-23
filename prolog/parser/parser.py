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

    def _parse_atom(self):
        token = self._advance()  # Consume the token

        if self._is_type(token, TokenType.TRUE):
            return TRUE_TERM  # インスタンスを直接返す
        if self._is_type(token, TokenType.FAIL):
            return Fail()
        if self._is_type(token, TokenType.CUT):
            return Cut()

        # 残りのコードは変更なし
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

    def _parse_term(self):
        logger.debug(
            f"Parser._parse_term entered. Current token: {self._peek()}, index: {self._current}"
        )

        atom_or_builtin_obj = self._parse_atom()
        logger.debug(
            f"Parser._parse_term after _parse_atom: atom_or_builtin_obj={atom_or_builtin_obj}, type={type(atom_or_builtin_obj)}, next token: {self._peek()}"
        )

        # 型チェックを修正：TRUE_TERMとの直接比較、FailおよびCutクラスとのisinstance比較
        if atom_or_builtin_obj is TRUE_TERM or isinstance(
            atom_or_builtin_obj, (Fail, Cut)
        ):  # Cutはprolog.core.types.Cut
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
            # 安全な属性アクセス
            lexeme = getattr(token, "lexeme", "N/A")
            token_type = getattr(token, "token_type", "Unknown")
            line = getattr(token, "line", -1)
            self._report(
                line,
                f"Parser._parse_term: Unhandled token type {token_type} ({lexeme}) for LHS parsing.",
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

    def _parse_arithmetic(self, variable_token):
        variable = self._create_variable(variable_token.lexeme)
        if not self._token_matches(TokenType.IS):
            self._report(
                self._peek().line, "Expected 'is' operator for arithmetic expression."
            )
            return None

        self._advance()  # Consume 'is'

        # ここで算術式の右辺をパースするロジックが必要
        # 簡単な例として、数値または変数を期待
        rhs_token = self._advance()
        expression_rhs = None

        if self._is_type(rhs_token, TokenType.NUMBER):
            expression_rhs = Number(rhs_token.literal)
        elif self._is_type(rhs_token, TokenType.VARIABLE):
            expression_rhs = self._create_variable(rhs_token.lexeme)
        # TODO: より複雑な算術式（例: X is Y + Z）のパースをサポートする
        else:
            self._report(
                rhs_token.line, f"Invalid right-hand side for 'is': {rhs_token.lexeme}"
            )
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
