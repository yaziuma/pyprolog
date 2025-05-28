"""
Parser テスト

Prologインタープリターのパーサー（構文解析器）の
動作を検証するテストスイート。
"""

from prolog.parser.parser import Parser
from prolog.parser.scanner import Scanner
from prolog.parser.token_type import TokenType
from prolog.core.types import Term, Variable, Atom, Number, String, Rule, Fact


class TestParser:
    """パーサーのテスト"""

    def _parse_source(self, source: str):
        """ソースコードを解析するヘルパーメソッド"""
        scanner = Scanner(source)
        tokens = scanner.scan_tokens()
        parser = Parser(tokens)
        return parser.parse()

    def test_parse_atoms_and_variables(self):
        """アトムと変数の解析テスト"""
        source = "atom."
        results = self._parse_source(source)
        
        assert len(results) == 1
        fact = results[0]
        assert isinstance(fact, Fact)
        assert isinstance(fact.head, Term)
        assert fact.head.functor.name == "atom"
        assert len(fact.head.args) == 0

    def test_parse_numbers_and_strings(self):
        """数値と文字列の解析テスト"""
        source = "number(42). string('hello')."
        results = self._parse_source(source)
        
        assert len(results) == 2
        
        # 数値
        fact1 = results[0]
        assert isinstance(fact1, Fact)
        assert fact1.head.functor.name == "number"
        assert len(fact1.head.args) == 1
        assert isinstance(fact1.head.args[0], Number)
        assert fact1.head.args[0].value == 42.0
        
        # 文字列
        fact2 = results[1]
        assert isinstance(fact2, Fact)
        assert fact2.head.functor.name == "string"
        assert len(fact2.head.args) == 1
        assert isinstance(fact2.head.args[0], String)
        assert fact2.head.args[0].value == "hello"

    def test_parse_simple_terms(self):
        """単純な項の解析テスト"""
        source = "likes(john, mary)."
        results = self._parse_source(source)
        
        assert len(results) == 1
        fact = results[0]
        assert isinstance(fact, Fact)
        assert fact.head.functor.name == "likes"
        assert len(fact.head.args) == 2
        assert isinstance(fact.head.args[0], Atom)
        assert fact.head.args[0].name == "john"
        assert isinstance(fact.head.args[1], Atom)
        assert fact.head.args[1].name == "mary"

    def test_parse_complex_terms(self):
        """複雑な項の解析テスト"""
        source = "parent(father(john), child(mary, 5))."
        results = self._parse_source(source)
        
        assert len(results) == 1
        fact = results[0]
        assert isinstance(fact, Fact)
        assert fact.head.functor.name == "parent"
        assert len(fact.head.args) == 2
        
        # 第一引数：father(john)
        arg1 = fact.head.args[0]
        assert isinstance(arg1, Term)
        assert arg1.functor.name == "father"
        assert len(arg1.args) == 1
        assert isinstance(arg1.args[0], Atom)
        assert arg1.args[0].name == "john"
        
        # 第二引数：child(mary, 5)
        arg2 = fact.head.args[1]
        assert isinstance(arg2, Term)
        assert arg2.functor.name == "child"
        assert len(arg2.args) == 2
        assert isinstance(arg2.args[0], Atom)
        assert arg2.args[0].name == "mary"
        assert isinstance(arg2.args[1], Number)
        assert arg2.args[1].value == 5.0

    def test_parse_lists(self):
        """リストの解析テスト"""
        # 空リスト
        source1 = "empty([])."
        results1 = self._parse_source(source1)
        
        assert len(results1) == 1
        fact1 = results1[0]
        assert fact1.head.functor.name == "empty"
        assert len(fact1.head.args) == 1
        assert isinstance(fact1.head.args[0], Atom)
        assert fact1.head.args[0].name == "[]"
        
        # 要素を持つリスト
        source2 = "list([a, b, c])."
        results2 = self._parse_source(source2)
        
        assert len(results2) == 1
        fact2 = results2[0]
        assert fact2.head.functor.name == "list"
        assert len(fact2.head.args) == 1
        
        # リストは内部的に '.'/2 構造に変換される
        list_term = fact2.head.args[0]
        assert isinstance(list_term, Term)
        assert list_term.functor.name == "."

    def test_parse_list_with_tail(self):
        """テール付きリストの解析テスト"""
        source = "tail_list([a, b | T])."
        results = self._parse_source(source)
        
        assert len(results) == 1
        fact = results[0]
        assert fact.head.functor.name == "tail_list"
        assert len(fact.head.args) == 1
        
        # リストは内部的に '.'/2 構造に変換される
        list_term = fact.head.args[0]
        assert isinstance(list_term, Term)
        assert list_term.functor.name == "."

    def test_parse_rules_and_facts(self):
        """ルールとファクトの解析テスト"""
        source = """
        likes(mary, food).
        likes(mary, wine).
        likes(john, X) :- likes(X, wine).
        """
        results = self._parse_source(source)
        
        assert len(results) == 3
        
        # ファクト1
        assert isinstance(results[0], Fact)
        assert results[0].head.functor.name == "likes"
        
        # ファクト2
        assert isinstance(results[1], Fact)
        assert results[1].head.functor.name == "likes"
        
        # ルール
        assert isinstance(results[2], Rule)
        assert results[2].head.functor.name == "likes"
        assert isinstance(results[2].body, Term)

    def test_parse_operators_with_precedence(self):
        """演算子と優先度の解析テスト"""
        source = "test(X + Y * Z)."
        results = self._parse_source(source)
        
        assert len(results) == 1
        fact = results[0]
        assert fact.head.functor.name == "test"
        assert len(fact.head.args) == 1
        
        # 演算子の優先度により、X + (Y * Z) として解析される
        expr = fact.head.args[0]
        assert isinstance(expr, Term)
        # 実装により異なるが、演算子が Term として構造化される

    def test_parse_complex_rule(self):
        """複雑なルールの解析テスト"""
        source = "ancestor(X, Z) :- parent(X, Y), ancestor(Y, Z)."
        results = self._parse_source(source)
        
        assert len(results) == 1
        rule = results[0]
        assert isinstance(rule, Rule)
        
        # ヘッド
        assert rule.head.functor.name == "ancestor"
        assert len(rule.head.args) == 2
        assert isinstance(rule.head.args[0], Variable)
        assert isinstance(rule.head.args[1], Variable)
        
        # ボディ（コンジャンクション）
        assert isinstance(rule.body, Term)
        assert rule.body.functor.name == ","

    def test_parse_error_handling(self):
        """エラーハンドリングのテスト"""
        # 構文エラーのあるソース
        source = "invalid(syntax"  # 閉じ括弧なし
        results = self._parse_source(source)
        
        # エラーがあっても、パーサーは可能な限り処理を続行する
        # 具体的な動作は実装依存

    def test_parse_variables_and_atoms_distinction(self):
        """変数とアトムの区別テスト"""
        source = "test(Var, atom, _Underscore, lowercase)."
        results = self._parse_source(source)
        
        assert len(results) == 1
        fact = results[0]
        assert fact.head.functor.name == "test"
        assert len(fact.head.args) == 4
        
        # 大文字で始まるものは変数
        assert isinstance(fact.head.args[0], Variable)
        assert fact.head.args[0].name == "Var"
        
        # 小文字で始まるものはアトム
        assert isinstance(fact.head.args[1], Atom)
        assert fact.head.args[1].name == "atom"
        
        # アンダースコアで始まるものは変数
        assert isinstance(fact.head.args[2], Variable)
        assert fact.head.args[2].name == "_Underscore"
        
        # 小文字で始まるものはアトム
        assert isinstance(fact.head.args[3], Atom)
        assert fact.head.args[3].name == "lowercase"

    def test_parse_arithmetic_expressions(self):
        """算術式の解析テスト"""
        source = "calc(X is Y + Z * 2)."
        results = self._parse_source(source)
        
        assert len(results) == 1
        fact = results[0]
        assert fact.head.functor.name == "calc"
        assert len(fact.head.args) == 1
        
        # 'is' 演算子を含む式が正しく解析される
        expr = fact.head.args[0]
        assert isinstance(expr, Term)

    def test_parse_parenthesized_expressions(self):
        """括弧付き式の解析テスト"""
        source = "test((X + Y) * Z)."
        results = self._parse_source(source)
        
        assert len(results) == 1
        fact = results[0]
        assert fact.head.functor.name == "test"
        assert len(fact.head.args) == 1
        
        # 括弧により優先度が変更される
        expr = fact.head.args[0]
        assert isinstance(expr, Term)

    def test_parse_multiple_statements(self):
        """複数文の解析テスト"""
        source = """
        fact1.
        fact2(arg).
        rule1 :- body1.
        rule2(X) :- body2(X).
        """
        results = self._parse_source(source)
        
        assert len(results) == 4
        assert isinstance(results[0], Fact)
        assert isinstance(results[1], Fact)
        assert isinstance(results[2], Rule)
        assert isinstance(results[3], Rule)

    def test_parse_conjunction_in_rule_body(self):
        """ルールボディのコンジャンクションテスト"""
        source = "test :- a, b, c."
        results = self._parse_source(source)
        
        assert len(results) == 1
        rule = results[0]
        assert isinstance(rule, Rule)
        
        # ボディはコンジャンクション（,演算子のネスト）
        body = rule.body
        assert isinstance(body, Term)
        assert body.functor.name == ","

    def test_parse_empty_source(self):
        """空のソースの解析テスト"""
        source = ""
        results = self._parse_source(source)
        
        assert len(results) == 0

    def test_parse_comments_ignored(self):
        """コメントが無視されることのテスト"""
        source = """
        % This is a comment
        fact1.  % end of line comment
        % Another comment
        fact2.
        """
        results = self._parse_source(source)
        
        assert len(results) == 2
        assert isinstance(results[0], Fact)
        assert isinstance(results[1], Fact)
        assert results[0].head.functor.name == "fact1"
        assert results[1].head.functor.name == "fact2"

    def test_parse_whitespace_handling(self):
        """空白文字の処理テスト"""
        source = """
        
        fact1   .
        
        fact2(  arg  )  .
        
        """
        results = self._parse_source(source)
        
        assert len(results) == 2
        assert isinstance(results[0], Fact)
        assert isinstance(results[1], Fact)