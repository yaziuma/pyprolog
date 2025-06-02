# テストスイート構成

## 3. テストスイート構成

### 3.1 Core Types テスト (`tests/core/`)

#### 3.1.1 基本データ型テスト (`test_types.py`)
```python
class TestBasicTypes:
    - test_atom_creation_and_equality()
    - test_variable_creation_and_equality()
    - test_number_creation_and_operations()
    - test_string_creation_and_operations()
    - test_term_creation_and_structure()
    - test_list_term_conversion()
    - test_rule_and_fact_creation()
```

#### 3.1.2 バインディング環境テスト (`test_binding_environment.py`)
```python
class TestBindingEnvironment:
    - test_bind_and_get_value()
    - test_parent_environment_inheritance()
    - test_copy_environment()
    - test_variable_scoping()
    - test_binding_conflicts()
```

#### 3.1.3 マージ・バインディングテスト (`test_merge_bindings.py`)
```python
class TestMergeBindings:
    - test_merge_dictionaries()
    - test_merge_binding_environments()
    - test_mixed_merging()
    - test_conflict_resolution()
    - test_unification_with_bindings()
```

### 3.2 Parser & Scanner テスト (`tests/parser/`)

#### 3.2.1 スキャナーテスト (`test_scanner.py`)
```python
class TestScanner:
    - test_basic_tokens()
    - test_operators_scanning()
    - test_numbers_and_strings()
    - test_variables_and_atoms()
    - test_special_characters()
    - test_comments_handling()
    - test_error_cases()
```

#### 3.2.2 パーサーテスト (`test_parser.py`)
```python
class TestParser:
    - test_parse_atoms_and_variables()
    - test_parse_numbers_and_strings()
    - test_parse_simple_terms()
    - test_parse_complex_terms()
    - test_parse_lists()
    - test_parse_rules_and_facts()
    - test_parse_operators_with_precedence()
    - test_parse_error_handling()
```

### 3.3 Operator Registry テスト (`tests/core/`)

#### 3.3.1 演算子レジストリテスト (`test_operators.py`)
```python
class TestOperatorRegistry:
    - test_builtin_operators_registration()
    - test_operator_precedence()
    - test_operator_associativity()
    - test_operator_types()
    - test_user_defined_operators()
    - test_token_type_mapping()
```

### 3.4 Runtime テスト (`tests/runtime/`)

#### 3.4.1 統合実行エンジンテスト (`test_interpreter.py`)
```python
class TestRuntime:
    - test_basic_fact_queries()
    - test_rule_resolution()
    - test_variable_unification()
    - test_arithmetic_operations()
    - test_comparison_operations()
    - test_logical_operations()
    - test_control_flow()
    - test_io_operations()
    - test_builtin_predicates()
```

#### 3.4.2 論理インタープリターテスト (`test_logic_interpreter.py`)
```python
class TestLogicInterpreter:
    - test_unification_basic()
    - test_unification_complex()
    - test_occurs_check()
    - test_variable_renaming()
    - test_goal_resolution()
    - test_backtracking()
```

#### 3.4.3 数学インタープリターテスト (`test_math_interpreter.py`)
```python
class TestMathInterpreter:
    - test_basic_arithmetic()
    - test_complex_expressions()
    - test_comparison_operations()
    - test_mathematical_functions()
    - test_type_checking()
    - test_error_handling()
```

### 3.5 統合テスト (`tests/integration/`)

#### 3.5.1 エンドツーエンドテスト (`test_end_to_end.py`)
```python
class TestEndToEnd:
    - test_simple_queries()
    - test_complex_queries()
    - test_recursive_rules()
    - test_list_operations()
    - test_cut_operations()
    - test_database_operations()
    - test_file_consultation()
```

### 3.6 システムテスト (`tests/system/`)

#### 3.6.1 実用的なPrologプログラムテスト (`test_real_programs.py`)
```python
class TestRealPrograms:
    - test_adventure_game()    # myadven.prolog
    - test_zebra_puzzle()      # puzzle1.prolog
    - test_general_programs()  # test.prolog
```

#### 3.6.2 REPLテスト (`test_repl.py`)
```python
class TestREPL:
    - test_interactive_queries()
    - test_command_handling()
    - test_error_display()
    - test_variable_display()
    - test_backtracking_interface()
```

### 3.7 パフォーマンステスト (`tests/performance/`)

#### 3.7.1 実行性能テスト (`test_performance.py`)
```python
class TestPerformance:
    - test_large_fact_database()
    - test_deep_recursion()
    - test_complex_unification()
    - test_memory_usage()
    - test_parsing_performance()
```

## 関連文書

- [システム概要とテスト戦略](./01_system_overview_and_strategy.md) - 全体戦略
- [テストデータとテスト実行環境](./03_test_data_and_environment.md) - 環境設定
- [テスト実装の優先順位](./05_implementation_priority.md) - 実装順序