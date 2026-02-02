import pytest

from pyprolog.runtime.interpreter import Runtime
from pyprolog.core.types import Number


@pytest.fixture
def runtime():
    return Runtime()


def _vals(solutions, var_name: str):
    out = []
    for sol in solutions:
        for k, v in sol.items():
            if getattr(k, "name", None) == var_name:
                out.append(v)
                break
        else:
            raise AssertionError(f"Variable {var_name} not found in solution: {sol}")
    return out


def _nums(xs):
    # 数値表現が int/float どちらでも落ちないように正規化（ガードレールの安定化）
    out = []
    for x in xs:
        if isinstance(x, Number):
            out.append(x.value)
        else:
            raise AssertionError(f"Expected Number, got {type(x)}: {x}")
    return out


def _exec(runtime: Runtime, goal: str):
    """
    目的：builtin を“実行”する（add_ruleではなくqueryを使う）
    成功したら少なくとも1解を返す想定。
    """
    sols = runtime.query(goal)
    assert len(sols) >= 1, f"Goal failed unexpectedly: {goal}"
    return sols


# ------------------------------------------------------------
# Guardrail 1: 動的更新＋インデクシング整合性（最終像から逆算）
#
# - assertz/asserta/retract を“実行”した結果が、即 query に反映される
# - retract した節が二度と候補に出ない（幽霊節NG = index更新の核心）
# - asserta/assertz の挿入位置が列挙順に反映される（順序意味論）
# ------------------------------------------------------------
def test_guardrail_dynamic_update_and_index_consistency(runtime):
    # ここが重要：add_rule じゃなく query で builtin 実行
    _exec(runtime, "assertz(p(1)).")
    _exec(runtime, "assertz(p(2)).")

    xs = _nums(_vals(runtime.query("p(X)."), "X"))
    assert xs == [1, 2]

    _exec(runtime, "retract(p(1)).")
    xs = _nums(_vals(runtime.query("p(X)."), "X"))
    assert xs == [2]  # 1 が残るなら index/候補キャッシュが腐ってる

    _exec(runtime, "asserta(p(0)).")
    xs = _nums(_vals(runtime.query("p(X)."), "X"))
    assert xs == [0, 2]  # asserta は先頭

    _exec(runtime, "assertz(p(3)).")
    xs = _nums(_vals(runtime.query("p(X)."), "X"))
    assert xs == [0, 2, 3]  # assertz は末尾


# ------------------------------------------------------------
# Guardrail 2: 連言（`,`）の解順序保持（最終像から逆算）
# - `,` 最適化（フラット化/トランポリン）後も、生成順が変わらない
# ------------------------------------------------------------
def test_guardrail_conjunction_solution_order_preserved(runtime):
    # これは普通に add_rule でOK（p/1, q/1 を“定義”する）
    assert runtime.add_rule("p(1).")
    assert runtime.add_rule("p(2).")
    assert runtime.add_rule("q(1).")
    assert runtime.add_rule("q(2).")

    sols = runtime.query("p(X), q(Y).")
    xs = _nums(_vals(sols, "X"))
    ys = _nums(_vals(sols, "Y"))
    pairs = list(zip(xs, ys))

    # Prolog の基本順序：左の解ごとに右を全探索
    assert pairs == [(1, 1), (1, 2), (2, 1), (2, 2)]


# ------------------------------------------------------------
# Guardrail 3: retract/1 の意味論（最終像から逆算）
# - retract(p(X)) が（少なくとも繰り返しで）全節を消せる
# - 消した節が候補に残らない（幽霊節NG）
#
# ※「1回の retract(p(X)) で全部返る（非決定）」まで縛るのは、
#   仕様確定後に強化でOK。まずは“消えること”を太く守る。
# ------------------------------------------------------------
def test_guardrail_retract_deletes_all_no_ghosts(runtime):
    from pyprolog.core.errors import PrologError

    _exec(runtime, "assertz(p(1)).")
    _exec(runtime, "assertz(p(2)).")
    _exec(runtime, "assertz(p(3)).")

    # まず1個は消える
    xs1 = _nums(_vals(_exec(runtime, "retract(p(X))."), "X"))
    assert len(xs1) >= 1

    # 残りを消し切る（最大回数で安全に）
    for _ in range(5):
        try:
            rem = runtime.query("p(_).")
            if rem == []:
                break
        except PrologError:
            # All clauses deleted, existence_error expected (undeclared predicate)
            break
        _exec(runtime, "retract(p(_)).")

    # After deleting all clauses without dynamic declaration, should raise existence_error
    with pytest.raises(PrologError) as exc_info:
        runtime.query("p(_).")
    assert "existence_error" in str(exc_info.value).lower()


