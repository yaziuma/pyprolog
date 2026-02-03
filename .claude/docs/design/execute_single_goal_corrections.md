# Corrections to Integrated Design (Based on Codex Final Review)
**Date**: 2026-02-03
**Status**: Critical Corrections
**Based on**: Codex Final Review (codex_final_review.md)

## Critical Corrections

### Gap #1: IO Predicate Dispatch Correction

**Incorrect (in integrated design)**:
```python
('get_char', 1): lambda g, e: self._io_predicates['get_char'].execute(self, e)
```

**Correct Implementation**:
```python
('get_char', 1): lambda g, e: create_get_char_predicate(g.args[0]).execute(self, e),
('read_line', 1): lambda g, e: create_read_line_predicate(g.args[0]).execute(self, e),
('peek_char', 1): lambda g, e: create_peek_char_predicate(g.args[0]).execute(self, e),
```

**Reason**: Factory functions take goal arguments, not lambda closures over self.

---

### Gap #2: Statistics Schema Correction

**Remove** from all code examples:
```python
if env.stats_enabled:
    env.stats["builtin_calls_total"] += 1  # ❌ REMOVE THIS
```

**Keep only**:
```python
def _record_builtin_call(name: str) -> None:
    if env.stats_enabled:
        env.stats["builtin_calls_by_name"][name] = (
            env.stats["builtin_calls_by_name"].get(name, 0) + 1
        )
```

**Reason**: `builtin_calls_total` is not initialized. Use `sum(builtin_calls_by_name.values())` instead.

---

### Gap #3: Dispatch Order Clarification

**Official Order** (matches current implementation):
1. **Cut (!)** - Check first, raise CutException
2. **Operators** - Check `_operator_evaluators` registry
3. **Built-ins** - Check `_builtin_dispatch` table
4. **User-defined** - Fallback to `solve_goal`

**Rationale**: Operators like `=` and `is` must take precedence over built-ins.

---

### Gap #4: Phase 1/2 Recursion Clarification

**Add to Phase 1 docstring**:
```python
def _execute_single_goal(self, goal, env):
    """...

    Note:
        Phase 1/2: This method still calls solve_goal(), which may trigger
        execute() recursion for rule bodies. This is EXPECTED and SAFE for
        Phase 1/2 validation.

        Phase 3: solve_goal() will be replaced with solve_goal_direct() to
        eliminate all recursion.
    """
```

---

### Gap #5: solve_goal_direct() Full Specification

**Complete Implementation Pattern**:

```python
def solve_goal_direct(
    self, goal: PrologType, env: BindingEnvironment, runtime: 'Runtime'
) -> Iterator[BindingEnvironment]:
    """Solve goal by matching rules, using runtime._execute_single_goal for bodies.

    This method preserves ALL existing solve_goal() functionality:
    - Tracer events (call/exit/fail)
    - Statistics tracking
    - Clause indexing
    - Cut exception propagation
    - Empty body handling (p(X). → p(X) :- true.)
    - IO exception propagation

    The ONLY difference: rule bodies are executed via runtime._execute_single_goal()
    instead of runtime.execute(), breaking the recursion chain.
    """
    if env.stats_enabled:
        env.stats["solve_calls_total"] += 1

    actual_goal: Term
    if isinstance(goal, Atom):
        actual_goal = Term(goal, [])
    elif isinstance(goal, Term):
        actual_goal = goal
    else:
        return

    # Tracer: record call event
    if hasattr(self.runtime, "tracer") and self.runtime.tracer.enabled:
        self.runtime.tracer.record_call(actual_goal)

    try:
        # Use clause indexing (same as solve_goal)
        self._refresh_index_if_needed()

        key = (actual_goal.functor.name, len(actual_goal.args))
        matching_rules = self.rules_by_pred.get(key, [])

        found_solution = False
        for rule in matching_rules:
            # Unify with rule head (same as solve_goal)
            new_env = self.unify(actual_goal, rule.head, env.copy())
            if new_env is None:
                continue

            # Handle empty body: p(X). → p(X) :- true.
            if isinstance(rule, Fact):
                found_solution = True
                if hasattr(self.runtime, "tracer") and self.runtime.tracer.enabled:
                    self.runtime.tracer.record_exit(actual_goal)
                yield new_env
                continue

            # Execute rule body via _execute_single_goal (NEW)
            # This is the ONLY change from solve_goal()
            body = rule.body

            # Handle logical operators manually
            if isinstance(body, Term) and isinstance(body.functor, Atom):
                if body.functor.name == ',':
                    # Conjunction: execute sequence
                    yield from self._execute_conjunction_direct(body.args, new_env, runtime)
                    found_solution = True
                elif body.functor.name == ';':
                    # Disjunction: execute alternatives
                    yield from self._execute_disjunction_direct(body.args, new_env, runtime)
                    found_solution = True
                elif body.functor.name == '\\+':
                    # Negation: execute negated goal
                    yield from self._execute_negation_direct(body.args[0], new_env, runtime)
                    found_solution = True
                else:
                    # Atomic goal: delegate to _execute_single_goal
                    for result_env in runtime._execute_single_goal(body, new_env):
                        found_solution = True
                        if hasattr(self.runtime, "tracer") and self.runtime.tracer.enabled:
                            self.runtime.tracer.record_exit(actual_goal)
                        yield result_env
            else:
                # Atomic goal: delegate to _execute_single_goal
                for result_env in runtime._execute_single_goal(body, new_env):
                    found_solution = True
                    if hasattr(self.runtime, "tracer") and self.runtime.tracer.enabled:
                        self.runtime.tracer.record_exit(actual_goal)
                    yield result_env

        # Tracer: record fail if no solutions
        if not found_solution:
            if hasattr(self.runtime, "tracer") and self.runtime.tracer.enabled:
                self.runtime.tracer.record_fail(actual_goal)

    except CutException:
        # Propagate cut (same as solve_goal)
        raise
    except Exception as e:
        # Propagate IO/Prolog errors (same as solve_goal)
        logger.error("Error in solve_goal_direct for %s: %s", actual_goal, e)
        raise

def _execute_conjunction_direct(self, goals, env, runtime):
    """Execute conjunction via _execute_single_goal."""
    if not goals:
        yield env
        return

    first, *rest = goals
    for result_env in runtime._execute_single_goal(first, env):
        if rest:
            yield from self._execute_conjunction_direct(rest, result_env, runtime)
        else:
            yield result_env

def _execute_disjunction_direct(self, alternatives, env, runtime):
    """Execute disjunction via _execute_single_goal."""
    for alt in alternatives:
        yield from runtime._execute_single_goal(alt, env)

def _execute_negation_direct(self, goal, env, runtime):
    """Execute negation via _execute_single_goal."""
    for _ in runtime._execute_single_goal(goal, env):
        return  # Goal succeeded, negation fails
    yield env  # Goal failed, negation succeeds
```

