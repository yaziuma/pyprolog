# Iterative Goal Execution Loop - Detailed Design Plan

## 1. Architecture Overview

### Current Architecture (Mutual Recursion)

The current implementation uses mutual recursion between three methods:

```
execute(goal, env)
    ↓
evaluator(args, env)  [for logical operators: ,/2, ;/2, \+/1]
    ↓
_execute_goal_sequence(goals, env)  [for conjunction]
    ↓
execute(goal, env)  [cycle repeats]
```

**Key characteristics:**
- Each method uses Python generators (`yield from`, `for ... yield`)
- Recursion naturally handles backtracking through generator exhaustion
- Cut exception propagation relies on call stack unwinding
- Stack depth scales with query complexity

### New Architecture (Explicit Stack)

Convert to iterative approach with explicit stack management:

```
execute_iterative(goal, env)
    ↓
main_loop with unified_stack: List[Frame]
    ↓
Frame dispatch (GoalFrame | GoalSeqFrame | OperatorFrame)
    ↓
yield results, no recursion
```

**Key characteristics:**
- Single execution loop with explicit stack of frames
- Each frame type encapsulates execution state
- Backtracking through frame manipulation
- Stack depth bounded by goal complexity, not Python recursion

### Key Differences and Benefits

| Aspect | Recursive | Iterative |
|--------|-----------|-----------|
| **Call stack** | Python recursion | Explicit data structure |
| **Backtracking** | Generator exhaustion + exception | Frame state management |
| **Debugging** | Deep call traces | Inspectable frame stack |
| **Cut handling** | Exception propagation | Frame stack manipulation |
| **Performance** | Function call overhead | Direct state transitions |
| **Maintainability** | Logic spread across methods | Centralized in main loop |

**Benefits:**
1. **Explicit control flow** - All execution state visible in frame stack
2. **Easier debugging** - Can inspect/log frame stack at any point
3. **Performance potential** - Eliminates recursive function call overhead
4. **Scalability** - No Python recursion depth limits
5. **Testability** - Can test frame transitions independently

---

## 2. Data Structures

### 2.1 Frame Base Class

```python
from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Iterator, Optional, List
from enum import Enum, auto

class FrameType(Enum):
    """Frame type discriminator for pattern matching."""
    GOAL = auto()
    GOAL_SEQ = auto()
    OPERATOR = auto()
    CHOICE_POINT = auto()

@dataclass
class Frame(ABC):
    """Base class for execution stack frames."""
    frame_type: FrameType
    env: BindingEnvironment

    @abstractmethod
    def step(self, interpreter: 'Interpreter') -> Optional[BindingEnvironment]:
        """Execute one step of this frame. Returns env on success, None to pop frame."""
        pass

    @abstractmethod
    def can_backtrack(self) -> bool:
        """Check if this frame has more alternatives to try."""
        pass
```

### 2.2 GoalFrame - Individual Goal Execution

```python
@dataclass
class GoalFrame(Frame):
    """Frame for executing a single goal.

    Encapsulates:
    - The goal to execute
    - Iterator over solutions
    - Current solution binding environment
    """
    frame_type: FrameType = FrameType.GOAL
    goal: PrologType = None
    solutions: Optional[Iterator[BindingEnvironment]] = None

    def step(self, interpreter: 'Interpreter') -> Optional[BindingEnvironment]:
        """Get next solution from goal execution."""
        if self.solutions is None:
            # First call: initialize solutions iterator
            self.solutions = interpreter._execute_single_goal(self.goal, self.env)

        try:
            next_env = next(self.solutions)
            return next_env
        except StopIteration:
            return None  # Signal to pop this frame

    def can_backtrack(self) -> bool:
        """Check if goal has more solutions."""
        return self.solutions is not None
```

### 2.3 GoalSeqFrame - Goal Sequence Execution