# ------------------------------------------------------------
# Guardrail 4: Dynamic Directive - Undefined predicate raises existence_error
# ------------------------------------------------------------
def test_guardrail_undefined_predicate_raises_existence_error(runtime):
    """GR-4: Undefined predicate should raise existence_error"""
    from pyprolog.core.errors import PrologError

    with pytest.raises(PrologError) as exc_info:
        runtime.query("undefined_predicate(X).")
    assert "existence_error" in str(exc_info.value).lower()
    assert "undefined_predicate/1" in str(exc_info.value)


# ------------------------------------------------------------
# Guardrail 5: Dynamic Directive - Declared predicate with no clauses fails
# ------------------------------------------------------------
def test_guardrail_dynamic_predicate_with_no_clauses_fails(runtime):
    """GR-5: Dynamic predicate with no clauses should fail, not error"""
    import tempfile
    import os

    # Create temp file with dynamic directive
    with tempfile.NamedTemporaryFile(mode='w', suffix='.prolog', delete=False, encoding='utf-8') as f:
        f.write(":- dynamic(p/1).\n")
        temp_file = f.name

    try:
        # Consult file with dynamic directive
        assert runtime.consult(temp_file)

        # Query should fail (not raise exception)
        solutions = runtime.query("p(X).")
        assert solutions == []

        # After assert and retract, should still fail
        _exec(runtime, "assertz(p(1)).")
        assert len(runtime.query("p(X).")) == 1

        _exec(runtime, "retract(p(1)).")
        solutions = runtime.query("p(X).")
        assert solutions == []  # Still fail, not error
    finally:
        os.unlink(temp_file)


# ------------------------------------------------------------
# Guardrail 6: Dynamic Directive - Undeclared predicate after retract raises error
# ------------------------------------------------------------
def test_guardrail_undeclared_predicate_after_retract_raises_error(runtime):
    """GR-6: Undeclared predicate after retract should raise existence_error"""
    from pyprolog.core.errors import PrologError

    # Assert without dynamic declaration
    _exec(runtime, "assertz(r(1)).")
    assert len(runtime.query("r(X).")) == 1

    # Retract all clauses
    _exec(runtime, "retract(r(1)).")

    # Query should raise existence_error (not fail)
    with pytest.raises(PrologError) as exc_info:
        runtime.query("r(X).")
    assert "existence_error" in str(exc_info.value).lower()
    assert "r/1" in str(exc_info.value)


# ------------------------------------------------------------
# Guardrail 7: Dynamic Directive - Index integrity after retract
# ------------------------------------------------------------
def test_guardrail_index_integrity_after_retract(runtime):
    """GR-7: After retract, no ghost clauses should remain in index"""
    _exec(runtime, "assertz(p(1)).")
    _exec(runtime, "assertz(p(2)).")

    # Retract all
    _exec(runtime, "retract(p(1)).")
    _exec(runtime, "retract(p(2)).")

    # Index should be clean (no ghost clauses)
    key = ("p", 1)
    # After retracting all clauses, the key should not be in rules_by_pred
    # or should be empty
    rules_by_pred = runtime.logic_interpreter.rules_by_pred
    if key in rules_by_pred:
        assert rules_by_pred[key] == []

    # Query should raise existence_error (undeclared predicate)
    from pyprolog.core.errors import PrologError
    with pytest.raises(PrologError) as exc_info:
        runtime.query("p(X).")
    assert "existence_error" in str(exc_info.value).lower()
