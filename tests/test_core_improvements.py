
import pytest
from prolog.logger import logger

logger.debug("test_core_improvements.py loaded")

from prolog.interpreter import Runtime
from prolog.parser import Parser
from prolog.scanner import Scanner
from prolog.types import Term, Variable, Number, Dot, TRUE, FALSE, CUT
# from prolog.builtins import Retract, AssertA, AssertZ # Not directly used in these refactored tests yet
# from prolog.errors import ParserError, PrologError, UnificationError # Not directly caught in these refactored tests yet

# --- Base Test Class with Helper Methods ---
class BaseTestCore:
    def setup_method(self, method):
        test_name = method.__name__
        logger.info(f"Setting up test: {test_name} in {self.__class__.__name__}")
        self.runtime = Runtime([])
        self.runtime.rules = []
        logger.debug(f"Test {test_name} Runtime initialized and rules cleared.")

    def teardown_method(self, method):
        test_name = method.__name__
        logger.info(f"Tearing down test: {test_name} in {self.__class__.__name__}")
        logger.debug(f"Test {test_name} finished.")

    def _query(self, query_str, print_solutions_manual=False):
        logger.info(f"Executing query: '{query_str}'")
        try:
            # Ensure the query string itself doesn't cause an immediate error before parsing
            if not isinstance(query_str, str):
                pytest.fail(f"Query string is not a string: {query_str}")

            solutions = list(self.runtime.query(query_str))
            logger.debug(f"Query '{query_str}' yielded solutions: {solutions}")
            if print_solutions_manual:
                print(f"Query: {query_str}")
                if solutions:
                    for sol_idx, sol in enumerate(solutions):
                        print(f"  Solution [{sol_idx}]: {sol}")
                else:
                    print("  No solutions.")
            return solutions
        except Exception as e:
            logger.error(f"Query '{query_str}' raised an exception: {e}", exc_info=True)
            pytest.fail(f"Query '{query_str}' raised an exception: {e}")

    def _consult(self, rules_str):
        logger.info(f"Consulting rules: '{rules_str[:100]}{'...' if len(rules_str) > 100 else ''}'")
        try:
            if not isinstance(rules_str, str):
                pytest.fail(f"Rules string is not a string: {rules_str}")
            self.runtime.consult_rules(rules_str)
            logger.debug(f"Rules consulted. Current rule count: {len(self.runtime.rules)}")
        except Exception as e:
            logger.error(f"Consult '{rules_str}' raised an exception: {e}", exc_info=True)
            pytest.fail(f"Consult '{rules_str}' raised an exception: {e}")

    def _assert_true(self, query_str, expected_bindings_list=None, exact_order=False):
        logger.info(f"Asserting true for query: '{query_str}' with expected_bindings: {expected_bindings_list}, exact_order={exact_order}")
        solutions = self._query(query_str)

        if expected_bindings_list is None: # Expecting success, at least one solution, bindings don't matter
            if not solutions:
                logger.error(f"Query '{query_str}' failed (no solutions). Expected success (any solution).")
                pytest.fail(f"Query '{query_str}' failed (no solutions). Expected success (any solution).")
            logger.info(f"Assert true for '{query_str}' (any solution) PASSED.")
            return

        if expected_bindings_list == []: # Expecting success with no specific variable bindings (e.g. ground query true)
            if not (len(solutions) == 1 and solutions[0] == {}): # Check for exactly one empty dict solution
                logger.error(f"Query '{query_str}' did not yield exactly one empty binding. Got: {solutions}. Expected success (ground query).")
                pytest.fail(f"Query '{query_str}' did not yield exactly one empty binding. Got: {solutions}. Expected success (ground query).")
            logger.info(f"Assert true for '{query_str}' (ground query success) PASSED.")
            return
        
        # If we expect specific bindings, `solutions` should not be empty.
        if not solutions and expected_bindings_list: # This condition implies expected_bindings_list is not None and not []
             logger.error(f"Query '{query_str}' failed (no solutions). Expected success with bindings: {expected_bindings_list}")
             pytest.fail(f"Query '{query_str}' failed (no solutions). Expected success with bindings: {expected_bindings_list}")


        processed_solutions = []
        for sol_binding_map in solutions:
            processed_sol = {}
            if not isinstance(sol_binding_map, dict):
                logger.error(f"Solution for '{query_str}' is not a dict: {sol_binding_map}")
                pytest.fail(f"Solution for '{query_str}' is not a dict: {sol_binding_map}")
            for var_obj, val_term in sol_binding_map.items():
                if not isinstance(var_obj, Variable):
                     logger.error(f"Key in solution binding for '{query_str}' is not a Variable: {var_obj}")
                     pytest.fail(f"Key in solution binding for '{query_str}' is not a Variable: {var_obj}")
                processed_sol[var_obj.name] = str(val_term) 
            processed_solutions.append(processed_sol)
        logger.debug(f"Processed actual solutions for '{query_str}': {processed_solutions}")

        processed_expected = []
        for expected_sol_map in expected_bindings_list:
            processed_exp = {}
            for var_name, val_obj in expected_sol_map.items(): 
                processed_exp[var_name] = str(val_obj) 
            processed_expected.append(processed_exp)
        logger.debug(f"Processed expected bindings for '{query_str}': {processed_expected}")
        
        assert len(processed_solutions) == len(processed_expected), \
                         f"Query '{query_str}': Expected {len(processed_expected)} solutions, got {len(processed_solutions)}. Solutions: {processed_solutions}, Expected: {processed_expected}"

        if exact_order:
            for i, expected_sol_dict in enumerate(processed_expected):
                assert processed_solutions[i] == expected_sol_dict, \
                                     f"Query '{query_str}', solution {i} (exact order): Expected {expected_sol_dict}, got {processed_solutions[i]}. All actual solutions: {processed_solutions}"
        else: 
            # Check that every expected solution is in the actual solutions
            for expected_sol_dict in processed_expected:
                assert expected_sol_dict in processed_solutions, \
                              f"Query '{query_str}': Expected solution {expected_sol_dict} not found in actual solutions {processed_solutions}"
            # Check that every actual solution was expected (prevents extra unexpected solutions)
            for actual_sol_dict in processed_solutions: 
                assert actual_sol_dict in processed_expected, \
                              f"Query '{query_str}': Unexpected solution {actual_sol_dict} found. Expected one of {processed_expected}"
        
        logger.info(f"Assert true for '{query_str}' PASSED.")


    def _assert_false(self, query_str):
        logger.info(f"Asserting false for query: '{query_str}'")
        solutions = self._query(query_str)
        # A query is false if it yields no solutions.
        if not solutions:
            logger.info(f"Assert false for '{query_str}' PASSED (no solutions).")
        else:
            logger.error(f"Query '{query_str}' succeeded, expected failure. Solutions: {solutions}")
            pytest.fail(f"Query '{query_str}' succeeded (solutions: {solutions}), expected failure.")

