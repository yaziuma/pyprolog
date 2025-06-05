# tests/runtime/test_io_predicates.py
import pytest
from pyprolog.runtime.interpreter import Runtime
from pyprolog.runtime.io_streams import StringStream
from pyprolog.core.types import (
    Atom,
    Variable,
)  # Term might be needed for query construction


class TestIOPredicates:
    @pytest.fixture(autouse=True)
    def setup_runtime(self):
        self.runtime = Runtime()
        # Ensure fresh streams for each test if IOManager is stateful across tests
        # or if tests modify global stdin/stdout through ConsoleStream.
        # For get_char, we'll primarily be setting StringStream on the IOManager.

    # Helper methods adapted from other test files
    def assertQueryTrue(
        self, query_string: str, expected_bindings_list=None, msg: str = None
    ):
        """
        Asserts that a query succeeds (yields at least one solution) and optionally
        checks the bindings of the first solution.
        """
        print(f"PYTHON_PRINT_ASSERT: Querying: '{query_string}'", flush=True)
        solutions = self.runtime.query(
            query_string
        )  # runtime.query returns List[Dict[Variable, Any]]
        print(
            f"PYTHON_PRINT_ASSERT: Solutions for '{query_string}': {solutions} (length: {len(solutions)})",
            flush=True,
        )

        if not solutions:
            assert False, (
                msg
                or f"Query '{query_string}' should succeed but failed (no solutions)."
            )

        if expected_bindings_list:  # Check specific bindings for the first solution
            first_solution_bindings = solutions[0]
            expected_first_solution_bindings = expected_bindings_list[0]

            processed_first_solution = {}
            for var_key, value in first_solution_bindings.items():
                if isinstance(var_key, Variable):
                    processed_first_solution[var_key.name] = value
                else:
                    processed_first_solution[str(var_key)] = value

            for (
                var_name_str,
                expected_value,
            ) in expected_first_solution_bindings.items():
                actual_value = processed_first_solution.get(var_name_str)
                assert actual_value == expected_value, (
                    msg
                    or f"Query '{query_string}', first solution: Var '{var_name_str}' expected <{expected_value}>, got <{actual_value}>."
                )

    def assertQueryFalse(self, query_string: str, msg: str = None):
        """
        Asserts that a query fails (yields no solutions).
        """
        print(f"PYTHON_PRINT_ASSERT: Querying: '{query_string}'", flush=True)
        solutions = self.runtime.query(query_string)
        print(
            f"PYTHON_PRINT_ASSERT: Solutions for '{query_string}': {solutions} (length: {len(solutions)})",
            flush=True,
        )
        assert len(solutions) == 0, (
            msg
            or f"Query '{query_string}' should fail but succeeded with {len(solutions)} solution(s)."
        )

    # --- Test Cases for get_char/1 ---

    def test_get_char_variable(self):
        """Test get_char(X) with a variable, X should bind to the character."""
        input_stream = StringStream("a")
        self.runtime.io_manager.set_input_stream(input_stream)

        self.assertQueryTrue("get_char(X)", [{"X": Atom("a")}])

    def test_get_char_multiple_calls(self):
        """Test multiple get_char calls to read sequential characters."""
        input_stream = StringStream("ab")
        self.runtime.io_manager.set_input_stream(input_stream)

        # First call
        self.assertQueryTrue("get_char(FirstChar)", [{"FirstChar": Atom("a")}])

        # Second call should read the next character
        # Note: This relies on the IOManager and StringStream maintaining state correctly.
        # If assertQueryTrue re-initializes things in an unexpected way, this might need adjustment.
        # Assuming runtime.query uses the *same* runtime instance and thus same IOManager instance.
        self.assertQueryTrue("get_char(SecondChar)", [{"SecondChar": Atom("b")}])

    def test_get_char_match_atom_success(self):
        """Test get_char(atom) when the next char matches the atom."""
        input_stream = StringStream("c")
        self.runtime.io_manager.set_input_stream(input_stream)

        self.assertQueryTrue("get_char(c)")  # No bindings to check, just success

    def test_get_char_mismatch_atom_failure(self):
        """Test get_char(atom) when the next char does not match the atom."""
        input_stream = StringStream("d")
        self.runtime.io_manager.set_input_stream(input_stream)

        self.assertQueryFalse("get_char(x)")

    def test_get_char_eof(self):
        """Test get_char(X) at end of file, X should bind to 'end_of_file'."""
        input_stream = StringStream("")  # Empty input string
        self.runtime.io_manager.set_input_stream(input_stream)

        self.assertQueryTrue("get_char(X)", [{"X": Atom("end_of_file")}])

    def test_get_char_eof_multiple_reads(self):
        """Test that get_char(X) consistently returns 'end_of_file' after EOF is reached."""
        input_stream = StringStream("a")
        self.runtime.io_manager.set_input_stream(input_stream)

        self.assertQueryTrue("get_char(X)", [{"X": Atom("a")}])  # Read 'a'
        self.assertQueryTrue("get_char(Y)", [{"Y": Atom("end_of_file")}])  # Read EOF
        self.assertQueryTrue(
            "get_char(Z)", [{"Z": Atom("end_of_file")}]
        )  # Read EOF again

    def test_get_char_already_bound_success(self):
        """Test get_char(BoundVar) where BoundVar is already bound to the next char."""
        # This requires a compound goal or pre-setting a variable, which is hard with just runtime.query
        # A simpler approach is to use a rule.
        self.runtime.add_rule("test_bound(X) :- X = a, get_char(X).")
        input_stream = StringStream("a")
        self.runtime.io_manager.set_input_stream(input_stream)
        self.assertQueryTrue("test_bound(What)")  # What will be 'a'

    def test_get_char_already_bound_fail(self):
        """Test get_char(BoundVar) where BoundVar is bound to a different char."""
        self.runtime.add_rule("test_bound_fail(X) :- X = x, get_char(X).")
        input_stream = StringStream("a")  # Stream will provide 'a'
        self.runtime.io_manager.set_input_stream(input_stream)
        self.assertQueryFalse(
            "test_bound_fail(What)"
        )  # X=x, get_char(x) will try to unify 'a' with 'x' -> fail
