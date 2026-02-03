# _execute_single_goal() Refactoring: Integrated Design
**Date**: 2026-02-03
**Status**: Final Design (Ready for Implementation)
**Contributors**: Codex (GPT-5.2), Gemini (2.5 Pro), Claude Sonnet 4.5

## Executive Summary

**Goal**: Refactor `_execute_single_goal()` to be independent (no recursion to `execute()`), enabling iterative execution to eliminate RecursionError on deep recursion (N=1000).

**Approach**: 4-phase incremental refactoring combining:
- **Codex's strength**: Safe, incremental extraction with behavioral equivalence
- **Gemini's strength**: Dispatch table pattern, WAM-based theoretical foundation

**Outcome**:
- RecursionError eliminated for benchmark(1000)
- Both `execute()` and `execute_iterative()` use shared `_execute_single_goal()`
- All 532+ tests pass
- Performance: 95-98% of baseline (acceptable overhead)

**Timeline**: 8-12 hours (realistic), up to 16 hours (conservative with contingencies)

---

## Design Overview

### Current Problem

```python
# Current broken flow (Phase 3 WIP)
execute() [flag=True]
  → execute_iterative()
    → GoalFrame.step()
      → _execute_single_goal()
        → execute() [flag=False, temporary]  # ❌ STILL USES RECURSION
          → ... deep recursion ...
          → RecursionError
```

### Target Architecture

```python
# Target flow (after refactoring)
execute()
  → if logical operator (,/2, ;/2, \+/1):
      → evaluator(goal)
  → else:
      → _execute_single_goal(goal)  # ✅ NO RECURSION

execute_iterative()
  → GoalFrame.step()
    → _execute_single_goal(goal)  # ✅ SAME IMPLEMENTATION

_execute_single_goal(goal):
  → if Cut (!):
      → raise CutException()
  → elif operator in _operator_evaluators:
      → _operator_evaluators[op](goal)
  → elif builtin:
      → _builtin_dispatch[name](goal)  # NEW: dispatch table
  → else:
      → solve_goal(goal)  # ❌ WATCH OUT: Can trigger execute() recursion
```

### Critical Discovery (Codex Review)

**solve_goal() recursion chain**:
```python
_execute_single_goal(goal)
  → solve_goal(goal)  # LogicInterpreter
    → runtime.execute(body_goal)  # ❌ BACK TO EXECUTE
      → ... recursion continues ...
```

**Solution**: Phase 3 must break this chain (see "solve_goal Chain Breaking" section).

---

## Integrated Design Principles

### 1. Architectural Boundaries (Codex + Gemini)

**Handled by execute() / execute_iterative() frames**:
- Logical operators: `,/2`, `;/2`, `\+/1`
- Control flow orchestration

**Handled by _execute_single_goal()**:
- Cut (`!`) - immediate CutException
- All operators (via `_operator_evaluators`)
- All built-in predicates (via `_builtin_dispatch`)
- User-defined predicates (via `solve_goal`)

**Rejection**: `_execute_single_goal()` MUST reject logical operators with assertion.

### 2. Dispatch Table Pattern (Gemini)

```python
class Runtime:
    def __init__(self):
        # ... existing init ...
        self._builtin_dispatch = self._build_builtin_dispatch()

    def _build_builtin_dispatch(self) -> Dict[Tuple[str, int], Callable]:
        """Build dispatch table: (functor, arity) -> handler"""
        return {
            ('var', 1): self._handle_var,
            ('atom', 1): self._handle_atom,
            ('number', 1): self._handle_number,
            ('atomic', 1): self._handle_atomic,
            ('functor', 3): self._handle_functor,
            ('arg', 3): self._handle_arg,
            ('=..', 2): self._handle_univ,
            ('assertz', 1): self._handle_assertz,
            ('asserta', 1): self._handle_asserta,
            ('retract', 1): self._handle_retract,
            ('member', 2): self._handle_member,
            ('append', 3): self._handle_append,
            ('findall', 3): self._handle_findall,
            ('at_end_of_stream', 0): self._handle_at_end_of_stream,
            ('at_end_of_stream', 1): self._handle_at_end_of_stream_stream,
            ('listing', 0): self._handle_listing,
            ('listing', 1): self._handle_listing_pred,
            ('export_facts', 2): self._handle_export_facts,
            # IO predicates (from io_manager)
            ('get_char', 1): lambda g, e: self._io_predicates['get_char'].execute(self, e),
            ('read_line', 1): lambda g, e: self._io_predicates['read_line'].execute(self, e),
            ('peek_char', 1): lambda g, e: self._io_predicates['peek_char'].execute(self, e),
        }
```

