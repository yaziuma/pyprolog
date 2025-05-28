from prolog.runtime.interpreter import Runtime
from prolog.core.types import (
    Variable,
    Term,
    Rule,
    Atom,
)
from prolog.parser.parser import Parser
from prolog.parser.scanner import Scanner


def test_simple_rule_match():
    known_term = Term("location", Term("computer"), Term("office"))
    x_var = Variable("X")  # Renamed to x_var to be explicit
    goal_term = Term("location", Term("computer"), x_var)

    # Term.match is expected to return a dictionary-like object or None
    bindings = goal_term.match(known_term)
    assert bindings is not None, "Term.match should return bindings, not None"

    # Check if x_var is in bindings and its value
    bound_value = bindings.get(x_var)
    assert bound_value is not None, f"Variable {x_var} not found in bindings"
    assert str(bound_value) == "office", f"Expected 'office', got '{str(bound_value)}'"

    substituted_goal = goal_term.substitute(bindings)
    assert str(substituted_goal) == "location(computer, office)"


def test_query_with_multiple_results():
    source = """
    location(computer, office).
    location(knife, kitchen).
    location(chair, office).
    location(shoe, hall).

    isoffice(X) :- location(computer, X), location(chair, X).
    """
    tokens = Scanner(source).scan_tokens()
    rules = Parser(tokens).parse()
    runtime = Runtime(rules)
    goal_text = "location(X, office)."

    X_var = Variable("X")

    expected_bindings_for_x = ["computer", "chair"]

    solutions_found = 0
    # runtime.query yields dictionaries of bindings
    for i, bindings_dict in enumerate(runtime.query(goal_text)):
        solutions_found += 1
        assert X_var in bindings_dict, (
            f"Variable X not in bindings: {bindings_dict} (solution {i + 1})"
        )
        bound_value_for_x = str(bindings_dict[X_var])
        assert bound_value_for_x == expected_bindings_for_x[i], (
            f"Binding for X was '{bound_value_for_x}', expected '{expected_bindings_for_x[i]}' (solution {i + 1})"
        )

    assert solutions_found == len(expected_bindings_for_x), (
        f"Expected {len(expected_bindings_for_x)} solutions, got {solutions_found}"
    )


def test_multi_term_query():
    source = """
    location(desk, office).
    location(apple, kitchen).
    location(flashlight, desk).
    location('washing machine', cellar).
    location(nani, 'washing machine').
    location(broccoli, kitchen).
    location(crackers, kitchen).
    location(computer, office).

    door(office, hall).
    door(kitchen, office).
    door(hall, 'dinning room').
    door(kitchen, cellar).
    door('dinninr room', kitchen).
    """
    tokens = Scanner(source).scan_tokens()
    rules = Parser(tokens).parse()
    runtime = Runtime(rules)
    goal_text = "door(kitchen, R), location(T, R)."

    R_var = Variable("R")
    T_var = Variable("T")

    expected_bindings_list = [
        {"R": "office", "T": "desk"},
        {"R": "office", "T": "computer"},
        {"R": "cellar", "T": "washing machine"},
    ]

    solutions_found = 0
    for i, bindings_dict in enumerate(runtime.query(goal_text)):
        solutions_found += 1
        assert R_var in bindings_dict, (
            f"Variable R not in bindings: {bindings_dict} (solution {i + 1})"
        )
        assert T_var in bindings_dict, (
            f"Variable T not in bindings: {bindings_dict} (solution {i + 1})"
        )

        bound_r = str(bindings_dict[R_var])
        bound_t = str(bindings_dict[T_var])

        expected_r = expected_bindings_list[i]["R"]
        expected_t = expected_bindings_list[i]["T"]

        assert bound_r == expected_r, (
            f"Binding for R was '{bound_r}', expected '{expected_r}' (solution {i + 1})"
        )
        assert bound_t == expected_t, (
            f"Binding for T was '{bound_t}', expected '{expected_t}' (solution {i + 1})"
        )

    assert solutions_found == len(expected_bindings_list), (
        f"Expected {len(expected_bindings_list)} solutions, got {solutions_found}"
    )


def test_support_for_string_literals():
    source = """
    customer('John Jones', boston, good_credit).
    customer('Sally Smith', chicago, good_credit).
    """
    tokens = Scanner(source).scan_tokens()
    rules = Parser(tokens).parse()
    runtime = Runtime(rules)
    goal_text = "customer('Sally Smith', Y, Z)."

    Y_var = Variable("Y")
    Z_var = Variable("Z")

    expected_bindings_list = [{"Y": "chicago", "Z": "good_credit"}]

    solutions_found = 0
    for i, bindings_dict in enumerate(runtime.query(goal_text)):
        solutions_found += 1
        assert Y_var in bindings_dict, (
            f"Variable Y not in bindings: {bindings_dict} (solution {i + 1})"
        )
        assert Z_var in bindings_dict, (
            f"Variable Z not in bindings: {bindings_dict} (solution {i + 1})"
        )

        bound_y = str(bindings_dict[Y_var])
        bound_z = str(bindings_dict[Z_var])

        expected_y = expected_bindings_list[i]["Y"]
        expected_z = expected_bindings_list[i]["Z"]

        assert bound_y == expected_y, (
            f"Binding for Y was '{bound_y}', expected '{expected_y}' (solution {i + 1})"
        )
        assert bound_z == expected_z, (
            f"Binding for Z was '{bound_z}', expected '{expected_z}' (solution {i + 1})"
        )

    assert solutions_found == len(expected_bindings_list), (
        f"Expected {len(expected_bindings_list)} solutions, got {solutions_found}"
    )
