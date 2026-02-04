# Implementation Plan: Iterative `_execute_body_direct`

**Date**: 2026-02-04
**Target**: `pyprolog/runtime/logic_interpreter.py:_execute_body_direct()` (lines 983-1021)
**Problem**: RecursionError at depth ~175-200 due to recursive conjunction/disjunction handling
**Goal**: Convert to iterative implementation using explicit stack

---

## Approach

**Selected: Integrate with Existing Frame-Based Engine**

Rationale:
- The repository already has a complete frame-based iterative engine (`execution_frames.py` + `interpreter.execute_iterative`)
- Implementing a separate trampoline/stack engine would create:
  - Semantic drift risk (two engines with different Prolog semantics)
  - Double maintenance burden
  - Integration complexity
- Recommended approach from design review: "Complete operator handling in the iterative engine and replace `_execute_body_direct` with delegation"

**Key Insight**: `_execute_body_direct` is essentially a **body operator evaluator**. It handles:
- Conjunction (`,/2`): sequential evaluation with environment threading
- Disjunction (`;/2`): alternative branches with backtracking
- Negation (`\+/1`): negation as failure with cut isolation

This maps directly to `OperatorFrame` in the existing frame-based engine.

---

## Data Structures

### Existing Infrastructure (execution_frames.py)

Already implemented:

```python
class FrameType(Enum):
    GOAL = auto()
    GOAL_SEQ = auto()
    OPERATOR = auto()  # ← Target for body operators
    CHOICE_POINT = auto()

@dataclass
class Frame(ABC):
    frame_type: FrameType
    env: BindingEnvironment

    @abstractmethod
    def step(self, interpreter) -> Optional[BindingEnvironment]:
        """Execute one step, return result or None"""

    @abstractmethod
    def can_backtrack(self) -> bool:
        """Check if frame has more alternatives"""

@dataclass
class OperatorFrame(Frame):
    """Handles logical operators (,/2, ;/2, \\+/1)"""
    operator: str
    operands: List[PrologType]
    state: OperatorState  # Enum: INIT, LEFT, RIGHT, etc.
    # ...implementation...
```

### Required Extensions

**OperatorState** (new enum for tracking operator evaluation state):

```python
class OperatorState(Enum):
    INIT = auto()           # Initial state
    CONJ_LEFT = auto()      # Conjunction: evaluating left
    CONJ_RIGHT = auto()     # Conjunction: evaluating right
    DISJ_LEFT = auto()      # Disjunction: trying left branch
    DISJ_RIGHT = auto()     # Disjunction: trying right branch
    NEG_TESTING = auto()    # Negation: testing inner goal
    NEG_RESULT = auto()     # Negation: yielding result
    DONE = auto()           # Operator finished
```

**OperatorFrame enhancements**:

```python
@dataclass
class OperatorFrame(Frame):
    operator: str  # ",", ";", "\\+"
    left: Optional[PrologType] = None
    right: Optional[PrologType] = None
    state: OperatorState = OperatorState.INIT
    left_solutions: Optional[Iterator[BindingEnvironment]] = None
    right_solutions: Optional[Iterator[BindingEnvironment]] = None
    current_left_env: Optional[BindingEnvironment] = None
    negation_succeeded: Optional[bool] = None
```

---

## Algorithm

### Iterative Body Evaluation (via OperatorFrame)

**Conjunction (`,/2`)** state machine:

1. **INIT**: Initialize left goal solutions iterator
2. **CONJ_LEFT**: Pull next left solution
   - If solution found: save to `current_left_env`, transition to CONJ_RIGHT
   - If exhausted: mark DONE
3. **CONJ_RIGHT**: Initialize right goal with `current_left_env`, pull solution
   - If solution found: yield result, stay in CONJ_RIGHT (for backtracking)
   - If exhausted: backtrack to CONJ_LEFT
4. **DONE**: Frame exhausted

