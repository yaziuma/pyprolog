"""Integration tests for iterative execution.

Tests execute_iterative() method comparing results with recursive execute().
"""

import pytest

from pyprolog.core.binding_environment import BindingEnvironment
from pyprolog.core.types import Atom, Number, Term, Variable
from pyprolog.parser.parser import Parser
from pyprolog.parser.scanner import Scanner
from pyprolog.runtime.interpreter import Runtime


@pytest.fixture
def interpreter():
    """Create a fresh interpreter for each test."""
    return Runtime()


@pytest.fixture
def env():
    """Create a fresh binding environment."""
    return BindingEnvironment()


def parse_goal(goal_str: str) -> Term:
    """Parse a goal string into a Term."""
    scanner = Scanner(goal_str)
    tokens = scanner.scan_tokens()
    parser = Parser(tokens)
    structures = parser.parse()
    return structures[0] if structures else None


class TestBasicIterativeExecution:
    """Test basic iterative execution functionality."""

    def test_simple_atom_goal(self, interpreter, env):
        """Test executing a simple atom goal."""
        # Define a simple fact
        interpreter.add_rule("test.")

        goal = Atom("test")

        # Compare recursive and iterative results
        recursive_results = list(interpreter.execute(goal, env))
        iterative_results = list(interpreter.execute_iterative(goal, env))

        assert len(recursive_results) == 1
        assert len(iterative_results) == 1
        assert recursive_results[0].bindings == iterative_results[0].bindings

    def test_simple_unification(self, interpreter, env):
        """Test simple unification goal."""
        # X = 42
        goal = Term(Atom("="), [Variable("X"), Number(42)])

        recursive_results = list(interpreter.execute(goal, env))
        iterative_results = list(interpreter.execute_iterative(goal, env))

        assert len(recursive_results) == 1
        assert len(iterative_results) == 1

        # Both should bind X to 42
        assert recursive_results[0].get_value("X") == Number(42)
        assert iterative_results[0].get_value("X") == Number(42)

    def test_failing_goal(self, interpreter, env):
        """Test that undefined goals raise PrologError."""
        # Undefined predicate raises error
        goal = Atom("undefined_predicate")

        # Both should raise PrologError
        with pytest.raises(Exception):  # PrologError
            list(interpreter.execute(goal, env))

        with pytest.raises(Exception):  # PrologError
            list(interpreter.execute_iterative(goal, env))


class TestConjunction:
    """Test conjunction (,/2) with iterative execution."""

    def test_simple_conjunction(self, interpreter, env):
        """Test simple conjunction of two goals."""
        # Define facts: a. b.
        interpreter.add_rule("a.")
        interpreter.add_rule("b.")

        # Goal: a, b
        goal = Term(Atom(","), [Atom("a"), Atom("b")])

        recursive_results = list(interpreter.execute(goal, env))
        iterative_results = list(interpreter.execute_iterative(goal, env))

        assert len(recursive_results) == 1
        assert len(iterative_results) == 1

    def test_conjunction_with_unification(self, interpreter, env):
        """Test conjunction with unification."""
        # Goal: X = 1, Y = 2
        goal = Term(
            Atom(","),
            [
                Term(Atom("="), [Variable("X"), Number(1)]),
                Term(Atom("="), [Variable("Y"), Number(2)]),
            ],
        )

        recursive_results = list(interpreter.execute(goal, env))
        iterative_results = list(interpreter.execute_iterative(goal, env))

        assert len(recursive_results) == 1
        assert len(iterative_results) == 1

        # Check bindings
        assert recursive_results[0].get_value("X") == Number(1)
        assert recursive_results[0].get_value("Y") == Number(2)
        assert iterative_results[0].get_value("X") == Number(1)
        assert iterative_results[0].get_value("Y") == Number(2)

    def test_conjunction_with_failure(self, interpreter, env):
        """Test conjunction where second goal fails."""
        # Define: a.
        interpreter.add_rule("a.")

        # Goal: a, fail (fail always fails)
        goal = Term(Atom(","), [Atom("a"), Atom("fail")])

        recursive_results = list(interpreter.execute(goal, env))
        iterative_results = list(interpreter.execute_iterative(goal, env))

        assert len(recursive_results) == 0
        assert len(iterative_results) == 0


