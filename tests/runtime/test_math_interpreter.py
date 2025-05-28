"""
Math Interpreter テスト

Prologインタープリターの数学的評価エンジンの
動作を検証するテストスイート。
"""

from prolog.runtime.math_interpreter import MathInterpreter
from prolog.core.binding_environment import BindingEnvironment
from prolog.core.types import Term, Variable, Number, Atom
from prolog.core.errors import PrologError


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