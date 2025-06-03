import pytest
from prolog.runtime.interpreter import Runtime
from prolog.core.types import Term, Variable, Atom, Number, Rule, Fact

class TestRecursiveRules:

    @pytest.fixture(autouse=True)
    def setup_runtime(self):
        self.runtime = Runtime()
        # Ensure a clean state for rules before each test
        self.runtime.rules.clear()
        if hasattr(self.runtime, 'logic_interpreter') and self.runtime.logic_interpreter:
            self.runtime.logic_interpreter.rules.clear()

    def assertQuerySolutions(self, query_string, expected_solutions_list, msg=None):
        """
        Asserts that the query yields a specific set of solutions in any order.
        expected_solutions_list is a list of dictionaries, where each dict
        maps variable names (str) to expected value objects (Atom, Number, Term, Variable).
        An empty dict {} in expected_solutions_list means a solution with no bindings (e.g. a fact).
        """
        print(f"PYTHON_PRINT_ASSERT: Querying: '{query_string}'", flush=True)
        solutions = self.runtime.query(query_string)
        print(f"PYTHON_PRINT_ASSERT: Solutions for '{query_string}': {solutions} (length: {len(solutions)})", flush=True)

        # Convert list of dicts of solutions to a list of frozensets of items for order-independent comparison
        # Also, convert Variable keys from solutions to string keys for easier comparison

        processed_solutions = []
        for sol_dict in solutions:
            processed_sol = {}
            for var_key, value in sol_dict.items():
                if isinstance(var_key, Variable):
                    processed_sol[var_key.name] = value
                else:
                    processed_sol[str(var_key)] = value # Should not happen with current runtime.query
            processed_solutions.append(frozenset(processed_sol.items()))

        processed_expected_solutions = []
        for expected_sol_dict in expected_solutions_list:
            processed_expected_sol = {}
            for var_name_str, expected_value in expected_sol_dict.items():
                 processed_expected_sol[var_name_str] = expected_value
            processed_expected_solutions.append(frozenset(processed_expected_sol.items()))

        assert len(processed_solutions) == len(processed_expected_solutions), \
            msg or f"Query '{query_string}' expected {len(processed_expected_solutions)} solutions, got {len(processed_solutions)}. Solutions: {solutions}"

        for expected_fs in processed_expected_solutions:
            assert expected_fs in processed_solutions, \
                msg or f"Query '{query_string}': Expected solution {dict(expected_fs)} not found in actual solutions {solutions}."

        # This also checks if there are any extra solutions in processed_solutions not in processed_expected_solutions
        for actual_fs in processed_solutions:
            assert actual_fs in processed_expected_solutions, \
                 msg or f"Query '{query_string}': Actual solution {dict(actual_fs)} was not expected. Expected: {expected_solutions_list}."


    def assertQueryTrue(self, query_string, expected_bindings_list=None, msg=None):
        """
        Asserts that the query succeeds (at least one solution).
        If expected_bindings_list is provided, checks the first solution for specific bindings.
        If expected_bindings_list is an empty list `[]`, it means success with no specific bindings to check.
        """
        print(f"PYTHON_PRINT_ASSERT: Querying: '{query_string}'", flush=True)
        solutions = self.runtime.query(query_string)
        print(f"PYTHON_PRINT_ASSERT: Solutions for '{query_string}': {solutions} (length: {len(solutions)})", flush=True)

        if expected_bindings_list is None: # Only check for success
            assert len(solutions) >= 1, msg or f"Query '{query_string}' should succeed but failed (no solutions)."
        elif not expected_bindings_list: # Empty list means succeed, no bindings to check (e.g. a fact).
            assert len(solutions) >= 1, msg or f"Query '{query_string}' should succeed but failed (no solutions)."
        else: # Check specific bindings for the first solution (can be extended or use assertQuerySolutions for multi-solution check)
            assert len(solutions) >= 1, msg or f"Query '{query_string}' expected at least one solution, got {len(solutions)}."
            # Check specific bindings for the first solution
            first_solution_bindings = solutions[0]
            expected_first_solution_bindings = expected_bindings_list[0] # Taking the first expected binding set

            # Convert Variable keys from solutions to string keys for easier comparison
            processed_first_solution = {}
            for var_key, value in first_solution_bindings.items():
                if isinstance(var_key, Variable):
                    processed_first_solution[var_key.name] = value
                else:
                    processed_first_solution[str(var_key)] = value

            for var_name_str, expected_value in expected_first_solution_bindings.items():
                actual_value = processed_first_solution.get(var_name_str)
                assert actual_value == expected_value, \
                    msg or f"Query '{query_string}', first solution: Var '{var_name_str}' expected <{expected_value}>, got <{actual_value}>."


    def assertQueryFalse(self, query_string, msg=None):
        """Asserts that the query fails (no solutions)."""
        print(f"PYTHON_PRINT_ASSERT: Querying: '{query_string}'", flush=True)
        solutions = self.runtime.query(query_string)
        print(f"PYTHON_PRINT_ASSERT: Solutions for '{query_string}': {solutions} (length: {len(solutions)})", flush=True)
        assert len(solutions) == 0, msg or f"Query '{query_string}' should fail but succeeded with {len(solutions)} solution(s)."

    # --- Test Cases ---

    def test_member_predicate(self):
        self.runtime.add_rule("member(X, [X|_]).")
        self.runtime.add_rule("member(X, [_|T]) :- member(X,T).")

        self.assertQueryTrue("member(a, [a,b,c])", [{}]) # Ground query, success
        self.assertQueryFalse("member(x, [a,b,c])")     # Ground query, failure

        # Query with a variable, expecting multiple solutions
        self.assertQuerySolutions("member(X, [a,b])", [
            {"X": Atom("a")},
            {"X": Atom("b")}
        ])
        self.assertQuerySolutions("member(X, [a])", [{"X": Atom("a")}])
        self.assertQueryFalse("member(X, [])") # Membership in empty list should fail

    def test_ancestor_predicate(self):
        self.runtime.add_rule("parent(john, mary).")
        self.runtime.add_rule("parent(mary, tom).")
        self.runtime.add_rule("parent(mary, jane).")
        self.runtime.add_rule("parent(sue, john).") # Adding one more generation

        self.runtime.add_rule("ancestor(X,Y) :- parent(X,Y).")
        self.runtime.add_rule("ancestor(X,Y) :- parent(X,Z), ancestor(Z,Y).")

        self.assertQueryTrue("ancestor(john, tom)", [{}])
        self.assertQueryTrue("ancestor(sue, tom)", [{}]) # Test multiple levels of ancestry

        # ancestor(john, X) -> mary, tom, jane
        self.assertQuerySolutions("ancestor(john, X)", [
            {"X": Atom("mary")},
            {"X": Atom("tom")},
            {"X": Atom("jane")}
        ])

        # ancestor(X, jane) -> mary, john, sue
        self.assertQuerySolutions("ancestor(X, jane)", [
            {"X": Atom("mary")}, # Direct parent
            {"X": Atom("john")}, # Grandparent via mary
            {"X": Atom("sue")}   # Great-grandparent via john, mary
        ])

        self.assertQueryFalse("ancestor(tom, john)") # No reverse ancestry

    def test_peano_addition(self):
        self.runtime.add_rule("add(0,X,X).")
        self.runtime.add_rule("add(s(X),Y,s(Z)) :- add(X,Y,Z).")

        # R = s(s(s(0))) -> s(s(s(0.0))) because 0 is parsed as Number(0.0)
        # s(0) + s(s(0)) = s(s(s(0)))
        expected_result_term1 = Term(Atom("s"), [Term(Atom("s"), [Term(Atom("s"), [Number(0.0)])])])
        self.assertQueryTrue("add(s(0), s(s(0)), R)", [{"R": expected_result_term1}])

        # X = s(s(0)) -> s(s(0.0))
        # s(s(0)) + s(0) = s(s(s(0)))
        expected_x_term2 = Term(Atom("s"), [Term(Atom("s"), [Number(0.0)])])
        self.assertQueryTrue("add(X, s(0), s(s(s(0))))", [{"X": expected_x_term2}])

        # Test with 0
        # 0 + s(0) = s(0)
        expected_r_term3 = Term(Atom("s"), [Number(0.0)])
        self.assertQueryTrue("add(0, s(0), R)", [{"R": expected_r_term3}])
        # s(0) + 0 = s(0)
        self.assertQueryTrue("add(s(0), 0, R)", [{"R": expected_r_term3}])

        # add(0,0,0) -> R = Number(0.0)
        self.assertQueryTrue("add(0,0,R)", [{"R": Number(0.0)}])

        # More complex: s(s(0)) + s(s(0)) = s(s(s(s(0)))) -> uses Number(0.0)
        # add(s(s(X)), Y, s(s(Z))) :- add(X,Y,Z)
        # add(s(s(0)), s(s(0)), R)
        # R = s(s(s(s(0.0))))
        expected_r_term4 = Term(Atom("s"), [Term(Atom("s"), [Term(Atom("s"), [Term(Atom("s"), [Number(0.0)])])])])
        self.assertQueryTrue("add(s(s(0)), s(s(0)), R)", [{"R": expected_r_term4}])

    def test_left_recursion_problem_naive_ancestor(self):
        # This test is expected to potentially cause issues if left-recursion is not handled
        # (e.g. by loop detection or reordering goals, though basic Prolog typically struggles).
        # ancestor(X,Y) :- ancestor(Z,Y), parent(X,Z). % Left-recursive version
        # ancestor(X,Y) :- parent(X,Y).
        self.runtime.add_rule("parent_lr(a,b).")
        self.runtime.add_rule("parent_lr(b,c).")
        self.runtime.add_rule("ancestor_lr(X,Y) :- ancestor_lr(Z,Y), parent_lr(X,Z).") # Problematic rule
        self.runtime.add_rule("ancestor_lr(X,Y) :- parent_lr(X,Y).")

        # Depending on the Prolog engine's sophistication, this might lead to an infinite loop.
        # We'll query something that should have a finite number of solutions.
        # If it loops, the test will time out or run out of memory.
        # We expect this to fail or be problematic for a simple interpreter.
        # For now, let's assert what *should* be true if it worked, but anticipate issues.

        # A simple query that should terminate due to the base case if evaluation order is right.
        # ancestor_lr(a,c)
        # Path 1: ancestor_lr(Z,c), parent_lr(a,Z)
        #   Z=b: ancestor_lr(b,c), parent_lr(a,b)
        #     ancestor_lr(b,c) -> parent_lr(b,c) (YES)
        #     parent_lr(a,b) (YES) -> Solution: ancestor_lr(a,c)
        # Path 2 (base case): parent_lr(a,c) (NO)

        # The issue is `ancestor_lr(Z,Y)` could call `ancestor_lr(Z1,Y), parent_lr(Z,Z1)` again and again.
        # A robust test would involve checking for non-termination, but that's hard here.
        # We will simply check if the correct solutions are found, assuming it *can* terminate.
        # If the interpreter has simple depth-first search without loop detection, this will likely fail.

        # Solutions for ancestor_lr(X,c) are X=b, X=a
        # Solutions for ancestor_lr(a,X) are X=b, X=c
        # print("Running left-recursion test. This might be slow or loop if not handled.")
        # For now, let's try a query that might expose the loop less directly if rule order is fixed
        # by the interpreter (e.g. always trying base cases first).
        # If the rule `ancestor_lr(X,Y) :- parent_lr(X,Y).` is tried first, it might work for some queries.

        # Querying ancestor_lr(a,X)
        # Try 1: ancestor_lr(Z,X), parent_lr(a,Z).
        #    parent_lr(a,Z) -> Z=b. Query becomes ancestor_lr(b,X).
        #       Try 1.1: ancestor_lr(Z1,X), parent_lr(b,Z1).
        #          parent_lr(b,Z1) -> Z1=c. Query becomes ancestor_lr(c,X).
        #             Try 1.1.1: ancestor_lr(Z2,X), parent_lr(c,Z2). parent_lr(c,Z2) fails.
        #             Try 1.1.2 (base): parent_lr(c,X). Fails. So ancestor_lr(c,X) fails.
        #          This means ancestor_lr(b,X) from this path needs another Z1. No other parent_lr(b,Z1).
        #       Try 1.2 (base): parent_lr(b,X) -> X=c. Solution: (a,c) via Z=b, X=c.
        # Try 2 (base): parent_lr(a,X) -> X=b. Solution: (a,b).

        # So, expected for ancestor_lr(a,X) are X=b and X=c.
        # This specific ordering might avoid the loop for this query if the interpreter is lucky or smart.
        self.assertQuerySolutions("ancestor_lr(a,X)", [
            {"X": Atom("b")},
            {"X": Atom("c")}
        ])
        # This one is more likely to loop: ancestor_lr(X,c)
        # Try 1: ancestor_lr(Z,c), parent_lr(X,Z).
        #    This is the problematic recursive call first.
        # If it loops, this test will fail.
        # For a basic engine, this is expected to fail by looping.
        # We'll assert the expected solutions if it *didn't* loop.
        # This test acts as a check for basic left-recursion handling.
        # A true test of non-termination is beyond simple assertQuery.
        # If this query returns the correct set, it implies some form of loop avoidance or specific evaluation strategy.
        self.assertQuerySolutions("ancestor_lr(X,c)", [
            {"X": Atom("b")}, # from parent_lr(b,c)
            {"X": Atom("a")}  # from parent_lr(a,b), ancestor_lr(b,c)
        ])
