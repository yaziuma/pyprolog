# Review: Gemini Goal Execution Patterns vs pyprolog Plan

**Date:** 2026-02-03
**Scope:** Critique of Gemini research recommendations vs local refactor plan
**Sources:**
- .claude/docs/research/goal_execution_patterns_gemini.md
- .claude/docs/design/execute_single_goal_refactor_plan.md

## Findings (Severity Ordered)

### Critical
1. **Logical operator handling is underspecified and conflicts with iterative frames.**
   Gemini’s _execute_single_goal() dispatch handles “operators” generically and does not explicitly exclude logical operators (,/2, ;/2, \+/1). In pyprolog, logical operators are handled by frames and by _create_logical_evaluator() in the recursive path. Routing them through operator evaluation inside _execute_single_goal() would bypass frames and can reintroduce recursion in iterative mode or change semantics.

2. **Dispatch uses functor strings where pyprolog uses Atom/Term structures.**
   The proposed checks compare goal.functor to string names directly. In pyprolog, functors are Atom objects and arity matters. A pure string check will silently miss built-ins/operators or misclassify them.

3. **Built-in predicate integration is incompatible with current class interfaces.**
   Gemini’s pattern instantiates predicate classes without required arguments and calls evaluate() (which pyprolog built-ins do not implement; they expose execute()). This is a direct mismatch that would break built-ins unless the whole predicate API is rewritten.

### High
4. **Arity is ignored in built-in dispatch.**
   The proposal gates built-ins by functor name only, but pyprolog relies on (name, arity) to distinguish predicates like listing/0 vs listing/1. Ignoring arity would misroute user-defined predicates or cause incorrect behavior when arity differs.

5. **Atom-only I/O operators are not addressed.**
   Current execute() explicitly handles Atom goals such as write/0, nl/0, and tab/0 by converting to Term and routing to IO operator evaluators. Gemini’s approach checks operators only when the goal is a Term, so Atom I/O operators can fail.

### Medium
6. **Cut handling bypasses existing operator pipeline.**
   The suggestion to raise CutException directly for Atom("!") bypasses the existing operator evaluator and built-in stats/tracing path. This risks inconsistent tracing and stats accounting compared to the current behavior.

7. **Instrumentation (stats/tracing) is not preserved.**
   The research does not mention _record_builtin_call or tracer hooks. In pyprolog, stats and tracing are important (e.g., solve_calls_by_pred, builtin_calls_by_name). Skipping these will regress observability.

8. **Performance overhead from per-call dispatch tables.**
   The example creates dispatch dicts and sets inside _execute_single_goal() on every call. This adds avoidable allocations in the hottest path.

### Low
9. **GoalFrame/StopIteration comments don’t match current implementation.**
   Gemini suggests catching StopIteration in the loop, but GoalFrame.step() already translates StopIteration into None. This is harmless but signals an incomplete read of current frames.

## Conflicts with Local Plan
- The local plan explicitly **rejects** logical operators in _execute_single_goal() and routes them via frames or execute() (see plan: logical operator routing and rejection). Gemini’s plan would likely handle logical operators in _execute_single_goal() unless additional guards are added.
- The local plan keeps **existing built-in execution semantics** (per-arity handling, IO special cases, stats). Gemini’s plan changes the predicate dispatch API and ignores arity, which conflicts with current behavior.

## Risks in Gemini’s Approach
- **Semantic drift** for logical operators and cut behavior in iterative mode.
- **Broken built-ins** due to API mismatches (evaluate vs execute, missing args).
- **Silent misrouting** of predicates when functor names overlap or arity differs.
- **Regression in IO operator handling** for Atom-only operator forms.
- **Loss of stats/tracing**, making debugging and performance diagnostics harder.

## Strengths in Gemini’s Design (Better Than Local Plan)
- Clear emphasis on **eliminating recursion** by making _execute_single_goal() independent.
- A helpful **dispatch-table mindset** that, if adapted to pyprolog’s interfaces, could reduce branching complexity.
- Explicit recognition of **operator evaluation vs built-in predicate handling** as separate concerns.

## Actionable Integration Recommendations
1. **Adopt the independence goal but keep the local plan’s logical-operator boundary.**
   Explicitly guard against ,/2, ;/2, \+/1 inside _execute_single_goal() and route them to frames/execute().

2. **Use arity-aware dispatch keyed by (functor_name, arity).**
   Build a static mapping once (class-level or Runtime init) to avoid per-call allocation.

3. **Preserve current built-in interfaces and stats/tracer hooks.**
   Keep _record_builtin_call and call predicate.execute() with correct arguments. Do not switch to evaluate() without a broader API change.

4. **Handle Atom goals explicitly (IO operators and Atom predicates).**
   Mirror the current execute() preprocessing: convert Atom IO operators to Term and route to operator evaluators; otherwise route to solve_goal.

5. **Keep operator evaluation order consistent with current semantics.**
   Preserve the precedence: IO operator Atom handling → operator evaluator (non-logical) → built-ins → solve_goal.

6. **Add tests that cover arity conflicts and Atom I/O operators.**
   Include cases like listing/0 vs listing/1, Atom goals for nl/0 and write/0, and deep recursion via execute_iterative().

## Suggested Combined Design
- Implement _execute_single_goal() by extracting the existing execute() logic (local plan).
- Add a precomputed dispatch map for built-ins to reduce branching, but keep interfaces and arity checks.
- Ensure logical operators are explicitly rejected in _execute_single_goal() to maintain the frame-based execution model.

