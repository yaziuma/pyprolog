from prolog.runtime.interpreter import Runtime
from prolog.parser.parser import Parser
from prolog.parser.scanner import Scanner


def test_logic_equal():
    source = """
    sum_eq_4(Y) :- X is Y + 2, X =:= 4.
    """
    tokens = Scanner(source).tokenize()
    rules = Parser(tokens)._parse_rule()
    assert rules is not None
    runtime = Runtime(rules)

    # Query that should succeed: 2 + 2 =:= 4.
    goal_text_succeed = "sum_eq_4(2)."
    solutions_succeed = list(runtime.query(goal_text_succeed))
    assert len(solutions_succeed) > 0, (
        "sum_eq_4(2) should succeed (bindings: {})".format(
            solutions_succeed[0] if solutions_succeed else "None"
        )
    )

    # Query that should fail: 3 + 2 =:= 4 (5 =:= 4 is false).
    goal_text_fail = "sum_eq_4(3)."
    solutions_fail = list(runtime.query(goal_text_fail))
    assert len(solutions_fail) == 0, "sum_eq_4(3) should fail"


def test_logic_not_equal():
    source = """
    sum_not_eq_4(Y) :- X is Y + 2, X =\= 4.
    """
    tokens = Scanner(source).tokenize()
    rules = Parser(tokens)._parse_rule()
    assert rules is not None
    runtime = Runtime(rules)

    # Query that should succeed: 3 + 2 =\= 4 (5 =\= 4 is true).
    goal_text_succeed = "sum_not_eq_4(3)."
    solutions_succeed = list(runtime.query(goal_text_succeed))
    assert len(solutions_succeed) > 0, "sum_not_eq_4(3) should succeed"

    # Query that should fail: 2 + 2 =\= 4 (4 =\= 4 is false).
    goal_text_fail = "sum_not_eq_4(2)."
    solutions_fail = list(runtime.query(goal_text_fail))
    assert len(solutions_fail) == 0, "sum_not_eq_4(2) should fail"


def test_logic_greater():
    source = """
    sum_gt_4(Y) :- X is Y + 2, X > 4.
    """
    tokens = Scanner(source).tokenize()
    rules = Parser(tokens)._parse_rule()
    assert rules is not None
    runtime = Runtime(rules)

    # Query that should succeed: 3 + 2 > 4 (5 > 4 is true).
    goal_text_succeed = "sum_gt_4(3)."
    solutions_succeed = list(runtime.query(goal_text_succeed))
    assert len(solutions_succeed) > 0, "sum_gt_4(3) should succeed"

    # Query that should fail: 2 + 2 > 4 (4 > 4 is false).
    goal_text_fail = "sum_gt_4(2)."
    solutions_fail = list(runtime.query(goal_text_fail))
    assert len(solutions_fail) == 0, "sum_gt_4(2) should fail"

    # Query that should fail: 1 + 2 > 4 (3 > 4 is false).
    goal_text_fail_less = "sum_gt_4(1)."
    solutions_fail_less = list(runtime.query(goal_text_fail_less))
    assert len(solutions_fail_less) == 0, "sum_gt_4(1) should fail"


def test_logic_greater_or_equal():
    source = """
    sum_ge_4(Y) :- X is Y + 2, X >= 4.
    """
    tokens = Scanner(source).tokenize()
    rules = Parser(tokens)._parse_rule()
    assert rules is not None
    runtime = Runtime(rules)

    # Query that should succeed: 3 + 2 >= 4 (5 >= 4 is true).
    goal_text_succeed1 = "sum_ge_4(3)."
    solutions_succeed1 = list(runtime.query(goal_text_succeed1))
    assert len(solutions_succeed1) > 0, "sum_ge_4(3) should succeed"

    # Query that should succeed: 2 + 2 >= 4 (4 >= 4 is true).
    goal_text_succeed2 = "sum_ge_4(2)."
    solutions_succeed2 = list(runtime.query(goal_text_succeed2))
    assert len(solutions_succeed2) > 0, "sum_ge_4(2) should succeed"

    # Query that should fail: 1 + 2 >= 4 (3 >= 4 is false).
    goal_text_fail = "sum_ge_4(1)."
    solutions_fail = list(runtime.query(goal_text_fail))
    assert len(solutions_fail) == 0, "sum_ge_4(1) should fail"


def test_logic_less():
    source = """
    sum_lt_4(Y) :- X is Y + 2, X < 4.
    """
    tokens = Scanner(source).tokenize()
    rules = Parser(tokens)._parse_rule()
    assert rules is not None
    runtime = Runtime(rules)

    # Query that should succeed: 1 + 2 < 4 (3 < 4 is true).
    goal_text_succeed = "sum_lt_4(1)."
    solutions_succeed = list(runtime.query(goal_text_succeed))
    assert len(solutions_succeed) > 0, "sum_lt_4(1) should succeed"

    # Query that should fail: 2 + 2 < 4 (4 < 4 is false).
    goal_text_fail = "sum_lt_4(2)."
    solutions_fail = list(runtime.query(goal_text_fail))
    assert len(solutions_fail) == 0, "sum_lt_4(2) should fail"

    # Query that should fail: 3 + 2 < 4 (5 < 4 is false).
    goal_text_fail_greater = "sum_lt_4(3)."
    solutions_fail_greater = list(runtime.query(goal_text_fail_greater))
    assert len(solutions_fail_greater) == 0, "sum_lt_4(3) should fail"


def test_logic_less_or_equal():
    source = """
    sum_le_4(Y) :- X is Y + 2, X =< 4.
    """
    tokens = Scanner(source).tokenize()
    rules = Parser(tokens)._parse_rule()
    assert rules is not None
    runtime = Runtime(rules)

    # Query that should succeed: 1 + 2 =< 4 (3 =< 4 is true).
    goal_text_succeed1 = "sum_le_4(1)."
    solutions_succeed1 = list(runtime.query(goal_text_succeed1))
    assert len(solutions_succeed1) > 0, "sum_le_4(1) should succeed"

    # Query that should succeed: 2 + 2 =< 4 (4 =< 4 is true).
    goal_text_succeed2 = "sum_le_4(2)."
    solutions_succeed2 = list(runtime.query(goal_text_succeed2))
    assert len(solutions_succeed2) > 0, "sum_le_4(2) should succeed"

    # Query that should fail: 3 + 2 =< 4 (5 =< 4 is false).
    goal_text_fail = "sum_le_4(3)."
    solutions_fail = list(runtime.query(goal_text_fail))
    assert len(solutions_fail) == 0, "sum_le_4(3) should fail"
