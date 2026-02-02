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

## ⚠️ Critical Implementation Concerns (Codex Review)

### 1. 🚨 CRITICAL: `seen` Set Implementation
- **Problem**: Using structural equality (`__eq__`/`__hash__`) will cause cycle detection to **fail or trigger recursion**
- **Solution**: Use **identity-based** only: `id(term)`
- **Current code**: ✅ Already uses `id(term)` (lines 36, 47)

### 2. ⚠️ HIGH: `seen` Check Timing
- **Problem**: Must check `seen` **after dereferencing**, not before
- **Reason**: Bound variables → compound/list transitions are missed otherwise
- **Correct order**:
  1. Dereference first
  2. Check if target variable
  3. Check `seen` (after deref)
  4. Expand children

### 3. ⚠️ MEDIUM: `ListTerm.tail` Edge Cases
- **Problem**: Tail can be variable, improper list, or circular reference
- **Solution**: Always push tail to stack (even if variable)
- **Current code**: Line 125-126 already handles this ✅

**Implementation Strategy** (from Codex consultation):

```python
def _occurs_check(
    self,
    var: Variable,
    term: PrologType,
    env: BindingEnvironment,
    seen: Optional[Set[int]] = None,
) -> bool:
    """
    Iterative occurs check using explicit stack (DFS).

    CRITICAL: Correct order is:
    1. Dereference first
    2. Check if target variable
    3. Check seen (AFTER deref)
    4. Expand children
    """
    if seen is None:
        seen = set()

    stack: list[PrologType] = [term]
    deref = self.dereference  # Local binding optimization

    while stack:
        # Step 1: Dereference FIRST
        current = deref(stack.pop(), env)

        # Step 2: Check if target variable (early return)
        if isinstance(current, Variable):
            if current == var:
                return True
            continue

        # Step 3 & 4: Check seen AFTER deref, then expand
        if isinstance(current, Term):
            term_id = id(current)  # Identity-based (not structural equality)
            if term_id in seen:
                continue
            seen.add(term_id)
            # Push in reverse order to maintain DFS order similar to recursion
            for i in range(len(current.args) - 1, -1, -1):
                stack.append(current.args[i])
            continue

        if isinstance(current, ListTerm):
            term_id = id(current)  # Identity-based (not structural equality)
            if term_id in seen:
                continue
            seen.add(term_id)
            # Push tail first (processed last), then elements in reverse
            # IMPORTANT: Always push tail, even if None (handles edge cases)
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

### Phase 1: Core Fix (30 min)
- [ ] Replace `_occurs_check()` with iterative version
- [ ] Verify correct order: deref → target check → seen check → expand
- [ ] Ensure `seen` uses `id()` only (identity-based)
- [ ] Run existing test suite to verify correctness
- [ ] Specifically test `benchmark(1000)` to confirm fix

### Phase 2: Edge Case Testing (15-30 min)
- [ ] Add circular structure test: `X = f(X)` must fail occurs check
- [ ] Test improper lists: `[1, 2 | 3]`
- [ ] Test deeply nested structures: `f(f(f(...)))`
- [ ] Verify performance is equivalent or better

### Phase 3: Deep Structure Validation (15-30 min)
- [ ] Test with deeper structures (benchmark(2000), benchmark(5000))
- [ ] Check memory usage doesn't increase significantly
- [ ] Confirm no RecursionError in any scenario

### Phase 4: Documentation (Optional)
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

- **Gemini Research**: 2026-02-02 (task ab5dea1) - Initial root cause analysis and solution proposal
- **Codex Review**: 2026-02-02 (task ae680f5) - Critical concerns identification and implementation guidance
- **Related Files**:
  - `pyprolog/runtime/logic_interpreter.py` (main file)
  - `pyprolog/core/types.py` (ListTerm definition)
  - `tests/benchmark/primes.pl` (test case)
  - `tests/benchmark/test_benchmarks.py` (benchmark test)

## Next Steps

### Before Implementation
1. ✅ Verify current code uses `id()` for `seen` set (already correct)
2. ✅ Confirm dereference-first order in new implementation (documented above)

### Implementation
3. Implement iterative `_occurs_check()` in `logic_interpreter.py:432-470`
4. Follow strict order: deref → target check → seen check → expand
5. Add docstring explaining the critical ordering

### Testing
6. Run `pytest tests/benchmark/test_benchmarks.py::test_primes_medium` to verify fix
7. Add circular structure test: `X = f(X)` (should fail occurs check)
8. Test improper lists: `[1, 2 | 3]`
9. Run full test suite: `pytest --cov=pyprolog tests`

### Validation
10. Test with deeper structures: benchmark(2000), benchmark(5000)
11. Verify no RecursionError in any scenario
12. Check performance hasn't degraded

### Documentation
13. Document changes in commit message
14. Consider adding benchmark(2000) test to prevent regression

---

## Time Estimate (Codex Review)

| Phase | Time | Note |
|-------|------|------|
| Code transformation only | 30 min | ✓ Realistic |
| + Edge case testing | +15-30 min | Circular structures, improper lists |
| + Deep structure validation | +15-30 min | benchmark(2000), benchmark(5000) |
| **Total (realistic)** | **45-90 min** | With proper testing |

**Status**: Ready for implementation (with critical concerns addressed)
**Estimated effort**: 45-90 minutes (implementation + comprehensive testing)
**Risk**: Low (well-understood transformation, but requires careful attention to deref-first order and identity-based `seen`)