```python
@dataclass
class GoalSeqFrame(Frame):
    """Frame for executing a sequence of goals (conjunction).

    Tracks:
    - Remaining goals to execute
    - Current goal index
    - Whether sequence completion should yield result
    """
    frame_type: FrameType = FrameType.GOAL_SEQ
    goals: List[PrologType] = None
    current_index: int = 0

    def step(self, interpreter: 'Interpreter') -> Optional[BindingEnvironment]:
        """Process goal sequence.

        Returns:
        - None: Need to push next goal frame (not done yet)
        - env: Sequence complete, yield this environment
        """
        if self.current_index >= len(self.goals):
            # All goals succeeded
            return self.env

        # Need to execute next goal
        return None  # Signals: push GoalFrame for goals[current_index]

    def advance(self, result_env: BindingEnvironment):
        """Advance to next goal after current goal succeeded."""
        self.env = result_env
        self.current_index += 1

    def can_backtrack(self) -> bool:
        """Goal sequences don't backtrack themselves; child goals do."""
        return False
```

### 2.4 OperatorFrame - Logical Operator Execution

```python
@dataclass
class OperatorFrame(Frame):
    """Frame for logical operators (,/2, ;/2, \+/1).

    Handles:
    - Conjunction (,): Flattened into GoalSeqFrame
    - Disjunction (;): Two alternative branches
    - Negation (\+): Success on failure check
    """
    frame_type: FrameType = FrameType.OPERATOR
    operator: str = None
    args: List[PrologType] = None
    state: str = "initial"  # "initial", "left", "right", "done"
    left_tried: bool = False

    def step(self, interpreter: 'Interpreter') -> Optional[BindingEnvironment]:
        """Execute operator-specific logic."""
        if self.operator == ",":
            # Conjunction: should be flattened to GoalSeqFrame
            # This is a fallback/transition case
            goals = interpreter._flatten_conjunction(
                Term(Atom(","), self.args)
            )
            return None  # Signal: replace with GoalSeqFrame(goals)

        elif self.operator == ";":
            # Disjunction: try left, then right
            if self.state == "initial":
                self.state = "left"
                return None  # Signal: push left goal
            elif self.state == "left":
                # Left branch exhausted, try right
                self.state = "right"
                return None  # Signal: push right goal
            else:
                return None  # Both branches exhausted, pop frame

        elif self.operator == "\\+":
            # Negation: succeed if goal fails
            if self.state == "initial":
                self.state = "checking"
                return None  # Signal: push goal to check failure
            else:
                # Goal failed, negation succeeds
                return self.env

        return None

    def can_backtrack(self) -> bool:
        """Disjunction can backtrack between branches."""
        return self.operator == ";" and self.state == "left"
```

### 2.5 ChoicePoint - Backtracking Support

```python
@dataclass
class ChoicePoint:
    """Checkpoint for backtracking.

    Records:
    - Stack state before a choice
    - Alternative to try on backtracking
    """
    stack_depth: int
    alternative_frame: Frame

    def restore(self, stack: List[Frame]):
        """Restore stack to choice point and push alternative."""
        # Truncate stack to checkpoint
        while len(stack) > self.stack_depth:
            stack.pop()
        # Push alternative frame
        stack.append(self.alternative_frame)
```

### 2.6 Unified Execution Stack

```python
@dataclass
class ExecutionState:
    """Complete execution state for iterative loop.

    Contains:
    - Main execution stack
    - Choice point stack (for backtracking)
    - Cut barrier (for !/0 handling)
    """
    stack: List[Frame]
    choice_points: List[ChoicePoint]
    cut_barrier: Optional[int] = None  # Stack depth at cut

    def push_goal(self, goal: PrologType, env: BindingEnvironment):
        """Push a new goal frame."""
        self.stack.append(GoalFrame(env=env, goal=goal))

    def push_goal_sequence(self, goals: List[PrologType], env: BindingEnvironment):
        """Push a goal sequence frame."""
        if not goals:
            # Empty sequence: immediately yield env
            return env
        self.stack.append(GoalSeqFrame(env=env, goals=goals, current_index=0))
        return None

    def push_choice_point(self, alternative: Frame):
        """Record a backtracking choice point."""
        cp = ChoicePoint(
            stack_depth=len(self.stack),
            alternative_frame=alternative
        )
        self.choice_points.append(cp)

    def backtrack(self) -> bool:
        """Backtrack to most recent choice point.

        Returns:
            True if backtracking successful, False if no more choice points.
        """
        if not self.choice_points:
            return False

        cp = self.choice_points.pop()
        cp.restore(self.stack)
        return True

    def apply_cut(self):
        """Apply cut: remove choice points up to barrier."""
        if self.cut_barrier is not None:
            # Remove choice points above cut barrier
            self.choice_points = [
                cp for cp in self.choice_points
                if cp.stack_depth < self.cut_barrier
            ]
```

