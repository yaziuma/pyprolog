# PyProlog Test Suite Overview

This document provides a comprehensive overview of the test suite for the PyProlog project, detailing the purpose and scope of each test file.

## Test Suite Optimization Status

**Recent Consolidations (2025-09-14):**
- **Eliminated duplicate tests**: Reduced from 51 to 49 test files (4% reduction)  
- **Unified exception testing**: `test_read_line_exception.py` → `test_exception_propagation.py`
- **Unified medical diagnosis tests**: `test_final_english.py` → `test_fixed_medical.py`
- **Code reduction**: ~400 lines of duplicate test code eliminated
- **Maintained full coverage**: All original test functionality preserved

## `tests/core`

This directory contains tests for the core data structures and fundamental mechanisms of the Prolog interpreter.

- **`test_binding_environment.py`**: Verifies the functionality of the `BindingEnvironment` class, which manages variable bindings. It tests variable scoping, shadowing, inheritance from parent environments, and environment copying.
- **`test_merge_bindings.py`**: Tests the `merge_bindings` utility function, which is crucial for combining different sets of variable bindings. It covers merging dictionaries, `BindingEnvironment` objects, and handling conflicts.
- **`test_new_operators.py`**: Specifically tests the newly introduced non-equality operators `<>` and `!=`, ensuring they work correctly for different data types and in various contexts.
- **`test_operators.py`**: Validates the `OperatorRegistry`, ensuring that built-in operators have the correct precedence, associativity, and type. It also tests the registration of user-defined operators.
- **`test_types.py`**: Checks the creation, equality, and representation of core Prolog data types like `Atom`, `Variable`, `Number`, `String`, `Term`, `ListTerm`, `Rule`, and `Fact`.
- **`test_variable_dereferencing.py`**: Focuses on the mechanism of dereferencing variables, which is the process of following a chain of variable bindings to find the final value. It includes tests for simple and chained dereferencing, circular reference detection, and handling of complex terms.

## `tests/parser`

Tests for the lexical and syntactical analysis of Prolog code.

- **`test_scanner.py`**: Tests the `Scanner` (lexical analyzer), which converts source code into a stream of tokens. It verifies the correct identification of operators, numbers, strings, variables, atoms, and handles special characters and comments, including support for Japanese characters.
- **`test_parser.py`**: Tests the `Parser` (syntax analyzer), which builds abstract syntax trees (ASTs) from tokens. It ensures that facts, rules, complex terms, lists, and expressions with operators are parsed correctly, including those with Japanese functors and atoms.

## `tests/runtime`

This directory contains tests for the Prolog runtime engine, covering the execution of predicates, I/O operations, and other runtime behaviors.

- **`test_arithmetic_edge_cases.py`**: Focuses on boundary conditions for arithmetic operations, such as large numbers, floating-point precision, infinity, NaN, and division by zero.
- **`test_built_in_unification.py`**: Tests the built-in unification and non-unification predicates, primarily `\=/2`.
- **`test_dynamic_predicates.py`**: Verifies the functionality of dynamic predicates like `asserta/1` and `assertz/1`, which allow for modifying the knowledge base at runtime.
- **`test_enhanced_runtime.py`**: Tests the `EnhancedRuntime`, a subclass of the standard `Runtime` that includes additional debugging and tracing capabilities.
- **`test_exception_propagation.py`**: **[UNIFIED]** Comprehensive tests ensuring that exceptions raised during I/O predicate execution are correctly propagated up the call stack. Uses a mock `InteractiveIOManager` to verify exception behavior in direct, nested, and deeply nested calls for both `get_char` and `read_line`. Includes mixed I/O operation testing and reverse-order execution patterns. **Previously consolidated from `test_read_line_exception.py`**.
- **`test_export_facts.py`**: Tests the `export_facts/2` predicate, which allows exporting facts from the knowledge base to formats like CSV, JSON, and TSV.
- **`test_interpreter.py`**: A major integration test for the `Runtime` class, verifying the end-to-end execution of queries, including fact resolution, rule application, arithmetic, comparisons, and various built-in predicates.
- **`test_io_infrastructure.py`**: Tests the basic I/O infrastructure, including `StringStream` for in-memory I/O and the `IOManager` for stream management.
- **`test_io_predicates.py`**: Focuses on the I/O predicates `get_char/1` and `read_line/1`, testing their behavior with different inputs and in various modes (inspection vs. generation) using `StringStream`.
- **`test_list_operations.py`**: Tests the built-in list manipulation predicates, specifically `member/2` and `append/3`, in various modes (generation, inspection, splitting).
- **`test_listing_predicates.py`**: Verifies the `listing/0` and `listing/1` predicates, which are used to display the currently loaded rules and facts in the knowledge base.
- **`test_logic_interpreter.py`**: Tests the core `LogicInterpreter`, focusing on the unification algorithm (`unify`), variable renaming, goal resolution, and backtracking mechanisms.
- **`test_math_interpreter.py`**: Tests the `MathInterpreter`, which evaluates arithmetic expressions. It covers basic arithmetic, comparisons, mathematical functions, and bitwise operations.
- **`test_meta_predicates.py`**: Tests meta-predicates like `findall/3`, which collect all solutions for a given goal.
- **`test_multiple_input.py`**: An integration test for a sample program (`multiple_input_calculator.pl`) that requires multiple user inputs, testing the robustness of input handling loops.
- **`test_peek_char.py`**: Tests the `peek_char/1` and `at_end_of_stream/0` predicates, which allow for non-destructive inspection of input streams.
- **`test_recursive_rules.py`**: Tests the runtime's ability to handle recursive rules, such as those for calculating ancestry or Peano arithmetic. It also includes tests for left-recursion.