**Disjunction (`;/2`)** state machine:

1. **INIT**: Transition to DISJ_LEFT
2. **DISJ_LEFT**: Initialize and pull from left branch solutions
   - If solution found: yield result, stay in DISJ_LEFT
   - If exhausted: transition to DISJ_RIGHT
   - **CutException handling**: propagate upward, skip right branch
3. **DISJ_RIGHT**: Initialize and pull from right branch solutions
   - If solution found: yield result, stay in DISJ_RIGHT
   - If exhausted: mark DONE
4. **DONE**: Frame exhausted

**Negation (`\+/1`)** state machine:

1. **INIT**: Transition to NEG_TESTING
2. **NEG_TESTING**: Initialize inner goal solutions iterator, pull once
   - If solution found: set `negation_succeeded = False`, mark DONE (fail)
   - If exhausted: set `negation_succeeded = True`, transition to NEG_RESULT
   - **CutException handling**: treat as solution found (negation fails)
3. **NEG_RESULT**: Yield original `env` (negation succeeds), mark DONE
4. **DONE**: Frame exhausted

### Atomic Goal Handling

When goal is not an operator (`,`, `;`, `\+`):
- Delegate to `runtime._execute_single_goal(goal, env)`
- Use existing `GoalFrame` for atomic goal execution

---

## Integration Points

### 1. LogicInterpreter._execute_body_direct()

**Current implementation**: Lines 983-1021 (recursive)

**New implementation** (delegating to iterative engine):

```python
def _execute_body_direct(
    self, body: PrologType, env: BindingEnvironment
) -> Iterator[BindingEnvironment]:
    """Execute goal body with logical operators.

    Delegates to iterative execution engine.
    """
    # Delegate to runtime's iterative engine
    yield from self.runtime.execute_iterative(body, env)
```

**Key change**: Instead of recursive calls to `_execute_body_direct`, the logic moves into `OperatorFrame.step()` which manages its own state iteratively.

### 2. Interpreter.execute_iterative()

**Current state**: Lines 880-900+ (partial implementation)

**Required enhancements**:

```python
def execute_iterative(
    self, goal: PrologType, env: BindingEnvironment
) -> Iterator[BindingEnvironment]:
    """Iterative goal execution using explicit stack."""
    state = ExecutionState(stack=[], choice_points=[])

    # Classify goal and push appropriate frame
    if isinstance(goal, Functor):
        functor_name = goal.name

        # Operators: push OperatorFrame
        if functor_name == "," and len(goal.args) == 2:
            state.stack.append(OperatorFrame(
                frame_type=FrameType.OPERATOR,
                operator=",",
                left=goal.args[0],
                right=goal.args[1],
                env=env
            ))
        elif functor_name == ";" and len(goal.args) == 2:
            state.stack.append(OperatorFrame(
                frame_type=FrameType.OPERATOR,
                operator=";",
                left=goal.args[0],
                right=goal.args[1],
                env=env
            ))
        elif functor_name == "\\+" and len(goal.args) == 1:
            state.stack.append(OperatorFrame(
                frame_type=FrameType.OPERATOR,
                operator="\\+",
                left=goal.args[0],
                env=env
            ))
        else:
            # Atomic goal: use GoalFrame
            state.push_goal(goal, env)
    else:
        # Atomic goal: use GoalFrame
        state.push_goal(goal, env)

    # Main execution loop
    while state.stack:
        frame = state.stack[-1]

        try:
            result = frame.step(self)

            if result is not None:
                yield result
                # Frame may have more solutions, keep it on stack
            elif not frame.can_backtrack():
                state.stack.pop()
        except CutException:
            # Propagate cut upward
            raise
        except StopIteration:
            state.stack.pop()
```

### 3. OperatorFrame.step() Implementation

**Conjunction**:

