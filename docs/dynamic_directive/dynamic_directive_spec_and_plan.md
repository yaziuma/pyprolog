# Dynamic Directive & Existence Semantics: Fixed Spec + Implementation Plan

## 1. Goals / Non-Goals

### Goals (support)
- **Dynamic directive**: `:- dynamic p/1.` only, using the existing predicate indicator AST (`Term(Atom("/"), [Atom("p"), Number(1)])`).
- **Procedure existence semantics** with stable behavior across runtime updates (`asserta/1`, `assertz/1`, `retract/1`, `retractall/1`).
- **Predicate registry** in `LogicInterpreter` to track declared/seen predicates and stabilize existence checks.
- **Parser return value unchanged**: `Parser.parse()` returns rules only; directives are retained internally by the parser.
- **Registry updates centralized** at `LogicInterpreter.add_rule()` to avoid missed registrations.
- **Minimal changes** oriented toward maintainability and implementation ease.

### Non-Goals (explicitly unsupported)
- ISO/SWI full compatibility.
- `multifile`, `thread_local`, `unknown` flag, `abolish/1`.
- Any directive other than `:- dynamic p/1.`.
- Adding new AST nodes or altering the parser return type.

---

## 2. Final Spec (with examples)

### 2.1 Existence semantics (procedure existence)

**Decision logic in `LogicInterpreter.solve_goal()` (fixed order):**
1. `true/0`, `fail/0` behave as they do today (no changes).
2. If `(name, arity)` is **not in predicate_registry** → raise `existence_error(procedure, name/arity)`.
3. If `(name, arity)` **is in predicate_registry** but there are **0 clauses** → **fail** (not an existence error).
4. If clauses exist → normal search/evaluation.

**Examples**
- **Undefined (not registered)**
  ```prolog
  q(X).           % -> existence_error(procedure, q/1)
  ```
- **Declared dynamic but no clauses**
  ```prolog
  :- dynamic p/1.
  p(X).           % -> fail
  ```
- **After all clauses removed**
  ```prolog
  :- dynamic p/1.
  assertz(p(1)).
  retract(p(1)).
  p(X).           % -> fail
  ```

### 2.2 Dynamic directive syntax acceptance
- Accepted only: `:- dynamic p/1.`
- The predicate indicator **must** use the existing AST pattern: `Term(Atom("/"), [Atom("p"), Number(1)])`.
- No new AST nodes are introduced.
- **All other directives** are treated as **unsupported**. They should be **ignored or surfaced as a clear error** per current parser behavior (but not converted into rules).

### 2.3 Predicate registry semantics
- **Location**: `LogicInterpreter.predicate_registry: set[(name, arity)]`.
- **Update rules**:
  - `:- dynamic p/1.` → **add** `(p, 1)`.
  - `asserta/1`, `assertz/1` → **add** `(name, arity)` if not already present.
  - `retract/1`, `retractall/1` → **do not delete** from registry.
  - `abolish/1` → **unsupported** (no registry removal).

### 2.4 Retract ordering
- **Not specified** (LIFO/FIFO permitted).
- **Minimum guarantees**:
  - Each `retract/1` call removes **exactly one clause**.
  - Repeated retractions can remove **all clauses**.
  - **No ghost clauses** remain in indices after all clauses are removed.

---

## 3. Architecture & Data (registry / directive flow)

### 3.1 Data placement
- `LogicInterpreter` holds `predicate_registry: set[(name, arity)]`.
- `Parser` retains directives internally (e.g., `parser.directives`) **without changing** `Parser.parse()` return value.

### 3.2 Flow (high-level)
1. **Parse**: `Parser.parse()` returns rules; directives are stored internally.
2. **Directive application**: caller reads parser directives and calls `LogicInterpreter.apply_dynamic(name, arity)`.
3. **Rule addition**: `LogicInterpreter.add_rule()` is the single entry point that **registers predicates** before inserting rules/clauses.