# --- 1. Basic Parsing, Types, and Simple Predicates ---
class TestBasicParsingAndTypes(BaseTestCore):

    def test_simple_fact_consult_and_query(self):
        logger.info("Starting test: test_simple_fact_consult_and_query")
        self._consult("p(a).")
        self._assert_true("p(a)", []) 
        self._assert_true("p(X)", [{"X": Term("a")}])
        self._assert_false("p(b)")

    def test_true_predicate(self):
        logger.info("Starting test: test_true_predicate")
        self._assert_true("true", [])

    def test_fail_predicate(self):
        logger.info("Starting test: test_fail_predicate")
        self._assert_false("fail")
        self._consult("my_fail :- fail.")
        self._assert_false("my_fail")

    def test_query_resulting_in_false_type(self): 
        logger.info(f"Starting test: test_query_resulting_in_false_type")
        self._assert_false("a = b") 
        self._consult("always_fail_rule :- fail.")
        self._assert_false("always_fail_rule")


# --- 2. List Processing ---
class TestListProcessing(BaseTestCore):

    def test_parse_empty_list_direct(self):
        logger.info(f"Starting test: test_parse_empty_list_direct")
        rule_tokens = Scanner("p([]).").tokenize()
        parsed_rule = Parser(rule_tokens).parse_rules()[0]
        empty_list_term = parsed_rule.head.args[0]

        assert isinstance(empty_list_term, Dot), "Empty list should be parsed as a Dot object."
        assert Term("[]") == empty_list_term.head, f"Head of empty list should be Term('[]'), got {empty_list_term.head}"
        assert empty_list_term.tail is None, f"Tail of empty list should be None, got {empty_list_term.tail}"

        self._consult("sum_list_basic([], 0).")
        self._consult("sum_list_basic([H|T], S) :- sum_list_basic(T, ST), S is H + ST.")
        self._assert_true("sum_list_basic([], Sum)", [{"Sum": Number(0)}])

    def test_empty_list_in_query(self):
        logger.info(f"Starting test: test_empty_list_in_query")
        self._consult("is_empty_list([]).")
        self._assert_true("is_empty_list([])", [])
        self._assert_false("is_empty_list([a])")

    def test_list_unification_with_empty_list(self):
        logger.info(f"Starting test: test_list_unification_with_empty_list")
        self._assert_true("X = [].", [{"X": Dot.from_list([])}])
        self._assert_true("[] = [].", [])
        self._assert_false("[] = [a].")
        self._assert_false("[a] = [].")

    def test_distinguish_empty_list_from_list_containing_empty_list(self):
        logger.info(f"Starting test: test_distinguish_empty_list_from_list_containing_empty_list")
        self._consult("p([]).")
        self._consult("q([[]]).")

        self._assert_true("p([])", [])
        self._assert_false("p([[]])")

        self._assert_true("q([[]])", [])
        list_of_empty_list = Dot.from_list([Dot.from_list([])])
        self._assert_true("q(X), X = [[]].", [{"X": list_of_empty_list}]) 
        self._assert_false("q([])")

    def test_recursive_list_processing_sum_list(self):
        logger.info(f"Starting test: test_recursive_list_processing_sum_list")
        self._consult("sum_list_rec([], 0).")
        self._consult("sum_list_rec([H|T], S) :- sum_list_rec(T, ST), S is H + ST.")
        self._assert_true("sum_list_rec([], X)", [{"X": Number(0)}])
        self._assert_true("sum_list_rec([1,2,3], X)", [{"X": Number(6)}])
        self._assert_true("sum_list_rec([10,20], X)", [{"X": Number(30)}])
        self._assert_false("sum_list_rec(abc, X)")

    def test_member_recursive(self):
        logger.info(f"Starting test: test_member_recursive")
        self._consult("member_rec(X, [X|_]).")
        self._consult("member_rec(X, [_|T]) :- member_rec(X, T).")
        self._assert_true("member_rec(a, [a,b,c])", []) 
        self._assert_true("member_rec(b, [a,b,c])", [])
        self._assert_true("member_rec(c, [a,b,c])", [])
        self._assert_false("member_rec(d, [a,b,c])")
        self._assert_false("member_rec(a, [])")

        self._assert_true("member_rec(X, [1,2,3])", 
                          [{"X": Number(1)}, {"X": Number(2)}, {"X": Number(3)}])

    def test_deeply_nested_recursive_calls_and_bindings_append(self):
        logger.info(f"Starting test: test_deeply_nested_recursive_calls_and_bindings_append")
        self._consult("append_rec([], L, L).")
        self._consult("append_rec([H|T1], L2, [H|T3]) :- append_rec(T1, L2, T3).")

        expected_list_1234 = Dot.from_list([Number(1), Number(2), Number(3), Number(4)])
        self._assert_true("append_rec([1,2], [3,4], X)", [{"X": expected_list_1234}])

        expected_x_ab = Dot.from_list([Term("a"), Term("b")])
        self._assert_true("append_rec(X, [c,d], [a,b,c,d])", [{"X": expected_x_ab}])

        expected_y_34 = Dot.from_list([Number(3), Number(4)])
        self._assert_true("append_rec([1,2], Y, [1,2,3,4])", [{"Y": expected_y_34}])
        
        self._assert_true("append_rec(X, Y, [a,b])", [
            {"X": Dot.from_list([]), "Y": Dot.from_list([Term("a"), Term("b")])},
            {"X": Dot.from_list([Term("a")]), "Y": Dot.from_list([Term("b")])},
            {"X": Dot.from_list([Term("a"), Term("b")]), "Y": Dot.from_list([])},
        ])