```python
def step(self, interpreter) -> Optional[BindingEnvironment]:
    if self.state == OperatorState.INIT:
        # Initialize left goal
        self.left_solutions = interpreter.execute_iterative(
            self.left, self.env
        )
        self.state = OperatorState.CONJ_LEFT

    if self.state == OperatorState.CONJ_LEFT:
        try:
            self.current_left_env = next(self.left_solutions)
            self.state = OperatorState.CONJ_RIGHT
            self.right_solutions = interpreter.execute_iterative(
                self.right, self.current_left_env
            )
        except StopIteration:
            self.state = OperatorState.DONE
            raise

    if self.state == OperatorState.CONJ_RIGHT:
        try:
            result = next(self.right_solutions)
            return result  # Yield this solution
        except StopIteration:
            # Right exhausted, backtrack to left
            self.state = OperatorState.CONJ_LEFT
            return self.step(interpreter)  # Tail recursion (single level)

    raise StopIteration  # DONE
```

**Disjunction**:

```python
def step(self, interpreter) -> Optional[BindingEnvironment]:
    if self.state == OperatorState.INIT:
        self.state = OperatorState.DISJ_LEFT
        self.left_solutions = interpreter.execute_iterative(
            self.left, self.env
        )

    if self.state == OperatorState.DISJ_LEFT:
        try:
            result = next(self.left_solutions)
            return result
        except CutException:
            # Cut in left branch: skip right, propagate
            self.state = OperatorState.DONE
            raise
        except StopIteration:
            # Left exhausted, try right
            self.state = OperatorState.DISJ_RIGHT
            self.right_solutions = interpreter.execute_iterative(
                self.right, self.env
            )

    if self.state == OperatorState.DISJ_RIGHT:
        try:
            result = next(self.right_solutions)
            return result
        except StopIteration:
            self.state = OperatorState.DONE
            raise

    raise StopIteration  # DONE
```

**Negation**:

```python
def step(self, interpreter) -> Optional[BindingEnvironment]:
    if self.state == OperatorState.INIT:
        self.state = OperatorState.NEG_TESTING
        self.left_solutions = interpreter.execute_iterative(
            self.left, self.env
        )

    if self.state == OperatorState.NEG_TESTING:
        try:
            _ = next(self.left_solutions)
            # Solution found: negation fails
            self.negation_succeeded = False
            self.state = OperatorState.DONE
            raise StopIteration
        except CutException:
            # Cut within negation: treat as solution found
            self.negation_succeeded = False
            self.state = OperatorState.DONE
            raise StopIteration
        except StopIteration:
            # No solution: negation succeeds
            self.negation_succeeded = True
            self.state = OperatorState.NEG_RESULT

    if self.state == OperatorState.NEG_RESULT:
        self.state = OperatorState.DONE
        return self.env  # Yield original environment

    raise StopIteration  # DONE
```

---

## Migration Strategy

### Phase 1: Complete OperatorFrame Implementation

**Tasks**:
1. Implement `OperatorState` enum in `execution_frames.py`
2. Enhance `OperatorFrame` with state machine fields
3. Implement `step()` methods for conjunction, disjunction, negation
4. Add cut exception handling logic

**Testing**:
- Unit tests for each operator in isolation
- Test cases: `test_operator_frame_conjunction`, `test_operator_frame_disjunction`, `test_operator_frame_negation`

### Phase 2: Enhance execute_iterative()

**Tasks**:
1. Add operator detection logic (classify `Functor` by name)
2. Push appropriate `OperatorFrame` for operators
3. Ensure existing atomic goal handling remains functional

**Testing**:
- Integration tests: simple conjunction/disjunction queries via `execute_iterative()`
- Verify equivalence with current behavior

### Phase 3: Replace _execute_body_direct

**Tasks**:
1. Replace recursive implementation with delegation:
   ```python
   def _execute_body_direct(self, body, env):
       yield from self.runtime.execute_iterative(body, env)
   ```