---

## 4. Impact Map (file / function)

> Note: exact filenames/functions should be mapped to current codebase names; update below during implementation.

| Area | File | Function / Responsibility | Change Type | Notes |
| --- | --- | --- | --- | --- |
| Parser | `pyprolog/parser.py` (or equivalent) | directive capture (`:- dynamic`) | **Modify** | Keep `parse()` return value (rules only); store directives internally.
| Parser usage | `pyprolog/loader.py` / `consult` path | apply directives after parse | **Add** | Call into `LogicInterpreter.apply_dynamic`.
| Interpreter | `pyprolog/interpreter.py` | `LogicInterpreter` registry storage | **Add** | `predicate_registry` field.
| Interpreter | `pyprolog/interpreter.py` | `add_rule()` | **Modify** | Centralize registry update here.
| Interpreter | `pyprolog/interpreter.py` | `solve_goal()` | **Modify** | Enforce existence ordering with registry check.
| Builtins | `pyprolog/builtins.py` | `asserta/1`, `assertz/1` | **Modify** | Ensure they funnel to `add_rule()` (registry updated).
| Builtins | `pyprolog/builtins.py` | `retract/1`, `retractall/1` | **Modify** | No registry removal; ensure retract semantics stable.

### Red flags (high risk of breaking behavior)
- **Parsing `:-`**: it can denote both directive and rule (`H :- B`). Make sure directive detection doesn’t steal real rules.
- **`solve_goal()` ordering**: existence checks must happen **before** clause search for non-registered predicates.
- **Registry updates**: all rule insertions must go through `add_rule()` to avoid missing registry entries.

---

## 5. Task Breakdown (commit-sized, minimal diffs)

### Task 1: Parser directive capture
- **Targets**: Parser file; parse loop that currently handles `:-`.
- **Changes**:
  - Detect `:- dynamic p/1.` and store in `parser.directives` (or equivalent).
  - Preserve current behavior for rules and other terms.
- **Acceptance**:
  - `parse()` output (rules) unchanged in shape/type.
  - `parser.directives` lists dynamic predicate indicators in order.
- **Risks / Mitigation**:
  - Risk: directive vs rule ambiguity. Mitigate by strict pattern match on `dynamic` and predicate indicator AST.
- **Rollback**:
  - Remove directive storage and revert to previous parse handling.

### Task 2: Introduce predicate registry in LogicInterpreter
- **Targets**: `LogicInterpreter` class.
- **Changes**:
  - Add `predicate_registry: set[(name, arity)]`.
  - Add `apply_dynamic(name, arity)` that registers predicate even with 0 clauses.
- **Acceptance**:
  - Registry exists and is reachable; no functional behavior change yet.
- **Risks / Mitigation**:
  - Risk: concurrency side-effects. Mitigate by confining registry to interpreter instance.
- **Rollback**:
  - Remove field and helper method.

### Task 3: Centralize registry update in `add_rule()`
- **Targets**: `LogicInterpreter.add_rule()`.
- **Changes**:
  - Ensure `(name, arity)` is added before clause insertion.
  - Remove any redundant registration elsewhere.
- **Acceptance**:
  - Any rule/consul/consult/`assert*` path that adds clauses registers predicates.
- **Risks / Mitigation**:
  - Risk: duplicate registrations or missing ones from bypass paths. Mitigate by ensuring all insertion paths call `add_rule()`.
- **Rollback**:
  - Revert `add_rule()` changes; reinstate previous ad-hoc registration if any.

### Task 4: Hook directive application after parse
- **Targets**: consult/load pipeline (file loading, REPL consult, etc.).
- **Changes**:
  - After parsing, iterate directives and call `apply_dynamic(name, arity)`.
- **Acceptance**:
  - `:- dynamic p/1.` with no clauses results in `p/1` being registered and failing (not erroring).
