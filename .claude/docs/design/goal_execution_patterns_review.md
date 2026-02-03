# Review: Gemini goal execution patterns vs local plan

Date: 2026-02-03
Scope: Review of goal execution refactor guidance and its fit with current runtime
Files reviewed:
- .claude/docs/research/goal_execution_patterns_gemini.md
- .claude/docs/design/execute_single_goal_refactor_plan.md

## Summary
Gemini provides useful high-level guidance on iterative execution and builtin dispatch, but it omits several pyprolog-specific behaviors (Atom IO operators, operator semantics, stats/tracing, and exception propagation). It also assumes APIs that differ from the current code (predicate class interfaces, IO predicate factories). The local plan is stronger for behavior preservation because it extracts existing execute() logic. A follow-on change should address remaining recursion through solve_goal.

## Gaps and edge cases in Gemini doc
- Atom IO operators are not covered (current execute() handles Atom goals that map to operator evaluators).
- Operator evaluators in pyprolog return mixed types (bool for arithmetic/comparison, iterator for others). Gemini assumes a single uniform return contract.
- Builtin dispatch by functor alone ignores arity (e.g., listing/0 vs listing/1).
- Predicate class APIs differ (current classes use execute(runtime, env) and sometimes expect dereferenced args, not evaluate(goal, env, runtime)).
- IO predicate factories take a single argument term, not io_manager. Gemini example does not match current signatures.
- Stats/tracing hooks and exception propagation (IOManager exceptions, PrologError) are not preserved.
- Recursion can still occur via solve_goal -> runtime.execute for rule bodies, even if _execute_single_goal stops calling execute().

## Dispatch pattern coverage
- Without explicit logical-operator exclusion, _execute_single_goal could incorrectly handle ,/2, ;/2, \+/1, conflicting with frame-based execution.
- Direct cut handling (raising CutException for Atom '!') bypasses operator evaluator logic and builtin-call stats.
- Atom vs Term handling is critical; Gemini doc treats mostly Term goals.

## Conflicts with local plan
- Gemini suggests builtin object evaluate() calls; local plan preserves current execute() behavior and APIs.
- Gemini proposes env.deref and io_manager injection that are not present in current code.
- Gemini does not enforce the architectural boundary for logical operators that the local plan explicitly adds.

## Risks of Gemini approach if applied directly
- Behavior drift for operators and builtins (wrong truthiness handling).
- Loss of stats, tracing, and detailed exception propagation.
- Incorrect handling of Atom IO operators and zero-arity calls.
- Recursion depth risk remains via solve_goal rule-body execution.
- Performance overhead if builtin dispatch tables are constructed per call.

## Recommended integration actions
1. Use the local plan extraction as the base to preserve behavior exactly.
2. After parity is proven, replace if/elif chains with a precomputed dispatch map keyed by (functor, arity).
3. Keep operator handling logic identical (including arithmetic/comparison boolean handling).
4. Preserve Atom IO operator handling and Atom-to-Term conversion for cut.
5. Add tests for: deep recursion, Atom IO operators, listing/0 vs listing/1, cut propagation, stats counts.
6. Plan a follow-on refactor to remove recursion through solve_goal by pushing rule bodies into the iterative ExecutionState.

## Strengths of Gemini doc
- Clear explanation of iterative execution patterns and WAM context.
- Suggests direct builtin dispatch and generator chaining to avoid execute() recursion.
- Provides a simple testing hook for deep recursion and acknowledges performance tradeoffs.
