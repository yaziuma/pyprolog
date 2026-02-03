#!/usr/bin/env python
"""Test depth=10 recursion quickly."""

from pyprolog.runtime.interpreter import Runtime

runtime = Runtime()
runtime.use_iterative_execution = True
runtime.add_rule('count(0).')
runtime.add_rule('count(N) :- N > 0, N1 is N - 1, count(N1).')

print('Testing depth=10...')
try:
    results = runtime.query('count(10).')
    print(f'Results: {len(results)}')
    if len(results) == 1:
        print('✓ Success!')
        exit(0)
    else:
        print(f'✗ Failed: expected 1 result, got {len(results)}')
        exit(1)
except Exception as e:
    print(f'✗ Error: {e}')
    import traceback
    traceback.print_exc()
    exit(1)