---

## 3. Implementation Strategy

### Phase 1: Data Structure Definition

**Objective:** Define all frame types without changing existing execution logic.

**Steps:**
1. Add frame classes to `pyprolog/runtime/execution_frames.py` (new file)
2. Add `ExecutionState` class
3. Write unit tests for frame creation and basic operations
4. Ensure no integration with existing interpreter yet

**Deliverables:**
- `execution_frames.py` with all frame types
- Unit tests: `tests/runtime/test_execution_frames.py`
- Documentation: Frame purpose and usage patterns

**Success criteria:**
- All frame unit tests pass
- No changes to `interpreter.py` yet
- Frame transitions testable in isolation

---

### Phase 2: Iterative execute_iterative() Implementation

**Objective:** Create new iterative execution method alongside existing recursive one.

**Steps:**
1. Add `execute_iterative(goal, env)` method to `Interpreter`
2. Implement main execution loop with frame dispatch
3. Handle simple goals (facts, rules) via `_execute_single_goal()`
4. Convert logical operators to frame-based execution
5. Implement backtracking through `ExecutionState`

**Key implementation:**

```python
def execute_iterative(
    self, goal: PrologType, env: BindingEnvironment
) -> Iterator[BindingEnvironment]:
    """Iterative goal execution using explicit stack.

    Replaces mutual recursion between execute/evaluator/_execute_goal_sequence.
    """
    state = ExecutionState(stack=[], choice_points=[])
    state.push_goal(goal, env)

    while state.stack:
        frame = state.stack[-1]

        try:
            result = frame.step(self)

            if result is None:
                # Frame needs more work or should be popped
                if not frame.can_backtrack():
                    state.stack.pop()
                continue

            # Frame produced a result
            if isinstance(frame, GoalSeqFrame):
                # Goal in sequence succeeded, advance
                frame.advance(result)
                # Push next goal if not done
                if frame.current_index < len(frame.goals):
                    next_goal = frame.goals[frame.current_index]
                    state.push_goal(next_goal, result)
                else:
                    # Sequence complete
                    yield result
                    state.stack.pop()

            elif isinstance(frame, GoalFrame):
                # Single goal succeeded
                yield result
                # Frame stays on stack for backtracking

            else:
                # Operator or other frame
                yield result

        except CutException:
            # Handle cut: remove choice points
            state.apply_cut()
            raise

        except StopIteration:
            # Frame exhausted, try backtracking
            if not state.backtrack():
                state.stack.pop()
```

**Deliverables:**
- `execute_iterative()` method in `Interpreter`
- Helper method `_execute_single_goal()` for atomic goals
- Integration tests comparing `execute()` vs `execute_iterative()` results

**Success criteria:**
- Basic queries work with `execute_iterative()`
- Simple conjunctions/disjunctions produce same results as `execute()`
- No existing tests broken (they still use `execute()`)

---

### Phase 3: Full Integration and Migration

**Objective:** Make `execute_iterative()` the primary execution method.

**Steps:**
1. Create feature flag: `use_iterative_execution` (default: False)
2. Update all internal calls to respect feature flag
3. Run full test suite with flag enabled
4. Fix any discrepancies in behavior
5. Benchmark performance comparison
6. Flip flag default to True
7. Remove old `execute()` method after validation period

**Migration approach:**
- **Incremental:** Feature flag allows gradual rollout
- **Validation:** Both methods available during transition
- **Rollback:** Can disable flag if issues found

**Backward compatibility:**
- External API unchanged (`execute()` name preserved)
- Internal refactoring only
- All 589 tests must pass unchanged

**Deliverables:**
- Feature flag system
- Performance benchmarks (before/after)
- Migration validation report
- Final cleanup of old recursive code

**Success criteria:**
- All 589 tests pass with iterative execution
- benchmark(1000) shows acceptable performance (≥95% of baseline)
- No regressions in cut/fail/backtracking behavior

---

## 4. Risk Assessment

### 4.1 Generator Compatibility Risks

