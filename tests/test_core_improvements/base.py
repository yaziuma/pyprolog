import pytest
from prolog.logger import logger

logger.debug("base.py loaded") # Changed from test_core_improvements.py

from prolog.interpreter import Runtime
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
                # 数値を処理する際の変換を修正 (仕様書 3)
                if isinstance(val_term, Number):
                    # 数値を文字列ではなく数値として処理
                    processed_sol[var_obj.name] = val_term.value
                    # または下記のように整数値との比較を許容
                    # processed_sol[var_obj.name] = float(val_term.value) # 仕様書のコメントに従い、まずは .value を使用
                elif isinstance(val_term, Term) and not val_term.args: # Atom
                    processed_sol[var_obj.name] = val_term.pred
                else:
                    processed_sol[var_obj.name] = str(val_term) # For complex terms or other types
            processed_solutions.append(processed_sol)
        logger.debug(f"Processed actual solutions for '{query_str}': {processed_solutions}")

        processed_expected = []
        for expected_sol_map in expected_bindings_list:
            processed_exp = {}
            for var_name, val_obj in expected_sol_map.items():
                # Process expected values similarly for consistent comparison
                if isinstance(val_obj, Number):
                    processed_exp[var_name] = val_obj.value
                elif isinstance(val_obj, Term) and not val_obj.args: # Atom
                    processed_exp[var_name] = val_obj.pred
                elif isinstance(val_obj, (int, float)): # Allow raw numbers in expected
                    processed_exp[var_name] = val_obj
                elif isinstance(val_obj, str): # Allow raw strings (atoms) in expected
                     processed_exp[var_name] = val_obj
                else:
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
