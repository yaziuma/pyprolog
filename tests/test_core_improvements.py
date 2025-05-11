import pytest # Changed from unittest
from prolog.logger import logger # Import logger

# Log module load first
logger.debug("test_core_improvements.py loaded")

from prolog.interpreter import Runtime
from prolog.parser import Parser
from prolog.scanner import Scanner
from prolog.types import Term, Variable, Number, Dot, TRUE, FALSE, CUT
from prolog.builtins import Retract, AssertA, AssertZ
from prolog.errors import ParserError, PrologError, UnificationError

class TestCoreImprovements: # Removed unittest.TestCase inheritance

    def setup_method(self, method): # Changed from setUp
        test_name = method.__name__
        logger.info(f"Setting up test: {test_name}")
        self.runtime = Runtime([])
        self.runtime.rules = [] # Explicitly clear for each test
        logger.debug(f"Test {test_name} Runtime initialized and rules cleared.")

    def teardown_method(self, method): # Changed from tearDown
        test_name = method.__name__
        logger.info(f"Tearing down test: {test_name}")
        logger.debug(f"Test {test_name} finished.")

    def _query(self, query_str, print_solutions_manual=False):
        logger.info(f"Executing query: '{query_str}'") # Simplified log, removed self.id()
        try:
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
            pytest.fail(f"Query '{query_str}' raised an exception: {e}") # Changed to pytest.fail

    def _consult(self, rules_str):
        logger.info(f"Consulting rules: '{rules_str[:100]}{'...' if len(rules_str) > 100 else ''}'") # Simplified log
        try:
            self.runtime.consult_rules(rules_str)
            logger.debug(f"Rules consulted. Current rule count: {len(self.runtime.rules)}")
        except Exception as e:
            logger.error(f"Consult '{rules_str}' raised an exception: {e}", exc_info=True)
            pytest.fail(f"Consult '{rules_str}' raised an exception: {e}") # Changed to pytest.fail

    def _assert_true(self, query_str, expected_bindings_list=None, exact_order=False):
        logger.info(f"Asserting true for query: '{query_str}' with expected_bindings: {expected_bindings_list}, exact_order={exact_order}") # Simplified log
        solutions = self._query(query_str)

        if not solutions:
            logger.error(f"Query '{query_str}' failed (no solutions). Expected success.")
            pytest.fail(f"Query '{query_str}' failed (no solutions). Expected success.") # Changed

        if expected_bindings_list is not None:
            processed_solutions = []
            for sol_binding_map in solutions:
                processed_sol = {}
                if not isinstance(sol_binding_map, dict):
                    logger.error(f"Solution for '{query_str}' is not a dict: {sol_binding_map}")
                    pytest.fail(f"Solution for '{query_str}' is not a dict: {sol_binding_map}") # Changed
                for var_obj, val_term in sol_binding_map.items():
                    if not isinstance(var_obj, Variable):
                         logger.error(f"Key in solution binding for '{query_str}' is not a Variable: {var_obj}")
                         pytest.fail(f"Key in solution binding for '{query_str}' is not a Variable: {var_obj}") # Changed
                    processed_sol[var_obj.name] = str(val_term)
                processed_solutions.append(processed_sol)
            logger.debug(f"Processed actual solutions for '{query_str}': {processed_solutions}")

            processed_expected = []
            for expected_sol_map in expected_bindings_list:
                processed_exp = {}
                for var_name, val_str_or_term_or_num in expected_sol_map.items():
                    processed_exp[var_name] = str(val_str_or_term_or_num)
                processed_expected.append(processed_exp)
            logger.debug(f"Processed expected bindings for '{query_str}': {processed_expected}")
            
            assert len(processed_solutions) == len(processed_expected), \
                             f"Query '{query_str}': Expected {len(processed_expected)} solutions, got {len(processed_solutions)}. Solutions: {processed_solutions}, Expected: {processed_expected}" # Changed

            if exact_order:
                for i, expected_sol_dict in enumerate(processed_expected):
                    assert processed_solutions[i] == expected_sol_dict, \
                                         f"Query '{query_str}', solution {i} (exact order): Expected {expected_sol_dict}, got {processed_solutions[i]}. All actual solutions: {processed_solutions}" # Changed
            else: 
                for expected_sol_dict in processed_expected:
                    assert expected_sol_dict in processed_solutions, \
                                  f"Query '{query_str}': Expected solution {expected_sol_dict} not found in actual solutions {processed_solutions}" # Changed
                for actual_sol_dict in processed_solutions: 
                    assert actual_sol_dict in processed_expected, \
                                  f"Query '{query_str}': Unexpected solution {actual_sol_dict} found. Expected one of {processed_expected}" # Changed
        
        logger.info(f"Assert true for '{query_str}' PASSED.") # Simplified log

    def _assert_false(self, query_str):
        logger.info(f"Asserting false for query: '{query_str}'") # Simplified log
        solutions = self._query(query_str)
        is_false = False
        if not solutions:
            is_false = True
        elif len(solutions) == 1 and isinstance(solutions[0], FALSE):
            is_false = True
        
        if not is_false:
            logger.error(f"Query '{query_str}' succeeded or yielded non-FALSE, expected failure. Solutions: {solutions}")
            pytest.fail(f"Query '{query_str}' succeeded or yielded non-FALSE, expected failure. Solutions: {solutions}") # Changed
        else:
            logger.info(f"Assert false for '{query_str}' PASSED.") # Simplified log

    # --- 2.1. パーサーの問題: 空リスト `[]` の誤解釈 ---
    def test_parse_empty_list(self):
        logger.info(f"Starting test: test_parse_empty_list") # Simplified log
        tokens = Scanner("[]").tokenize()
        parsed_term = Parser(tokens).parse_terms()
        
        assert isinstance(parsed_term, Dot), "Empty list should be parsed as a Dot object." # Changed
        assert Term("[]") == parsed_term.head, f"Head of empty list should be Term('[]'), got {parsed_term.head}" # Changed
        assert parsed_term.tail is None, f"Tail of empty list should be None, got {parsed_term.tail}" # Changed

        self.runtime.consult_rules("sum_list([], 0).")
        self.runtime.consult_rules("sum_list([H|T], S) :- sum_list(T, ST), S is H + ST.")
        self._assert_true("sum_list([], Sum)", [{"Sum": Number(0)}])

    def test_empty_list_in_query(self):
        logger.info(f"Starting test: test_empty_list_in_query") # Simplified log
        self.runtime.consult_rules("is_empty_list([]).")
        self._assert_true("is_empty_list([])")
        self._assert_false("is_empty_list([a])")

    def test_list_unification_with_empty_list(self):
        logger.info(f"Starting test: test_list_unification_with_empty_list") # Simplified log
        self._assert_true("X = [].", [{"X": Dot.from_list([])}])
        self._assert_true("[] = [].")
        self._assert_false("[] = [a].")
        self._assert_false("[a] = [].")

    def test_distinguish_empty_list_from_list_containing_empty_list(self):
        logger.info(f"Starting test: test_distinguish_empty_list_from_list_containing_empty_list") # Simplified log
        self.runtime.consult_rules("p([]).")
        self.runtime.consult_rules("q([[]]).")

        self._assert_true("p([])")
        self._assert_false("p([[]])")

        self._assert_true("q([[]])")
        list_of_empty_list = Dot.from_list([Dot.from_list([])])
        self._assert_true("q(X), X = [[]].", [{"X": list_of_empty_list}])
        self._assert_false("q([])")

    # --- 2.2.1. インタプリタの問題: カット演算子 (`!`) の処理不備 ---
    def test_cut_operator_simple(self):
        logger.info(f"Starting test: test_cut_operator_simple") # Simplified log
        self.runtime.consult_rules("p(X) :- q(X), !, r(X).")
        self.runtime.consult_rules("p(X) :- s(X).")
        self.runtime.consult_rules("q(1).")
        self.runtime.consult_rules("q(2).")
        self.runtime.consult_rules("r(1).")
        self.runtime.consult_rules("r(2).")
        self.runtime.consult_rules("s(3).")
        self._assert_true("p(X)", [{"X": Number(1)}])

    def test_cut_in_rule_body_only(self):
        logger.info(f"Starting test: test_cut_in_rule_body_only") # Simplified log
        self.runtime.consult_rules("cut_test1 :- !.")
        self.runtime.consult_rules("cut_test1 :- fail.")
        self._assert_true("cut_test1")

        self.runtime.consult_rules("cut_test2(a) :- !.")
        self.runtime.consult_rules("cut_test2(b).")
        self._assert_true("cut_test2(X)", [{"X": Term("a")}])

    def test_cut_prevents_backtracking_for_alternatives_in_same_predicate(self):
        logger.info(f"Starting test: test_cut_prevents_backtracking_for_alternatives_in_same_predicate") # Simplified log
        self.runtime.consult_rules("pred_cut(X) :- a(X), !, b(X).")
        self.runtime.consult_rules("pred_cut(fallback).")
        self.runtime.consult_rules("a(1).")
        self.runtime.consult_rules("a(2).")
        self.runtime.consult_rules("b(1).")
        self._assert_true("pred_cut(X)", [{"X": Number(1)}])

    def test_cut_prevents_backtracking_for_goals_before_cut(self):
        logger.info(f"Starting test: test_cut_prevents_backtracking_for_goals_before_cut") # Simplified log
        self.runtime.consult_rules("path(X,Y) :- edge(X,Z), !, path(Z,Y).")
        self.runtime.consult_rules("path(X,X).")
        self.runtime.consult_rules("edge(a,b).")
        self.runtime.consult_rules("edge(a,c).")
        self.runtime.consult_rules("edge(b,d).")
        results = self._query("path(a,Y)")
        assert len(results) == 1 # Changed
        assert results[0] == {"Y": Term("d")} # Changed

    def test_cut_with_failure_after_cut(self):
        logger.info(f"Starting test: test_cut_with_failure_after_cut") # Simplified log
        self.runtime.consult_rules("try_cut(X) :- first(X), !, second(X).")
        self.runtime.consult_rules("try_cut(default).")
        self.runtime.consult_rules("first(1).")
        self.runtime.consult_rules("first(2).")
        self.runtime.consult_rules("second(1) :- fail.")
        self.runtime.consult_rules("second(2).")
        self._assert_false("try_cut(1)")

    # --- 2.2.2. インタプリタの問題: 変数束縛と再帰ルールの処理不備 ---
    def test_recursive_rule_variable_binding(self):
        logger.info(f"Starting test: test_recursive_rule_variable_binding") # Simplified log
        self.runtime.consult_rules("pow10(0, 1).")
        self.runtime.consult_rules("pow10(N, R) :- N > 0, N1 is N - 1, pow10(N1, R1), R is 10 * R1.")
        self._assert_true("pow10(0, X)", [{"X": Number(1)}])
        self._assert_true("pow10(1, X)", [{"X": Number(10)}])
        self._assert_true("pow10(2, X)", [{"X": Number(100)}])
        self._assert_true("pow10(3, X)", [{"X": Number(1000)}])
        self._assert_false("pow10(-1, X)")

    def test_recursive_list_processing(self):
        logger.info(f"Starting test: test_recursive_list_processing") # Simplified log
        self.runtime.consult_rules("sum_list_rec([], 0).")
        self.runtime.consult_rules("sum_list_rec([H|T], S) :- sum_list_rec(T, ST), S is H + ST.")
        self._assert_true("sum_list_rec([], X)", [{"X": Number(0)}])
        self._assert_true("sum_list_rec([1,2,3], X)", [{"X": Number(6)}])
        self._assert_true("sum_list_rec([10,20], X)", [{"X": Number(30)}])
        self._assert_false("sum_list_rec(abc, X)")

    def test_factorial_recursive(self):
        logger.info(f"Starting test: test_factorial_recursive") # Simplified log
        self.runtime.consult_rules("factorial(0, 1).")
        self.runtime.consult_rules("factorial(N, F) :- N > 0, N1 is N - 1, factorial(N1, F1), F is N * F1.")
        self._assert_true("factorial(0, X)", [{"X": Number(1)}])
        self._assert_true("factorial(1, X)", [{"X": Number(1)}])
        self._assert_true("factorial(3, X)", [{"X": Number(6)}])
        self._assert_true("factorial(5, X)", [{"X": Number(120)}])
        self._assert_false("factorial(-1, X)")

    def test_member_recursive(self):
        logger.info(f"Starting test: test_member_recursive") # Simplified log
        self.runtime.consult_rules("member_rec(X, [X|_]).")
        self.runtime.consult_rules("member_rec(X, [_|T]) :- member_rec(X, T).")
        self._assert_true("member_rec(a, [a,b,c])", [{}])
        self._assert_true("member_rec(b, [a,b,c])", [{}])
        self._assert_true("member_rec(c, [a,b,c])", [{}])
        self._assert_false("member_rec(d, [a,b,c])")
        self._assert_false("member_rec(a, [])")

        results = self._query("member_rec(X, [1,2,3])")
        expected_results = [{"X": Number(1)}, {"X": Number(2)}, {"X": Number(3)}]
        assert len(results) == len(expected_results), "Incorrect number of solutions for member_rec(X, [1,2,3])" # Changed
        for res in results:
            assert res in expected_results, f"Unexpected solution {res} for member_rec(X, [1,2,3])" # Changed

    def test_deeply_nested_recursive_calls_and_bindings(self):
        logger.info(f"Starting test: test_deeply_nested_recursive_calls_and_bindings") # Simplified log
        self.runtime.consult_rules("append_rec([], L, L).")
        self.runtime.consult_rules("append_rec([H|T1], L2, [H|T3]) :- append_rec(T1, L2, T3).")

        expected_list = Dot.from_list([Number(1), Number(2), Number(3), Number(4)])
        self._assert_true("append_rec([1,2], [3,4], X)", [{"X": expected_list}])

        expected_x = Dot.from_list([Term("a"), Term("b")])
        self._assert_true("append_rec(X, [c,d], [a,b,c,d])", [{"X": expected_x}])

        expected_y = Dot.from_list([Number(3), Number(4)])
        self._assert_true("append_rec([1,2], Y, [1,2,3,4])", [{"Y": expected_y}])

        results = self._query("append_rec(X, Y, [a,b])")
        expected_append_xy = [
            {"X": Dot.from_list([]), "Y": Dot.from_list([Term("a"), Term("b")])},
            {"X": Dot.from_list([Term("a")]), "Y": Dot.from_list([Term("b")])},
            {"X": Dot.from_list([Term("a"), Term("b")]), "Y": Dot.from_list([])},
        ]
        assert len(results) == len(expected_append_xy) # Changed
        for r in results:
            found = False
            for expected_r in expected_append_xy:
                if str(r.get(Variable("X"))) == str(expected_r.get("X")) and \
                   str(r.get(Variable("Y"))) == str(expected_r.get("Y")):
                    found = True
                    break
            assert found, f"Unexpected solution: {r} for append_rec(X,Y,[a,b])" # Changed

    # --- 2.2.3. インタプリタの問題: `is` 述語と変数束縛の不備 ---
    def test_is_predicate_simple_arithmetic(self):
        logger.info(f"Starting test: test_is_predicate_simple_arithmetic") # Simplified log
        self._assert_true("X is 1 + 2", [{"X": Number(3)}])
        self._assert_true("X is 5 - 1", [{"X": Number(4)}])
        self._assert_true("X is 3 * 4", [{"X": Number(12)}])
        self._assert_true("X is 10 / 2", [{"X": Number(5)}])
        self._assert_true("X is 10 / 4", [{"X": Number(2.5)}])
        self._assert_true("X is 1 + 2 * 3", [{"X": Number(7)}])

    def test_is_predicate_with_bound_variables(self):
        logger.info(f"Starting test: test_is_predicate_with_bound_variables") # Simplified log
        self.runtime.consult_rules("calc(A, B, C) :- C is A + B.")
        self._assert_true("calc(3, 5, X)", [{"X": Number(8)}])
        self._assert_true("A=3, B is A+1.", [{"A":Number(3), "B": Number(4)}])

    def test_is_predicate_unbinding_left_variable(self):
        logger.info(f"Starting test: test_is_predicate_unbinding_left_variable") # Simplified log
        self._assert_false("1 is X")
        self._assert_false("Y=1, Y is X")

    def test_is_predicate_non_evaluable_expression(self):
        logger.info(f"Starting test: test_is_predicate_non_evaluable_expression") # Simplified log
        self._assert_false("X is Y + 2")
        self._assert_false("X is foo(1)")
        self._assert_false("X is 1/0")

    def test_is_predicate_in_rule_body(self):
        logger.info(f"Starting test: test_is_predicate_in_rule_body") # Simplified log
        self.runtime.consult_rules("add_one(A, B) :- B is A + 1.")
        self._assert_true("add_one(5, X)", [{"X": Number(6)}])
        self._assert_false("add_one(X, 6)") # B is A+1 cannot solve for A

    def test_is_predicate_chaining(self):
        logger.info(f"Starting test: test_is_predicate_chaining") # Simplified log
        # A is 1+2, B is A*3, C is B-A.
        self._assert_true("A is 1+2, B is A*3, C is B-A.", [{"A": Number(3), "B": Number(9), "C": Number(6)}])

    def test_is_predicate_comparison_after_binding(self):
        logger.info(f"Starting test: test_is_predicate_comparison_after_binding") # Simplified log
        # X is 2*2, X > 3.
        self._assert_true("X is 2*2, X > 3.", [{"X": Number(4)}])
        # Y is 1*1, Y > 3. -> should fail
        self._assert_false("Y is 1*1, Y > 3.")

    # --- 2.3. 算術演算機能の不足 ---
    def test_mod_operator(self):
        logger.info(f"Starting test: test_mod_operator") # Simplified log
        self._assert_true("X is 10 mod 3", [{"X": Number(1)}])
        self._assert_true("X is 10 mod -3", [{"X": Number(1)}]) # Standard Prolog behavior often matches sign of dividend
        self._assert_true("X is -10 mod 3", [{"X": Number(2)}]) # Or matches sign of divisor, or positive. Check pieprolog.
        self._assert_true("X is -10 mod -3", [{"X": Number(2)}])# Check pieprolog behavior for consistency.
        self._assert_true("X is 5 mod 5", [{"X": Number(0)}])
        self._assert_false("X is 1 mod 0") # Error

    def test_integer_division_operator_div(self): # Assuming // or div
        logger.info(f"Starting test: test_integer_division_operator_div") # Simplified log
        # Assuming 'div' or '//' for integer division based on pieprolog's capabilities
        # If pieprolog uses `/` for float division, we need a specific integer division operator
        # For now, let's assume `//` is the target for integer division
        self._assert_true("X is 10 // 3", [{"X": Number(3)}])
        self._assert_true("X is 10 // 4", [{"X": Number(2)}])
        self._assert_true("X is 10 // -3", [{"X": Number(-4)}]) # Or -3, check pieprolog behavior (floor)
        self._assert_true("X is -10 // 3", [{"X": Number(-4)}]) # (floor)
        self._assert_true("X is -10 // -3", [{"X": Number(3)}]) # (floor)
        self._assert_false("X is 1 // 0") # Error

    # --- 2.4. prolog.types.FALSE の扱いの問題 ---
    def test_query_resulting_in_false_type(self):
        logger.info(f"Starting test: test_query_resulting_in_false_type") # Simplified log
        # This test assumes that a query like 1=0, or a failing builtin,
        # might internally produce prolog.types.FALSE, and the wrapper should
        # convert this to Python False (no solutions, or specific False marker).
        # The _assert_false helper already checks for empty solutions list OR solutions == [FALSE()]
        self._assert_false("1 = 0")
        self.runtime.consult_rules("always_fail :- fail.")
        self._assert_false("always_fail")
        self._assert_false("X is 1/0") # Should result in failure/error, caught by _assert_false

    # --- Additional test for CUT behavior based on issue description ---
    def test_cut_match_behavior(self):
        logger.info(f"Starting test: test_cut_match_behavior") # Simplified log
        # Test if `cut.match(other, bindings)` always returns {}
        # This is more of an internal behavior test if directly accessible,
        # or an indirect test via rules.
        # Direct test (if Cut was easily instantiable and matchable outside interpreter):
        # cut_term = CUT() # Assuming CUT is the representation of '!'
        # bindings = {}
        # result_bindings = cut_term.match(Term("anything"), bindings)
        # self.assertEqual(result_bindings, {})

        # Indirect test via rules:
        # rule_with_cut_in_head( ! ) :- true.  <- This is not standard Prolog syntax.
        # Facts can be `!`. or `term(!).`
        # Let's test if `X = !` works and what `X` becomes.
        # And if `! = !` works.

        # Querying for cut itself.
        # If `!` is a term that can be unified:
        self.runtime.consult_rules("is_cut(!).")
        self._assert_true("is_cut(!)") # Should succeed if ! is a term.
        self._assert_true("X = !, is_cut(X).", [{"X": CUT}]) # X should be bound to the CUT object/representation

        # Test unification of two cuts
        self._assert_true("! = !.")

        # Test unification of cut with a variable
        self._assert_true("X = !.", [{"X": CUT}])

        # Test unification of cut with a non-cut term
        self._assert_false("! = a.")
        self._assert_false("a = !.")

        # Test cut in a structure
        self.runtime.consult_rules("struct_has_cut(s(!)).")
        self._assert_true("struct_has_cut(s(!))")
        self._assert_true("struct_has_cut(s(X)), X = !.", [{"X": CUT}])
        self._assert_false("struct_has_cut(s(a))")

        # Test from issue: builtins.Cut.match always succeeds with {}
        # This implies `X = !` should succeed with `X` bound to `CUT`.
        # And `! = atom` should fail.
        # The _assert_true and _assert_false above cover these.
        # If `Cut.match` had a different behavior, these might fail.
        # For example, if `Cut.match` only matched `CUT`, then `X = !` would work,
        # but if it always returned `{}` without checking `other`, then `! = a` might
        # incorrectly succeed if not handled by a higher-level unification logic.
        # However, the `Term.match` in `types.py` usually handles the primary dispatch.
        # `builtins.Cut` is for when `!` is a goal. `types.CUT` is the term representation.
        # The tests above use `types.CUT` implicitly via the parser.
        logger.info("Finished test_cut_match_behavior")