#!/usr/bin/env python
"""Test deep recursion to verify solve_goal → execute recursion chain issue."""

from pyprolog.runtime.interpreter import Runtime
import sys

def test_deep_recursion(depth: int):
    """Test recursive predicate with given depth."""
    runtime = Runtime()
    runtime.use_iterative_execution = True

    # Define recursive counting predicate
    runtime.add_rule('count(0).')
    runtime.add_rule('count(N) :- N > 0, N1 is N - 1, count(N1).')

    print(f"\nTesting depth={depth} with iterative execution...")

    try:
        results = runtime.query(f'count({depth}).')
        if len(results) == 1:
            print(f"✓ Success at depth={depth}")
            return True
        else:
            print(f"✗ Failed at depth={depth}: Expected 1 result, got {len(results)}")
            return False
    except RecursionError as e:
        print(f"✗ RecursionError at depth={depth}: {e}")
        return False
    except Exception as e:
        print(f"✗ Error at depth={depth}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("Deep Recursion Test")
    print("=" * 60)
    print("Testing solve_goal → execute recursion chain issue")
    print("Expected: RecursionError at depth=1000 (Phase 3 not done)")

    # Test progressively deeper recursion
    depths = [10, 50, 100, 500, 1000]
    results = {}

    for depth in depths:
        results[depth] = test_deep_recursion(depth)
        if not results[depth]:
            print(f"\n⚠ Failed at depth={depth}. Stopping further tests.")
            break

    print("\n" + "=" * 60)
    print("Summary:")
    for depth, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  depth={depth:4d}: {status}")

    if all(results.values()):
        print("\n✓ All depths passed! solve_goal recursion may be fixed.")
    else:
        print("\n⚠ Phase 3 needed: Break solve_goal → execute recursion chain")
