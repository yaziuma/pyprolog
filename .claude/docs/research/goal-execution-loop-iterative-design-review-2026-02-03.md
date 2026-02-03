# Goal Execution Loop Iterative Design Review (2026-02-03)

Scope: review of the refactoring plan to replace execute/evaluator/_execute_goal_sequence mutual recursion with an explicit frame/stack loop.

Key recommendations:
- Make _execute_single_goal the single dispatch point for all non-logical-operator goals, including built-ins and solve_goal; reuse it from both execute() and execute_iterative() to avoid drift.
- Replace _execute_goal_sequence with GoalSeqFrame for iterative execution; keep _execute_goal_sequence only for legacy execute() to avoid recursion in the new path.
- Convert logical/control operators (,/2, ;/2, \\+/1, !, ->/2) to frame step logic for the iterative engine. Keep existing evaluators for legacy execute().
- Map cut to an explicit control signal in the ExecutionState (apply_cut + barrier), avoiding Python exception propagation in the iterative path except where needed to preserve legacy semantics.

Risks to watch:
- Behavioral drift between execute() and execute_iterative() if built-in dispatch is duplicated.
- Cut/if-then/negation interactions: ensure cut only prunes within the correct barrier and does not escape to the query level.
- \\+/1 and findall/3 should run in isolated execution states or clearly documented scoping to avoid contaminating outer choice points.
- State machine correctness: ensure frames only emit results to parents, not directly to top-level, when inside operator frames.
