# RecursionError Solutions Review (2026-02-04)

Scope: review of `.claude/docs/research/recursion-error-solutions.md` against current runtime design and execution stack work-in-progress.

Key findings (severity-ordered):
- HIGH: The recommended "Stack of Iterators" is a second execution engine. The repo already has an explicit stack engine (`pyprolog/runtime/execution_frames.py`, `interpreter.execute_iterative`). Implementing a new trampoline risks semantic drift and double maintenance. Align with the existing frame-based engine instead.
- HIGH: The note "Approach 1 can be added to pyprolog/runtime/interpreter.py" is too narrow. The RecursionError is triggered in `logic_interpreter._execute_body_direct`, so raising the recursion limit in a single entrypoint will not be reliable across call paths and only masks the root cause.
- HIGH: The stack proposal does not specify how to preserve cut/negation/disjunction semantics or environment isolation. These are the most failure-prone parts in a Prolog engine and are already nuanced in current code.
- MEDIUM: The "unlimited depth / 10,000+" claim is optimistic. Other recursive helpers (e.g., conjunction flattening, term traversals) can still hit limits, and heap pressure/generator overhead will cap practical depth.
- MEDIUM: The "flatten conjunctions" approach still needs an iterative flattener; a recursive flattener will reproduce the same failure for large conjunction chains.

Design alignment:
- `DESIGN.md` already records a decision to replace mutual recursion with explicit frames and choice points. The recommended fix should build on the existing `ExecutionState`/`GoalFrame`/`GoalSeqFrame`/`OperatorFrame` infrastructure rather than a new trampoline.

Recommended approach:
- Adopt the explicit stack path, but re-use and complete the current frame-based engine. Treat `sys.setrecursionlimit` as a temporary debug-only escape hatch, not a production fix.

Implementation order (if agreeing with the stack approach):
1) Complete operator handling in the iterative engine (`;`, `\+`, `!`) with correct cut barriers and isolation of environments for branches.
2) Replace `_execute_body_direct` with a thin delegator to the iterative engine, or move rule body evaluation onto the shared execution loop.
3) Implement iterative conjunction flattening to avoid recursion in preprocessing.
4) Add parity tests (old vs new engine) on representative queries before removing or quarantining the old path.

Test strategy during migration:
- Minimal set: deep conjunction chain, deep rule recursion (e.g., `ancestor`), disjunction with backtracking, negation with and without solutions, cut inside conjunction/disjunction/negation, and a case with side effects to confirm current behavior remains.

Risk mitigation:
- Keep the legacy path only for test comparison (not runtime fallback), and add targeted assertions for cut/negation semantics to detect regressions early.

Status: Review complete.

Addendum (2026-02-04):
- MEDIUM: The "10,000+ depth" claim is speculative; heap growth from env copies/unification and other recursive helpers can still cap depth. Recommend framing as "heap-limited" without numeric promises.
- MEDIUM: Conjunction flattening must be iterative and semantics-preserving across operator boundaries; naive flattening can reorder goals or break cut/negation semantics when nested in `;/2` or `\+/1`.
- MEDIUM: Raising `sys.setrecursionlimit` can interfere with host environments/tests and still fail in other recursive hot paths (term traversal, unification); treat it as a temporary debug switch, not runtime config.