# --- 3. Arithmetic and 'is' Predicate ---
class TestArithmeticAndIsPredicate(BaseTestCore):

    def test_is_predicate_simple_arithmetic(self):
        logger.info(f"Starting test: test_is_predicate_simple_arithmetic")
        self._assert_true("X is 1 + 2", [{"X": Number(3)}])
        self._assert_true("X is 5 - 1", [{"X": Number(4)}])
        self._assert_true("X is 3 * 4", [{"X": Number(12)}])
        self._assert_true("X is 10 / 2", [{"X": Number(5.0)}])
        self._assert_true("X is 10 / 4", [{"X": Number(2.5)}])
        self._assert_true("X is 1 + 2 * 3", [{"X": Number(7)}])

    def test_is_predicate_with_bound_variables(self):
        logger.info(f"Starting test: test_is_predicate_with_bound_variables")
        self._consult("calc(A, B, C) :- C is A + B.")
        self._assert_true("calc(3, 5, X)", [{"X": Number(8)}])
        self._assert_true("A=3, B is A+1.", [{"A":Number(3), "B": Number(4)}])

    def test_is_predicate_unbinding_left_variable(self):
        logger.info(f"Starting test: test_is_predicate_unbinding_left_variable")
        self._assert_false("1 is X") 
        self._assert_false("Y=1, Y is X")
        self._assert_true("X is 1+0, X = 1.", [{"X": Number(1)}]) 
        self._assert_false("1 = Z, Z is 1+2.") 

    def test_is_predicate_non_evaluable_expression(self):
        logger.info(f"Starting test: test_is_predicate_non_evaluable_expression")
        self._assert_false("X is Y + 2") 
        self._assert_false("X is foo(1)") 
        self._assert_false("X is 1/0") 

    def test_is_predicate_in_rule_body(self):
        logger.info(f"Starting test: test_is_predicate_in_rule_body")
        self._consult("add_one(A, B) :- B is A + 1.")
        self._assert_true("add_one(5, X)", [{"X": Number(6)}])
        self._assert_false("add_one(X, 6)")

    def test_is_predicate_chaining(self):
        logger.info(f"Starting test: test_is_predicate_chaining")
        self._assert_true("A is 1+2, B is A*3, C is B-A.", [{"A": Number(3), "B": Number(9), "C": Number(6)}])

    def test_is_predicate_comparison_after_binding(self):
        logger.info(f"Starting test: test_is_predicate_comparison_after_binding")
        self._assert_true("X is 2*2, X > 3.", [{"X": Number(4)}])
        self._assert_false("Y is 1*1, Y > 3.")

    def test_mod_operator(self):
        logger.info(f"Starting test: test_mod_operator")
        self._assert_true("X is 10 mod 3", [{"X": Number(1)}])
        self._assert_true("X is 10 mod -3", [{"X": Number(1)}]) 
        self._assert_true("X is -10 mod 3", [{"X": Number(2)}]) 
        self._assert_true("X is -10 mod -3", [{"X": Number(-1)}])
        self._assert_true("X is 5 mod 5", [{"X": Number(0)}])
        self._assert_false("X is 1 mod 0")

    def test_integer_division_operator_div(self): 
        logger.info(f"Starting test: test_integer_division_operator_div")
        self._assert_true("X is 10 // 3", [{"X": Number(3)}]) 
        self._assert_true("X is 10 // 4", [{"X": Number(2)}])  
        self._assert_true("X is 10 // -3", [{"X": Number(-3)}]) 
        self._assert_true("X is -10 // 3", [{"X": Number(-3)}]) 
        self._assert_true("X is -10 // -3", [{"X": Number(3)}])
        self._assert_false("X is 1 // 0")