## `tests/integration`

These tests verify the interaction and collaboration of multiple components of the system in end-to-end scenarios.

- **`test_end_to_end.py`**: A placeholder for comprehensive end-to-end tests. It includes a working test for a Japanese medical diagnosis knowledge base, demonstrating the system's ability to handle a complex, real-world-like program.
- **`test_fixed_medical.py`**: **[UNIFIED]** Comprehensive medical diagnosis system tests using both direct rule addition (`add_rule`) and file-based KB loading approaches. Tests core functionality, English KB parsing, and diagnosis logic execution. **Previously consolidated from `test_final_english.py`**.
- **`test_listing_export_integration.py`**: An integration test that verifies the consistency and combined functionality of the `listing` and `export_facts` predicates.

## `tests/unified_input`

This directory is dedicated to testing the new "Unified Input System", a major architectural refactoring for handling all forms of input.

- **`test_io_predicate_base.py`**: Tests the abstract base class `IOPredicate`, which uses a template method pattern to standardize the implementation of I/O predicates.
- **`test_unified_input_system.py`**: Unit tests for the `UnifiedInputSystem` and `ThreadingController` classes, which are the core of the new input architecture. It covers mode switching, handler routing, and thread management.
- **`test_io_manager_integration.py`**: Tests the integration of the `UnifiedInputSystem` with the existing `IOManager`, ensuring backward compatibility of old APIs and the correct functioning of new ones.
- **`test_integration.py`**: The final integration test for the entire unified input system, verifying that `IOPredicate`, `UnifiedInputSystem`, and `IOManager` work together correctly, including in multi-threaded ("true continuation") scenarios.

## Other Tests

- **`tests/conftest.py`**: Contains shared fixtures, helper functions, and configurations for the pytest framework, although it appears to be structured for general testing, not just pytest.
- **`tests/test_japanese_functor_support.py`**: An integration test suite specifically designed to validate the complete lifecycle of Japanese functor support, from mapping (`FunctorMapper`) through scanning, parsing, and runtime execution.
- **`tests/japanese/test_medical_diagnosis_jp.py`**: A detailed test suite for a Japanese medical diagnosis knowledge base, checking the correctness of various facts, rules, and queries. It has some overlap with the test in `test_end_to_end.py`.
- **`tests/tools/...`**: Contains tests for the high-level tools built on top of the runtime.
  - **`test_explain_tool.py`**: Tests the `ExplainTool` for explaining query execution traces.
  - **`test_search_tool.py`**: Tests the `SearchTool` for searching rules and facts in the knowledge base.
  - **`test_validate_tool.py`**: Tests the `ValidateTool` for static analysis of the Prolog code.
- **`tests/util/test_functor_mapper.py`**: Unit tests for the `FunctorMapper` class, which handles the mapping of non-ASCII (e.g., Japanese) identifiers to a safe internal format.
- **`tests/validation/...`**: Contains tests for the static validation components.
  - **`test_analyzers.py`**: Tests the individual analysis modules (`ConflictAnalyzer`, `ReachabilityAnalyzer`, `UndefinedAnalyzer`).
  - **`test_validation_result.py`**: Tests the data structures used to store and summarize validation results (`ValidationResult`, `ValidationIssue`).
