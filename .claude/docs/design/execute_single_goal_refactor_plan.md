# _execute_single_goal() Refactoring Plan

**Date:** 2026-02-03
**Scope:** Eliminate recursion between execute() and _execute_single_goal()
**Goal:** Make _execute_single_goal() independent and reusable from both execute() and execute_iterative()

## Problem Statement

Current implementation (lines 782-811) has a critical recursion issue:
```python
def _execute_single_goal(self, goal, env):
    saved_flag = self.use_iterative_execution
    self.use_iterative_execution = False
    try:
        yield from self.execute(goal, env)  # RECURSION!
    finally:
        self.use_iterative_execution = saved_flag
```

This causes:
- execute() → execute_iterative() → GoalFrame.step() → _execute_single_goal() → execute()
- Defeats the purpose of iterative execution
- Still vulnerable to RecursionError

## Design Principles

1. **Single Dispatch Point**: _execute_single_goal() becomes THE canonical handler for all non-logical-operator goals
2. **No Recursion**: _execute_single_goal() must NOT call execute()
3. **Code Reuse**: execute() delegates to _execute_single_goal() to avoid drift
4. **Scope Separation**: Logical operators (,/2, ;/2, \+/1) handled by frames, NOT by _execute_single_goal()
5. **Preserve Semantics**: All exception handling, logging, stats must be maintained

## Refactoring Plan

### Phase 1: Extract Core Logic

**Extract from execute() lines 479-780 into _execute_single_goal()**

#### 1.1 Goal Preprocessing (lines 485-543)
Move to _execute_single_goal():
- Atom('!') conversion to Term
- Atom vs Term routing
- IO operator special handling for Atoms
- Normal predicate solve_goal for Atoms

#### 1.2 Built-in Predicates (lines 602-762)
Move to _execute_single_goal():
- var/1
- atom/1
- number/1
- atom_number/2
- functor/3
- arg/3
- =../2
- asserta/1, assertz/1
- member/2
- append/3
- findall/3
- get_char/1, read_line/1, peek_char/1
- at_end_of_stream/0
- retract/1
- listing/0, listing/1
- export_facts/2

#### 1.3 Operator Evaluation (lines 544-601)
Move to _execute_single_goal():
- Operator registry lookup
- Arithmetic operators (not 'is')
- Comparison operators
- Other operators (=, is, etc.)
- **EXCLUDE**: ,/2, ;/2, \+/1 (handled by frames)

#### 1.4 Fallback to solve_goal (lines 763-780)
Move to _execute_single_goal():
- User-defined predicate resolution via logic_interpreter.solve_goal()

#### 1.5 Helper Function
Move _record_builtin_call() helper (lines 479-483) into _execute_single_goal() scope

### Phase 2: Logical Operator Routing

**Create dispatch logic for logical operators**

In _execute_single_goal(), detect and REJECT logical operators:

```python
def _execute_single_goal(self, goal, env):
    # Detect logical operators early
    if isinstance(goal, Term):
        functor_name = goal.functor.name if hasattr(goal.functor, 'name') else str(goal.functor)
        if functor_name in (',', ';', '\\+'):
            raise ValueError(
                f"Logical operator {functor_name} must be handled by execute() or frames, "
                f"not _execute_single_goal()"
            )

    # ... rest of implementation
```

This enforces architectural boundary.

### Phase 3: Refactor execute()

**Transform execute() to orchestrate logical operators and delegate atomic goals**

New execute() structure:

```python
def execute(self, goal, env):
    logger.debug("EXECUTE: Called with goal: %s", goal)

    # Feature flag: Use iterative execution if enabled
    if self.use_iterative_execution:
        yield from self.execute_iterative(goal, env)
        return

    # Check if goal is a logical operator
    if isinstance(goal, Term):
        functor_name = goal.functor.name if hasattr(goal.functor, 'name') else str(goal.functor)

        # Logical operators: handle with existing evaluators
        if functor_name == ',':
            yield from self._evaluators[','](goal.args, env)
            return
        elif functor_name == ';':
            yield from self._evaluators[';'](goal.args, env)
            return
        elif functor_name == '\\+':
            yield from self._evaluators['\\+'](goal.args, env)
            return

    # All other goals: delegate to _execute_single_goal
    yield from self._execute_single_goal(goal, env)
```