class TestDisjunction:
    """Test disjunction (;/2) with iterative execution."""

    def test_simple_disjunction(self, interpreter, env):
        """Test simple disjunction."""
        # Define: a. b.
        interpreter.add_rule("a.")
        interpreter.add_rule("b.")

        # Goal: a ; b
        goal = Term(Atom(";"), [Atom("a"), Atom("b")])

        recursive_results = list(interpreter.execute(goal, env))
        iterative_results = list(interpreter.execute_iterative(goal, env))

        # Should succeed twice (once for a, once for b)
        assert len(recursive_results) == 2
        assert len(iterative_results) == 2

    def test_disjunction_left_succeeds(self, interpreter, env):
        """Test disjunction where only left branch succeeds."""
        # Define: a.
        interpreter.add_rule("a.")

        # Goal: a ; fail (fail always fails)
        goal = Term(Atom(";"), [Atom("a"), Atom("fail")])

        recursive_results = list(interpreter.execute(goal, env))
        iterative_results = list(interpreter.execute_iterative(goal, env))

        # Should succeed once (from a)
        assert len(recursive_results) == 1
        assert len(iterative_results) == 1

    def test_disjunction_right_succeeds(self, interpreter, env):
        """Test disjunction where only right branch succeeds."""
        # Define: b.
        interpreter.add_rule("b.")

        # Goal: fail ; b (fail always fails)
        goal = Term(Atom(";"), [Atom("fail"), Atom("b")])

        recursive_results = list(interpreter.execute(goal, env))
        iterative_results = list(interpreter.execute_iterative(goal, env))

        # Should succeed once (from b)
        assert len(recursive_results) == 1
        assert len(iterative_results) == 1


class TestNegation:
    """Test negation (\\+/1) with iterative execution."""

    def test_negation_of_failure(self, interpreter, env):
        """Test negation of failing goal succeeds."""
        # Goal: \+ fail (fail always fails, so negation succeeds)
        goal = Term(Atom("\\+"), [Atom("fail")])

        recursive_results = list(interpreter.execute(goal, env))
        iterative_results = list(interpreter.execute_iterative(goal, env))

        assert len(recursive_results) == 1
        assert len(iterative_results) == 1

    def test_negation_of_success(self, interpreter, env):
        """Test negation of succeeding goal fails."""
        # Define: a.
        interpreter.add_rule("a.")

        # Goal: \+ a (a succeeds, so negation fails)
        goal = Term(Atom("\\+"), [Atom("a")])

        recursive_results = list(interpreter.execute(goal, env))
        iterative_results = list(interpreter.execute_iterative(goal, env))

        assert len(recursive_results) == 0
        assert len(iterative_results) == 0


class TestComplexQueries:
    """Test complex queries combining multiple operators."""

    def test_nested_conjunction(self, interpreter, env):
        """Test nested conjunctions."""
        # Define: a. b. c.
        interpreter.add_rule("a.")
        interpreter.add_rule("b.")
        interpreter.add_rule("c.")

        # Goal: a, (b, c)
        goal = Term(
            Atom(","),
            [Atom("a"), Term(Atom(","), [Atom("b"), Atom("c")])],
        )

        recursive_results = list(interpreter.execute(goal, env))
        iterative_results = list(interpreter.execute_iterative(goal, env))

        assert len(recursive_results) == 1
        assert len(iterative_results) == 1

    def test_conjunction_and_disjunction(self, interpreter, env):
        """Test combination of conjunction and disjunction."""
        # Define: a. b. c.
        interpreter.add_rule("a.")
        interpreter.add_rule("b.")
        interpreter.add_rule("c.")

        # Goal: a, (b ; c)
        goal = Term(
            Atom(","),
            [Atom("a"), Term(Atom(";"), [Atom("b"), Atom("c")])],
        )

        recursive_results = list(interpreter.execute(goal, env))
        iterative_results = list(interpreter.execute_iterative(goal, env))

        # Should succeed twice (a,b) and (a,c)
        assert len(recursive_results) == 2
        assert len(iterative_results) == 2


class TestUndefinedPredicate:
    """Test that undefined predicates raise PrologError."""

    def test_undefined_predicate_raises_error(self, interpreter, env):
        """Test that querying an undefined predicate raises PrologError."""
        from pyprolog.core.errors import PrologError

        # Goal: undefined_predicate_that_does_not_exist_xyz123
        goal = Atom("undefined_predicate_that_does_not_exist_xyz123")

        # Both recursive and iterative should raise PrologError
        with pytest.raises(PrologError) as exc_info:
            list(interpreter.execute(goal, env))
        assert "existence_error" in str(exc_info.value).lower()
        assert "undefined_predicate_that_does_not_exist_xyz123" in str(exc_info.value)

        with pytest.raises(PrologError) as exc_info:
            list(interpreter.execute_iterative(goal, env))
        assert "existence_error" in str(exc_info.value).lower()
        assert "undefined_predicate_that_does_not_exist_xyz123" in str(exc_info.value)
