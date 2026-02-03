#!/usr/bin/env python
"""Phase 1 validation test - verify _execute_single_goal works with iterative execution."""

from pyprolog.runtime.interpreter import Runtime

def test_basic_iterative():
    """Test basic query with iterative execution enabled."""
    runtime = Runtime()
    runtime.use_iterative_execution = True

    runtime.add_rule('parent(alice, bob).')
    runtime.add_rule('parent(bob, charlie).')

    results = runtime.query('parent(alice, X).')

    print(f"Results: {results}")
    assert len(results) == 1, f"Expected 1 result, got {len(results)}"
    print("✓ Basic iterative test passed!")

def test_builtin_predicates():
    """Test built-in predicates with iterative execution."""
    runtime = Runtime()
    runtime.use_iterative_execution = True

    # Test var/1
    results = runtime.query('var(X).')
    assert len(results) == 1, "var(X) should succeed"
    print("✓ var/1 test passed!")

    # Test atom/1
    results = runtime.query('atom(foo).')
    assert len(results) == 1, "atom(foo) should succeed"
    print("✓ atom/1 test passed!")

    # Test number/1
    results = runtime.query('number(42).')
    assert len(results) == 1, "number(42) should succeed"
    print("✓ number/1 test passed!")

def test_operators():
    """Test operators with iterative execution."""
    runtime = Runtime()
    runtime.use_iterative_execution = True

    # Test unification
    results = runtime.query('X = 5.')
    assert len(results) == 1, "X = 5 should succeed"
    print("✓ Unification test passed!")

    # Test arithmetic
    results = runtime.query('X is 2 + 3.')
    assert len(results) == 1, "X is 2 + 3 should succeed"
    print("✓ Arithmetic test passed!")

if __name__ == '__main__':
    print("Phase 1 Validation Tests")
    print("=" * 50)

    try:
        test_basic_iterative()
        test_builtin_predicates()
        test_operators()
        print("\n" + "=" * 50)
        print("All Phase 1 tests passed! ✓")
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
