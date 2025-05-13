from prolog.logger import logger
from prolog.types import Number
from .base import BaseTestCore

# --- 5. Recursion (Non-list specific, or more complex) ---
class TestRecursion(BaseTestCore):

    def test_recursive_rule_variable_binding_pow10(self): 
        logger.info(f"Starting test: test_recursive_rule_variable_binding_pow10")
        self._consult("pow10(0, 1).")
        self._consult("pow10(N, R) :- N > 0, N1 is N - 1, pow10(N1, R1), R is 10 * R1.")
        self._assert_true("pow10(0, X)", [{"X": Number(1)}])
        self._assert_true("pow10(1, X)", [{"X": Number(10)}])
        self._assert_true("pow10(2, X)", [{"X": Number(100)}])
        self._assert_true("pow10(3, X)", [{"X": Number(1000)}])
        self._assert_false("pow10(-1, X)") 

    def test_factorial_recursive(self):
        logger.info(f"Starting test: test_factorial_recursive")
        self._consult("factorial(0, 1).")
        self._consult("factorial(N, F) :- N > 0, N1 is N - 1, factorial(N1, F1), F is N * F1.")
        self._assert_true("factorial(0, X)", [{"X": Number(1)}])
        self._assert_true("factorial(1, X)", [{"X": Number(1)}])
        self._assert_true("factorial(3, X)", [{"X": Number(6)}])
        self._assert_true("factorial(5, X)", [{"X": Number(120)}])
        self._assert_false("factorial(-1, X)")
