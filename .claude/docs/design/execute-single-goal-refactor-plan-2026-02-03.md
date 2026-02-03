# Execute Single Goal Refactor Plan (2026-02-03)

## Scope
Refactor `Runtime._execute_single_goal()` in `pyprolog/runtime/interpreter.py` to become the single dispatch point for non-logical goals, with no recursion into `execute()`. Preserve existing behavior, exceptions, logging, and stats.

## Key Constraints
- `_execute_single_goal()` must NOT call `execute()`.
- Logical operators `,/2`, `;/2`, `\+/1` are **not** handled by `_execute_single_goal()`.
- Built-ins, operators (except above), and `solve_goal` are handled.
- Cut `!/0` must work in both legacy and iterative paths.
- Reuse existing operator evaluators and built-in predicates.

## Extraction Plan (Code Movement)
1. Move the following blocks from `execute()` into `_execute_single_goal()`:
   - Goal normalization (`Atom('!')` special-case, `Term` vs `Atom`, Atom IO operator handling, Atom solve_goal fallback).
   - `functor_name`/`op_info` resolution and unified operator evaluator handling (arith/comparison/logical/control/io) with existing try/excepts.
   - Built-in predicate dispatch (var/1, atom/1, number/1, atom_number/2, functor/3, arg/3, =../2, asserta/1, assertz/1, member/2, append/3, findall/3, get_char/1, read_line/1, peek_char/1, at_end_of_stream/0, retract/1, listing/0, listing/1, export_facts/2).
   - `solve_goal` fallback for user-defined predicates.
2. Keep the existing logging statements *verbatim* inside the moved blocks to preserve log patterns.
3. Keep `_record_builtin_call` semantics; either:
   - move it into `_execute_single_goal()` and add a thin shared helper method for use in `execute()` logical-operator path, or
   - keep a small local helper in both `execute()` and `_execute_single_goal()` that call a shared `_record_builtin_call(env, name)` method.

## Logical Operator Routing
- Add a helper like `_is_logical_control_operator(goal)` (or similar) that detects `,/2`, `;/2`, `\+/1` from `Term` (and no Atom case).
- In `_execute_single_goal()`, if detected, **do not** evaluate; raise a clear internal error or early-return to signal misuse.
- In `execute()` (legacy), intercept these operators and delegate to the existing logical evaluator path (`_operator_evaluators`) so behavior stays unchanged.
- In `execute_iterative()`, ensure logical operators are routed to `OperatorFrame`/`GoalSeqFrame` instead of `GoalFrame`.

## execute() Refactor Shape (Legacy)
```
if use_iterative_execution:
    yield from execute_iterative(...)
    return

if _is_logical_operator_goal(goal):
    # use existing evaluator + existing exception handling + stats logging
    yield from _execute_logical_operator(goal, env)
    return

yield from _execute_single_goal(goal, env)
```
- `_execute_logical_operator()` should re-use the same evaluator block used today (stats, CutException propagation, IOManager exception propagation, PrologError passthrough).

## execute_iterative() Integration
- Update `ExecutionState.push_goal()` (or add a new dispatch method) to:
  - push `OperatorFrame` (or `GoalSeqFrame` for conjunction) when goal is `,/2`, `;/2`, or `\+/1`.
  - push `GoalFrame` for all other goals.
- Keep `GoalFrame.step()` calling `_execute_single_goal()` for non-logical goals.

## Edge Cases to Preserve
- Atom IO operators (e.g., `nl`, `write`, `tab`) should continue to be handled as operators when called as atoms.
- Atom `'!'` should be normalized to `Term(Atom('!'), [])` and executed via control evaluator (raises `CutException`).
- Arithmetic/comparison operators return boolean; retain the current “yield env on True” behavior.
- IO exceptions (Input required / input_type) must be propagated unchanged.
- Built-ins that catch/propagate `CutException` (functor/3, arg/3, =../2, member/2, append/3) must keep current behavior.
- `findall/3` keeps its internal cut behavior; no extra handling in `_execute_single_goal()`.

## Suggested Change Order
1. Add helper(s) for logical-operator detection and shared stats recording.
2. Copy/move non-logical execution body from `execute()` into `_execute_single_goal()`; ensure it does **not** call `execute()`.
3. Refactor `execute()` to call `_execute_single_goal()` for non-logical goals, and keep existing logical operator evaluator path.
4. Update `ExecutionState.push_goal()` or `execute_iterative()` to route logical operators to frames.
5. Run targeted tests (built-ins, operator evals, logical ops, cut) then full suite.

## Testing Focus
- Regression: built-ins (var/1, atom/1, number/1, atom_number/2, functor/3, arg/3, =../2, asserta/1, assertz/1, member/2, append/3, findall/3).
- Operators: arithmetic (is/2, +/2, etc.), comparison (</2, >=/2), logical (==/2, \==/2, \=/2, <>/2, !=/2), control (!/0, ->/2), IO ops.
- Iterative: conjunction/disjunction/negation should be handled by frames (not `_execute_single_goal()`).
