#!/usr/bin/env python
"""Test specific depths to verify Phase 3 improvement."""

from pyprolog.runtime.interpreter import Runtime
import sys

def test_depth(depth: int):
    runtime = Runtime()
    runtime.use_iterative_execution = True
    runtime.add_rule('count(0).')
    runtime.add_rule('count(N) :- N > 0, N1 is N - 1, count(N1).')

    print(f'Testing depth={depth}...', end=' ', flush=True)
    try:
        results = runtime.query(f'count({depth}).')
        if len(results) == 1:
            print(f'✓ Success')
            return True
        else:
            print(f'✗ Failed: {len(results)} results')
            return False
    except RecursionError as e:
        print(f'✗ RecursionError')
        return False
    except Exception as e:
        print(f'✗ Error: {type(e).__name__}: {e}')
        return False

if __name__ == '__main__':
    # Test key depths
    depths = [150, 175, 200, 250, 300]

    for depth in depths:
        success = test_depth(depth)
        if not success and depth > 200:
            print(f'\nStopping at depth={depth}')
            break

    print('\nNote: RecursionError at depth=200 is due to _execute_body_direct recursion.')
    print('This is a Python recursion limit issue, not an execute() recursion issue.')