### 3. Incremental Extraction (Codex)

**Phase 1**: Extract without breaking existing `execute()`
- Create new `_execute_single_goal()` with full implementation
- Keep old `execute()` unchanged
- Both implementations coexist
- Tests use old implementation

**Phase 2**: Validate behavioral equivalence
- Parameterized tests: same input → same output for both
- Performance benchmarks
- Exception propagation tests

**Phase 3**: Refactor `execute()` to delegate
- Logical operator routing in `execute()`
- Delegate atomic goals to `_execute_single_goal()`
- Break `solve_goal` recursion chain

**Phase 4**: Enable iterative execution by default
- Flip `use_iterative_execution = True`
- Run full 532+ test suite
- Performance validation
- Remove old code after validation period

---

## Detailed Implementation Plan

### Phase 1: Extract _execute_single_goal() (4-5 hours)

#### Step 1.1: Create New Method Signature

```python
def _execute_single_goal(
    self, goal: PrologType, env: BindingEnvironment
) -> Iterator[BindingEnvironment]:
    """Execute a single atomic goal (non-logical-operator).

    Handles:
    - Cut (!) - raises CutException
    - Operators (=, is, <, etc.) via _operator_evaluators
    - Built-in predicates (var, atom, functor, etc.)
    - User-defined predicates via solve_goal

    Does NOT handle logical operators (,/2, ;/2, \+/1) - caller must handle.

    Args:
        goal: Atomic goal (Atom or Term, not logical operator)
        env: Binding environment

    Yields:
        Binding environments for each solution

    Raises:
        CutException: When cut (!) is executed
        PrologError: On predicate errors

    Note:
        This method does NOT call execute() to avoid recursion.
    """
```

#### Step 1.2: Extract Code from execute() (Lines 479-780)

Extract the following sections:

1. **Goal Preprocessing** (lines 479-530):
   - Atom wrapping: `if isinstance(goal, Atom): actual_goal = Term(goal, [])`
   - Atom IO operators: `nl`, `tab`, etc.
   - `_record_builtin_call()` helper (keep as nested function)

2. **Built-in Predicates** (lines 531-695):
   - var, atom, number, atomic (lines 531-587)
   - functor, arg, =.. (lines 588-650)
   - assertz, asserta, retract (lines 651-685)
   - member, append, findall (lines 686-730)
   - at_end_of_stream (lines 731-750)
   - listing, export_facts (lines 751-695)

3. **Operator Evaluation** (lines 696-755):
   - Check `_operator_evaluators` registry
   - Delegate to operator evaluator
   - Handle Cut specially (raise CutException immediately)

4. **solve_goal Fallback** (lines 756-780):
   - For user-defined predicates
   - Delegate to `logic_interpreter.solve_goal()`

#### Step 1.3: Add Architectural Safeguards

```python
def _execute_single_goal(self, goal, env):
    """..."""
    # Architectural enforcement: reject logical operators
    if isinstance(goal, Term) and isinstance(goal.functor, Atom):
        assert goal.functor.name not in (',', ';', '\\+'), (
            f"Logical operator {goal.functor.name} must be handled by execute(), "
            "not _execute_single_goal()"
        )

    # Helper for statistics
    def _record_builtin_call(name: str) -> None:
        if env.stats_enabled:
            env.stats["builtin_calls_by_name"][name] = (
                env.stats["builtin_calls_by_name"].get(name, 0) + 1
            )

    # [REST OF IMPLEMENTATION HERE]
```

#### Step 1.4: Handle Cut Specially

