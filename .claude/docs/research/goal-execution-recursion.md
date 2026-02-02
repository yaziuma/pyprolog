# Goal execution recursion analysis (pyprolog)

## Summary
The RecursionError is caused by Python call stack growth in the Prolog goal execution path. Although `_execute_goal_sequence` uses an explicit stack, it still creates iterators via `execute(...)`, and `execute` delegates to `logic_interpreter.solve_goal`, which `yield from` calls back into `runtime.execute` for rule bodies. This mutual recursion (`execute → evaluator → _execute_goal_sequence → execute` plus `execute → solve_goal → execute`) builds nested generator frames proportional to goal depth and recursive predicates. Deep benchmarks can therefore hit Python’s recursion limit even when tests pass.

## Evidence (code paths)
- `pyprolog/runtime/interpreter.py`:
  - `_execute_goal_sequence` calls `self.execute(...)` for each goal.
  - `_create_logical_evaluator` for `,` and `;` uses `_execute_goal_sequence` and `self.execute(...)`.
  - `execute` uses `yield from` on operator evaluators and, for non-operators, delegates to `logic_interpreter.solve_goal`.
- `pyprolog/runtime/logic_interpreter.py`:
  - `solve_goal` executes rule bodies via `yield from self.runtime.execute(...)`.

## Recommended direction
Move to an explicit, iterative execution loop that maintains its own goal stack and choice-point stack (WAM-style). Keep `execute()` as the public generator but implement it as a driver loop over frames rather than recursive `yield from` chains. This reduces dependence on Python recursion depth while preserving backtracking semantics.

## Risks
- Cut (`!`) semantics and backtracking order must be preserved carefully.
- Generator-based builtins will need a small adapter to fit the explicit loop.
- Tracing and stats collection may need adjustments to match current call/exit ordering.

## Suggested implementation sketch
1. Introduce a `GoalFrame`/`ChoicePoint` structure.
2. Make `execute()` a loop that pushes frames instead of calling itself.
3. Change evaluators and `solve_goal` to return “next goals” or iterators managed by the loop.
4. Add a deep-recursion benchmark test to prevent regression.
