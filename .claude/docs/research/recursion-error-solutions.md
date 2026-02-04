# RecursionError Solutions for Prolog Interpreter

**Date:** 2026-02-04
**Context:** Python Prolog interpreter failing with RecursionError at depth ~175-200 in `_execute_body_direct()`

## Problem Summary

The method `_execute_body_direct()` recursively handles:
1. Conjunction (,/2): left goal then right goal
2. Disjunction (;/2): try left, backtrack to right
3. Negation (\+/1): negation as failure

Stack trace shows: `_execute_body_direct()` → `_execute_body_direct()` (recursive)

## Solution Approaches (ranked by feasibility)

### 1. Increase Recursion Limit (Band-aid)
- **Description:** Increase `sys.setrecursionlimit()` to a higher value (e.g., 5000 or 10000).
- **Implementation Complexity:** Very Low (1 line of code).
- **Performance Impact:** Negligible overhead, but increases memory usage per deep recursion.
- **Risks:** Delays the crash rather than preventing it. Can lead to hard segmentation faults (C-stack overflow) if set too high.
- **Feasibility:** Immediate temporary fix.

### 2. Flatten Conjunctions & Tail-Call Optimization (Partial Logic Fix)
- **Description:** Detect chains of conjunctions `(A, (B, (C, ...)))` and flatten them into a list `[A, B, C, ...]`. Then, execute this list using a manual loop that simulates tail recursion optimization for the "rest of the goals".
- **Implementation Complexity:** Medium. Requires changing the parser or `_execute_body_direct` to flatten terms, and writing a custom looper for the list.
- **Performance Impact:** Positive. Reduces stack depth from O(N) to O(1) for simple conjunction chains.
- **Risks:** Only fixes recursion caused by *conjunctions*. Does not fix deep recursion caused by actual logical rule depth (e.g., `ancestor` rules).

### 3. Trampoline / Stack of Iterators (Robust Fix)
- **Description:** Refactor the interpreter to use an explicit heap-allocated stack of generators/iterators instead of the Python call stack.
- **Implementation Complexity:** High. Requires rewriting the core `_execute_body_direct` to yield "continuation" objects or "tasks" instead of recursively calling `yield from`.
- **Performance Impact:** Mixed. Slower per-step due to object creation/management overhead, but enables infinite recursion depth (limited only by heap memory).
- **Risks:** Significant rewrite of the core logic engine. Harder to debug than standard stack traces.

## Recommended Approach: Stack of Iterators (Approach 3)

**Why this is best for Python Prolog interpreter:**

For a proper Prolog interpreter, you must manage your own stack. The current `_execute_body_direct` fails at depth ~175-200. While flattening conjunctions (Approach 2) addresses common cases, deep rule recursion (e.g., `ancestor` rules) still causes issues. Approach 3 is the correct software engineering solution.

**High-Level Implementation Steps:**

1. **Define `Frame` class:**
   ```python
   @dataclass
   class Frame:
       goals: list
       env: BindingEnvironment
       generator: Iterator
   ```

2. **Main Loop:**
   ```python
   stack = [InitialFrame(query)]
   while stack:
       frame = stack[-1]
       try:
           # Advance current frame's generator
           next_step = next(frame.generator)
           if isinstance(next_step, Call):
               # Push new frame for subgoal
               stack.append(Frame(next_step.goal, next_step.env))
           elif isinstance(next_step, Result):
               # Yield result, maybe pop frame?
               yield next_step.env
       except StopIteration:
           stack.pop()
   ```

3. **Refactor `_execute_body_direct`:**
   - Instead of recursive `yield from` calls
   - Yield continuation objects (`Call`, `Result`)
   - Let main loop manage stack

4. **Test incrementally:**
   - Start with simple queries
   - Gradually test deeper recursion
   - Validate backtracking still works

**Expected Depth Improvement:**

- Current: ~175-200 depth limit (Python call stack)
- After: Unlimited depth (heap-limited only)
- Practical: 10,000+ depth should work without issues

## Alternative: Quick Fix with Approach 1

If immediate unblocking is needed:

```python
import sys
sys.setrecursionlimit(5000)  # Add to interpreter initialization
```

This provides temporary relief but should be followed by Approach 3 for production use.

## References

- **General Technique:** "Trampolining" in Python generators
- **Prolog Implementation:** Warren Abstract Machine (WAM) uses explicit stacks for environments and choice points
- **Python Specifics:** `yield from` allows delegation but consumes stack. Explicit stack of iterators prevents this.
  - [Python Generator Trampoline](https://legacy.python.org/workshops/1997-10/proceedings/savnik/run.html)
  - [Recursion to Iteration in Python](https://stackoverflow.com/questions/13591970/does-python-optimize-tail-recursion)

## Implementation Notes

- **Approach 1** can be added immediately to `pyprolog/runtime/interpreter.py`
- **Approach 3** requires refactoring `pyprolog/runtime/logic_interpreter.py`
- Consider creating a feature branch for Approach 3 implementation
- Maintain comprehensive test coverage during refactoring