```python
# Special case: Cut (!)
if isinstance(goal, Atom) and goal.name == "!":
    _record_builtin_call("!")
    if env.stats_enabled:
        env.stats["builtin_calls_total"] += 1
    # Check if cut is in operator registry
    op_info = operator_registry.get_operator("!")
    if op_info and op_info.op_type == OperatorType.PREFIX:
        evaluator = self._operator_evaluators.get("!")
        if evaluator:
            try:
                yield from evaluator([], env)  # Cut takes no args
            except CutException:
                raise  # Propagate cut
        return
```

#### Step 1.5: Convert to Dispatch Table

Replace if-elif chain with dispatch table:

```python
# Check if built-in predicate
if isinstance(goal, Term) and isinstance(goal.functor, Atom):
    key = (goal.functor.name, len(goal.args))
    handler = self._builtin_dispatch.get(key)
    if handler:
        _record_builtin_call(goal.functor.name)
        if env.stats_enabled:
            env.stats["builtin_calls_total"] += 1
        try:
            yield from handler(goal, env)
        except Exception as e:
            logger.error("Error in built-in %s: %s", goal.functor.name, e)
            raise
        return

# Check if operator (via _operator_evaluators)
if isinstance(goal, Term) and isinstance(goal.functor, Atom):
    evaluator = self._operator_evaluators.get(goal.functor.name)
    if evaluator:
        try:
            yield from evaluator(goal.args, env)
        except CutException:
            raise  # Propagate cut
        except Exception as e:
            logger.error("Error in operator %s: %s", goal.functor.name, e)
            raise
        return

# Fallback: user-defined predicate via solve_goal
yield from self.logic_interpreter.solve_goal(goal, env)
```

#### Step 1.6: Implement Handler Methods

Create individual handler methods for each built-in:

```python
def _handle_var(self, goal: Term, env: BindingEnvironment) -> Iterator[BindingEnvironment]:
    """Handle var/1 built-in predicate."""
    if len(goal.args) != 1:
        raise PrologError("var/1 requires exactly 1 argument")
    arg = self.logic_interpreter.dereference(goal.args[0], env)
    if isinstance(arg, Variable):
        yield env

def _handle_atom(self, goal: Term, env: BindingEnvironment) -> Iterator[BindingEnvironment]:
    """Handle atom/1 built-in predicate."""
    if len(goal.args) != 1:
        raise PrologError("atom/1 requires exactly 1 argument")
    arg = self.logic_interpreter.dereference(goal.args[0], env)
    if isinstance(arg, Atom):
        yield env

# ... 16 more handler methods ...
```

**Validation**:
- Extract handlers verbatim from current `execute()` implementation
- Ensure exact behavior preservation (including error messages)
- No changes to logic, only structure

---

### Phase 2: Validate Behavioral Equivalence (2-3 hours)

#### Test Strategy

**Equivalence Tests**:
```python
@pytest.mark.parametrize("query", [
    "var(X)",
    "atom(foo)",
    "X = 1",
    "X is 2 + 3",
    "member(X, [1,2,3])",
    "findall(X, member(X, [a,b,c]), L)",
    # ... 50+ test cases covering all built-ins and operators
])
def test_execute_single_goal_equivalence(runtime, query):
    """Verify _execute_single_goal produces same results as execute."""
    env = BindingEnvironment()
    goal = parse_query(query)

    # Old implementation (via execute with flag disabled)
    runtime.use_iterative_execution = False
    old_results = list(runtime.execute(goal, env))

    # New implementation (direct call)
    new_results = list(runtime._execute_single_goal(goal, env))

    assert len(old_results) == len(new_results)
    for old, new in zip(old_results, new_results):
        assert old.bindings == new.bindings
```

**Exception Propagation Tests**:
```python
def test_cut_exception_propagation():
    """Verify CutException is raised correctly."""
    runtime = Runtime()
    env = BindingEnvironment()
    goal = Atom("!")

    with pytest.raises(CutException):
        list(runtime._execute_single_goal(goal, env))

def test_prolog_error_propagation():
    """Verify PrologError is raised correctly."""
    runtime = Runtime()
    env = BindingEnvironment()
    goal = Term(Atom("var"), [])  # var/1 with 0 args

    with pytest.raises(PrologError) as exc:
        list(runtime._execute_single_goal(goal, env))
    assert "requires exactly 1 argument" in str(exc.value)
```