- **Risks / Mitigation**:
  - Risk: directive ordering vs rule addition. Mitigate by applying dynamic directives **before** rule additions in the same file.
- **Rollback**:
  - Remove directive handling in loader; parse still returns rules.

### Task 5: Update `solve_goal()` existence semantics
- **Targets**: `LogicInterpreter.solve_goal()`.
- **Changes**:
  - Implement 4-step order (true/fail, registry missing => error, registry with 0 clauses => fail, else evaluate).
- **Acceptance**:
  - All examples in section 2.1 behave as specified.
- **Risks / Mitigation**:
  - Risk: builtins might bypass. Mitigate by keeping `true/0` and `fail/0` exceptions first.
- **Rollback**:
  - Revert to previous solve logic.

### Task 6: Builtins alignment (assert/retract)
- **Targets**: builtins for `asserta/1`, `assertz/1`, `retract/1`, `retractall/1`.
- **Changes**:
  - Ensure `assert*` uses `add_rule()` to register.
  - Ensure `retract*` does **not** remove from registry.
- **Acceptance**:
  - Registry contains predicates asserted at runtime even before any consult.
- **Risks / Mitigation**:
  - Risk: index desync / ghost clauses. Mitigate by verifying clause removal with guardrail tests.
- **Rollback**:
  - Restore previous builtin logic.

### Task 7: Guardrail tests (semantic only)
- **Targets**: test harness/docs (as applicable).
- **Changes**:
  - Add a minimal semantic test sequence (see section 6).
- **Acceptance**:
  - Tests pass and confirm existence semantics and ghost-clause absence.
- **Risks / Mitigation**:
  - Risk: tests too strict. Mitigate by keeping only semantic-level checks.
- **Rollback**:
  - Remove tests if they block pipeline (but keep spec intact).

---

## 6. Guardrail Tests (semantic only)

> Only semantic-level checks; do not proliferate fine-grained unit tests.

### Case A: Undefined predicate => existence error
```prolog
q(X).            % existence_error(procedure, q/1)
```

### Case B: dynamic + retract => fail
```prolog
:- dynamic p/1.
assertz(p(1)).
retract(p(1)).
p(X).            % fail
```

### Case C: index consistency (no ghost clause)
```prolog
assertz(p(1)).
retract(p(1)).
p(X).            % fail
```

---

## 7. Implementation Checklist (manual, safe order)

- [ ] **Parser**: confirm `:- dynamic p/1.` is captured as a directive (not converted into rules).
- [ ] **Registry**: add `predicate_registry` to `LogicInterpreter` and initialize cleanly.
- [ ] **Directive application**: ensure directives are applied **before** adding rules from the same file.
- [ ] **add_rule()**: verify all rule insertion paths (consult + assert*) flow through it.
- [ ] **solve_goal()**: apply existence ordering and ensure `true/0`, `fail/0` remain special-cased.
- [ ] **Builtins**: `assert*` registers; `retract*` never unregisters.
- [ ] **Guardrails**: run the three semantic checks in section 6.

### If something fails, where to look first
- **Directive not taking effect** → Parser directive capture or consult pipeline.
- **existence_error vs fail mismatch** → `solve_goal()` ordering or registry population.
- **Ghost clause / index mismatch** → retract implementation or index maintenance.

---

## 8. Risks & Rollback

### Key risks
- **`:-` ambiguity**: directive vs rule parsing can break valid clauses if not strictly matched to `dynamic`.
- **Registry drift**: if any path inserts clauses without `add_rule()`, existence checks become inconsistent.
- **Retract index desync**: ghost clauses can remain if index cleanup is incomplete.

### Rollback strategy
- Revert in reverse order of tasks (7 → 1). This isolates high-risk behavior changes:
  1. Tests/docs
  2. Builtins alignment
  3. `solve_goal()` ordering
  4. Directive application
  5. `add_rule()` registry update
  6. Registry field
  7. Parser directive capture

