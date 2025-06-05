import unittest
from pyprolog.runtime.interpreter import Runtime
from pyprolog.core.types import Variable, Number
from pyprolog.core.errors import PrologError


class TestDynamicPredicates(unittest.TestCase):
    def setUp(self):
        self.runtime = Runtime()
        # Clear rules explicitly for each test, though Runtime init should be clean
        self.runtime.rules.clear()
        if (
            hasattr(self.runtime, "logic_interpreter")
            and self.runtime.logic_interpreter
        ):
            self.runtime.logic_interpreter.rules.clear()

    def assertQueryTrue(self, query_string, expected_bindings_list=None, msg=None):
        solutions = self.runtime.query(query_string)

        if expected_bindings_list is None:
            self.assertGreaterEqual(
                len(solutions),
                1,
                msg
                or f"Query '{query_string}' should succeed but failed (no solutions).",
            )
        elif not expected_bindings_list:
            self.assertGreaterEqual(
                len(solutions),
                1,
                msg
                or f"Query '{query_string}' should succeed but failed (no solutions).",
            )
        else:
            self.assertEqual(
                len(solutions),
                len(expected_bindings_list),
                msg
                or f"Query '{query_string}' expected {len(expected_bindings_list)} solutions, got {len(solutions)}.",
            )
            for i, expected_bindings in enumerate(expected_bindings_list):
                solution_bindings = solutions[i]
                for var_name_str, expected_value in expected_bindings.items():
                    var_key = Variable(var_name_str)
                    actual_value = solution_bindings.get(var_key)
                    self.assertEqual(
                        actual_value,
                        expected_value,
                        msg
                        or f"Query '{query_string}', solution {i + 1}: Var '{var_name_str}' expected <{expected_value}>, got <{actual_value}>.",
                    )

    def assertQueryFalse(self, query_string, msg=None):
        solutions = self.runtime.query(query_string)
        self.assertEqual(
            len(solutions),
            0,
            msg
            or f"Query '{query_string}' should fail but succeeded with {len(solutions)} solution(s).",
        )

    def assertPrologError(self, query_string, error_type=PrologError, msg=None):
        # This helper assumes query() might raise PrologError directly,
        # or that execute() within query() does.
        # Current Runtime.query catches all exceptions and returns [].
        # So, this helper might need adjustment based on how error handling is finalized.
        # For now, we'll check if query returns [] and a specific error was logged (if possible)
        # or if a specific type of error is expected to be re-raised by query().
        # Given current Runtime.query, we expect [] for errors during execution.
        solutions = self.runtime.query(query_string)
        self.assertEqual(
            len(solutions),
            0,
            msg
            or f"Query '{query_string}' expected to fail due to error, but returned solutions.",
        )
        # Ideally, we would also check a log for the specific error message/type.

    # 1. Fact assertion and order
    def test_asserta_fact(self):
        self.assertQueryTrue("asserta(p(1)).", [{}])
        # p(1) があることを確認
        sols_p1 = self.runtime.query("p(X)")
        self.assertEqual(len(sols_p1), 1)
        self.assertEqual(
            sols_p1[0].get(Variable("X")), Number(1.0)
        )  # Parser creates Number(1.0)

        self.assertQueryTrue("asserta(p(0)).", [{}])
        # p(0) が先頭に追加され、p(1) が次にくることを確認
        sols_p2 = self.runtime.query("p(X)")
        self.assertEqual(len(sols_p2), 2)
        self.assertEqual(
            sols_p2[0].get(Variable("X")), Number(0.0)
        )  # asserta は先頭に追加
        self.assertEqual(sols_p2[1].get(Variable("X")), Number(1.0))

    def test_assertz_fact(self):
        self.assertQueryTrue("assertz(p(1)).", [{}])
        # p(1) があることを確認
        sols_p1 = self.runtime.query("p(X)")
        self.assertEqual(len(sols_p1), 1)
        self.assertEqual(sols_p1[0].get(Variable("X")), Number(1.0))

        self.assertQueryTrue("assertz(p(2)).", [{}])
        # p(1) が最初にあり、p(2) が末尾に追加されることを確認
        sols_p2 = self.runtime.query("p(X)")
        self.assertEqual(len(sols_p2), 2)
        self.assertEqual(
            sols_p2[0].get(Variable("X")), Number(1.0)
        )  # assertz は末尾に追加
        self.assertEqual(sols_p2[1].get(Variable("X")), Number(2.0))

    # 2. Rule assertion
    def test_asserta_rule(self):
        self.assertQueryTrue("asserta((q(X) :- X > 0)).", [{}])
        self.assertQueryTrue("q(5)", [{}])
        self.assertQueryFalse("q(-1)")
        # Add another rule with asserta
        self.assertQueryTrue("asserta((q(X) :- X < -10)).", [{}])
        self.assertQueryTrue("q(-15)", [{}])  # Should use the new rule first
        self.assertQueryTrue("q(5)", [{}])  # Old rule should still work

    def test_assertz_rule(self):
        self.assertQueryTrue("assertz((r(X) :- X > 0)).", [{}])
        self.assertQueryTrue("r(5)", [{}])
        self.assertQueryFalse("r(-1)")
        # Add another rule with assertz
        self.assertQueryTrue("assertz((r(X) :- X < -10)).", [{}])
        self.assertQueryTrue("r(5)", [{}])  # First rule should still be tried first
        self.assertQueryTrue("r(-15)", [{}])  # Second rule tried after the first fails

    # 3. Clauses with variables (current implementation does not rename)
    def test_assert_with_variables(self):
        # asserta(data(X)). query data(Y). X and Y should be different vars.
        # Current naive implementation will likely make X a specific var in the DB.
        self.assertQueryTrue("asserta(data(X)).", [{}])
        # Querying data(Y) should find a solution where Y gets unified with the X from data(X).
        # Since X was not instantiated at assert time, it's a variable in the DB.
        # This is complex: is X in data(X) a specific _G variable, or treated as 'X'?
        # Let's assume the parser creates Variable('X').
        # So the DB contains data(X).
        # Query data(Y) -> Y = X. If findall existed: findall(Y, data(Y), Z) -> Z = [X] (a variable)
        solutions1 = self.runtime.query("data(Y)")
        self.assertEqual(len(solutions1), 1)
        # Y should be unified with the variable X from the database.
        # This means Y is now also a variable, aliased to the DB's X.
        self.assertIsInstance(
            solutions1[0].get(Variable("Y")), Variable, "Y should be a variable"
        )

        # Assert another clause with the same variable name X.
        # asserta(other_data(X)).
        # This X should be independent of the first X.
        self.assertQueryTrue("asserta(other_data(X)).", [{}])
        solutions2 = self.runtime.query("other_data(Z)")
        self.assertEqual(len(solutions2), 1)
        self.assertIsInstance(
            solutions2[0].get(Variable("Z")), Variable, "Z should be a variable"
        )

        # Crucially, the X in data(X) and other_data(X) should be different instances if skolemization worked.
        # Without skolemization, if we query: data(myval), other_data(myval).
        # This would succeed if X was the *same* variable.
        # This test is hard to write perfectly without skolemization.
        # Let's try to see if they are treated as the same variable by binding one.
        self.assertQueryTrue("data(john).", [{}])  # data(X) in DB now means X=john

        # Now, if we query other_data(W), what is W?
        # If X in data(X) and X in other_data(X) were the *same* variable instance due to no renaming,
        # then other_data(W) would yield W=john.
        # If they are different (even if named 'X'), then other_data(W) would yield W as a variable.
        solutions3 = self.runtime.query("other_data(W)")
        self.assertEqual(len(solutions3), 1)
        # We expect W to be a variable, NOT john, if variables are treated somewhat correctly (even if not fully skolemized)
        # If X was a global 'X', then this would fail.
        # Our current asserta just puts the term as-is. If parser uses same Var('X') obj, then it's an issue.
        # This will likely expose issues.
        # For now, let's assume the parser creates new Variable objects for each clause parsed.
        # The current behavior is that the Variable('X') object itself is stored.
        # If we assert data(john), then X in data(X) becomes john.
        # If we then query other_data(W), and X in other_data(X) was the *same* Variable object,
        # W would become john. This is not desired.
        # However, our current test structure and assertQueryTrue might not expose this well
        # if Variable objects are compared by name only in `assertEqual`.
        # A better test would be:
        # asserta(data(X)).
        # asserta(other_data(X)).
        # data(john).
        # query other_data(W) -> W should still be a variable, not john.

        # Simpler test:
        self.assertQueryTrue("asserta(v_holder(Var)).", [{}])
        sol_v1 = self.runtime.query("v_holder(A)")
        self.assertEqual(len(sol_v1), 1)
        var_A = sol_v1[0].get(Variable("A"))
        self.assertIsInstance(var_A, Variable)

        # Assert another fact with a variable of the same name.
        # The new Variable('Var') in the parser for `another_v(Var)` should be a different object.
        self.assertQueryTrue("asserta(another_v(Var)).", [{}])
        sol_v2 = self.runtime.query("another_v(B)")
        self.assertEqual(len(sol_v2), 1)
        var_B = sol_v2[0].get(Variable("B"))
        self.assertIsInstance(var_B, Variable)

        # Check they are indeed different variables, not unified through some global 'Var'
        if hasattr(var_A, "name") and hasattr(
            var_B, "name"
        ):  # Make sure they are Variable objects
            self.assertNotEqual(
                id(var_A),
                id(var_B),
                "Variables from different asserta should be different objects/scopes",
            )

        # Test binding one and checking the other (if they were accidentally the same instance)
        self.assertQueryTrue(
            "v_holder(first_val).", [{}]
        )  # Binds Var in v_holder to first_val
        sol_v3 = self.runtime.query(
            "another_v(C)"
        )  # C should be unified with Var from another_v
        self.assertIsInstance(
            sol_v3[0].get(Variable("C")),
            Variable,
            "Var in another_v should remain unbound by v_holder(first_val)",
        )

    # 4. Instantiation errors
    def test_assert_uninstantiated_variable(self):
        # Standard Prolog: error(instantiation_error, asserta/1)
        # Our implementation should raise PrologError, leading to query returning []
        self.assertPrologError("asserta(X).")
        self.assertPrologError("assertz(Y).")

    # 5. Invalid clause errors
    def test_assert_invalid_clause(self):
        # Standard Prolog: error(type_error(callable, 123), asserta/1)
        self.assertPrologError("asserta(123).")
        self.assertPrologError("assertz(3.14).")
        # Standard Prolog: error(type_error(callable, (a:-123)), asserta/1) if body is not callable
        self.assertPrologError("asserta((a:-123)).")
        # Syntax for rule might be 'a :- 123.'
        # The parser should handle `(H:-B)` as a Term(':-', [H,B]).
        # Our builtins.py converts this to Rule.
        # The check `if not isinstance(rule_body, (Term, Atom, Variable))` might be too strict or not quite right.
        # A number is not Term, Atom, or Variable. So this should raise PrologError in the builtin.
        # So, assertPrologError (i.e. solutions are []) is the expected outcome.


if __name__ == "__main__":
    unittest.main()