# --- 4. Cut Operator ---
class TestCutOperator(BaseTestCore):

    def test_cut_operator_simple(self):
        logger.info(f"Starting test: test_cut_operator_simple")
        self._consult("p(X) :- q(X), !, r(X).")
        self._consult("p(X) :- s(X).")
        self._consult("q(1).")
        self._consult("q(2).") 
        self._consult("r(1).")
        self._consult("s(3).") 
        self._assert_true("p(X)", [{"X": Number(1)}]) 

    def test_cut_in_rule_body_only(self):
        logger.info(f"Starting test: test_cut_in_rule_body_only")
        self._consult("cut_test1 :- !.")
        self._consult("cut_test1 :- fail.") 
        self._assert_true("cut_test1", []) 

        self._consult("cut_test2(a) :- !.")
        self._consult("cut_test2(b).") 
        self._assert_true("cut_test2(X)", [{"X": Term("a")}])

    def test_cut_prevents_backtracking_for_alternatives_in_same_predicate(self):
        logger.info(f"Starting test: test_cut_prevents_backtracking_for_alternatives_in_same_predicate")
        self._consult("pred_cut(X) :- a(X), !, b(X).")
        self._consult("pred_cut(fallback).") 
        self._consult("a(1).")
        self._consult("a(2).") 
        self._consult("b(1).")
        self._assert_true("pred_cut(X)", [{"X": Number(1)}])

    def test_cut_prevents_backtracking_for_goals_before_cut(self):
        logger.info(f"Starting test: test_cut_prevents_backtracking_for_goals_before_cut")
        self._consult("path(X,Y) :- edge(X,Z), !, path(Z,Y).") 
        self._consult("path(X,X).")
        self._consult("edge(a,b).")
        self._consult("edge(a,c).") 
        self._consult("edge(b,d).")
        self._assert_true("path(a,Y)", [{"Y": Term("d")}])


    def test_cut_with_failure_after_cut(self):
        logger.info(f"Starting test: test_cut_with_failure_after_cut")
        self._consult("try_cut(X) :- first(X), !, second(X).")
        self._consult("try_cut(default).") 
        self._consult("first(1).")
        self._consult("first(2).")
        self._consult("second(1) :- fail.") 
        self._consult("second(2).")
        self._assert_false("try_cut(1)")
        self._assert_true("try_cut(2)", []) 

    def test_cut_match_behavior(self): 
        logger.info(f"Starting test: test_cut_match_behavior")
        self._consult("is_cut_term(!).") 
        self._assert_true("is_cut_term(!)", []) 
        self._assert_true("X = !, is_cut_term(X).", [{"X": CUT}]) 

        self._assert_true("! = !.", []) 
        self._assert_true("X = !.", [{"X": CUT}])
        self._assert_false("! = a.")
        self._assert_false("a = !.")

        self._consult("struct_has_cut(s(!)).")
        self._assert_true("struct_has_cut(s(!))", []) 
        self._assert_true("struct_has_cut(s(X)), X = !.", [{"X": CUT}])
        self._assert_false("struct_has_cut(s(a))")
        logger.info("Finished test_cut_match_behavior")

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
