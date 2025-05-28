# Prologインタープリター テスト概要設計書（旧版）

> **注意**: このファイルは分割されました。新しい構造については [test_design/README.md](./test_design/README.md) を参照してください。

## 1. システム概要

本システムは、Python実装のPrologインタープリターです。以下の主要コンポーネントで構成されています：

### 主要コンポーネント
- **Parser & Scanner**: Prologソースコードの字句解析・構文解析
- **Core Types**: Prologの基本データ型（Term, Variable, Atom, Number等）
- **Operator Registry**: 演算子の統合管理システム
- **Runtime**: 統合実行エンジン
- **Math & Logic Interpreters**: 算術・論理演算の専門評価器
- **CLI**: REPL機能を含むコマンドラインインターface

## 2. テスト戦略

### 2.1 テストレベル
- **単体テスト**: 各モジュール・クラスの個別機能
- **統合テスト**: モジュール間の連携動作
- **システムテスト**: エンドツーエンドの実行フロー
- **受け入れテスト**: 実際のPrologプログラムの実行検証

### 2.2 テスト観点
- **機能性**: 基本的なProlog機能の正確性
- **互換性**: 標準Prologとの互換性
- **パフォーマンス**: 実行速度・メモリ使用量
- **エラーハンドリング**: 例外処理・エラーメッセージ
- **拡張性**: 新しい演算子・述語の追加

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

## 4. テストデータ

### 4.1 基本テストケース
- 単純なファクトとルール
- 算術・比較演算
- リスト操作
- 再帰処理

### 4.2 複雑なテストケース
- 既存のPrologプログラム（冒険ゲーム、パズル）
- エラーケース
- エッジケース

### 4.3 パフォーマンステストケース
- 大量データ処理
- 深い再帰
- 複雑な単一化

## 5. テスト実行環境

### 5.1 必要なツール
- **pytest**: テストフレームワーク
- **pytest-cov**: カバレッジ測定
- **pytest-benchmark**: パフォーマンス測定
- **pytest-mock**: モッキング

### 5.2 設定ファイル
- `pytest.ini`: pytest設定
- `conftest.py`: 共通フィクスチャ
- `.coveragerc`: カバレッジ設定

## 6. テスト品質指標

### 6.1 カバレッジ目標
- **行カバレッジ**: 90%以上
- **分岐カバレッジ**: 85%以上
- **関数カバレッジ**: 95%以上

### 6.2 実行時間目標
- 単体テスト: 各テストクラス < 1秒
- 統合テスト: 各テストクラス < 5秒
- システムテスト: 全体 < 30秒

## 7. 継続的テスト

### 7.1 自動化
- GitHub Actions での自動テスト実行
- プルリクエスト時の必須テスト
- 毎日のパフォーマンステスト

### 7.2 レポーティング
- カバレッジレポート
- パフォーマンストレンド
- 失敗テストの詳細ログ

## 8. テスト実装の優先順位

### Phase 1: 基盤テスト
1. Core Types テスト
2. Parser & Scanner テスト
3. Operator Registry テスト

### Phase 2: 実行エンジンテスト
1. Math Interpreter テスト
2. Logic Interpreter テスト
3. Runtime テスト

### Phase 3: 統合・システムテスト
1. 統合テスト
2. REPL テスト
3. 実用プログラムテスト

### Phase 4: 品質・パフォーマンステスト
1. エラーハンドリングテスト
2. パフォーマンステスト
3. ストレステスト

この設計書に基づいて、段階的にテストコードを実装していくことで、品質の高いPrologインタープリターを保証できます。