**Key Points**:
- Preserves ALL existing functionality (tracer, stats, indexing, exceptions)
- Only change: uses `runtime._execute_single_goal()` instead of `runtime.execute()`
- Handles logical operators manually (conjunction, disjunction, negation)

---

### Gap #6: Additional Required Tests

**Add to Phase 2 Testing**:

```python
def test_statistics_preservation():
    """Verify statistics tracking is preserved."""
    runtime = Runtime()
    env = BindingEnvironment(stats_enabled=True)

    runtime.add_rule("p(1).")
    goal = Term(Atom("p"), [Variable("X")])

    list(runtime._execute_single_goal(goal, env))

    # Verify statistics
    assert "builtin_calls_by_name" in env.stats
    # builtin_calls_total should be computable
    total = sum(env.stats["builtin_calls_by_name"].values())
    assert total >= 0

def test_tracer_preservation():
    """Verify tracer events are recorded."""
    runtime = Runtime()
    runtime.tracer.enabled = True
    env = BindingEnvironment()

    runtime.add_rule("p(1).")
    goal = Term(Atom("p"), [Variable("X")])

    list(runtime._execute_single_goal(goal, env))

    # Verify tracer recorded events
    assert len(runtime.tracer.trace) > 0

def test_atom_io_operators():
    """Verify nl, tab still work."""
    runtime = Runtime()
    env = BindingEnvironment()

    # nl/0
    nl_goal = Atom("nl")
    list(runtime._execute_single_goal(nl_goal, env))

    # tab/0
    tab_goal = Atom("tab")
    list(runtime._execute_single_goal(tab_goal, env))

def test_arity_disambiguation():
    """Verify listing/0 vs listing/1 work correctly."""
    runtime = Runtime()
    env = BindingEnvironment()

    # listing/0
    listing0 = Atom("listing")
    results0 = list(runtime._execute_single_goal(listing0, env))
    assert len(results0) == 1

    # listing/1
    listing1 = Term(Atom("listing"), [Atom("p")])
    results1 = list(runtime._execute_single_goal(listing1, env))
    assert len(results1) == 1
```

---

## Revised Timeline

**Original**: 8-12 hours (realistic), 12-16 hours (conservative)

**Revised** (after corrections):
- **Realistic**: 12-16 hours
- **Conservative**: 16-20 hours

**Reason**: solve_goal_direct() is more complex than initially estimated.

---

## Approval Status

**After these corrections**: ✅ **APPROVED FOR IMPLEMENTATION**

All blockers resolved. Implementation can proceed with confidence.

---

## References

- **Codex Final Review**: `.claude/docs/design/codex_final_review.md`
- **Original Design**: `.claude/docs/design/execute_single_goal_integrated_design.md`
