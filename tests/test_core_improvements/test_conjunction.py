from prolog.logger import logger
from prolog.types import Term, Variable, Number
from .base import BaseTestCore


# --- 1.5. 結合と単一化テスト ---
class TestConjunctionAndUnification(BaseTestCore):
    """
    結合ゴールと単一化に関する詳細なテスト
    """

    def test_simple_conjunction(self):
        """単純な結合ゴールのテスト"""
        logger.info("Starting test: test_simple_conjunction")
        self._consult("a. b.")
        self._assert_true("a, b", [])

    def test_conjunction_with_failure(self):
        """一部が失敗する結合ゴールのテスト"""
        logger.info("Starting test: test_conjunction_with_failure")
        self._consult("a. c.")
        self._assert_false("a, b")
        self._assert_false("b, a")

    def test_conjunction_with_variables(self):
        """変数を含む結合ゴールのテスト"""
        logger.info("Starting test: test_conjunction_with_variables")
        self._consult("a(1). a(2). b(2).")
        self._assert_true("a(X), b(X)", [{"X": Number(2)}])
        self._assert_false("b(X), a(3)")

    def test_simple_unification(self):
        """単純な単一化のテスト"""
        logger.info("Starting test: test_simple_unification")
        self._assert_true("X = a", [{"X": Term("a")}])
        self._assert_true("X = 1", [{"X": Number(1)}])
        self._assert_true("X = Y", [{"X": Variable("Y"), "Y": Variable("X")}])

    def test_complex_structure_unification(self):
        """複雑な構造の単一化のテスト"""
        logger.info("Starting test: test_complex_structure_unification")
        self._assert_true("p(X, b) = p(a, Y)", [{"X": Term("a"), "Y": Term("b")}])
        self._assert_false("p(a, b) = p(X, c)")
        self._assert_false("p(a) = q(a)")
        self._assert_false("p(a, b) = p(a)")

    def test_unification_with_multiple_occurrences(self):
        """同じ変数が複数回出現する単一化のテスト"""
        logger.info("Starting test: test_unification_with_multiple_occurrences")
        self._assert_true("p(X, X) = p(a, a)", [{"X": Term("a")}])
        self._assert_false("p(X, X) = p(a, b)")
        self._assert_true("p(X, Y, X) = p(a, b, a)", [{"X": Term("a"), "Y": Term("b")}])

    def test_unification_in_rule_body(self):
        """ルールボディでの単一化のテスト"""
        logger.info("Starting test: test_unification_in_rule_body")
        self._consult("match(X, Y) :- X = Y.")
        self._assert_true("match(a, a)", [])
        self._assert_false("match(a, b)")
        self._assert_true("match(X, a)", [{"X": Term("a")}])
        self._assert_true("match(X, Y)", [{"X": Variable("Y"), "Y": Variable("X")}])