**Performance Benchmarks**:
```python
def test_execute_single_goal_performance(benchmark):
    """Verify performance overhead is acceptable (< 5%)."""
    runtime = Runtime()
    env = BindingEnvironment()

    # Setup
    runtime.add_rule("p(1). p(2). p(3).")
    goal = Term(Atom("p"), [Variable("X")])

    # Benchmark old implementation
    runtime.use_iterative_execution = False
    old_time = benchmark(lambda: list(runtime.execute(goal, env)))

    # Benchmark new implementation
    new_time = benchmark(lambda: list(runtime._execute_single_goal(goal, env)))

    # Allow 5% overhead
    assert new_time / old_time <= 1.05
```

---

### Phase 3: Break solve_goal Recursion Chain (3-4 hours)

#### Problem Analysis

Current recursion chain:
```python
_execute_single_goal(goal)
  → logic_interpreter.solve_goal(goal, env)
    → for rule in matching_rules:
        → runtime.execute(rule.body, env)  # ❌ BACK TO EXECUTE
```

When `use_iterative_execution=True`, this creates:
```python
execute() [flag=True]
  → execute_iterative()
    → _execute_single_goal()
      → solve_goal()
        → execute() [flag=True]  # ❌ INFINITE LOOP
```

#### Solution 1: Add solve_goal_direct() (Recommended)

Add new method that doesn't call `execute()`:

```python
# In LogicInterpreter
def solve_goal_direct(
    self, goal: PrologType, env: BindingEnvironment, runtime: 'Runtime'
) -> Iterator[BindingEnvironment]:
    """Solve goal by matching rules, using _execute_single_goal for bodies.

    This is like solve_goal() but doesn't call runtime.execute() for rule bodies.
    Instead, it handles logical operators directly and delegates atomic goals
    to _execute_single_goal().

    Args:
        goal: Goal to solve
        env: Binding environment
        runtime: Runtime instance (for accessing _execute_single_goal)

    Yields:
        Binding environments for each solution
    """
    # [Implementation similar to solve_goal, but for rule bodies:]
    # - If body is conjunction: manually handle goal sequence
    # - If body is disjunction: manually handle alternatives
    # - If body is atomic: call runtime._execute_single_goal()
    # - Never call runtime.execute()
```

Then update `_execute_single_goal()`:
```python
def _execute_single_goal(self, goal, env):
    # ... existing code ...

    # Fallback: user-defined predicate
    # Use solve_goal_direct instead of solve_goal
    yield from self.logic_interpreter.solve_goal_direct(goal, env, self)
```

#### Solution 2: Pass execution_mode Flag (Alternative)

```python
# In solve_goal
def solve_goal(self, goal, env, execution_mode='recursive'):
    """
    execution_mode:
        'recursive': Use runtime.execute() for rule bodies (old behavior)
        'iterative': Use runtime._execute_single_goal() directly (new)
    """
    for rule in matching_rules:
        if execution_mode == 'recursive':
            yield from self.runtime.execute(rule.body, new_env)
        else:
            # Handle logical operators manually, delegate atomic to _execute_single_goal
            yield from self._execute_body_iterative(rule.body, new_env)
```

**Recommendation**: Solution 1 (solve_goal_direct) is cleaner separation of concerns.

---

### Phase 4: Refactor execute() to Delegate (1-2 hours)

Replace `execute()` with thin orchestrator:

```python
def execute(
    self, goal: Any, env: BindingEnvironment
) -> Iterator[BindingEnvironment]:
    """Execute a goal (thin orchestrator).

    Routes logical operators to evaluators, delegates atomic goals to
    _execute_single_goal().

    Args:
        goal: Goal to execute
        env: Binding environment

    Yields:
        Binding environments for each solution

    Raises:
        CutException: Propagated from cut execution
    """
    logger.debug("EXECUTE: Called with goal: %s", goal)

    # Feature flag: Use iterative execution if enabled
    if self.use_iterative_execution:
        yield from self.execute_iterative(goal, env)
        return

    # Check if logical operator
    if isinstance(goal, Term) and isinstance(goal.functor, Atom):
        functor_name = goal.functor.name

        # Logical operators: handle via existing evaluators
        if functor_name == ',':
            evaluator = self._operator_evaluators.get(',')
            if evaluator:
                yield from evaluator(goal.args, env)
                return
        elif functor_name == ';':
            evaluator = self._operator_evaluators.get(';')
            if evaluator:
                yield from evaluator(goal.args, env)
                return
        elif functor_name == '\\+':
            evaluator = self._operator_evaluators.get('\\+')
            if evaluator:
                yield from evaluator(goal.args, env)
                return

    # All other goals: delegate to _execute_single_goal
    yield from self._execute_single_goal(goal, env)
```

