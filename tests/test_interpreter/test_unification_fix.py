# tests/test_interpreter/test_unification.py
from prolog.runtime.interpreter import Runtime
from prolog.core.types import Variable, Term, Rule, TRUE_TERM
from prolog.parser.parser import Parser
from prolog.parser.scanner import Scanner


def test_unification_in_rule_body():
    """変数同士の単一化をルールボディ内でテストする"""
    source = """
    match(X, Y) :- X = Y.
    """
    tokens = Scanner(source).tokenize()
    rules = Parser(tokens)._parse_rule()
    assert rules is not None
    runtime = Runtime(rules)

    # テスト1: 具体的な値同士の単一化
    goal_text = "match(hello, hello)."
    solutions = list(runtime.query(goal_text))
    assert len(solutions) > 0, "match(hello, hello) should succeed"

    # テスト2: 変数と具体値の単一化
    X_var = Variable("X")
    goal_text2 = "match(X, world)."
    solutions2 = list(runtime.query(goal_text2))
    assert len(solutions2) > 0, "match(X, world) should succeed"

    # 変数Xがworldにバインドされていることを確認
    bindings = solutions2[0]
    assert X_var in bindings
    assert str(bindings[X_var]) == "world"

    # テスト3: 異なる値の単一化は失敗すべき
    goal_text3 = "match(hello, world)."
    solutions3 = list(runtime.query(goal_text3))
    assert len(solutions3) == 0, "match(hello, world) should fail"


def test_variable_to_variable_unification():
    """変数同士の単一化テスト"""
    source = """
    equal(X, X).
    test_var_unify(A, B) :- equal(A, B).
    """
    tokens = Scanner(source).tokenize()
    rules = Parser(tokens)._parse_rule()
    assert rules is not None
    runtime = Runtime(rules)

    # 変数同士の単一化
    A_var = Variable("A")
    B_var = Variable("B")
    goal_text = "test_var_unify(A, B)."
    solutions = list(runtime.query(goal_text))
    assert len(solutions) > 0, "Variable unification should succeed"

    # AとBが同じ値にバインドされていることを確認
    # （どちらか一方が具体値、もう一方が変数の場合もある）
    bindings = solutions[0]
    if A_var in bindings and B_var in bindings:
        # 両方バインドされている場合、同じ値であることを確認
        assert bindings[A_var] == bindings[B_var]
    elif A_var in bindings:
        # Aがバインドされている場合、Bは同じ値にバインドされているはず
        assert bindings[A_var] == B_var or B_var in bindings
    elif B_var in bindings:
        # Bがバインドされている場合、Aは同じ値にバインドされているはず
        assert bindings[B_var] == A_var or A_var in bindings


def test_direct_unification_operator():
    """直接的な = 演算子のテスト"""
    source = """
    fact(a).
    fact(b).
    """
    tokens = Scanner(source).tokenize()
    rules = Parser(tokens)._parse_rule()
    assert rules is not None
    runtime = Runtime(rules)

    # 直接の単一化テスト
    X_var = Variable("X")
    goal_text = "X = hello."
    solutions = list(runtime.query(goal_text))
    assert len(solutions) > 0, "X = hello should succeed"

    bindings = solutions[0]
    assert X_var in bindings
    assert str(bindings[X_var]) == "hello"