2. Add `use_iterative_execution` flag check (already present in `solve_goal_direct`)

**Testing**:
- Run full test suite (532 tests)
- Focus on: deep recursion tests, backtracking, cut, negation
- Compare results with legacy path (if available)

### Phase 4: Validate and Clean Up

**Tasks**:
1. Run benchmark tests to verify no RecursionError at depth 200+
2. Profile performance (ensure no significant regression)
3. Remove or quarantine legacy recursive code
4. Update documentation

**Testing**:
- Performance benchmarks: depth 500, 1000 queries
- Memory profiling: ensure no excessive environment copying
- Edge cases: cut in nested contexts, negation with disjunction

---

## Risks & Mitigations

### Risk 1: Cut Semantics Break

**Description**: Cut (`!`) must prevent backtracking to earlier choice points. Incorrect handling in iterative stack can cause semantic divergence.

**Mitigation**:
- Add explicit "cut barrier" tracking in `ExecutionState`
- Test cut in all contexts: conjunction, disjunction, negation
- Reference test: `test_cut_in_nested_context`

### Risk 2: Environment Isolation in Branches

**Description**: Disjunction branches must not share bindings. Conjunction must thread environments correctly.

**Mitigation**:
- Each `OperatorFrame` captures `env` at initialization
- Conjunction: right goal receives left solution environment
- Disjunction: both branches use original `env`
- Test: `test_disjunction_environment_isolation`

### Risk 3: Negation as Failure Edge Cases

**Description**: Negation must:
1. Not propagate cut outside its scope
2. Fail if inner goal succeeds
3. Succeed if inner goal fails

**Mitigation**:
- Wrap inner goal execution in try/except for `CutException`
- Test negation with cut inside: `\+(a, !, fail)`
- Test negation success/failure: `\+(fail)`, `\+(true)`

### Risk 4: Performance Regression

**Description**: Frame allocation and iterator creation overhead may slow execution.

**Mitigation**:
- Profile before/after on representative queries
- Optimize hot paths (e.g., inline atomic goal detection)
- Use `__slots__` in Frame classes to reduce memory
- Accept minor overhead for correctness (heap-limited depth > stack-limited depth)

### Risk 5: Incomplete Migration

**Description**: Other recursive paths may still hit limits (e.g., term unification, conjunction flattening).

**Mitigation**:
- Identify all recursive hot paths via profiling
- Prioritize `_execute_body_direct` (highest depth consumption)
- Document remaining limits in design docs
- Add iterative unification if needed (future work)

---

## Implementation Order Summary

1. **OperatorFrame state machine** (1-2 days)
   - Implement `OperatorState`, enhance `OperatorFrame`
   - Unit tests for each operator
2. **execute_iterative() integration** (1 day)
   - Add operator classification and frame dispatch
   - Integration tests
3. **_execute_body_direct replacement** (1 day)
   - Replace recursive calls with delegation
   - Run full test suite
4. **Validation and cleanup** (1 day)
   - Benchmarks, profiling, documentation
   - Remove legacy code

**Total estimated effort**: 4-5 days

---

## Success Criteria

- [ ] No RecursionError at depth 500+ (benchmark test)
- [ ] All 532 existing tests pass
- [ ] Cut semantics preserved (verified by targeted tests)
- [ ] Negation semantics preserved (verified by targeted tests)
- [ ] Disjunction backtracking works correctly
- [ ] Performance within 20% of current implementation
- [ ] Code review approved by maintainer

---

## References

- **Current code**: `pyprolog/runtime/logic_interpreter.py:983-1021`
- **Frame infrastructure**: `pyprolog/runtime/execution_frames.py`
- **Design review**: `.claude/docs/research/recursion-error-solutions-review-2026-02-04.md`
- **Existing iterative engine**: `interpreter.execute_iterative()` (lines 880+)

---

**Next Steps**: Begin Phase 1 (OperatorFrame implementation) upon approval.