**Risk:** Iterative approach might not preserve generator semantics correctly.

**Specific concerns:**
- Lazy evaluation of solutions (only compute when pulled)
- Proper StopIteration propagation
- Memory efficiency (don't materialize all solutions)

**Mitigation:**
- Frame `step()` methods return single result, not list
- Main loop yields immediately, doesn't accumulate
- Unit tests verify lazy evaluation (e.g., infinite goal sequences)
- Test: Generator that produces 1000 solutions but only pull 10

**Validation tests:**
```python
def test_lazy_evaluation():
    """Verify solutions computed on demand."""
    # Goal that produces infinite solutions
    runtime.consult_string("num(0). num(N) :- num(M), N is M + 1.")

    solutions = []
    gen = runtime.execute_iterative(parse("num(X)"), env)

    # Pull only 5 solutions
    for i, env in enumerate(gen):
        solutions.append(env)
        if i >= 4:
            break

    assert len(solutions) == 5  # Should not compute more
```

---

### 4.2 Backtracking Correctness Risks

**Risk:** Frame-based backtracking might not match recursive generator backtracking.

**Specific concerns:**
- Choice point management (when to create, when to remove)
- Environment restoration on backtracking
- Multiple backtrack points in complex queries

**Mitigation:**
- Explicit `ChoicePoint` stack separate from execution stack
- Store environment snapshots at choice points
- Test complex backtracking scenarios extensively
- Compare trace logs between recursive and iterative

**Validation tests:**
```python
def test_complex_backtracking():
    """Test multiple choice points and backtracking."""
    runtime.consult_string("""
        path(a, b).
        path(b, c).
        path(c, d).
        path(b, e).
        path(e, f).
        connected(X, Y) :- path(X, Y).
        connected(X, Y) :- path(X, Z), connected(Z, Y).
    """)

    # Should find all paths from a to any node
    results_recursive = list(runtime.execute(parse("connected(a, X)"), env))
    results_iterative = list(runtime.execute_iterative(parse("connected(a, X)"), env))

    assert len(results_recursive) == len(results_iterative)
    # Note: Order might differ, so compare sets
    assert set(results_recursive) == set(results_iterative)
```

---

### 4.3 Cut/Fail/Builtin Operator Risks

**Risk:** Cut (!) semantics are complex and must remove choice points correctly.

**Specific concerns:**
- Cut barrier placement (which choice points to remove)
- Cut in nested conjunctions
- Cut interaction with disjunction
- Fail forcing backtracking

**Mitigation:**
- `ExecutionState.cut_barrier` tracks stack depth at cut context
- `apply_cut()` removes only choice points above barrier
- Extensive tests for cut in various contexts
- Compare behavior with SWI-Prolog reference

**Validation tests:**
```python
def test_cut_in_disjunction():
    """Test cut within disjunction branches."""
    runtime.consult_string("""
        test(1) :- !.
        test(2).
        disjunction_cut(X) :- (test(X), ! ; test(X)).
    """)

    # Should only return X=1 (cut prevents test(2))
    results = list(runtime.execute_iterative(parse("disjunction_cut(X)"), env))
    assert len(results) == 1
    assert results[0].get_binding("X") == 1

def test_cut_in_nested_conjunction():
    """Test cut behavior in nested goals."""
    runtime.consult_string("""
        a(1). a(2).
        b(3). b(4).
        test(X, Y) :- a(X), !, b(Y).
    """)

    # Cut after a(1) should prevent trying a(2)
    # But should still backtrack through b(Y)
    results = list(runtime.execute_iterative(parse("test(X, Y)"), env))
    assert len(results) == 2  # (1,3) and (1,4)
    assert all(env.get_binding("X") == 1 for env in results)
```

---

### 4.4 Performance Regression Risks

**Risk:** Iterative approach might be slower due to frame overhead.

**Specific concerns:**
- Frame object creation/destruction cost
- Stack manipulation overhead
- More complex dispatch logic

**Mitigation:**
- Use `@dataclass` with `slots=True` for frames (memory efficiency)
- Minimize frame allocations (reuse where possible)
- Profile before/after with `cProfile`
- Optimize hot paths identified by profiling

**Performance targets:**
- benchmark(1000): ≥95% of current performance
- Simple query overhead: <5% increase
- Complex query (deep backtracking): ±10% acceptable

**Monitoring:**
```python
def benchmark_comparison():
    """Compare recursive vs iterative performance."""
    query = parse("benchmark(1000)")

    # Recursive
    start = time.perf_counter()
    list(runtime.execute(query, env))
    recursive_time = time.perf_counter() - start

    # Iterative
    start = time.perf_counter()
    list(runtime.execute_iterative(query, env))
    iterative_time = time.perf_counter() - start

    ratio = iterative_time / recursive_time
    assert ratio < 1.05, f"Performance regression: {ratio:.2%}"
```

---

## 5. Testing Strategy

### 5.1 Phase 1 Testing (Data Structures)

**Unit tests for frame operations:**

```python
# tests/runtime/test_execution_frames.py

def test_goal_frame_initialization():
    """Test GoalFrame creation and basic properties."""
    goal = parse("member(X, [1,2,3])")
    frame = GoalFrame(env=env, goal=goal)
    assert frame.frame_type == FrameType.GOAL
    assert frame.goal == goal
    assert frame.solutions is None

def test_goal_seq_frame_advancement():
    """Test GoalSeqFrame tracks progress through goals."""
    goals = [parse("a(X)"), parse("b(X)"), parse("c(X)")]
    frame = GoalSeqFrame(env=env, goals=goals, current_index=0)

    assert frame.current_index == 0
    frame.advance(env)
    assert frame.current_index == 1
    frame.advance(env)
    assert frame.current_index == 2

def test_choice_point_restore():
    """Test ChoicePoint stack restoration."""
    stack = [
        GoalFrame(env=env, goal=parse("a")),
        GoalFrame(env=env, goal=parse("b")),
        GoalFrame(env=env, goal=parse("c")),
    ]

    alternative = GoalFrame(env=env, goal=parse("d"))
    cp = ChoicePoint(stack_depth=2, alternative_frame=alternative)

    cp.restore(stack)
    assert len(stack) == 3  # Restored to depth 2, then pushed alternative
    assert stack[-1].goal == parse("d")
```

**Execution:**
```bash
pytest tests/runtime/test_execution_frames.py -v
```

**Success criteria:**
- All frame unit tests pass
- Frame creation, state transitions work correctly
- No dependencies on `Interpreter` class yet

---

### 5.2 Phase 2 Testing (Iterative Execution)

**Integration tests comparing recursive and iterative:**

```python
# tests/runtime/test_iterative_execution.py

@pytest.mark.parametrize("query_str,expected_count", [
    ("member(X, [1,2,3])", 3),
    ("append([1,2], [3,4], X)", 1),
    ("between(1, 5, X)", 5),
])
def test_iterative_matches_recursive(runtime, query_str, expected_count):
    """Verify iterative execution produces same results as recursive."""
    query = parse(query_str)
    env = BindingEnvironment()

    recursive_results = list(runtime.execute(query, env))
    iterative_results = list(runtime.execute_iterative(query, env))

    assert len(recursive_results) == expected_count
    assert len(iterative_results) == expected_count
    assert recursive_results == iterative_results

def test_conjunction_iterative():
    """Test conjunction with iterative execution."""
    runtime.consult_string("""
        a(1). a(2).
        b(3). b(4).
        test(X, Y) :- a(X), b(Y).
    """)

    results = list(runtime.execute_iterative(parse("test(X, Y)"), env))
    assert len(results) == 4  # 2 * 2 combinations

def test_disjunction_iterative():
    """Test disjunction with iterative execution."""
    runtime.consult_string("test(X) :- X = 1 ; X = 2.")

    results = list(runtime.execute_iterative(parse("test(X)"), env))
    assert len(results) == 2
```

**Execution:**
```bash
# Run only iterative tests
pytest tests/runtime/test_iterative_execution.py -v

# Run alongside existing tests (recursive still used)
pytest tests/runtime/ -v
```

**Success criteria:**
- Iterative execution produces identical results to recursive
- All parameterized test cases pass
- Complex queries (conjunction, disjunction, negation) work correctly

---

### 5.3 Phase 3 Testing (Full Migration)

**Full test suite with feature flag:**

```python
# Modify conftest.py to support feature flag
@pytest.fixture
def runtime_iterative():
    """Runtime with iterative execution enabled."""
    runtime = Runtime()
    runtime.interpreter.use_iterative_execution = True
    return runtime

# Run all 589 tests with iterative execution
pytest --use-iterative -v
```

**Performance benchmarking:**

```python
# tests/benchmark/test_iterative_performance.py

def test_benchmark_1000_iterative(runtime_iterative):
    """Verify benchmark(1000) performance acceptable."""
    runtime_iterative.consult_string("""
        benchmark(0).
        benchmark(N) :- N > 0, N1 is N - 1, benchmark(N1).
    """)

    start = time.perf_counter()
    list(runtime_iterative.execute_iterative(parse("benchmark(1000)"), env))
    duration = time.perf_counter() - start

    # Should complete in reasonable time (baseline: ~X seconds)
    assert duration < baseline * 1.05  # Allow 5% overhead
```

**Regression detection:**

```bash
# Run full suite with both modes and compare
pytest --compare-modes -v --tb=short

# Expected output:
# ✓ 589/589 tests pass in recursive mode
# ✓ 589/589 tests pass in iterative mode
# ✓ Results identical for all tests
```

**Success criteria:**
- All 589 tests pass with iterative execution
- benchmark(1000) performance within 5% of baseline
- No behavioral differences between modes
- Memory usage comparable (no leaks)

---

### 5.4 New Tests for Stack-Based Execution

**Tests specific to iterative implementation:**

```python
def test_frame_stack_inspection():
    """Verify frame stack can be inspected during execution."""
    runtime.consult_string("recurse(0). recurse(N) :- N > 0, N1 is N - 1, recurse(N1).")

    # Hook to inspect stack depth
    max_depth = 0
    def stack_hook(state: ExecutionState):
        nonlocal max_depth
        max_depth = max(max_depth, len(state.stack))

    runtime.interpreter.add_execution_hook(stack_hook)
    list(runtime.execute_iterative(parse("recurse(5)"), env))

    assert max_depth <= 10  # Should be bounded

def test_cut_removes_choice_points():
    """Verify cut correctly removes choice points from stack."""
    runtime.consult_string("""
        test(1) :- !.
        test(2).
    """)

    gen = runtime.execute_iterative(parse("test(X)"), env)
    result1 = next(gen)

    # After cut, no more solutions
    with pytest.raises(StopIteration):
        next(gen)

def test_infinite_generator_termination():
    """Verify infinite generators can be terminated early."""
    runtime.consult_string("infinite(N) :- infinite(M), N is M + 1.")
    runtime.consult_string("infinite(0).")

    gen = runtime.execute_iterative(parse("infinite(X)"), env)

    # Pull just 5 solutions
    solutions = [next(gen) for _ in range(5)]
    assert len(solutions) == 5

    # Generator still alive, can continue
    next(gen)  # Should not raise
```

---

### 5.5 Test Execution Workflow

**Per phase:**

1. **Phase 1:** Unit tests only
   ```bash
   pytest tests/runtime/test_execution_frames.py -v
   ```

2. **Phase 2:** Unit + integration tests
   ```bash
   pytest tests/runtime/test_execution_frames.py tests/runtime/test_iterative_execution.py -v
   ```

3. **Phase 3:** Full suite with feature flag
   ```bash
   # With flag disabled (baseline)
   pytest tests/ -v

   # With flag enabled (validation)
   pytest tests/ -v --use-iterative

   # Comparison mode
   pytest tests/ -v --compare-modes
   ```

**Continuous validation:**
- Run benchmark suite after each phase
- Compare memory usage (valgrind, tracemalloc)
- Profile hot paths (cProfile)
- Check test coverage (should remain ≥80%)

---

## Summary

This design converts the current mutual recursion pattern to an explicit stack-based iterative approach:

1. **Data structures** provide clear execution state representation
2. **Incremental migration** allows validation at each step
3. **Risk mitigation** addresses generator semantics, backtracking, cut, and performance
4. **Comprehensive testing** ensures correctness and prevents regressions

The iterative approach offers better debuggability, explicit control flow, and eliminates Python recursion depth limits while maintaining full compatibility with existing tests and behavior.
