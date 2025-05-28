# prolog/parser/parser.py
from prolog.parser.token import Token
from prolog.parser.token_type import TokenType
from prolog.core.types import Term, Variable, Atom, Number, String, Rule, Fact
from prolog.core.operators import operator_registry, Associativity
from typing import List, Optional, Callable, Union
import logging

logger = logging.getLogger(__name__)


def default_error_handler(token: Token, message: str):
    logger.error(f"Parse error at '{token.lexeme}': {message}")


class Parser:
    """演算子統合設計を活用したパーサー"""

    def __init__(
        self,
        tokens: List[Token],
        error_handler: Callable[[Token, str], None] = default_error_handler,
    ):
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
        """ルール解析（統合設計対応版）"""
        head_term = self._parse_term()
        if head_term is None:
            return None

        # Termに変換 (Atom以外もTermにラップする)
        if not isinstance(head_term, Term):
            if isinstance(head_term, Atom):
                head_term = Term(head_term, [])
            elif isinstance(head_term, (Number, String, Variable)):
                # Atom以外の型をfunctorとしてTermを作成する場合は、Atomに変換する
                head_term = Term(Atom(str(head_term)), [])
            else:
                # 予期しない型の場合はエラー処理またはNoneを返す
                self._error(
                    self._previous(), f"Unexpected head term type: {type(head_term)}"
                )
                return None

        if self._match(TokenType.COLONMINUS):
            # ルール本体の解析
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

            # 統合設計：コンジャンクションも通常の Term として構築
            body = self._build_conjunction(body_terms)
            if isinstance(body, Atom):
                body = Term(body, [])

            return Rule(head_term, body)
        else:
            return Fact(head_term)

    def _build_conjunction(self, terms: List) -> Union[Term, Atom]:
        """項リストからコンジャンクションを構築（統合設計版）"""
        if len(terms) == 1:
            return terms[0]

        # 演算子統合設計：カンマ演算子として構築
        result = terms[-1]
        for i in range(len(terms) - 2, -1, -1):
            # 統合設計：通常の Term として構築
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
        return getattr(token, "token_type", TokenType.EOF)

    def _error(self, token: Token, message: str):
        self._error_handler(token, message)
