#!/usr/bin/env python
"""Test progressive depth to find recursion limit."""

from pyprolog.runtime.interpreter import Runtime
import sys

depths = [10, 50, 100, 200, 300]

for depth in depths:
    runtime = Runtime()
    runtime.use_iterative_execution = True
    runtime.add_rule('count(0).')
    runtime.add_rule('count(N) :- N > 0, N1 is N - 1, count(N1).')

    print(f'Testing depth={depth}...', end=' ', flush=True)
    try:
        results = runtime.query(f'count({depth}).')
        if len(results) == 1:
            print(f'✓ Success')
        else:
            print(f'✗ Failed: {len(results)} results')
            break
    except RecursionError as e:
        print(f'✗ RecursionError')
        break
    except Exception as e:
        print(f'✗ Error: {e}')
        break

print('Done')