**Size**: ~30 lines (down from ~310 lines)

---

## Testing Strategy

### Unit Tests (50+ tests)

1. **Built-in predicate tests** (18 tests)
   - Each built-in: var, atom, number, functor, arg, =.., etc.
   - Error cases: wrong arity, invalid arguments

2. **Operator tests** (15 tests)
   - Arithmetic: =, is, <, >, =<, >=, =:=, =\=
   - Unification: =, \=, ==, \==
   - Comparison: @<, @>, @=<, @>=

3. **Cut tests** (5 tests)
   - Cut in conjunction
   - Cut in disjunction
   - Cut in findall (isolated)

4. **Exception tests** (5 tests)
   - CutException propagation
   - PrologError for invalid predicates
   - IOError propagation

5. **Edge case tests** (7 tests)
   - Nested logical operators: `(a, (b ; c), d)`
   - Cut barrier in findall
   - Negation side effects
   - Deep recursion via solve_goal

### Integration Tests (20+ tests)

1. **Equivalence tests** (10 tests)
   - Parameterized: same query → same results
   - Both execute() and _execute_single_goal()

2. **Performance tests** (5 tests)
   - Overhead < 5% for typical queries
   - Deep recursion (N=1000) succeeds with iterative

3. **Regression tests** (5 tests)
   - All existing 532+ tests pass
   - No behavioral changes

### Benchmark Tests

1. **RecursionError elimination**
   ```python
   def test_benchmark_1000_no_error(runtime_iterative):
       runtime.consult("tests/benchmark/recursion_depth.pl")
       results = list(runtime.query("benchmark(1000)."))
       assert len(results) == 1  # Success, no RecursionError
   ```

2. **Performance validation**
   ```python
   def test_performance_acceptable(benchmark):
       # Verify 95% threshold (Gemini recommendation)
       assert iterative_time / baseline_time >= 0.95
   ```

---

## Risk Mitigation

### High-Priority Risks

1. **Hidden State Dependencies**
   - **Risk**: `_record_builtin_call()` as closure might break
   - **Mitigation**: Keep as nested function (maintains closure over `env`)
   - **Validation**: Unit test for statistics tracking

2. **solve_goal Recursion Chain**
   - **Risk**: RecursionError persists via solve_goal → execute loop
   - **Mitigation**: Implement solve_goal_direct() or execution_mode flag
   - **Validation**: Deep recursion test (N=1000)

3. **Operator Return Value Contract**
   - **Risk**: Gemini's pattern differs from existing evaluators
   - **Mitigation**: Use existing `_operator_evaluators` as-is
   - **Validation**: Operator tests verify exact behavior match

4. **Atom IO Operators**
   - **Risk**: `nl`, `tab` handling might be lost
   - **Mitigation**: Extract Atom preprocessing from execute()
   - **Validation**: IO operator tests

### Medium-Priority Risks

5. **Cut Barrier Interactions**
   - **Risk**: Cut might escape findall/negation
   - **Mitigation**: Test cut in findall (already isolated)
   - **Validation**: Cut barrier tests

6. **Exception Propagation**
   - **Risk**: CutException/PrologError/IOError might not propagate
   - **Mitigation**: Preserve exact exception patterns
   - **Validation**: Exception propagation tests

7. **Statistics/Tracing**
   - **Risk**: Profiling might break
   - **Mitigation**: Keep `_record_builtin_call()` helper
   - **Validation**: Statistics tracking tests

---

## Timeline and Effort