**Key changes:**
- execute() becomes a thin orchestrator
- Logical operators handled by existing evaluators
- All atomic goals delegated to _execute_single_goal()
- Eliminates 300+ lines of duplication

### Phase 4: Integration with execute_iterative()

**No changes needed** - GoalFrame.step() already calls _execute_single_goal():

```python
# pyprolog/runtime/execution_frames.py:105
self.solutions = interpreter._execute_single_goal(self.goal, self.env)
```

Once _execute_single_goal() is independent, this just works.

### Phase 5: Handle Cut (!)

**Cut must work in both paths**

Current execute() has special handling for Atom('!') → Term('!', []):

```python
if isinstance(goal, Atom) and goal.name == "!" and "!" in self._operator_evaluators:
    processed_goal = Term(goal, [])
```

In _execute_single_goal():
- Keep this preprocessing
- Cut evaluation via operator evaluator
- Raises CutException (propagates through both paths)

No special changes needed - cut works through operator registry.

### Phase 6: Validation Strategy

**Testing order to keep tests passing:**

1. **Extract _execute_single_goal() implementation** (keep execute() unchanged)
   - Run full test suite
   - Verify no behavior change (both implementations coexist)

2. **Refactor execute() to delegate atomic goals**
   - Run test suite incrementally:
     - Built-in predicate tests
     - Operator tests
     - User-defined predicate tests
   - Verify legacy execute() still works

3. **Enable execute_iterative() by default**
   - Run full test suite
   - Compare legacy vs iterative execution paths

4. **Remove legacy code**
   - After both paths verified equivalent

### Phase 7: Edge Cases & Special Handling

#### 7.1 Findall/3 Isolation
- findall/3 runs Goal in isolated scope (no choice point contamination)
- Already handled by FindallPredicate.execute()
- No changes needed

#### 7.2 Negation (\+/1) Isolation
- Handled by frames in execute_iterative()
- Handled by evaluator in execute()
- _execute_single_goal() never sees it (architectural boundary)

#### 7.3 IO Operators (get_char, read_line, etc.)
- Can raise IOManager exceptions
- Exception propagation preserved in _execute_single_goal()
- No changes to exception handling

#### 7.4 Exception Propagation
Preserve all existing exception patterns:
- CutException: propagate through
- IOManager exceptions: propagate through
- PrologError: propagate through
- General Exception in operators: log and return (no yield)

#### 7.5 Stats Recording
- _record_builtin_call() helper moved into _execute_single_goal()
- All builtin calls still recorded
- Stats tracking unchanged

## Implementation Checklist

- [ ] Extract _execute_single_goal() core implementation
  - [ ] Goal preprocessing logic
  - [ ] Built-in predicate handlers (18 predicates)
  - [ ] Operator evaluation (exclude ,/2, ;/2, \+/1)
  - [ ] solve_goal fallback
  - [ ] _record_builtin_call() helper
  - [ ] Exception handling patterns
  - [ ] Logging patterns

- [ ] Add logical operator detection/rejection in _execute_single_goal()

- [ ] Refactor execute() to delegate
  - [ ] Logical operator routing (,/2, ;/2, \+/1)
  - [ ] Delegate all atomic goals to _execute_single_goal()
  - [ ] Remove duplicated code

- [ ] Run test suite
  - [ ] tests/unit/ (basic functionality)
  - [ ] tests/runtime/ (interpreter tests)
  - [ ] tests/integration/ (end-to-end)
  - [ ] tests/japanese/ (UTF-8 support)

- [ ] Verify execute_iterative() works correctly
  - [ ] No RecursionError
  - [ ] Same results as execute()
  - [ ] Cut behavior preserved

- [ ] Document architectural decision
  - [ ] Update .claude/docs/architecture/
  - [ ] Add code comments explaining separation

## Function Signatures

### Before

