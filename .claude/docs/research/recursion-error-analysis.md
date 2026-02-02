# RecursionError Analysis for pyprolog Interpreter

**Date**: 2026-02-02
**Status**: Root cause identified, solution proposed

## Problem Statement

pyprolog interpreter hits Python's recursion limit during `benchmark(1000)` test:
- Error occurs in `logic_interpreter.py` in `_occurs_check()` method
- Sieve of Eratosthenes algorithm (primes.pl) triggers deep recursion
- Python default recursion limit: ~1000 frames

## Root Cause Analysis

### Current Implementation (Recursive)

**File**: `pyprolog/runtime/logic_interpreter.py:432-470`

```python
def _occurs_check(
    self,
    var: Variable,
    term: PrologType,
    env: BindingEnvironment,
    seen: Optional[Set[int]] = None,
) -> bool:
    if seen is None:
        seen = set()

    term_deref = self.dereference(term, env)

    if isinstance(term_deref, Variable):
        return var == term_deref

    if isinstance(term_deref, Term):
        term_id = id(term_deref)
        if term_id in seen:
            return False
        seen.add(term_id)

        for arg in term_deref.args:
            if self._occurs_check(var, arg, env, seen):  # ← RECURSION
                return True
        return False

    if isinstance(term_deref, ListTerm):
        term_id = id(term_deref)
        if term_id in seen:
            return False
        seen.add(term_id)

        for element in term_deref.elements:
            if self._occurs_check(var, element, env, seen):  # ← RECURSION
                return True
        if term_deref.tail is not None:
            return self._occurs_check(var, term_deref.tail, env, seen)  # ← RECURSION

    return False
```

**Recursion points:**
1. Line 454: `Term.args` recursion
2. Line 465: `ListTerm.elements` recursion
3. Line 468: `ListTerm.tail` recursion

### Why RecursionError Occurs

- `benchmark(1000)` creates deep list structures during Sieve of Eratosthenes
- Each recursive call consumes one Python stack frame
- Python recursion limit (~1000) is exceeded for large N
- `dereference()` is already iterative (line 472), but `_occurs_check()` is not

## Solutions (Prioritized)

### ✅ Solution 1: Convert to Iterative with Explicit Stack (RECOMMENDED)

**Approach**: Replace recursion with DFS using explicit stack

**Benefits:**
- No recursion limit issues
- Same time complexity O(n)
- Minimal memory overhead
- Preserves existing logic

**Implementation Strategy** (from Codex consultation):

```python
def _occurs_check(
    self,
    var: Variable,
    term: PrologType,
    env: BindingEnvironment,
    seen: Optional[Set[int]] = None,
) -> bool:
    if seen is None:
        seen = set()

    stack: list[PrologType] = [term]
    deref = self.dereference  # Local binding optimization

    while stack:
        current = deref(stack.pop(), env)

        if isinstance(current, Variable):
            if current == var:
                return True
            continue

        if isinstance(current, Term):
            term_id = id(current)
            if term_id in seen:
                continue
            seen.add(term_id)
            # Push in reverse order to maintain DFS order similar to recursion
            for i in range(len(current.args) - 1, -1, -1):
                stack.append(current.args[i])
            continue

        if isinstance(current, ListTerm):
            term_id = id(current)
            if term_id in seen:
                continue
            seen.add(term_id)
            # Push tail first (processed last), then elements in reverse
            if current.tail is not None:
                stack.append(current.tail)
            for i in range(len(current.elements) - 1, -1, -1):
                stack.append(current.elements[i])
            continue

    return False
```

**Key Design Decisions:**
1. **LIFO Stack (not Queue)**: DFS matches recursive behavior, minimal memory
2. **Seen set preserved**: Same cycle detection mechanism
3. **Early return**: Return True immediately when var found
4. **Local binding**: `deref = self.dereference` reduces lookup overhead

### ❌ Solution 2: Increase sys.setrecursionlimit() (NOT RECOMMENDED)

**Why not:**
- Band-aid solution, not root fix
- Deeper structures will still fail
- Risk of actual stack overflow on C level
- Production systems should not rely on this

**Only acceptable for:**
- Temporary debugging
- Quick workaround while implementing iterative solution

### 🔧 Additional Optimizations

1. **Local method binding**: Cache `self.dereference` in local variable
2. **Type check optimization**: Consider using `match` statement (Python 3.10+)
3. **ListTerm tail optimization**: For long tail chains, could use separate while loop (low priority)

## Implementation Plan

### Phase 1: Core Fix
- [ ] Replace `_occurs_check()` with iterative version
- [ ] Run existing test suite to verify correctness
- [ ] Specifically test `benchmark(1000)` to confirm fix

### Phase 2: Validation
- [ ] Test with deeper structures (benchmark(2000), benchmark(5000))
- [ ] Verify performance is equivalent or better
- [ ] Check memory usage doesn't increase significantly

### Phase 3: Documentation
- [ ] Add comments explaining iterative approach
- [ ] Document why recursion was removed
- [ ] Update any related documentation

## Trade-offs Analysis

| Aspect | Recursive | Iterative |
|--------|-----------|-----------|
| Code readability | High | Medium |
| Stack safety | Low (1000 limit) | High (heap limited) |
| Performance | Baseline | Slightly better (no call overhead) |
| Memory usage | Stack frames | Explicit stack (heap) |
| Maintainability | High | Medium |

**Recommendation**: Iterative wins on stack safety, which is critical for production use.

## References

- **Codex Consultation**: 2026-02-02 (task be98233)
- **Related Files**:
  - `pyprolog/runtime/logic_interpreter.py` (main file)
  - `pyprolog/core/types.py` (ListTerm definition)
  - `tests/benchmark/primes.pl` (test case)
  - `tests/benchmark/test_benchmarks.py` (benchmark test)

## Next Steps

1. Implement iterative `_occurs_check()` in `logic_interpreter.py`
2. Run `pytest tests/benchmark/test_benchmarks.py::test_benchmark_1000` to verify
3. Run full test suite: `pytest --cov=pyprolog tests`
4. Document changes in commit message
5. Consider adding benchmark(2000) test to prevent regression

---

**Status**: Ready for implementation
**Estimated effort**: 30 minutes (implementation + testing)
**Risk**: Low (well-understood transformation, existing tests validate correctness)