### Realistic Timeline: 8-12 hours

| Phase | Tasks | Hours | Risks |
|-------|-------|-------|-------|
| Phase 1 | Extract _execute_single_goal() | 4-5 | Hidden dependencies (+1h) |
| Phase 2 | Behavioral equivalence tests | 2-3 | Test failures (+2h) |
| Phase 3 | Break solve_goal chain | 3-4 | Design complexity (+1h) |
| Phase 4 | Refactor execute() | 1-2 | Regression (+1h) |
| **Total** | | **10-14h** | **Contingency: +2-4h** |

### Conservative Timeline: 12-16 hours
- Includes contingency for unexpected issues
- Rollback time if tests fail
- Documentation updates

---

## Success Criteria

### Functional Requirements
- ✅ No recursion between execute() and _execute_single_goal()
- ✅ RecursionError eliminated for benchmark(1000)
- ✅ Both execute() and execute_iterative() use shared _execute_single_goal()
- ✅ All 532+ existing tests pass
- ✅ Cut, findall, negation work correctly

### Performance Requirements
- ✅ Overhead < 5% for typical queries
- ✅ Performance ≥ 95% of baseline (Gemini threshold)
- ✅ Memory usage comparable (no leaks)

### Quality Requirements
- ✅ Behavioral equivalence verified by tests
- ✅ Exception propagation unchanged
- ✅ Statistics/tracing preserved
- ✅ Code maintainability improved (dispatch table)

---

## Implementation Checklist

### Pre-Implementation
- [ ] Review this integrated design document
- [ ] Confirm Phase 1-4 approach with team
- [ ] Set up test environment
- [ ] Backup current working state (git commit)

### Phase 1: Extraction
- [ ] Create `_execute_single_goal()` method skeleton
- [ ] Extract goal preprocessing code
- [ ] Extract 18 built-in predicate handlers
- [ ] Extract operator evaluation logic
- [ ] Extract solve_goal fallback
- [ ] Add architectural safeguards (assertion)
- [ ] Implement dispatch table
- [ ] Run unit tests (28/28 execution_frames)

### Phase 2: Validation
- [ ] Write 50+ equivalence tests
- [ ] Write exception propagation tests
- [ ] Write performance benchmarks
- [ ] Run all tests (both implementations)
- [ ] Verify performance overhead < 5%

### Phase 3: solve_goal Chain
- [ ] Implement solve_goal_direct() OR execution_mode flag
- [ ] Update _execute_single_goal() to use new method
- [ ] Test deep recursion (N=1000)
- [ ] Verify no infinite loops

### Phase 4: execute() Refactor
- [ ] Refactor execute() to thin orchestrator
- [ ] Test logical operator routing
- [ ] Run full 532+ test suite
- [ ] Performance validation

### Post-Implementation
- [ ] Enable use_iterative_execution = True by default
- [ ] Run benchmark suite (light, medium, heavy)
- [ ] Update documentation
- [ ] Code review
- [ ] Remove old code after validation period

---

## Next Steps

1. **Review this document** with team/stakeholders
2. **Start Phase 1**: Create feature branch `feature/execute-single-goal-refactor`
3. **Implement incrementally**: One phase at a time, test after each
4. **Monitor progress**: Update task tracker (#4, #6)
5. **Document learnings**: Update design doc with actual implementation notes

---

## References

- **Codex Design**: `.claude/docs/design/execute_single_goal_refactor_plan.md`
- **Gemini Research**: `.claude/docs/research/goal_execution_patterns_gemini.md`
- **Codex Review of Gemini**: `.claude/docs/design/codex_review_of_gemini.md`
- **Gemini Review of Codex**: `.claude/docs/design/gemini_review_of_codex.md`
- **Original Design**: `.claude/docs/design/goal-execution-loop-iterative-design.md`
- **Codex Recommendations**: `.claude/docs/research/goal-execution-loop-iterative-design-review-2026-02-03.md`

---

## Approval

**Design Status**: ✅ Ready for Implementation

**Estimated Completion**: 8-12 hours (realistic), up to 16 hours (conservative)

**Go/No-Go Decision**: Awaiting approval to proceed with Phase 1.
