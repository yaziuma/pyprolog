from prolog.logger import logger
from prolog.types import Number
from .base import BaseTestCore


# --- 3.5. より詳細な算術演算テスト ---
class TestAdvancedArithmetic(BaseTestCore):
    """
    より複雑な算術演算に関するテスト
    """

    def test_arithmetic_with_variables(self):
        """変数を含む算術演算のテスト"""
        logger.info("Starting test: test_arithmetic_with_variables")
        self._assert_true("X = 5, Y is X + 3", [{"X": Number(5), "Y": Number(8)}])
        self._assert_true(
            "X = 10, Y = 2, Z is X / Y",
            [{"X": Number(10), "Y": Number(2), "Z": Number(5.0)}],
        )

    def test_arithmetic_comparison(self):
        """算術比較のテスト"""
        logger.info("Starting test: test_arithmetic_comparison")
        self._assert_true("5 > 3", [])
        self._assert_false("3 > 5")
        self._assert_true("5 >= 5", [])
        self._assert_true("3 < 5", [])
        self._assert_false("5 < 3")
        self._assert_true("5 =< 5", [])
        self._assert_true("5 == 5", [])
        self._assert_false("5.0 == 5.1")
        self._assert_true("5 =/ 6", [])
        self._assert_false("5 =/ 5")

    def test_complex_arithmetic_expressions(self):
        """複雑な算術式のテスト"""
        logger.info("Starting test: test_complex_arithmetic_expressions")
        self._assert_true("X is 2 + 3 * 4", [{"X": Number(14)}])  # 2 + (3 * 4)
        self._assert_true("X is (2 + 3) * 4", [{"X": Number(20)}])
        self._assert_true("X is 10 - 2 - 3", [{"X": Number(5)}])  # (10 - 2) - 3

    def test_division_and_modulo(self):
        """除算と剰余のテスト"""
        logger.info("Starting test: test_division_and_modulo")
        self._assert_true("X is 10 / 3", [{"X": Number(10 / 3)}])  # 浮動小数点除算
        self._assert_true("X is 10 // 3", [{"X": Number(3)}])  # 整数除算
        self._assert_true("X is 10 mod 3", [{"X": Number(1)}])  # 剰余

        # ゼロ除算
        self._assert_false("X is 10 / 0")
        self._assert_false("X is 10 // 0")
        self._assert_false("X is 10 mod 0")
