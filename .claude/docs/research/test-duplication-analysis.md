# Test Duplication Analysis

**Analysis Date:** 2026-02-04
**Source:** `/home/yuichi/projects/prolog_mcp_group/pyprolog/docs/non_benchmark_test_cases.md`
**Analyzer:** Gemini CLI

---

Based on the analysis of `docs/non_benchmark_test_cases.md`, here is the duplication report and consolidation plan.

## Duplication Analysis
- **Total test files:** 43 (excluding disabled/benchmark files)
- **Total test cases:** ~590
- **Duplicate patterns found:** 5 major patterns

The analysis identified significant redundancy where "God-Class" test files (like `test_interpreter.py`) re-verify functionality that is already exhaustively covered by specialized test suites.

## Specific Recommendations

### 1. Decompose `tests/runtime/test_interpreter.py` (Major Redundancy)
This file contains "smoke tests" for features that have since gained their own dedicated test suites.
- **Duplicates:**
    - `test_list_operations` → Covered by `tests/runtime/test_list_operations.py`
    - `test_arithmetic_operations`, `test_built_in_arithmetic` → Covered by `tests/runtime/test_math_interpreter.py`
    - `test_dynamic_predicates` → Covered by `tests/runtime/test_dynamic_predicates.py`
    - `test_built_in_unification` → Covered by `tests/runtime/test_built_in_unification.py`
    - `test_io_operations` → Covered by `tests/runtime/test_io_predicates.py`
- **Consolidation Suggestion:** Remove these specific tests from `test_interpreter.py` and rely on the specialized files. Keep `test_interpreter.py` focused only on high-level integration of the interpreter loop itself.

### 2. Consolidate Dereferencing Logic
Core variable logic is tested in both the `core` unit tests and `runtime` logic tests.
- **Duplicates:**
    - `tests/runtime/test_logic_interpreter.py`: `test_circular_reference_detection`, `test_dereference`, `test_dereference_complex_chain`
    - `tests/core/test_variable_dereferencing.py`: `test_circular_reference_detection`, `test_simple_dereferencing`, `test_chain_dereferencing`
- **Consolidation Suggestion:** Remove the dereferencing mechanism tests from `test_logic_interpreter.py` and treat `tests/core/test_variable_dereferencing.py` as the authoritative source for this logic.

### 3. Unified Medical Diagnosis Testing
The exact same heavy integration scenario is run in multiple places.
- **Duplicates:**
    - `tests/integration/test_end_to_end.py`: `test_medical_diagnosis_japanese`
    - `tests/japanese/test_medical_diagnosis_jp.py`: (Entire suite)
- **Consolidation Suggestion:** Remove the medical diagnosis test case from `test_end_to_end.py`. The specialized `test_medical_diagnosis_jp.py` covers this scenario more comprehensively.

### 4. Single Source for List Membership
- **Duplicates:**
    - `tests/runtime/test_recursive_rules.py`: `test_member_predicate`
    - `tests/runtime/test_list_operations.py`: `test_member_*`
- **Consolidation Suggestion:** Remove `test_member_predicate` from `test_recursive_rules.py`. It is fully covered by the extensive `test_list_operations.py` suite.

### 5. Listing & Export Overlap
- **Duplicates:**
    - `tests/runtime/test_listing_predicates.py`: `test_listing_zero_predicate_basic`
    - `tests/integration/test_listing_export_integration.py`: `test_listing_shows_all_predicates`
- **Consolidation Suggestion:** Merge the unit-level checks from `test_listing_predicates.py` into the integration suite `test_listing_export_integration.py` to avoid testing the same `listing/0` output behavior twice.

## Estimated Reduction
- **Current:** ~590 tests
- **After consolidation:** ~560 tests
- **Reduction:** ~30 tests (5%)
- **Benefit:** Reduced maintenance burden and faster test execution by removing redundant coverage of arithmetic, unification, and list operations.

## Implementation Priority

1. **High Impact:** Decompose `test_interpreter.py` (eliminates most redundancy)
2. **Medium Impact:** Consolidate dereferencing tests
3. **Low Impact (but clean):** Remove duplicate medical diagnosis, member, and listing tests

## Next Steps

- Create PRs for each consolidation pattern
- Verify test coverage remains stable after removals
- Update documentation to reflect new test organization
