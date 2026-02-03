#!/usr/bin/env python
"""Debug conjunction handling in iterative execution."""

from pyprolog.runtime.interpreter import Runtime
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

def test_simple_conjunction():
    """Test simple conjunction with iterative execution."""
    runtime = Runtime()
    runtime.use_iterative_execution = True

    # Test 1: Simple conjunction
    print("\n" + "=" * 60)
    print("Test 1: Simple conjunction")
    runtime.add_rule('p(1).')
    runtime.add_rule('q(2).')

    results = runtime.query('p(X), q(Y).')
    print(f"Results: {results}")
    print(f"Expected: 1 result with X=1, Y=2")
    print(f"Actual: {len(results)} results")

    if len(results) == 1 and 'X' in str(results[0]) and 'Y' in str(results[0]):
        print("✓ Test 1 passed")
        return True
    else:
        print("✗ Test 1 failed")
        return False

def test_rule_with_conjunction():
    """Test rule with conjunction in body."""
    runtime = Runtime()
    runtime.use_iterative_execution = True

    # Test 2: Rule with conjunction
    print("\n" + "=" * 60)
    print("Test 2: Rule with conjunction in body")
    runtime.add_rule('p(1).')
    runtime.add_rule('q(2).')
    runtime.add_rule('r(X, Y) :- p(X), q(Y).')

    results = runtime.query('r(A, B).')
    print(f"Results: {results}")
    print(f"Expected: 1 result with A=1, B=2")
    print(f"Actual: {len(results)} results")

    if len(results) == 1:
        print("✓ Test 2 passed")
        return True
    else:
        print("✗ Test 2 failed")
        return False

if __name__ == '__main__':
    print("Conjunction Debug Tests")
    print("=" * 60)

    try:
        result1 = test_simple_conjunction()
        result2 = test_rule_with_conjunction()

        if result1 and result2:
            print("\n" + "=" * 60)
            print("All tests passed! ✓")
        else:
            print("\n" + "=" * 60)
            print("Some tests failed ✗")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
