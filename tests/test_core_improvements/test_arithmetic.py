from prolog.logger import logger
from prolog.types import Number
from .base import BaseTestCore

# --- 3. Arithmetic and 'is' Predicate ---
class TestArithmeticAndIsPredicate(BaseTestCore):

    def test_is_predicate_simple_arithmetic(self):
        logger.info("Starting test: test_is_predicate_simple_arithmetic")
        self._assert_true("X is 1 + 2", [{"X": Number(3)}])
        self._assert_true("X is 5 - 1", [{"X": Number(4)}])
        self._assert_true("X is 3 * 4", [{"X": Number(12)}])
        self._assert_true("X is 10 / 2", [{"X": Number(5.0)}])
        self._assert_true("X is 10 / 4", [{"X": Number(2.5)}])
        self._assert_true("X is 1 + 2 * 3", [{"X": Number(7)}])

    def test_is_predicate_with_bound_variables(self):
        logger.info("Starting test: test_is_predicate_with_bound_variables")
        self._consult("calc(A, B, C) :- C is A + B.")
        self._assert_true("calc(3, 5, X)", [{"X": Number(8)}])
        self._assert_true("A=3, B is A+1.", [{"A":Number(3), "B": Number(4)}])

    def test_is_predicate_unbinding_left_variable(self):
        logger.info("Starting test: test_is_predicate_unbinding_left_variable")
        self._assert_false("1 is X") 
        self._assert_false("Y=1, Y is X")
        self._assert_true("X is 1+0, X = 1.", [{"X": Number(1)}]) 
        self._assert_false("1 = Z, Z is 1+2.") 

    def test_is_predicate_non_evaluable_expression(self):
        logger.info("Starting test: test_is_predicate_non_evaluable_expression")
        self._assert_false("X is Y + 2") 
        self._assert_false("X is foo(1)") 
        self._assert_false("X is 1/0") 

    def test_is_predicate_in_rule_body(self):
        logger.info("Starting test: test_is_predicate_in_rule_body")
        self._consult("add_one(A, B) :- B is A + 1.")
        self._assert_true("add_one(5, X)", [{"X": Number(6)}])
        self._assert_false("add_one(X, 6)")

    def test_is_predicate_chaining(self):
        logger.info("Starting test: test_is_predicate_chaining")
        self._assert_true("A is 1+2, B is A*3, C is B-A.", [{"A": Number(3), "B": Number(9), "C": Number(6)}])

    def test_is_predicate_comparison_after_binding(self):
        logger.info("Starting test: test_is_predicate_comparison_after_binding")
        self._assert_true("X is 2*2, X > 3.", [{"X": Number(4)}])
        self._assert_false("Y is 1*1, Y > 3.")

    def test_mod_operator(self):
        logger.info("Starting test: test_mod_operator")
        self._assert_true("X is 10 mod 3", [{"X": Number(1)}])
        self._assert_true("X is 10 mod -3", [{"X": Number(1)}]) 
        self._assert_true("X is -10 mod 3", [{"X": Number(2)}]) 
        self._assert_true("X is -10 mod -3", [{"X": Number(-1)}])
        self._assert_true("X is 5 mod 5", [{"X": Number(0)}])
        self._assert_false("X is 1 mod 0")

    def test_integer_division_operator_div(self): 
        logger.info("Starting test: test_integer_division_operator_div")
        self._assert_true("X is 10 // 3", [{"X": Number(3)}]) 
        self._assert_true("X is 10 // 4", [{"X": Number(2)}])  
        self._assert_true("X is 10 // -3", [{"X": Number(-3)}]) 
        self._assert_true("X is -10 // 3", [{"X": Number(-3)}]) 
        self._assert_true("X is -10 // -3", [{"X": Number(3)}])
        self._assert_false("X is 1 // 0")