```python
def execute(self, goal: Any, env: BindingEnvironment) -> Iterator[BindingEnvironment]:
    """310 lines of mixed logic"""

def _execute_single_goal(self, goal: PrologType, env: BindingEnvironment) -> Iterator[BindingEnvironment]:
    """4 lines calling execute()"""
```

### After

```python
def execute(self, goal: Any, env: BindingEnvironment) -> Iterator[BindingEnvironment]:
    """Orchestrate logical operators, delegate atomic goals (~30 lines)"""
    if self.use_iterative_execution:
        yield from self.execute_iterative(goal, env)
        return

    # Handle logical operators: ,/2, ;/2, \+/1
    if is_logical_operator(goal):
        yield from self._evaluators[operator](goal.args, env)
        return

    # Delegate all atomic goals
    yield from self._execute_single_goal(goal, env)

def _execute_single_goal(self, goal: PrologType, env: BindingEnvironment) -> Iterator[BindingEnvironment]:
    """Execute atomic goal: built-ins, operators (non-logical), solve_goal (~280 lines)"""

    # Reject logical operators
    if is_logical_operator(goal):
        raise ValueError("Logical operators must be handled by execute()")

    # Helper for stats
    def _record_builtin_call(name: str) -> None:
        ...

    # Goal preprocessing
    # Built-in predicates
    # Operator evaluation
    # solve_goal fallback
```

## Risks & Mitigations

### Risk 1: Behavioral Drift
**Risk:** execute() and _execute_single_goal() implementations diverge over time

**Mitigation:**
- _execute_single_goal() is THE canonical implementation
- execute() delegates to it (single source of truth)
- Add tests that verify both paths produce identical results

### Risk 2: Exception Handling Changes
**Risk:** Exception propagation behavior changes during refactoring

**Mitigation:**
- Preserve exact exception handling patterns
- Test CutException propagation explicitly
- Test IOManager exception propagation
- Test PrologError propagation

### Risk 3: Cut Barrier Interactions
**Risk:** Cut behavior differs between execute() and execute_iterative()

**Mitigation:**
- Cut handled consistently through operator evaluator
- Both paths use same CutException mechanism
- execute_iterative() has additional ExecutionState.apply_cut() for frame cleanup
- Test cut in nested contexts

### Risk 4: Stats Recording Breaks
**Risk:** Builtin call stats not recorded correctly

**Mitigation:**
- _record_builtin_call() stays with the implementation
- Verify stats collection in tests
- Use existing test infrastructure

### Risk 5: Test Suite Breakage
**Risk:** Existing tests fail after refactoring

**Mitigation:**
- Incremental refactoring (coexist old/new implementations)
- Run tests after each phase
- Roll back if tests fail
- Focus on one category at a time (built-ins, operators, solve_goal)

## Success Criteria

1. ✅ _execute_single_goal() does NOT call execute()
2. ✅ No RecursionError in execute_iterative()
3. ✅ All 532 tests pass
4. ✅ execute() and execute_iterative() produce identical results
5. ✅ Cut behavior preserved in both paths
6. ✅ Exception handling unchanged
7. ✅ Stats recording unchanged
8. ✅ Code duplication eliminated (execute() delegates to _execute_single_goal())

## Code Size Estimate

- execute() before: ~310 lines
- execute() after: ~30 lines (orchestration only)
- _execute_single_goal() before: ~4 lines
- _execute_single_goal() after: ~280 lines (extracted logic)
- Net change: Similar total, better separation of concerns

## Timeline Estimate

1. Phase 1 (Extract): 2-3 hours
2. Phase 2 (Logical operator routing): 30 minutes
3. Phase 3 (Refactor execute): 1 hour
4. Phase 4 (Integration): Already done
5. Phase 5 (Cut handling): Already done
6. Phase 6 (Testing): 1-2 hours
7. Phase 7 (Edge cases): 1 hour

**Total:** 6-8 hours of focused work

## Next Steps

1. Read full execute() implementation (lines 464-780)
2. Create _execute_single_goal() stub with extracted logic
3. Run tests to verify coexistence
4. Refactor execute() to delegate
5. Enable iterative execution by default
6. Validate with full test suite
