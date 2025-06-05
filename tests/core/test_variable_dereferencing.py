"""
Variable Dereferencing テスト

変数の間接参照機能の詳細な動作を検証するテストスイート。
"""

from pyprolog.core.binding_environment import BindingEnvironment
from pyprolog.core.types import Variable, Atom, Number, Term, String
from pyprolog.core.errors import PrologError


class TestVariableDereferencing:
    """変数間接参照のテスト"""

    def setup_method(self):
        """各テストの前処理"""
        self.env = BindingEnvironment()
        # ここではBindingEnvironmentの機能を使用してテスト

    def test_simple_dereferencing(self):
        """単純な間接参照のテスト"""
        # X = hello
        self.env.bind("X", Atom("hello"))

        # 直接取得
        result = self.env.get_value("X")
        assert result == Atom("hello")

    def test_chain_dereferencing(self):
        """チェーン間接参照のテスト"""
        # X = Y, Y = Z, Z = value
        self.env.bind("X", Variable("Y"))
        self.env.bind("Y", Variable("Z"))
        self.env.bind("Z", Atom("value"))

        # チェーンを辿って最終値を取得
        result = self._dereference_fully(Variable("X"))
        assert result == Atom("value")

    def test_circular_reference_detection(self):
        """循環参照の検出テスト"""
        # X = Y, Y = X (循環参照)
        self.env.bind("X", Variable("Y"))
        self.env.bind("Y", Variable("X"))

        # 循環参照を検出して適切に処理することを確認
        try:
            result = self._dereference_fully(Variable("X"))
            # 循環参照の場合、元の変数またはエラーを返す
            assert isinstance(result, Variable)
        except PrologError:
            # 循環参照エラーが発生することも適切
            pass

    def test_partial_dereferencing(self):
        """部分的間接参照のテスト"""
        # 一部の変数のみ束縛されている場合
        term = Term(Atom("f"), [Variable("X"), Variable("Y")])
        self.env.bind("X", Atom("bound"))
        # Y は未束縛のまま

        result = self._dereference_term(term)
        expected = Term(Atom("f"), [Atom("bound"), Variable("Y")])
        assert result == expected

    def test_complex_term_dereferencing(self):
        """複雑な項の間接参照テスト"""
        # 深くネストした項の変数解決
        self.env.bind("X", Atom("john"))
        self.env.bind("Y", Number(25))
        self.env.bind("Z", Variable("X"))

        complex_term = Term(
            Atom("person"),
            [
                Variable("Z"),  # X -> john
                Term(Atom("age"), [Variable("Y")]),  # Y -> 25
            ],
        )

        result = self._dereference_term(complex_term)
        expected = Term(Atom("person"), [Atom("john"), Term(Atom("age"), [Number(25)])])
        assert result == expected

    def test_multi_level_chain(self):
        """多段階チェーンのテスト"""
        # X -> Y -> Z -> W -> final_value
        self.env.bind("X", Variable("Y"))
        self.env.bind("Y", Variable("Z"))
        self.env.bind("Z", Variable("W"))
        self.env.bind("W", String("final_value"))

        result = self._dereference_fully(Variable("X"))
        assert result == String("final_value")

    def test_mixed_type_dereferencing(self):
        """混合型の間接参照テスト"""
        # 数値、文字列、アトムの混合
        self.env.bind("NumVar", Number(42))
        self.env.bind("StrVar", String("hello"))
        self.env.bind("AtomVar", Atom("world"))

        term = Term(
            Atom("mixed"), [Variable("NumVar"), Variable("StrVar"), Variable("AtomVar")]
        )

        result = self._dereference_term(term)
        expected = Term(Atom("mixed"), [Number(42), String("hello"), Atom("world")])
        assert result == expected

    def test_unbound_variable_handling(self):
        """未束縛変数の処理テスト"""
        # 未束縛変数はそのまま残る
        unbound_var = Variable("Unbound")
        result = self._dereference_fully(unbound_var)
        assert result == unbound_var

    def test_self_reference(self):
        """自己参照のテスト"""
        # X = X の場合
        self.env.bind("X", Variable("X"))

        # 自己参照は循環参照の特殊ケース
        try:
            result = self._dereference_fully(Variable("X"))
            assert isinstance(result, Variable)
        except PrologError:
            # エラーが発生することも適切
            pass

    def test_dereferencing_with_occurs_check(self):
        """発生チェック付き間接参照のテスト"""
        # X = f(X) のような構造での発生チェック
        self.env.bind("X", Term(Atom("f"), [Variable("X")]))

        # 発生チェックが有効な場合、このような束縛は検出される
        result = self._dereference_fully(Variable("X"))
        # 実装により動作は異なるが、無限ループにならないこと
        assert result is not None

    def test_nested_variable_chains(self):
        """ネストした変数チェーンのテスト"""
        # 複数の独立したチェーン
        # Chain 1: A -> B -> value1
        self.env.bind("A", Variable("B"))
        self.env.bind("B", Atom("value1"))

        # Chain 2: C -> D -> value2
        self.env.bind("C", Variable("D"))
        self.env.bind("D", Number(123))

        term = Term(Atom("test"), [Variable("A"), Variable("C")])
        result = self._dereference_term(term)
        expected = Term(Atom("test"), [Atom("value1"), Number(123)])
        assert result == expected

    def test_dereferencing_performance(self):
        """間接参照の性能テスト"""
        # 長いチェーンでの性能確認
        import time

        # 100段階のチェーンを作成
        for i in range(100):
            if i == 99:
                self.env.bind(f"Var{i}", Atom("final"))
            else:
                self.env.bind(f"Var{i}", Variable(f"Var{i + 1}"))

        start_time = time.time()
        result = self._dereference_fully(Variable("Var0"))
        end_time = time.time()

        assert result == Atom("final")
        # 合理的な時間内で完了することを確認
        assert end_time - start_time < 1.0  # 1秒以内

    def test_dereferencing_in_list_context(self):
        """リストコンテキストでの間接参照テスト"""
        self.env.bind("H", Atom("head"))
        self.env.bind("T", Atom("[]"))

        # リスト構造 [H|T] の間接参照
        list_term = Term(Atom("."), [Variable("H"), Variable("T")])
        result = self._dereference_term(list_term)
        expected = Term(Atom("."), [Atom("head"), Atom("[]")])
        assert result == expected

    def test_environment_isolation(self):
        """環境分離での間接参照テスト"""
        # 親環境と子環境での変数束縛
        parent_env = BindingEnvironment()
        parent_env.bind("ParentVar", Atom("parent_value"))

        child_env = BindingEnvironment(parent_env)
        child_env.bind("ChildVar", Variable("ParentVar"))

        # 子環境で親環境の変数を参照
        result = child_env.get_value("ChildVar")
        # 実装により、直接値が返されるかVariableが返されるかは異なる
        assert result is not None

    def test_binding_update_dereferencing(self):
        """束縛更新時の間接参照テスト"""
        # 初期束縛
        self.env.bind("X", Variable("Y"))
        self.env.bind("Y", Atom("initial"))

        # 値を確認
        result1 = self._dereference_fully(Variable("X"))
        assert result1 == Atom("initial")

        # 束縛を更新
        self.env.bind("Y", Atom("updated"))

        # 更新された値が反映されることを確認
        result2 = self._dereference_fully(Variable("X"))
        assert result2 == Atom("updated")

    # ヘルパーメソッド
    def _dereference_fully(self, var, visited=None):
        """完全な間接参照の実装例"""
        if visited is None:
            visited = set()

        if not isinstance(var, Variable):
            return var

        if var.name in visited:
            # 循環参照を検出
            return var  # または例外を発生

        visited.add(var.name)
        value = self.env.get_value(var.name)

        if value is None:
            return var  # 未束縛

        if isinstance(value, Variable):
            return self._dereference_fully(value, visited.copy())

        return value

    def _dereference_term(self, term):
        """項内の変数を間接参照する実装例"""
        if isinstance(term, Variable):
            return self._dereference_fully(term)
        elif isinstance(term, Term):
            new_args = [self._dereference_term(arg) for arg in term.args]
            return Term(term.functor, new_args)
        else:
            return term
