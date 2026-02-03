# Review: execute_single_goal_integrated_design.md

Date: 2026-02-03
Scope: Integrated design review vs codex_review_of_gemini.md and gemini_review_of_codex.md
Files reviewed:
- .claude/docs/design/execute_single_goal_integrated_design.md
- .claude/docs/design/codex_review_of_gemini.md
- .claude/docs/design/gemini_review_of_codex.md

## Summary
The integrated design addresses most high-priority critiques (operator return contract, Atom IO operators, arity-aware dispatch, logical-operator exclusion, iterative execution safety, and expanded testing). However, there are material gaps and inconsistencies that require revisions before implementation, especially around IO predicate dispatch, stats handling, and the solve_goal recursion break.

## Addressed concerns
- Operator return-value contract preserved by reusing existing _operator_evaluators.
- Atom IO operators explicitly preserved in extraction and risk mitigation.
- Builtin dispatch keyed by (functor, arity) resolves arity ambiguity (listing/0 vs listing/1).
- Logical operators excluded from _execute_single_goal via assertion.
- solve_goal recursion identified and assigned to a dedicated phase.
- Testing expanded to include equivalence, exceptions, cut, and recursion depth.

## Remaining gaps / risks
1. IO predicate dispatch mismatch
   - Design uses self._io_predicates and execute(self, env) without passing goal args.
   - Current implementation uses create_*_predicate(goal_arg).execute(self, env).
   - Risk: breakage of get_char/read_line/peek_char behavior.

2. Stats handling inconsistency
   - Design introduces env.stats["builtin_calls_total"], which does not exist today.
   - Potential KeyError or stats schema drift.

3. Dispatch order inconsistency
   - Design alternates between "operators first" and "builtins first" in different sections.
   - Current behavior evaluates operators before builtins; order changes can cause subtle drift.

4. _execute_single_goal recursion promise vs actual behavior
   - Docstring claims no execute() recursion, but Phase 1/2 still call solve_goal(), which calls runtime.execute() for rule bodies.
   - Needs explicit statement of transitional behavior to avoid confusion and incorrect assumptions.

5. solve_goal_direct under-specified
   - Must preserve: existence checks, tracer events (call/exit/fail), stats, indexing, cut propagation, "fact-as-:-" patch, and IO exception propagation.
   - Current design sketch omits these details, risking behavior drift and regression.

6. Testing strategy gaps
   - No explicit tests for stats/tracing preservation.
   - Atom IO operators not explicitly listed in tests.
   - Performance thresholds may be too strict/flaky; also benchmarks are ignored by default (pytest addopts).

## Verdict
Needs revision before implementation. No showstoppers, but the unresolved mismatches are high-risk for behavioral regressions.

## Suggested fixes
- Align IO dispatch with current factory signatures or explicitly introduce _io_predicates with a migration plan.
- Remove or define builtin_calls_total in stats schema.
- Decide and document operator-vs-builtin dispatch order (keep current "operators first").
- Clarify transitional recursion in Phase 1/2 and update docstring accordingly.
- Specify solve_goal_direct in detail or refactor solve_goal to accept a strategy for body execution while reusing the same logic.
- Add tests for stats/tracing, Atom IO operators, and listing/0 vs listing/1.
