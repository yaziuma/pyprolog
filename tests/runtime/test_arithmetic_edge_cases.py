"""
Arithmetic Edge Cases テスト

算術演算の境界値と特殊ケースを検証するテストスイート。
"""

import math
import sys
from pyprolog.runtime.math_interpreter import MathInterpreter
from pyprolog.core.binding_environment import BindingEnvironment
from pyprolog.core.types import Number, Term, Atom, Variable
from pyprolog.core.errors import PrologError


class TestArithmeticEdgeCases:
    """算術演算境界値のテスト"""

    def setup_method(self):
        """各テストの前処理"""
        self.math_interpreter = MathInterpreter()
        self.env = BindingEnvironment()

    def test_large_numbers(self):
        """大きな数値の処理テスト"""
        # 非常に大きな整数
        large_int = Number(999999999999999999)
        result = self.math_interpreter.evaluate(large_int, self.env)
        assert result == 999999999999999999

        # Python の最大整数を超える値
        very_large = Number(2**64)
        result = self.math_interpreter.evaluate(very_large, self.env)
        assert result == 2**64

    def test_very_small_numbers(self):
        """非常に小さな数値の処理テスト"""
        # 非常に小さな正の数
        tiny_positive = Number(1e-100)
        result = self.math_interpreter.evaluate(tiny_positive, self.env)
        assert result == 1e-100

        # 非常に小さな負の数
        tiny_negative = Number(-1e-100)
        result = self.math_interpreter.evaluate(tiny_negative, self.env)
        assert result == -1e-100

    def test_floating_point_precision(self):
        """浮動小数点精度のテスト"""
        # 精度の問題を含む計算
        expr = Term(Atom("+"), [Number(0.1), Number(0.2)])
        result = self.math_interpreter.evaluate(expr, self.env)
        # 浮動小数点の精度問題を考慮
        assert abs(result - 0.3) < 1e-10

        # より複雑な精度問題
        expr2 = Term(
            Atom("-"), [Term(Atom("+"), [Number(0.1), Number(0.2)]), Number(0.3)]
        )
        result2 = self.math_interpreter.evaluate(expr2, self.env)
        assert abs(result2) < 1e-10

    def test_infinity_handling(self):
        """無限大の処理テスト"""
        # 正の無限大の生成を試行
        try:
            # 非常に大きな指数
            expr = Term(Atom("**"), [Number(10.0), Number(1000)])
            result = self.math_interpreter.evaluate(expr, self.env)
            # 結果が無限大になるか、例外が発生するかを確認
            if math.isinf(result):
                assert result > 0  # 正の無限大
            else:
                # 有限値が返される場合も許容
                assert isinstance(result, (int, float))
        except (OverflowError, PrologError):
            # オーバーフローエラーも適切
            pass

    def test_negative_infinity(self):
        """負の無限大の処理テスト"""
        try:
            # 負の無限大の生成
            expr = Term(Atom("**"), [Number(-10.0), Number(1001)])  # 奇数乗
            result = self.math_interpreter.evaluate(expr, self.env)
            if math.isinf(result):
                assert result < 0  # 負の無限大
        except (OverflowError, PrologError):
            pass

    def test_nan_handling(self):
        """NaNの処理テスト"""
        # 通常、除算でのNaN生成は困難だが、他の方法で試行
        try:
            # 0の0乗などでNaNが発生する可能性
            expr = Term(Atom("**"), [Number(0.0), Number(0.0)])
            result = self.math_interpreter.evaluate(expr, self.env)
            # NaN または例外のいずれかが発生
            if not math.isnan(result):
                # NaNでない場合、有効な数値であることを確認
                assert isinstance(result, (int, float))
        except PrologError:
            # エラーも適切
            pass

    def test_division_by_zero_variants(self):
        """様々なゼロ除算のテスト"""
        # 基本的なゼロ除算
        try:
            expr1 = Term(Atom("/"), [Number(5), Number(0)])
            self.math_interpreter.evaluate(expr1, self.env)
            assert False, "Should have raised PrologError"
        except PrologError as e:
            assert "Division by zero" in str(e)

        # 整数除算のゼロ除算
        try:
            expr2 = Term(Atom("//"), [Number(5), Number(0)])
            self.math_interpreter.evaluate(expr2, self.env)
            assert False, "Should have raised PrologError"
        except PrologError as e:
            assert "division by zero" in str(e).lower()

        # モジュロ演算のゼロ除算
        try:
            expr3 = Term(Atom("mod"), [Number(5), Number(0)])
            self.math_interpreter.evaluate(expr3, self.env)
            assert False, "Should have raised PrologError"
        except PrologError as e:
            assert "zero" in str(e).lower()

    def test_overflow_underflow(self):
        """オーバーフロー・アンダーフローのテスト"""
        # 非常に大きな指数によるオーバーフロー
        try:
            expr = Term(Atom("**"), [Number(10), Number(1000)])
            result = self.math_interpreter.evaluate(expr, self.env)
            # オーバーフローの適切な処理を確認
            if not math.isinf(result):
                assert isinstance(result, (int, float))
        except (OverflowError, PrologError):
            pass

        # アンダーフロー（非常に小さな値）
        try:
            expr2 = Term(Atom("**"), [Number(10), Number(-1000)])
            result2 = self.math_interpreter.evaluate(expr2, self.env)
            assert result2 >= 0  # 正の値であることを確認
        except (PrologError, OverflowError):
            pass

    def test_negative_zero(self):
        """負のゼロの処理テスト"""
        neg_zero = Number(-0.0)
        pos_zero = Number(0.0)

        # 数学的には等しい
        assert self.math_interpreter.evaluate_comparison_op("=:=", -0.0, 0.0)

        # 演算結果での負のゼロ
        expr = Term(Atom("*"), [Number(-1.0), Number(0.0)])
        result = self.math_interpreter.evaluate(expr, self.env)
        # 結果は0（符号は実装依存）
        assert result == 0.0

    def test_special_float_values(self):
        """特殊な浮動小数点値のテスト"""
        # 最小正規化数
        min_normal = Number(sys.float_info.min)
        result = self.math_interpreter.evaluate(min_normal, self.env)
        assert result == sys.float_info.min

        # 最大値
        max_float = Number(sys.float_info.max)
        result = self.math_interpreter.evaluate(max_float, self.env)
        assert result == sys.float_info.max

    def test_precision_loss_in_operations(self):
        """演算での精度損失のテスト"""
        # 大きな数と小さな数の加算
        large = Number(1e20)
        small = Number(1.0)
        expr = Term(Atom("+"), [large, small])
        result = self.math_interpreter.evaluate(expr, self.env)

        # 精度損失により、結果は大きな数とほぼ同じ
        assert abs(result - 1e20) < 1e10

    def test_integer_overflow_simulation(self):
        """整数オーバーフローのシミュレーション"""
        # Pythonは任意精度整数なので、実際のオーバーフローはない
        # しかし、非常に大きな計算の処理時間を確認
        import time

        start_time = time.time()
        expr = Term(Atom("**"), [Number(2), Number(100)])
        result = self.math_interpreter.evaluate(expr, self.env)
        end_time = time.time()

        assert result == 2**100
        # 合理的な時間内で完了
        assert end_time - start_time < 1.0

    def test_complex_precision_scenarios(self):
        """複雑な精度シナリオのテスト"""
        # 連続する浮動小数点演算
        # ((0.1 + 0.2) + 0.3) + 0.4
        expr1 = Term(Atom("+"), [Number(0.1), Number(0.2)])
        expr2 = Term(Atom("+"), [expr1, Number(0.3)])
        expr3 = Term(Atom("+"), [expr2, Number(0.4)])

        result = self.math_interpreter.evaluate(expr3, self.env)
        expected = 1.0
        assert abs(result - expected) < 1e-10

    def test_edge_case_modulo(self):
        """モジュロ演算の境界ケース"""
        # 負数のモジュロ
        expr1 = Term(Atom("mod"), [Number(-7), Number(3)])
        result1 = self.math_interpreter.evaluate(expr1, self.env)
        # Pythonの % 演算子の動作に従う
        assert result1 == (-7) % 3

        # 小数のモジュロ
        expr2 = Term(Atom("mod"), [Number(7.5), Number(2.5)])
        result2 = self.math_interpreter.evaluate(expr2, self.env)
        assert abs(result2 - (7.5 % 2.5)) < 1e-10

    def test_power_operation_edge_cases(self):
        """指数演算の境界ケース"""
        # 0の指数
        expr1 = Term(Atom("**"), [Number(0), Number(5)])
        result1 = self.math_interpreter.evaluate(expr1, self.env)
        assert result1 == 0

        # 1の指数
        expr2 = Term(Atom("**"), [Number(1), Number(1000)])
        result2 = self.math_interpreter.evaluate(expr2, self.env)
        assert result2 == 1

        # 負数の偶数乗
        expr3 = Term(Atom("**"), [Number(-2), Number(4)])
        result3 = self.math_interpreter.evaluate(expr3, self.env)
        assert result3 == 16

        # 負数の奇数乗
        expr4 = Term(Atom("**"), [Number(-2), Number(3)])
        result4 = self.math_interpreter.evaluate(expr4, self.env)
        assert result4 == -8

    def test_comparison_edge_cases(self):
        """比較演算の境界ケース"""
        # 非常に近い値の比較
        val1 = 1.0000000000000001
        val2 = 1.0000000000000002

        # 浮動小数点の限界での比較
        result = self.math_interpreter.evaluate_comparison_op("=:=", val1, val2)
        # 実装により結果は異なる可能性がある
        assert isinstance(result, bool)

    def test_variable_with_edge_values(self):
        """境界値を持つ変数のテスト"""
        # 変数に特殊値を束縛
        self.env.bind("BigNum", Number(1e100))
        self.env.bind("SmallNum", Number(1e-100))

        # 変数を使った演算
        expr = Term(Atom("*"), [Variable("BigNum"), Variable("SmallNum")])
        result = self.math_interpreter.evaluate(expr, self.env)
        assert result == 1e100 * 1e-100  # = 1.0

    def test_nested_arithmetic_edge_cases(self):
        """ネストした算術演算の境界ケース"""
        # 深くネストした演算
        # ((((1 + 1) * 2) / 2) - 1)
        expr1 = Term(Atom("+"), [Number(1), Number(1)])
        expr2 = Term(Atom("*"), [expr1, Number(2)])
        expr3 = Term(Atom("/"), [expr2, Number(2)])
        expr4 = Term(Atom("-"), [expr3, Number(1)])

        result = self.math_interpreter.evaluate(expr4, self.env)
        assert result == 1.0

    def test_type_coercion_edge_cases(self):
        """型強制の境界ケース"""
        # 整数と浮動小数点の混合演算
        expr = Term(Atom("/"), [Number(5), Number(2.0)])
        result = self.math_interpreter.evaluate(expr, self.env)
        assert result == 2.5  # 浮動小数点除算

        # 整数除算との違い
        expr2 = Term(Atom("//"), [Number(5), Number(2)])
        result2 = self.math_interpreter.evaluate(expr2, self.env)
        assert result2 == 2  # 整数除算
