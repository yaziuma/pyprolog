# tests/test_interpreter/test_operator_integration.py
"""演算子統合設計の機能テスト"""

from prolog.runtime.interpreter import Runtime
from prolog.core.operators import operator_registry, OperatorType
from prolog.core.types import Variable
from prolog.parser.parser import Parser
from prolog.parser.scanner import Scanner

def test_operator_registry_integration():
    """演算子レジストリの統合テスト"""
    # 算術演算子が正しく登録されているか
    plus_op = operator_registry.get_operator("+")
    assert plus_op is not None
    assert plus_op.operator_type == OperatorType.ARITHMETIC
    assert plus_op.precedence == 500
    
    # 比較演算子が正しく登録されているか
    eq_op = operator_registry.get_operator("=:=")
    assert eq_op is not None
    assert eq_op.operator_type == OperatorType.COMPARISON
    assert eq_op.precedence == 700

def test_dynamic_token_generation():
    """動的TokenType生成のテスト"""
    from prolog.parser.token_type import TokenType
    
    # 演算子トークンが動的に生成されているか
    assert hasattr(TokenType, 'PLUS')
    assert hasattr(TokenType, 'EQUALCOLONEQUAL')
    assert hasattr(TokenType, 'IS')

def test_unified_operator_evaluation():
    """統合された演算子評価のテスト"""
    source = """
    test_arithmetic(X, Y, Z) :- Z is X + Y.
    test_comparison(X, Y) :- X =:= Y.
    test_unification(X, Y) :- X = Y.
    """
    tokens = Scanner(source).scan_tokens()
    rules = Parser(tokens).parse()
    runtime = Runtime(rules)
    
    # 算術演算子テスト
    solutions = runtime.query("test_arithmetic(3, 4, Z).")
    assert len(solutions) > 0
    Z_var = Variable("Z")
    assert Z_var in solutions[0]
    assert float(str(solutions[0][Z_var])) == 7.0
    
    # 比較演算子テスト
    solutions_eq = runtime.query("test_comparison(5, 5).")
    assert len(solutions_eq) > 0
    
    solutions_neq = runtime.query("test_comparison(5, 6).")
    assert len(solutions_neq) == 0
    
    # 単一化演算子テスト
    solutions_unify = runtime.query("test_unification(hello, X).")
    assert len(solutions_unify) > 0
    X_var = Variable("X")
    assert X_var in solutions_unify[0]
    assert str(solutions_unify[0][X_var]) == "hello"

def test_operator_precedence_integration():
    """演算子優先度の統合テスト"""
    source = """
    calc(Result) :- Result is 2 + 3 * 4.
    """
    tokens = Scanner(source).scan_tokens()
    rules = Parser(tokens).parse()
    runtime = Runtime(rules)
    
    solutions = runtime.query("calc(R).")
    assert len(solutions) > 0
    R_var = Variable("R")
    # 2 + (3 * 4) = 14 （演算子優先度が正しく処理されている）
    assert float(str(solutions[0][R_var])) == 14.0
