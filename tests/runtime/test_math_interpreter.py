"""
Math Interpreter テスト

Prologインタープリターの数学的評価エンジンの
動作を検証するテストスイート。
"""

from pyprolog.runtime.math_interpreter import MathInterpreter
from pyprolog.core.binding_environment import BindingEnvironment
from pyprolog.core.types import Term, Variable, Number, Atom
from pyprolog.core.errors import PrologError


class TestMathInterpreter:
    """数学インタープリターのテスト"""

    def setup_method(self):
        """各テストメソッドの前に実行される初期化"""
        self.math_interpreter = MathInterpreter()
        self.env = BindingEnvironment()

    def test_basic_arithmetic(self):
        """基本的な算術演算のテスト"""
        # 数値の評価
        assert self.math_interpreter.evaluate(Number(42), self.env) == 42
        assert self.math_interpreter.evaluate(Number(3.14), self.env) == 3.14

        # 加算
        expr_add = Term(Atom("+"), [Number(5), Number(3)])
        assert self.math_interpreter.evaluate(expr_add, self.env) == 8

        # 減算
        expr_sub = Term(Atom("-"), [Number(10), Number(4)])
        assert self.math_interpreter.evaluate(expr_sub, self.env) == 6

        # 乗算
        expr_mult = Term(Atom("*"), [Number(6), Number(7)])
        assert self.math_interpreter.evaluate(expr_mult, self.env) == 42

        # 除算
        expr_div = Term(Atom("/"), [Number(15), Number(3)])
        assert self.math_interpreter.evaluate(expr_div, self.env) == 5.0

    def test_complex_expressions(self):
        """複雑な式の評価テスト"""
        # (2 + 3) * 4
        inner_expr = Term(Atom("+"), [Number(2), Number(3)])
        complex_expr = Term(Atom("*"), [inner_expr, Number(4)])
        assert self.math_interpreter.evaluate(complex_expr, self.env) == 20

        # 2 + 3 * 4 (優先度は外部で解決済みと仮定)
        mult_expr = Term(Atom("*"), [Number(3), Number(4)])
        expr = Term(Atom("+"), [Number(2), mult_expr])
        assert self.math_interpreter.evaluate(expr, self.env) == 14

    def test_comparison_operations(self):
        """比較演算のテスト"""
        # 等価比較
        assert self.math_interpreter.evaluate_comparison_op("=:=", 5, 5) == True
        assert self.math_interpreter.evaluate_comparison_op("=:=", 5, 3) == False

        # 非等価比較
        assert self.math_interpreter.evaluate_comparison_op("=\\=", 5, 3) == True
        assert self.math_interpreter.evaluate_comparison_op("=\\=", 5, 5) == False

        # 大小比較
        assert self.math_interpreter.evaluate_comparison_op("<", 3, 5) == True
        assert self.math_interpreter.evaluate_comparison_op("<", 5, 3) == False

        assert self.math_interpreter.evaluate_comparison_op(">", 5, 3) == True
        assert self.math_interpreter.evaluate_comparison_op(">", 3, 5) == False

        # 以下・以上比較
        assert self.math_interpreter.evaluate_comparison_op("=<", 3, 5) == True
        assert self.math_interpreter.evaluate_comparison_op("=<", 5, 5) == True
        assert self.math_interpreter.evaluate_comparison_op("=<", 5, 3) == False

        assert self.math_interpreter.evaluate_comparison_op(">=", 5, 3) == True
        assert self.math_interpreter.evaluate_comparison_op(">=", 5, 5) == True
        assert self.math_interpreter.evaluate_comparison_op(">=", 3, 5) == False

    def test_mathematical_functions(self):
        """数学関数のテスト"""
        # abs/1 関数
        abs_expr = Term(Atom("abs"), [Number(-5)])
        assert self.math_interpreter.evaluate(abs_expr, self.env) == 5

        abs_expr_pos = Term(Atom("abs"), [Number(3)])
        assert self.math_interpreter.evaluate(abs_expr_pos, self.env) == 3

        # max/2 関数
        max_expr = Term(Atom("max"), [Number(3), Number(7)])
        assert self.math_interpreter.evaluate(max_expr, self.env) == 7

        max_expr2 = Term(Atom("max"), [Number(10), Number(5)])
        assert self.math_interpreter.evaluate(max_expr2, self.env) == 10

        # min/2 関数
        min_expr = Term(Atom("min"), [Number(3), Number(7)])
        assert self.math_interpreter.evaluate(min_expr, self.env) == 3

        min_expr2 = Term(Atom("min"), [Number(10), Number(5)])
        assert self.math_interpreter.evaluate(min_expr2, self.env) == 5

    def test_variable_evaluation(self):
        """変数を含む式の評価テスト"""
        # 変数を束縛
        self.env.bind("X", Number(5))
        self.env.bind("Y", Number(3))

        # X + Y
        expr = Term(Atom("+"), [Variable("X"), Variable("Y")])
        assert self.math_interpreter.evaluate(expr, self.env) == 8

        # X * Y
        expr_mult = Term(Atom("*"), [Variable("X"), Variable("Y")])
        assert self.math_interpreter.evaluate(expr_mult, self.env) == 15

    def test_type_checking(self):
        """型チェックのテスト"""
        # 数値アトムの評価
        atom_num = Atom("42")
        assert self.math_interpreter.evaluate(atom_num, self.env) == 42.0

        atom_float = Atom("3.14")
        assert self.math_interpreter.evaluate(atom_float, self.env) == 3.14

    def test_error_handling(self):
        """エラーハンドリングのテスト"""
        # ゼロ除算
        try:
            expr_div_zero = Term(Atom("/"), [Number(5), Number(0)])
            self.math_interpreter.evaluate(expr_div_zero, self.env)
            assert False, "Should have raised PrologError"
        except PrologError as e:
            assert "Division by zero" in str(e)

        # 整数除算のゼロ除算
        try:
            expr_int_div_zero = Term(Atom("//"), [Number(5), Number(0)])
            self.math_interpreter.evaluate(expr_int_div_zero, self.env)
            assert False, "Should have raised PrologError"
        except PrologError as e:
            assert "Integer division by zero" in str(e)

        # 未束縛変数
        try:
            unbound_var = Variable("Z")
            self.math_interpreter.evaluate(unbound_var, self.env)
            assert False, "Should have raised PrologError"
        except PrologError as e:
            assert "not instantiated" in str(e)

        # 非数値アトム
        try:
            non_numeric_atom = Atom("hello")
            self.math_interpreter.evaluate(non_numeric_atom, self.env)
            assert False, "Should have raised PrologError"
        except PrologError as e:
            assert "Cannot evaluate atom" in str(e)

        # 未知の演算子
        try:
            unknown_op = Term(Atom("unknown_op"), [Number(1), Number(2)])
            self.math_interpreter.evaluate(unknown_op, self.env)
            assert False, "Should have raised PrologError"
        except PrologError as e:
            assert "Unknown mathematical function" in str(e)

    def test_symptom_score_calculation(self):
        """症状マッチスコア計算ロジックのテスト"""
        # Helper to simulate Prolog's list_to_prolog_number_list and sum_list/evaluate
        def calculate_score(probabilities: list) -> float:
            if not probabilities: # prolog: length(マッチした確率, マッチ数), (マッチ数 > 0 -> ... ; スコア = 0)
                return 0.0

            # Simulate sum_list using MathInterpreter for evaluation
            # prolog: sum_list(マッチした確率, 合計)
            # For [0.9, 0.7, 0.6], sum_expr becomes Term(Atom("+"), [Term(Atom("+"), [Number(0.9), Number(0.7)]), Number(0.6)])
            # For a single element list like [0.9], it's just Number(0.9)
            if len(probabilities) == 1:
                sum_expr = Number(probabilities[0])
            else:
                # Build nested sum expression: e.g., +(+(arg1, arg2), arg3)
                sum_expr = Number(probabilities[0]) # Initialize with the first element
                for i in range(1, len(probabilities)):
                    sum_expr = Term(Atom("+"), [sum_expr, Number(probabilities[i])])

            evaluated_sum = self.math_interpreter.evaluate(sum_expr, self.env)

            # Simulate division for the average
            # prolog: スコア is 合計 / マッチ数
            # Ensure evaluated_sum is treated as a number for the division
            division_expr = Term(Atom("/"), [Number(evaluated_sum), Number(len(probabilities))])
            score = self.math_interpreter.evaluate(division_expr, self.env)
            return score

        # 1. 確率リストが空の場合 (マッチ数 = 0)
        # Prolog: スコア = 0
        assert calculate_score([]) == 0.0

        # 2. 通常の確率リスト
        # Prolog: マッチした確率 = [0.9, 0.7, 0.6], マッチ数 = 3
        # Prolog: 合計 = 0.9 + 0.7 + 0.6 = 2.2
        # Prolog: スコア = 2.2 / 3 = 0.73333...
        probs1 = [0.9, 0.7, 0.6]
        expected_score1 = (0.9 + 0.7 + 0.6) / 3
        assert abs(calculate_score(probs1) - expected_score1) < 0.0001

        # 3. 単一の確率
        # Prolog: マッチした確率 = [0.8], マッチ数 = 1
        # Prolog: 合計 = 0.8
        # Prolog: スコア = 0.8 / 1 = 0.8
        probs2 = [0.8]
        expected_score2 = 0.8 / 1
        assert abs(calculate_score(probs2) - expected_score2) < 0.0001

        # 4. 非常に小さい確率値を含むリスト
        # Prolog: マッチした確率 = [0.0000001, 0.0000002], マッチ数 = 2
        # Prolog: 合計 = 0.0000001 + 0.0000002 = 0.0000003
        # Prolog: スコア = 0.0000003 / 2 = 0.00000015
        probs3 = [0.0000001, 0.0000002]
        expected_score3 = (0.0000001 + 0.0000002) / 2
        # This test is crucial for the reported issue.
        assert abs(calculate_score(probs3) - expected_score3) < 0.00000001

        # 5. 確率値が0.0のみのリスト
        # Prolog: マッチした確率 = [0.0, 0.0, 0.0], マッチ数 = 3
        # Prolog: 合計 = 0.0 + 0.0 + 0.0 = 0.0
        # Prolog: スコア = 0.0 / 3 = 0.0
        probs4 = [0.0, 0.0, 0.0]
        expected_score4 = 0.0 # 0.0 / 3 is 0.0
        assert abs(calculate_score(probs4) - expected_score4) < 0.0001

        # 6. 症状が一つの場合 (Prologの例: 疾患症状(風邪, 鼻水, 0.9) のみ)
        # Prolog: マッチした確率 = [0.9], マッチ数 = 1, スコア = 0.9
        probs5 = [0.9]
        expected_score5 = 0.9 / 1
        assert abs(calculate_score(probs5) - expected_score5) < 0.0001

        # 7. 症状が複数で、一部マッチしない場合 (Prolog側でフィルタリングされる前提のテスト)
        # Prolog: マッチした確率 = [0.7, 0.6], マッチ数 = 2
        # Prolog: 合計 = 0.7 + 0.6 = 1.3
        # Prolog: スコア = 1.3 / 2 = 0.65
        probs6 = [0.7, 0.6]
        expected_score6 = (0.7 + 0.6) / 2
        assert abs(calculate_score(probs6) - expected_score6) < 0.0001

    def test_bitwise_operations(self):
        """ビット単位演算のテスト"""
        # AND
        expr_and = Term(Atom("&"), [Number(6), Number(3)])  # 6 (110) & 3 (011) = 2 (010)
        assert self.math_interpreter.evaluate(expr_and, self.env) == 2

        # OR
        expr_or = Term(Atom("|"), [Number(6), Number(3)])   # 6 (110) | 3 (011) = 7 (111)
        assert self.math_interpreter.evaluate(expr_or, self.env) == 7

        # XOR
        expr_xor = Term(Atom("^"), [Number(6), Number(3)])  # 6 (110) ^ 3 (011) = 5 (101)
        assert self.math_interpreter.evaluate(expr_xor, self.env) == 5

        # NOT (単項)
        expr_not = Term(Atom("~"), [Number(6)])            # ~6 (110) = -7 (2の補数)
        assert self.math_interpreter.evaluate(expr_not, self.env) == -7

        # 左シフト
        expr_lshift = Term(Atom("<<"), [Number(3), Number(2)]) # 3 (011) << 2 = 12 (1100)
        assert self.math_interpreter.evaluate(expr_lshift, self.env) == 12

        # 右シフト
        expr_rshift = Term(Atom(">>"), [Number(6), Number(1)]) # 6 (110) >> 1 = 3 (011)
        assert self.math_interpreter.evaluate(expr_rshift, self.env) == 3

    def test_advanced_operations(self):
        """高度な演算のテスト"""
        # 指数演算
        expr_power = Term(Atom("**"), [Number(2), Number(3)])
        assert self.math_interpreter.evaluate(expr_power, self.env) == 8

        # 整数除算
        expr_int_div = Term(Atom("//"), [Number(7), Number(3)])
        assert self.math_interpreter.evaluate(expr_int_div, self.env) == 2

        # モジュロ演算
        expr_mod = Term(Atom("mod"), [Number(7), Number(3)])
        assert self.math_interpreter.evaluate(expr_mod, self.env) == 1

    def test_unary_operations(self):
        """単項演算のテスト"""
        # 単項マイナス
        expr_neg = Term(Atom("-"), [Number(5)])
        assert self.math_interpreter.evaluate(expr_neg, self.env) == -5

        # 単項プラス
        expr_pos = Term(Atom("+"), [Number(5)])
        assert self.math_interpreter.evaluate(expr_pos, self.env) == 5

    def test_nested_variable_resolution(self):
        """ネストした変数解決のテスト"""
        # X = Y, Y = 42
        self.env.bind("Y", Number(42))
        self.env.bind("X", Variable("Y"))

        # Xを評価すると42になる
        assert self.math_interpreter.evaluate(Variable("X"), self.env) == 42

        # X + 8 = 50
        expr = Term(Atom("+"), [Variable("X"), Number(8)])
        assert self.math_interpreter.evaluate(expr, self.env) == 50

    def test_floating_point_operations(self):
        """浮動小数点演算のテスト"""
        # 浮動小数点の加算
        expr_float_add = Term(Atom("+"), [Number(3.14), Number(2.86)])
        result = self.math_interpreter.evaluate(expr_float_add, self.env)
        assert abs(result - 6.0) < 0.0001  # 浮動小数点の精度を考慮

        # 浮動小数点の除算
        expr_float_div = Term(Atom("/"), [Number(1), Number(3)])
        result_div = self.math_interpreter.evaluate(expr_float_div, self.env)
        assert abs(result_div - 0.333333) < 0.001

    def test_mixed_integer_float_operations(self):
        """整数と浮動小数点の混合演算テスト"""
        # 整数 + 浮動小数点
        expr_mixed = Term(Atom("+"), [Number(5), Number(3.14)])
        result = self.math_interpreter.evaluate(expr_mixed, self.env)
        assert abs(result - 8.14) < 0.0001

        # 整数 * 浮動小数点
        expr_mixed_mult = Term(Atom("*"), [Number(2), Number(3.5)])
        result_mult = self.math_interpreter.evaluate(expr_mixed_mult, self.env)
        assert abs(result_mult - 7.0) < 0.0001

    def test_comparison_with_variables(self):
        """変数を含む比較のテスト"""
        self.env.bind("A", Number(5))
        self.env.bind("B", Number(3))

        # A と B の直接的な数値比較はevaluate_comparison_opで行う
        a_val = self.math_interpreter.evaluate(Variable("A"), self.env)
        b_val = self.math_interpreter.evaluate(Variable("B"), self.env)

        assert self.math_interpreter.evaluate_comparison_op(">", a_val, b_val) == True
        assert self.math_interpreter.evaluate_comparison_op("<", a_val, b_val) == False
        assert self.math_interpreter.evaluate_comparison_op("=:=", a_val, a_val) == True

    def test_function_arity_validation(self):
        """関数のアリティ検証テスト"""
        # abs関数に2つの引数を渡す（エラーになるはず）
        try:
            invalid_abs = Term(Atom("abs"), [Number(1), Number(2)])
            self.math_interpreter.evaluate(invalid_abs, self.env)
            assert False, "Should have raised PrologError"
        except PrologError as e:
            assert "Unknown mathematical function" in str(e)

        # max関数に1つの引数を渡す（エラーになるはず）
        try:
            invalid_max = Term(Atom("max"), [Number(1)])
            self.math_interpreter.evaluate(invalid_max, self.env)
            assert False, "Should have raised PrologError"
        except PrologError as e:
            assert "Unknown mathematical function" in str(e)
