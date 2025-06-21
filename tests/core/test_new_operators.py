"""
新しい演算子 <> と != のテスト
"""

from pyprolog.parser.scanner import Scanner
from pyprolog.parser.parser import Parser
from pyprolog.runtime.interpreter import Runtime
from pyprolog.core.binding_environment import BindingEnvironment


class TestNewOperators:
    """新しい非等価演算子のテストクラス"""

    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.runtime = Runtime([])

    def execute_goal(self, source):
        """ゴールを実行して結果を返す"""
        tokens = Scanner(source).scan_tokens()
        goals = Parser(tokens).parse()
        if goals:
            goal = goals[0]
            actual_goal = goal.head if hasattr(goal, 'head') else goal
            env = BindingEnvironment()
            return list(self.runtime.execute(actual_goal, env))
        return []

    def test_not_equal_operator_different_atoms(self):
        """<> 演算子：異なるアトムで成功"""
        solutions = self.execute_goal("a <> b.")
        assert len(solutions) == 1, "Different atoms should succeed with <>"

    def test_not_equal_operator_same_atoms(self):
        """<> 演算子：同じアトムで失敗"""
        solutions = self.execute_goal("a <> a.")
        assert len(solutions) == 0, "Same atoms should fail with <>"

    def test_not_equal_operator_different_numbers(self):
        """<> 演算子：異なる数値で成功"""
        solutions = self.execute_goal("1 <> 2.")
        assert len(solutions) == 1, "Different numbers should succeed with <>"

    def test_not_equal_operator_same_numbers(self):
        """<> 演算子：同じ数値で失敗"""
        solutions = self.execute_goal("1 <> 1.")
        assert len(solutions) == 0, "Same numbers should fail with <>"

    def test_not_equal_alt_operator_different_atoms(self):
        """!= 演算子：異なるアトムで成功"""
        solutions = self.execute_goal("hello != world.")
        assert len(solutions) == 1, "Different atoms should succeed with !="

    def test_not_equal_alt_operator_same_atoms(self):
        """!= 演算子：同じアトムで失敗"""
        solutions = self.execute_goal("hello != hello.")
        assert len(solutions) == 0, "Same atoms should fail with !="

    def test_not_equal_alt_operator_different_numbers(self):
        """!= 演算子：異なる数値で成功"""
        solutions = self.execute_goal("3.14 != 2.71.")
        assert len(solutions) == 1, "Different numbers should succeed with !="

    def test_not_equal_alt_operator_same_numbers(self):
        """!= 演算子：同じ数値で失敗"""
        solutions = self.execute_goal("3.14 != 3.14.")
        assert len(solutions) == 0, "Same numbers should fail with !="

    def test_not_equal_mixed_types(self):
        """<> 演算子：異なる型で成功"""
        solutions = self.execute_goal("1 <> hello.")
        assert len(solutions) == 1, "Different types should succeed with <>"

    def test_not_equal_alt_mixed_types(self):
        """!= 演算子：異なる型で成功"""
        solutions = self.execute_goal("world != 42.")
        assert len(solutions) == 1, "Different types should succeed with !="

    def test_comparison_with_traditional_operator(self):
        """従来の \\= 演算子との比較"""
        # 従来の演算子
        solutions_old = self.execute_goal("a \\= b.")
        # 新しい演算子
        solutions_new = self.execute_goal("a <> b.")
        solutions_alt = self.execute_goal("a != b.")

        assert len(solutions_old) == 1, "Traditional \\= should work"
        assert len(solutions_new) == 1, "New <> should work"
        assert len(solutions_alt) == 1, "New != should work"

    def test_rule_with_new_operators(self):
        """ルール内での新しい演算子の使用"""
        # ルールを定義
        rule_source = "different(X, Y) :- X <> Y."
        tokens = Scanner(rule_source).scan_tokens()
        rules = Parser(tokens).parse()
        runtime = Runtime(rules)

        # ゴールを実行
        goal_source = "different(a, b)."
        goal_tokens = Scanner(goal_source).scan_tokens()
        goal_parsed = Parser(goal_tokens).parse()
        goal = goal_parsed[0].head if hasattr(goal_parsed[0], 'head') else goal_parsed[0]

        env = BindingEnvironment()
        solutions = list(runtime.execute(goal, env))
        assert len(solutions) == 1, "Rule with <> should work for different terms"

        # 同じ値でテスト
        goal_source2 = "different(a, a)."
        goal_tokens2 = Scanner(goal_source2).scan_tokens()
        goal_parsed2 = Parser(goal_tokens2).parse()
        goal2 = goal_parsed2[0].head if hasattr(goal_parsed2[0], 'head') else goal_parsed2[0]

        env2 = BindingEnvironment()
        solutions2 = list(runtime.execute(goal2, env2))
        assert len(solutions2) == 0, "Rule with <> should fail for same terms"

    def test_rule_with_alt_operator(self):
        """ルール内での != 演算子の使用"""
        # ルールを定義
        rule_source = "not_same(X, Y) :- X != Y."
        tokens = Scanner(rule_source).scan_tokens()
        rules = Parser(tokens).parse()
        runtime = Runtime(rules)

        # 異なる値でテスト
        goal_source = "not_same(1, 2)."
        goal_tokens = Scanner(goal_source).scan_tokens()
        goal_parsed = Parser(goal_tokens).parse()
        goal = goal_parsed[0].head if hasattr(goal_parsed[0], 'head') else goal_parsed[0]

        env = BindingEnvironment()
        solutions = list(runtime.execute(goal, env))
        assert len(solutions) == 1, "Rule with != should work for different values"

    def test_compound_expressions(self):
        """複合式での新しい演算子の使用"""
        # 複数の非等価条件
        rule_source = "all_different(X, Y, Z) :- X <> Y, Y != Z, X <> Z."
        tokens = Scanner(rule_source).scan_tokens()
        rules = Parser(tokens).parse()
        runtime = Runtime(rules)

        # すべて異なる値でテスト
        goal_source = "all_different(a, b, c)."
        goal_tokens = Scanner(goal_source).scan_tokens()
        goal_parsed = Parser(goal_tokens).parse()
        goal = goal_parsed[0].head if hasattr(goal_parsed[0], 'head') else goal_parsed[0]

        env = BindingEnvironment()
        solutions = list(runtime.execute(goal, env))
        assert len(solutions) == 1, "Compound expression with new operators should work"

        # 一部同じ値でテスト（失敗するはず）
        goal_source2 = "all_different(a, a, c)."
        goal_tokens2 = Scanner(goal_source2).scan_tokens()
        goal_parsed2 = Parser(goal_tokens2).parse()
        goal2 = goal_parsed2[0].head if hasattr(goal_parsed2[0], 'head') else goal_parsed2[0]

        env2 = BindingEnvironment()
        solutions2 = list(runtime.execute(goal2, env2))
        assert len(solutions2) == 0, "Compound expression should fail when some values are same"