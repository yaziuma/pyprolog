# ベンチマーク以外のテストケース分析

## 対象外
- tests/benchmark/ 配下（ベンチマーク）
- tests/benchmark_guardrails/ 配下（ベンチマーク関連ガードレール）

## テストケース一覧

### tests/core/test_binding_environment.py

| テストケース | テストのファイルパス | 確認内容 |
| --- | --- | --- |
| `test_bind_and_get_value` | `tests/core/test_binding_environment.py` | 基本的な束縛と値取得のテスト |
| `test_parent_environment_inheritance` | `tests/core/test_binding_environment.py` | 親環境からの継承テスト |
| `test_variable_shadowing` | `tests/core/test_binding_environment.py` | 変数のシャドウイングテスト |
| `test_copy_environment` | `tests/core/test_binding_environment.py` | 環境のコピーテスト |
| `test_copy_with_parent_environment` | `tests/core/test_binding_environment.py` | 親環境を持つ環境のコピーテスト |
| `test_variable_scoping` | `tests/core/test_binding_environment.py` | 変数スコープのテスト |
| `test_binding_conflicts` | `tests/core/test_binding_environment.py` | 束縛の競合テスト |
| `test_term_binding` | `tests/core/test_binding_environment.py` | Term型の束縛テスト |
| `test_variable_to_variable_binding` | `tests/core/test_binding_environment.py` | 変数から変数への束縛テスト |
| `test_empty_environment` | `tests/core/test_binding_environment.py` | 空の環境のテスト |
| `test_environment_representation` | `tests/core/test_binding_environment.py` | 環境の文字列表現テスト |

### tests/core/test_merge_bindings.py

| テストケース | テストのファイルパス | 確認内容 |
| --- | --- | --- |
| `test_merge_dictionaries` | `tests/core/test_merge_bindings.py` | 辞書同士のマージテスト |
| `test_merge_conflicting_dictionaries` | `tests/core/test_merge_bindings.py` | 競合する辞書のマージテスト |
| `test_merge_variable_with_concrete_value` | `tests/core/test_merge_bindings.py` | 変数と具体値の競合テスト |
| `test_merge_binding_environments` | `tests/core/test_merge_bindings.py` | BindingEnvironment同士のマージテスト |
| `test_merge_dict_with_binding_environment` | `tests/core/test_merge_bindings.py` | 辞書とBindingEnvironmentのマージテスト |
| `test_merge_with_none` | `tests/core/test_merge_bindings.py` | Noneとのマージテスト |
| `test_conflict_resolution` | `tests/core/test_merge_bindings.py` | 競合解決のテスト |
| `test_mixed_merging` | `tests/core/test_merge_bindings.py` | 混合データ型のマージテスト |
| `test_bindings_to_dict` | `tests/core/test_merge_bindings.py` | BindingEnvironmentから辞書への変換テスト |
| `test_dict_to_binding_environment` | `tests/core/test_merge_bindings.py` | 辞書からBindingEnvironmentへの変換テスト |
| `test_empty_bindings_conversion` | `tests/core/test_merge_bindings.py` | 空のバインディングの変換テスト |
| `test_nested_environment_conversion` | `tests/core/test_merge_bindings.py` | ネストした環境の変換テスト |
| `test_apply_substitution_with_dict` | `tests/core/test_merge_bindings.py` | 辞書による置換適用テスト |
| `test_apply_substitution_with_binding_environment` | `tests/core/test_merge_bindings.py` | BindingEnvironmentによる置換適用テスト |
| `test_apply_substitution_complex_terms` | `tests/core/test_merge_bindings.py` | 複雑な項への置換適用テスト |

### tests/core/test_new_operators.py

| テストケース | テストのファイルパス | 確認内容 |
| --- | --- | --- |
| `test_not_equal_operator_different_atoms` | `tests/core/test_new_operators.py` | <> 演算子：異なるアトムで成功 |
| `test_not_equal_operator_same_atoms` | `tests/core/test_new_operators.py` | <> 演算子：同じアトムで失敗 |
| `test_not_equal_operator_different_numbers` | `tests/core/test_new_operators.py` | <> 演算子：異なる数値で成功 |
| `test_not_equal_operator_same_numbers` | `tests/core/test_new_operators.py` | <> 演算子：同じ数値で失敗 |
| `test_not_equal_alt_operator_different_atoms` | `tests/core/test_new_operators.py` | != 演算子：異なるアトムで成功 |
| `test_not_equal_alt_operator_same_atoms` | `tests/core/test_new_operators.py` | != 演算子：同じアトムで失敗 |
| `test_not_equal_alt_operator_different_numbers` | `tests/core/test_new_operators.py` | != 演算子：異なる数値で成功 |
| `test_not_equal_alt_operator_same_numbers` | `tests/core/test_new_operators.py` | != 演算子：同じ数値で失敗 |
| `test_not_equal_mixed_types` | `tests/core/test_new_operators.py` | <> 演算子：異なる型で成功 |
| `test_not_equal_alt_mixed_types` | `tests/core/test_new_operators.py` | != 演算子：異なる型で成功 |
| `test_comparison_with_traditional_operator` | `tests/core/test_new_operators.py` | 従来の \= 演算子との比較 |
| `test_rule_with_new_operators` | `tests/core/test_new_operators.py` | ルール内での新しい演算子の使用 |
| `test_rule_with_alt_operator` | `tests/core/test_new_operators.py` | ルール内での != 演算子の使用 |
| `test_compound_expressions` | `tests/core/test_new_operators.py` | 複合式での新しい演算子の使用 |

### tests/core/test_operators.py

| テストケース | テストのファイルパス | 確認内容 |
| --- | --- | --- |
| `test_builtin_operators_registration` | `tests/core/test_operators.py` | 組み込み演算子の登録テスト |
| `test_operator_precedence` | `tests/core/test_operators.py` | 演算子優先度のテスト |
| `test_operator_associativity` | `tests/core/test_operators.py` | 演算子結合性のテスト |
| `test_operator_types` | `tests/core/test_operators.py` | 演算子タイプのテスト |
| `test_user_defined_operators` | `tests/core/test_operators.py` | ユーザー定義演算子のテスト |
| `test_token_type_mapping` | `tests/core/test_operators.py` | トークンタイプマッピングのテスト |
| `test_operators_by_type` | `tests/core/test_operators.py` | タイプ別演算子取得のテスト |
| `test_operators_by_precedence` | `tests/core/test_operators.py` | 優先度別演算子取得のテスト |
| `test_operator_arity` | `tests/core/test_operators.py` | 演算子のアリティテスト |
| `test_operator_symbols_sorted` | `tests/core/test_operators.py` | 演算子記号のソート取得テスト |
| `test_singleton_pattern` | `tests/core/test_operators.py` | シングルトンパターンのテスト |
| `test_operator_info_validation` | `tests/core/test_operators.py` | OperatorInfo の検証テスト |
| `test_nonexistent_operator` | `tests/core/test_operators.py` | 存在しない演算子のテスト |
| `test_io_operators` | `tests/core/test_operators.py` | 入出力演算子のテスト |

### tests/core/test_types.py

| テストケース | テストのファイルパス | 確認内容 |
| --- | --- | --- |
| `test_atom_creation_and_equality` | `tests/core/test_types.py` | Atomの作成と等価性テスト |
| `test_variable_creation_and_equality` | `tests/core/test_types.py` | Variableの作成と等価性テスト |
| `test_number_creation_and_operations` | `tests/core/test_types.py` | Numberの作成と操作テスト |
| `test_string_creation_and_operations` | `tests/core/test_types.py` | Stringの作成と操作テスト |
| `test_term_creation_and_structure` | `tests/core/test_types.py` | Termの作成と構造テスト |
| `test_list_term_conversion` | `tests/core/test_types.py` | ListTermの変換テスト |
| `test_rule_and_fact_creation` | `tests/core/test_types.py` | RuleとFactの作成テスト |
| `test_empty_list_representation` | `tests/core/test_types.py` | 空リストの表現テスト |
| `test_simple_list_representation` | `tests/core/test_types.py` | 単純なリストの表現テスト |
| `test_tail_list_representation` | `tests/core/test_types.py` | テール付きリストの表現テスト |
| `test_nested_list_representation` | `tests/core/test_types.py` | ネストしたリストの表現テスト |
| `test_list_equality` | `tests/core/test_types.py` | リストの等価性テスト |
| `test_list_hashing` | `tests/core/test_types.py` | リストのハッシュテスト |
| `test_nested_terms` | `tests/core/test_types.py` | ネストしたTermのテスト |
| `test_mixed_data_types` | `tests/core/test_types.py` | 混合データ型のテスト |
| `test_rule_with_complex_body` | `tests/core/test_types.py` | 複雑なボディを持つRuleのテスト |

### tests/core/test_variable_dereferencing.py

| テストケース | テストのファイルパス | 確認内容 |
| --- | --- | --- |
| `test_simple_dereferencing` | `tests/core/test_variable_dereferencing.py` | 単純な間接参照のテスト |
| `test_chain_dereferencing` | `tests/core/test_variable_dereferencing.py` | チェーン間接参照のテスト |
| `test_circular_reference_detection` | `tests/core/test_variable_dereferencing.py` | 循環参照の検出テスト |
| `test_partial_dereferencing` | `tests/core/test_variable_dereferencing.py` | 部分的間接参照のテスト |
| `test_complex_term_dereferencing` | `tests/core/test_variable_dereferencing.py` | 複雑な項の間接参照テスト |
| `test_multi_level_chain` | `tests/core/test_variable_dereferencing.py` | 多段階チェーンのテスト |
| `test_mixed_type_dereferencing` | `tests/core/test_variable_dereferencing.py` | 混合型の間接参照テスト |
| `test_unbound_variable_handling` | `tests/core/test_variable_dereferencing.py` | 未束縛変数の処理テスト |
| `test_self_reference` | `tests/core/test_variable_dereferencing.py` | 自己参照のテスト |
| `test_dereferencing_with_occurs_check` | `tests/core/test_variable_dereferencing.py` | 発生チェック付き間接参照のテスト |
| `test_nested_variable_chains` | `tests/core/test_variable_dereferencing.py` | ネストした変数チェーンのテスト |
| `test_dereferencing_performance` | `tests/core/test_variable_dereferencing.py` | 間接参照の性能テスト |
| `test_dereferencing_in_list_context` | `tests/core/test_variable_dereferencing.py` | リストコンテキストでの間接参照テスト |
| `test_environment_isolation` | `tests/core/test_variable_dereferencing.py` | 環境分離での間接参照テスト |
| `test_binding_update_dereferencing` | `tests/core/test_variable_dereferencing.py` | 束縛更新時の間接参照テスト |

### tests/integration/test_end_to_end.py

| テストケース | テストのファイルパス | 確認内容 |
| --- | --- | --- |
| `test_simple_queries` | `tests/integration/test_end_to_end.py` | 単純なクエリのテスト |
| `test_complex_queries` | `tests/integration/test_end_to_end.py` | 複雑なクエリのテスト |
| `test_recursive_rules` | `tests/integration/test_end_to_end.py` | 再帰ルールのテスト |
| `test_arithmetic_integration` | `tests/integration/test_end_to_end.py` | 算術演算の統合テスト |
| `test_list_operations` | `tests/integration/test_end_to_end.py` | リスト操作の統合テスト |
| `test_cut_behavior` | `tests/integration/test_end_to_end.py` | カットの動作テスト |
| `test_negation_as_failure` | `tests/integration/test_end_to_end.py` | 失敗による否定のテスト |
| `test_variable_scoping` | `tests/integration/test_end_to_end.py` | 変数スコープのテスト |
| `test_complex_unification` | `tests/integration/test_end_to_end.py` | 複雑な単一化のテスト |
| `test_meta_predicates` | `tests/integration/test_end_to_end.py` | メタ述語のテスト |
| `test_error_recovery` | `tests/integration/test_end_to_end.py` | エラー回復のテスト |
| `test_performance_basic` | `tests/integration/test_end_to_end.py` | 基本的なパフォーマンステスト |
| `test_memory_management_integration` | `tests/integration/test_end_to_end.py` | メモリ管理の統合テスト |
| `test_parser_integration` | `tests/integration/test_end_to_end.py` | パーサー統合のテスト |
| `test_runtime_state_management` | `tests/integration/test_end_to_end.py` | ランタイム状態管理のテスト |
| `test_comprehensive_scenario` | `tests/integration/test_end_to_end.py` | 包括的なシナリオテスト |
| `test_query_parsing` | `tests/integration/test_end_to_end.py` | クエリ解析のテスト |
| `test_multiple_solutions` | `tests/integration/test_end_to_end.py` | 複数解のテスト |
| `test_built_in_predicates` | `tests/integration/test_end_to_end.py` | 組み込み述語のテスト |
| `test_constraint_satisfaction` | `tests/integration/test_end_to_end.py` | 制約充足のテスト |
| `test_database_operations` | `tests/integration/test_end_to_end.py` | データベース操作のテスト |
| `test_exception_handling` | `tests/integration/test_end_to_end.py` | 例外処理のテスト |
| `test_module_system` | `tests/integration/test_end_to_end.py` | モジュールシステムのテスト |
| `test_io_operations` | `tests/integration/test_end_to_end.py` | 入出力操作のテスト |
| `test_term_inspection` | `tests/integration/test_end_to_end.py` | 項検査のテスト |
| `test_type_checking_integration` | `tests/integration/test_end_to_end.py` | 型チェック統合のテスト |
| `test_goal_expansion` | `tests/integration/test_end_to_end.py` | ゴール展開のテスト |
| `test_operator_definitions` | `tests/integration/test_end_to_end.py` | 演算子定義のテスト |
| `test_dcg_support` | `tests/integration/test_end_to_end.py` | DCG（文法規則）サポートのテスト |
| `test_debugging_support` | `tests/integration/test_end_to_end.py` | デバッグサポートのテスト |
| `test_profiling_support` | `tests/integration/test_end_to_end.py` | プロファイリングサポートのテスト |
| `test_multi_threading` | `tests/integration/test_end_to_end.py` | マルチスレッドのテスト |
| `test_garbage_collection` | `tests/integration/test_end_to_end.py` | ガベージコレクションのテスト |
| `test_foreign_interface` | `tests/integration/test_end_to_end.py` | 外部インターフェースのテスト |
| `test_serialization` | `tests/integration/test_end_to_end.py` | シリアル化のテスト |
| `test_incremental_compilation` | `tests/integration/test_end_to_end.py` | インクリメンタルコンパイルのテスト |
| `test_optimization` | `tests/integration/test_end_to_end.py` | 最適化のテスト |
| `test_stress_scenarios` | `tests/integration/test_end_to_end.py` | ストレステストシナリオ |
| `test_edge_case_integration` | `tests/integration/test_end_to_end.py` | 境界ケース統合テスト |
| `test_medical_diagnosis_japanese` | `tests/integration/test_end_to_end.py` | 日本語医療診断KBのエンドツーエンドテスト |

### tests/integration/test_fixed_medical.py

| テストケース | テストのファイルパス | 確認内容 |
| --- | --- | --- |
| `test_working_medical_diagnosis` | `tests/integration/test_fixed_medical.py` | Test medical diagnosis using add_rule instead of file loading |
| `test_english_diagnosis_system` | `tests/integration/test_fixed_medical.py` | Test English diagnosis system with file-based KB loading |

### tests/integration/test_listing_export_integration.py

| テストケース | テストのファイルパス | 確認内容 |
| --- | --- | --- |
| `test_listing_shows_all_predicates` | `tests/integration/test_listing_export_integration.py` | listing/0がすべての述語（事実とルール）を表示することを確認 |
| `test_listing_specific_predicates` | `tests/integration/test_listing_export_integration.py` | listing/1で特定の述語のみを表示 |
| `test_export_facts_only_exports_facts` | `tests/integration/test_listing_export_integration.py` | export_facts/2が事実のみをエクスポートし、ルールは除外することを確認 |
| `test_listing_and_export_consistency` | `tests/integration/test_listing_export_integration.py` | listing表示内容とexportの内容に一貫性があることを確認 |
| `test_multiple_predicate_export` | `tests/integration/test_listing_export_integration.py` | 複数の異なる述語の独立したエクスポート |
| `test_listing_after_dynamic_changes` | `tests/integration/test_listing_export_integration.py` | 動的な知識ベース変更後のlisting動作 |
| `test_export_after_dynamic_changes` | `tests/integration/test_listing_export_integration.py` | 動的な知識ベース変更後のexport動作 |
| `test_error_recovery_in_mixed_operations` | `tests/integration/test_listing_export_integration.py` | エラー発生時の回復動作テスト |
| `test_complex_query_integration` | `tests/integration/test_listing_export_integration.py` | 複雑なクエリとの統合テスト |
| `test_japanese_integration` | `tests/integration/test_listing_export_integration.py` | 日本語データとの統合テスト |
| `test_large_knowledge_base_listing` | `tests/integration/test_listing_export_integration.py` | 大規模知識ベースでのlisting性能テスト |
| `test_large_dataset_export` | `tests/integration/test_listing_export_integration.py` | 大規模データセットのexport性能テスト |

### tests/japanese/test_medical_diagnosis_jp.py

| テストケース | テストのファイルパス | 確認内容 |
| --- | --- | --- |
| `test_medical_diagnosis_comprehensive` | `tests/japanese/test_medical_diagnosis_jp.py` | 医療診断システムの包括的統合テスト |
| `test_basic_disease_facts` | `tests/japanese/test_medical_diagnosis_jp.py` | 基本的な疾患ファクトのテスト |
| `test_basic_symptom_facts` | `tests/japanese/test_medical_diagnosis_jp.py` | 基本的な症状ファクトのテスト |
| `test_disease_symptom_relations` | `tests/japanese/test_medical_diagnosis_jp.py` | 疾患と症状の関連性テスト |
| `test_risk_factors` | `tests/japanese/test_medical_diagnosis_jp.py` | リスク要因のテスト |
| `test_age_categories` | `tests/japanese/test_medical_diagnosis_jp.py` | 年齢カテゴリのテスト |
| `test_season_factors` | `tests/japanese/test_medical_diagnosis_jp.py` | 季節要因のテスト |
| `test_recommended_tests` | `tests/japanese/test_medical_diagnosis_jp.py` | 推奨検査のテスト |
| `test_emergency_level_assessment` | `tests/japanese/test_medical_diagnosis_jp.py` | 緊急度評価のテスト |
| `test_symptom_match_score_calculation` | `tests/japanese/test_medical_diagnosis_jp.py` | 症状マッチスコア計算のテスト |
| `test_comprehensive_patient_diagnosis` | `tests/japanese/test_medical_diagnosis_jp.py` | 包括的な患者診断テスト |
| `test_auxiliary_predicates` | `tests/japanese/test_medical_diagnosis_jp.py` | 補助述語のテスト |
| `test_japanese_variable_support` | `tests/japanese/test_medical_diagnosis_jp.py` | 日本語変数名対応のテスト |
| `test_edge_cases_and_error_handling` | `tests/japanese/test_medical_diagnosis_jp.py` | エッジケースとエラーハンドリングのテスト |
| `test_without_knowledge_base` | `tests/japanese/test_medical_diagnosis_jp.py` | 知識ベースなしでの基本動作テスト |
| `test_japanese_atom_parsing` | `tests/japanese/test_medical_diagnosis_jp.py` | 日本語アトムの解析テスト |

### tests/parser/test_parser.py

| テストケース | テストのファイルパス | 確認内容 |
| --- | --- | --- |
| `test_parse_atoms_and_variables` | `tests/parser/test_parser.py` | アトムと変数の解析テスト |
| `test_parse_numbers_and_strings` | `tests/parser/test_parser.py` | 数値と文字列の解析テスト |
| `test_parse_simple_terms` | `tests/parser/test_parser.py` | 単純な項の解析テスト |
| `test_parse_complex_terms` | `tests/parser/test_parser.py` | 複雑な項の解析テスト |
| `test_parse_lists` | `tests/parser/test_parser.py` | リストの解析テスト |
| `test_parse_list_with_tail` | `tests/parser/test_parser.py` | テール付きリストの解析テスト |
| `test_parse_rules_and_facts` | `tests/parser/test_parser.py` | ルールとファクトの解析テスト |
| `test_parse_operators_with_precedence` | `tests/parser/test_parser.py` | 演算子と優先度の解析テスト |
| `test_parse_complex_rule` | `tests/parser/test_parser.py` | 複雑なルールの解析テスト |
| `test_parse_error_handling` | `tests/parser/test_parser.py` | エラーハンドリングのテスト |
| `test_parse_variables_and_atoms_distinction` | `tests/parser/test_parser.py` | 変数とアトムの区別テスト |
| `test_parse_arithmetic_expressions` | `tests/parser/test_parser.py` | 算術式の解析テスト |
| `test_parse_parenthesized_expressions` | `tests/parser/test_parser.py` | 括弧付き式の解析テスト |
| `test_parse_multiple_statements` | `tests/parser/test_parser.py` | 複数文の解析テスト |
| `test_parse_japanese_facts` | `tests/parser/test_parser.py` | 日本語を含むファクトの解析テスト |
| `test_parse_japanese_rules` | `tests/parser/test_parser.py` | 日本語を含むルールの解析テスト |
| `test_parse_japanese_string_as_atom_in_term` | `tests/parser/test_parser.py` | 項内部の日本語文字列（アトムとして）の解析テスト |
| `test_parse_mixed_japanese_english_terms` | `tests/parser/test_parser.py` | 日本語と英語が混在する項の解析テスト |
| `test_parse_conjunction_in_rule_body` | `tests/parser/test_parser.py` | ルールボディのコンジャンクションテスト |
| `test_parse_empty_source` | `tests/parser/test_parser.py` | 空のソースの解析テスト |
| `test_parse_comments_ignored` | `tests/parser/test_parser.py` | コメントが無視されることのテスト |
| `test_parse_whitespace_handling` | `tests/parser/test_parser.py` | 空白文字の処理テスト |

### tests/parser/test_scanner.py

| テストケース | テストのファイルパス | 確認内容 |
| --- | --- | --- |
| `test_basic_tokens` | `tests/parser/test_scanner.py` | 基本トークンのスキャンテスト |
| `test_operators_scanning` | `tests/parser/test_scanner.py` | 演算子のスキャンテスト |
| `test_numbers_and_strings` | `tests/parser/test_scanner.py` | 数値と文字列のスキャンテスト |
| `test_variables_and_atoms` | `tests/parser/test_scanner.py` | 変数とアトムのスキャンテスト |
| `test_special_characters` | `tests/parser/test_scanner.py` | 特殊文字のスキャンテスト |
| `test_comments_handling` | `tests/parser/test_scanner.py` | コメント処理のテスト |
| `test_error_cases` | `tests/parser/test_scanner.py` | エラーケースのテスト |
| `test_keywords_recognition` | `tests/parser/test_scanner.py` | キーワード認識のテスト |
| `test_whitespace_handling` | `tests/parser/test_scanner.py` | 空白処理のテスト |
| `test_line_tracking` | `tests/parser/test_scanner.py` | 行番号追跡のテスト |
| `test_complex_expression` | `tests/parser/test_scanner.py` | 複雑な式のスキャンテスト |
| `test_list_syntax` | `tests/parser/test_scanner.py` | リスト構文のスキャンテスト |
| `test_float_numbers` | `tests/parser/test_scanner.py` | 浮動小数点数のスキャンテスト |
| `test_empty_source` | `tests/parser/test_scanner.py` | 空のソースのテスト |
| `test_multiline_string` | `tests/parser/test_scanner.py` | 複数行文字列のテスト |
| `test_japanese_atoms` | `tests/parser/test_scanner.py` | 日本語アトムのスキャンテスト |
| `test_japanese_string_literals` | `tests/parser/test_scanner.py` | 日本語を含む文字列リテラルのスキャンテスト |
| `test_japanese_variable_like_atoms` | `tests/parser/test_scanner.py` | 日本語の変数のようなアトムのスキャンテスト（通常アトムとして扱われることを期待） |
| `test_mixed_japanese_and_english_atoms` | `tests/parser/test_scanner.py` | 日本語と英語が混在するアトムのスキャンテスト |

### tests/runtime/test_arithmetic_edge_cases.py

| テストケース | テストのファイルパス | 確認内容 |
| --- | --- | --- |
| `test_large_numbers` | `tests/runtime/test_arithmetic_edge_cases.py` | 大きな数値の処理テスト |
| `test_very_small_numbers` | `tests/runtime/test_arithmetic_edge_cases.py` | 非常に小さな数値の処理テスト |
| `test_floating_point_precision` | `tests/runtime/test_arithmetic_edge_cases.py` | 浮動小数点精度のテスト |
| `test_infinity_handling` | `tests/runtime/test_arithmetic_edge_cases.py` | 無限大の処理テスト |
| `test_negative_infinity` | `tests/runtime/test_arithmetic_edge_cases.py` | 負の無限大の処理テスト |
| `test_nan_handling` | `tests/runtime/test_arithmetic_edge_cases.py` | NaNの処理テスト |
| `test_division_by_zero_variants` | `tests/runtime/test_arithmetic_edge_cases.py` | 様々なゼロ除算のテスト |
| `test_overflow_underflow` | `tests/runtime/test_arithmetic_edge_cases.py` | オーバーフロー・アンダーフローのテスト |
| `test_negative_zero` | `tests/runtime/test_arithmetic_edge_cases.py` | 負のゼロの処理テスト |
| `test_special_float_values` | `tests/runtime/test_arithmetic_edge_cases.py` | 特殊な浮動小数点値のテスト |
| `test_precision_loss_in_operations` | `tests/runtime/test_arithmetic_edge_cases.py` | 演算での精度損失のテスト |
| `test_integer_overflow_simulation` | `tests/runtime/test_arithmetic_edge_cases.py` | 整数オーバーフローのシミュレーション |
| `test_complex_precision_scenarios` | `tests/runtime/test_arithmetic_edge_cases.py` | 複雑な精度シナリオのテスト |
| `test_edge_case_modulo` | `tests/runtime/test_arithmetic_edge_cases.py` | モジュロ演算の境界ケース |
| `test_power_operation_edge_cases` | `tests/runtime/test_arithmetic_edge_cases.py` | 指数演算の境界ケース |
| `test_comparison_edge_cases` | `tests/runtime/test_arithmetic_edge_cases.py` | 比較演算の境界ケース |
| `test_variable_with_edge_values` | `tests/runtime/test_arithmetic_edge_cases.py` | 境界値を持つ変数のテスト |
| `test_nested_arithmetic_edge_cases` | `tests/runtime/test_arithmetic_edge_cases.py` | ネストした算術演算の境界ケース |
| `test_type_coercion_edge_cases` | `tests/runtime/test_arithmetic_edge_cases.py` | 型強制の境界ケース |

### tests/runtime/test_built_in_unification.py

| テストケース | テストのファイルパス | 確認内容 |
| --- | --- | --- |
| `test_non_unifiable_atoms` | `tests/runtime/test_built_in_unification.py` | 不同アトム同士は\=/2が成功し、同一アトムは失敗することを確認。 |
| `test_non_unifiable_numbers` | `tests/runtime/test_built_in_unification.py` | 数値の\=/2（同値・異値、1と1.0の扱い）を確認。 |
| `test_non_unifiable_variable_ground` | `tests/runtime/test_built_in_unification.py` | 未束縛変数と具体値の\=/2が失敗することを確認。 |
| `test_non_unifiable_variables_unbound` | `tests/runtime/test_built_in_unification.py` | 未束縛変数同士の\=/2や同一変数の扱いを確認。 |
| `test_non_unifiable_compound_terms_structure` | `tests/runtime/test_built_in_unification.py` | 複合項のファンクタ/アリティ差異で\=/2が成功することを確認。 |
| `test_non_unifiable_compound_terms_args` | `tests/runtime/test_built_in_unification.py` | 複合項の引数差異で\=/2が成功/失敗する条件を確認。 |
| `test_non_unifiable_lists` | `tests/runtime/test_built_in_unification.py` | リスト構造の\=/2の成功/失敗条件を確認。 |
| `test_non_unifiable_with_occurs_check_implication` | `tests/runtime/test_built_in_unification.py` | 発生チェック（X= f(X)）で\=/2が成功することを確認。 |

### tests/runtime/test_clause_indexing.py

| テストケース | テストのファイルパス | 確認内容 |
| --- | --- | --- |
| `test_cut_order_preserved_with_arg0_indexing` | `tests/runtime/test_clause_indexing.py` | arg0インデックス有効時もカットによる探索順が保持されることを確認。 |
| `test_fallback_for_variable_arg0` | `tests/runtime/test_clause_indexing.py` | arg0が変数の場合に全節へフォールバックすることを確認。 |
| `test_secondary_index_preserves_consult_order` | `tests/runtime/test_clause_indexing.py` | 二次インデックスでもconsult順を保つことを確認。 |
| `test_secondary_index_miss_falls_back_to_primary` | `tests/runtime/test_clause_indexing.py` | 二次インデックス不一致時に主インデックスへフォールバックすることを確認。 |

### tests/runtime/test_dynamic_predicates.py

| テストケース | テストのファイルパス | 確認内容 |
| --- | --- | --- |
| `test_asserta_fact` | `tests/runtime/test_dynamic_predicates.py` | asserta/1が事実を先頭に追加し、順序に反映されることを確認。 |
| `test_assertz_fact` | `tests/runtime/test_dynamic_predicates.py` | assertz/1が事実を末尾に追加し、順序に反映されることを確認。 |
| `test_asserta_rule` | `tests/runtime/test_dynamic_predicates.py` | asserta/1で追加したルールが先に適用されることを確認。 |
| `test_assertz_rule` | `tests/runtime/test_dynamic_predicates.py` | assertz/1で追加したルールが後に適用されることを確認。 |
| `test_assert_with_variables` | `tests/runtime/test_dynamic_predicates.py` | 変数を含むアサートで変数スコープが衝突しないことを確認。 |
| `test_assert_uninstantiated_variable` | `tests/runtime/test_dynamic_predicates.py` | 未束縛変数のasserta/assertzがエラー扱いになることを確認。 |
| `test_assert_invalid_clause` | `tests/runtime/test_dynamic_predicates.py` | 不正な節（数値・不正ボディなど）のasserta/assertzが失敗することを確認。 |

### tests/runtime/test_enhanced_runtime.py

| テストケース | テストのファイルパス | 確認内容 |
| --- | --- | --- |
| `test_enhanced_runtime_integration` | `tests/runtime/test_enhanced_runtime.py` | 強化されたランタイムの統合テスト |
| `test_minimal_diagnosis_approach` | `tests/runtime/test_enhanced_runtime.py` | 分析ファイルの提案：段階的デバッグアプローチの実装 |
| `test_initialization` | `tests/runtime/test_enhanced_runtime.py` | 初期化テスト |
| `test_trace_functionality` | `tests/runtime/test_enhanced_runtime.py` | トレース機能のテスト |
| `test_error_handling` | `tests/runtime/test_enhanced_runtime.py` | エラー処理のテスト |
| `test_builtin_predicates` | `tests/runtime/test_enhanced_runtime.py` | 分析ファイルの提案：組み込み述語の個別テスト |
| `test_complex_predicate_calls` | `tests/runtime/test_enhanced_runtime.py` | 分析ファイルの提案：複雑な述語呼び出しパターンのテスト |
| `test_medical_kb_basic` | `tests/runtime/test_enhanced_runtime.py` | 医療KBの基本テスト（実際のKBが存在しない場合はスキップ） |
| `test_enhanced_runtime_inheritance` | `tests/runtime/test_enhanced_runtime.py` | EnhancedRuntimeがRuntimeを正しく継承していることを確認 |
| `test_builtin_predicates_initialization` | `tests/runtime/test_enhanced_runtime.py` | 組み込み述語の初期化テスト |

### tests/runtime/test_exception_propagation.py

| テストケース | テストのファイルパス | 確認内容 |
| --- | --- | --- |
| `test_direct_get_char_exception` | `tests/runtime/test_exception_propagation.py` | 直接get_char述語での例外伝播テスト |
| `test_nested_predicate_exception` | `tests/runtime/test_exception_propagation.py` | ネストされた述語での例外伝播テスト |
| `test_deeper_nesting_exception` | `tests/runtime/test_exception_propagation.py` | より深いネストでの例外伝播テスト |
| `test_direct_read_line_exception` | `tests/runtime/test_exception_propagation.py` | 直接read_line述語での例外伝播テスト |
| `test_nested_read_line_exception` | `tests/runtime/test_exception_propagation.py` | ネストされたread_line述語での例外伝播テスト |
| `test_mixed_io_operations` | `tests/runtime/test_exception_propagation.py` | get_charとread_lineの混合テスト |
| `test_mixed_io_read_line_then_get_char` | `tests/runtime/test_exception_propagation.py` | 混合IOテスト: read_line → get_char |
| `test_deeply_nested_read_line` | `tests/runtime/test_exception_propagation.py` | 深くネストされたread_line述語のテスト |

### tests/runtime/test_execution_frames.py

| テストケース | テストのファイルパス | 確認内容 |
| --- | --- | --- |
| `test_frame_type_values` | `tests/runtime/test_execution_frames.py` | Verify all frame types are defined. |
| `test_goal_frame_initialization` | `tests/runtime/test_execution_frames.py` | Test GoalFrame creation and basic properties. |
| `test_goal_frame_can_backtrack` | `tests/runtime/test_execution_frames.py` | Test can_backtrack returns True when solutions iterator exists. |
| `test_goal_frame_step_returns_none_when_exhausted` | `tests/runtime/test_execution_frames.py` | Test step returns None when solutions exhausted. |
| `test_goal_seq_frame_initialization` | `tests/runtime/test_execution_frames.py` | Test GoalSeqFrame creation. |
| `test_goal_seq_frame_advancement` | `tests/runtime/test_execution_frames.py` | Test GoalSeqFrame tracks progress through goals. |
| `test_goal_seq_frame_step_completion` | `tests/runtime/test_execution_frames.py` | Test step returns env when all goals completed. |
| `test_goal_seq_frame_step_not_done` | `tests/runtime/test_execution_frames.py` | Test step returns None when more goals remain. |
| `test_goal_seq_frame_cannot_backtrack` | `tests/runtime/test_execution_frames.py` | Test goal sequences don't backtrack themselves. |
| `test_operator_frame_initialization` | `tests/runtime/test_execution_frames.py` | Test OperatorFrame creation. |
| `test_disjunction_can_backtrack` | `tests/runtime/test_execution_frames.py` | Test disjunction can backtrack when in left state. |
| `test_conjunction_cannot_backtrack` | `tests/runtime/test_execution_frames.py` | Test conjunction (,) doesn't backtrack at operator level. |
| `test_negation_cannot_backtrack` | `tests/runtime/test_execution_frames.py` | Test negation (\+) doesn't backtrack. |
| `test_choice_point_creation` | `tests/runtime/test_execution_frames.py` | Test ChoicePoint initialization. |
| `test_choice_point_restore` | `tests/runtime/test_execution_frames.py` | Test ChoicePoint stack restoration. |
| `test_choice_point_restore_empty_stack` | `tests/runtime/test_execution_frames.py` | Test restore when stack is deeper than checkpoint. |
| `test_execution_state_initialization` | `tests/runtime/test_execution_frames.py` | Test ExecutionState creation. |
| `test_push_goal` | `tests/runtime/test_execution_frames.py` | Test pushing a goal frame. |
| `test_push_goal_sequence` | `tests/runtime/test_execution_frames.py` | Test pushing a goal sequence frame. |
| `test_push_goal_sequence_empty` | `tests/runtime/test_execution_frames.py` | Test pushing empty goal sequence returns env immediately. |
| `test_push_choice_point` | `tests/runtime/test_execution_frames.py` | Test recording a choice point. |
| `test_backtrack_success` | `tests/runtime/test_execution_frames.py` | Test successful backtracking. |
| `test_backtrack_failure` | `tests/runtime/test_execution_frames.py` | Test backtracking with no choice points. |
| `test_apply_cut` | `tests/runtime/test_execution_frames.py` | Test cut removes choice points above barrier. |
| `test_apply_cut_no_barrier` | `tests/runtime/test_execution_frames.py` | Test cut does nothing when no barrier set. |
| `test_repr` | `tests/runtime/test_execution_frames.py` | Test string representation. |
| `test_goal_seq_with_multiple_goals` | `tests/runtime/test_execution_frames.py` | Test goal sequence frame with multiple goals. |
| `test_execution_state_complex_workflow` | `tests/runtime/test_execution_frames.py` | Test complex execution state workflow. |

### tests/runtime/test_export_facts.py

| テストケース | テストのファイルパス | 確認内容 |
| --- | --- | --- |
| `test_export_facts_csv_basic` | `tests/runtime/test_export_facts.py` | CSV形式での基本的なエクスポートテスト |
| `test_export_facts_json_basic` | `tests/runtime/test_export_facts.py` | JSON形式での基本的なエクスポートテスト |
| `test_export_facts_tsv_basic` | `tests/runtime/test_export_facts.py` | TSV形式での基本的なエクスポートテスト |
| `test_export_facts_only_facts_not_rules` | `tests/runtime/test_export_facts.py` | 事実のみがエクスポートされ、ルールは除外されることのテスト |
| `test_export_facts_nonexistent_predicate` | `tests/runtime/test_export_facts.py` | 存在しない述語を指定した場合のテスト |
| `test_export_facts_invalid_file_path` | `tests/runtime/test_export_facts.py` | 無効なファイルパスでのテスト |
| `test_export_facts_invalid_predicate_format` | `tests/runtime/test_export_facts.py` | 無効な述語指定形式のテスト |
| `test_export_facts_with_japanese_data` | `tests/runtime/test_export_facts.py` | 日本語データを含む事実のエクスポートテスト |
| `test_export_facts_with_complex_terms` | `tests/runtime/test_export_facts.py` | 複雑な項を含む事実のエクスポートテスト |
| `test_export_facts_file_overwrite` | `tests/runtime/test_export_facts.py` | 既存ファイルの上書きテスト |
| `test_export_facts_large_dataset` | `tests/runtime/test_export_facts.py` | 大量データのエクスポートテスト |
| `test_export_facts_unicode_handling` | `tests/runtime/test_export_facts.py` | Unicode文字の処理テスト |

### tests/runtime/test_interpreter.py

| テストケース | テストのファイルパス | 確認内容 |
| --- | --- | --- |
| `test_basic_fact_queries` | `tests/runtime/test_interpreter.py` | 基本的なファクトクエリのテスト |
| `test_rule_resolution` | `tests/runtime/test_interpreter.py` | ルール解決のテスト |
| `test_arithmetic_operations` | `tests/runtime/test_interpreter.py` | 算術演算のテスト |
| `test_comparison_operations` | `tests/runtime/test_interpreter.py` | 比較演算のテスト |
| `test_logical_operations` | `tests/runtime/test_interpreter.py` | 論理演算のテスト |
| `test_control_flow` | `tests/runtime/test_interpreter.py` | 制御フローのテスト |
| `test_builtin_predicates` | `tests/runtime/test_interpreter.py` | 組み込み述語のテスト (write/nl are tested via output, not solution count here) |
| `test_variable_unification` | `tests/runtime/test_interpreter.py` | 変数単一化のテスト |
| `test_recursive_rules` | `tests/runtime/test_interpreter.py` | 再帰ルールのテスト |
| `test_list_operations` | `tests/runtime/test_interpreter.py` | リスト操作のテスト |
| `test_negation_as_failure` | `tests/runtime/test_interpreter.py` | 失敗による否定のテスト |
| `test_cut_behavior` | `tests/runtime/test_interpreter.py` | カットの動作テスト |
| `test_meta_predicates` | `tests/runtime/test_interpreter.py` | メタ述語のテスト |
| `test_dynamic_predicates` | `tests/runtime/test_interpreter.py` | 動的述語のテスト (asserta/assertz/retract) |
| `test_error_handling` | `tests/runtime/test_interpreter.py` | エラーハンドリングのテスト |
| `test_query_parsing` | `tests/runtime/test_interpreter.py` | クエリ解析のテスト |
| `test_multiple_solutions` | `tests/runtime/test_interpreter.py` | 複数解のテスト |
| `test_performance_basic` | `tests/runtime/test_interpreter.py` | 基本性能のテスト |
| `test_memory_management` | `tests/runtime/test_interpreter.py` | メモリ管理のテスト |
| `test_goal_stack_management` | `tests/runtime/test_interpreter.py` | ゴールスタック管理のテスト |
| `test_built_in_arithmetic` | `tests/runtime/test_interpreter.py` | 組み込み算術のテスト |
| `test_built_in_comparison` | `tests/runtime/test_interpreter.py` | 組み込み比較のテスト |
| `test_built_in_unification` | `tests/runtime/test_interpreter.py` | 組み込み単一化のテスト (=, \=, ==, \==) |
| `test_io_operations` | `tests/runtime/test_interpreter.py` | 入出力操作のテスト |
| `test_term_manipulation` | `tests/runtime/test_interpreter.py` | 項操作のテスト (=../2, arg/3, functor/3) |
| `test_type_checking` | `tests/runtime/test_interpreter.py` | 型チェックのテスト (var/1, atom/1, number/1) |
| `test_database_operations` | `tests/runtime/test_interpreter.py` | データベース操作のテスト |
| `test_exception_handling` | `tests/runtime/test_interpreter.py` | 例外処理のテスト |
| `test_module_system` | `tests/runtime/test_interpreter.py` | モジュールシステムのテスト |
| `test_constraint_handling` | `tests/runtime/test_interpreter.py` | 制約処理のテスト |
| `test_tabling_memoization` | `tests/runtime/test_interpreter.py` | 表化・メモ化のテスト |

### tests/runtime/test_io_infrastructure.py

| テストケース | テストのファイルパス | 確認内容 |
| --- | --- | --- |
| `test_string_stream_read` | `tests/runtime/test_io_infrastructure.py` | Test reading characters from StringStream. |
| `test_string_stream_write` | `tests/runtime/test_io_infrastructure.py` | Test writing characters to StringStream's internal buffer. |
| `test_string_stream_write_with_external_buffer` | `tests/runtime/test_io_infrastructure.py` | Test writing to StringStream with an externally provided buffer. |
| `test_string_stream_reset_input` | `tests/runtime/test_io_infrastructure.py` | Test resetting the input string in StringStream. |
| `test_string_stream_clear_output` | `tests/runtime/test_io_infrastructure.py` | Test clearing the output buffer in StringStream. |
| `test_io_manager_default_streams` | `tests/runtime/test_io_infrastructure.py` | Test that IOManager defaults to ConsoleStream for output. |
| `test_io_manager_set_input_handler_and_request_input` | `tests/runtime/test_io_infrastructure.py` | Test request_input with StreamInputHandler. |
| `test_io_manager_write_char` | `tests/runtime/test_io_infrastructure.py` | Test write_char_to_current in IOManager. |
| `test_runtime_has_io_manager` | `tests/runtime/test_io_infrastructure.py` | Test that a Runtime instance has an IOManager. |

### tests/runtime/test_io_predicates.py

| テストケース | テストのファイルパス | 確認内容 |
| --- | --- | --- |
| `test_get_char_variable` | `tests/runtime/test_io_predicates.py` | Test get_char(X) with a variable, X should bind to the character. |
| `test_get_char_multiple_calls` | `tests/runtime/test_io_predicates.py` | Test multiple get_char calls to read sequential characters. |
| `test_get_char_match_atom_success` | `tests/runtime/test_io_predicates.py` | Test get_char(atom) when the next char matches the atom. |
| `test_get_char_mismatch_atom_failure` | `tests/runtime/test_io_predicates.py` | Test get_char(atom) when the next char does not match the atom. |
| `test_get_char_eof` | `tests/runtime/test_io_predicates.py` | Test get_char(X) at end of file, X should bind to 'end_of_file'. |
| `test_get_char_eof_multiple_reads` | `tests/runtime/test_io_predicates.py` | Test that get_char(X) consistently returns 'end_of_file' after EOF is reached. |
| `test_get_char_already_bound_success` | `tests/runtime/test_io_predicates.py` | Test get_char(BoundVar) where BoundVar is already bound to the next char. |
| `test_get_char_already_bound_fail` | `tests/runtime/test_io_predicates.py` | Test get_char(BoundVar) where BoundVar is bound to a different char. |
| `test_read_line_variable` | `tests/runtime/test_io_predicates.py` | Test read_line(X) with a variable, X should bind to the line as a string. |
| `test_read_line_multiple_lines` | `tests/runtime/test_io_predicates.py` | Test reading multiple lines sequentially. |
| `test_read_line_empty_line` | `tests/runtime/test_io_predicates.py` | Test reading an empty line. |
| `test_read_line_without_newline` | `tests/runtime/test_io_predicates.py` | Test reading a line without trailing newline. |
| `test_read_line_eof` | `tests/runtime/test_io_predicates.py` | Test read_line(X) at end of file, X should bind to 'end_of_file'. |
| `test_read_line_match_string_success` | `tests/runtime/test_io_predicates.py` | Test read_line(atom) when the line matches the atom. |
| `test_read_line_match_string_failure` | `tests/runtime/test_io_predicates.py` | Test read_line(atom) when the line does not match the atom. |
| `test_read_line_japanese_characters` | `tests/runtime/test_io_predicates.py` | Test read_line with Japanese characters. |
| `test_read_line_with_spaces` | `tests/runtime/test_io_predicates.py` | Test read_line with leading/trailing spaces. |
| `test_read_line_already_bound_success` | `tests/runtime/test_io_predicates.py` | Test read_line(BoundVar) where BoundVar is already bound to the line. |
| `test_read_line_already_bound_fail` | `tests/runtime/test_io_predicates.py` | Test read_line(BoundVar) where BoundVar is bound to a different line. |

### tests/runtime/test_iterative_execution.py

| テストケース | テストのファイルパス | 確認内容 |
| --- | --- | --- |
| `test_simple_atom_goal` | `tests/runtime/test_iterative_execution.py` | Test executing a simple atom goal. |
| `test_simple_unification` | `tests/runtime/test_iterative_execution.py` | Test simple unification goal. |
| `test_failing_goal` | `tests/runtime/test_iterative_execution.py` | Test that undefined goals raise PrologError. |
| `test_simple_conjunction` | `tests/runtime/test_iterative_execution.py` | Test simple conjunction of two goals. |
| `test_conjunction_with_unification` | `tests/runtime/test_iterative_execution.py` | Test conjunction with unification. |
| `test_conjunction_with_failure` | `tests/runtime/test_iterative_execution.py` | Test conjunction where second goal fails. |
| `test_simple_disjunction` | `tests/runtime/test_iterative_execution.py` | Test simple disjunction. |
| `test_disjunction_left_succeeds` | `tests/runtime/test_iterative_execution.py` | Test disjunction where only left branch succeeds. |
| `test_disjunction_right_succeeds` | `tests/runtime/test_iterative_execution.py` | Test disjunction where only right branch succeeds. |
| `test_negation_of_failure` | `tests/runtime/test_iterative_execution.py` | Test negation of failing goal succeeds. |
| `test_negation_of_success` | `tests/runtime/test_iterative_execution.py` | Test negation of succeeding goal fails. |
| `test_nested_conjunction` | `tests/runtime/test_iterative_execution.py` | Test nested conjunctions. |
| `test_conjunction_and_disjunction` | `tests/runtime/test_iterative_execution.py` | Test combination of conjunction and disjunction. |
| `test_undefined_predicate_raises_error` | `tests/runtime/test_iterative_execution.py` | Test that querying an undefined predicate raises PrologError. |

### tests/runtime/test_list_operations.py

| テストケース | テストのファイルパス | 確認内容 |
| --- | --- | --- |
| `test_member_inspection_mode` | `tests/runtime/test_list_operations.py` | Test member/2 in inspection mode (element is ground). |
| `test_member_generation_mode` | `tests/runtime/test_list_operations.py` | Test member/2 in generation mode (element is a variable). |
| `test_member_list_argument_types` | `tests/runtime/test_list_operations.py` | Test member/2 with various types for the list argument. |
| `test_member_element_and_list_vars` | `tests/runtime/test_list_operations.py` | Test member/2 where elements and list items are variables. |
| `test_member_complex_elements` | `tests/runtime/test_list_operations.py` | Test member/2 with complex terms as elements. |
| `test_append_predicate` | `tests/runtime/test_list_operations.py` | append/3の結合・検査・分解モード、異常系/不正リストの挙動を確認。 |

### tests/runtime/test_listing_predicates.py

| テストケース | テストのファイルパス | 確認内容 |
| --- | --- | --- |
| `test_listing_zero_predicate_basic` | `tests/runtime/test_listing_predicates.py` | listing/0の基本動作テスト |
| `test_listing_one_predicate_person_2` | `tests/runtime/test_listing_predicates.py` | listing/1でperson/2を指定するテスト |
| `test_listing_one_predicate_parent_2` | `tests/runtime/test_listing_predicates.py` | listing/1でparent/2を指定するテスト |
| `test_listing_one_predicate_nonexistent` | `tests/runtime/test_listing_predicates.py` | 存在しない述語を指定した場合のテスト |
| `test_listing_one_predicate_invalid_format` | `tests/runtime/test_listing_predicates.py` | 無効な述語指定形式のテスト |
| `test_listing_empty_knowledge_base` | `tests/runtime/test_listing_predicates.py` | 空の知識ベースでのlisting/0テスト |
| `test_listing_with_japanese_predicates` | `tests/runtime/test_listing_predicates.py` | 日本語述語名でのテスト |
| `test_listing_with_complex_rules` | `tests/runtime/test_listing_predicates.py` | 複雑なルールでのテスト |
| `test_listing_with_numbers_and_variables` | `tests/runtime/test_listing_predicates.py` | 数値と変数を含む述語のテスト |
| `test_listing_with_special_characters` | `tests/runtime/test_listing_predicates.py` | 特殊文字を含む述語のテスト |

### tests/runtime/test_logic_interpreter.py

| テストケース | テストのファイルパス | 確認内容 |
| --- | --- | --- |
| `test_unification_basic` | `tests/runtime/test_logic_interpreter.py` | 基本的な単一化のテスト |
| `test_unification_complex` | `tests/runtime/test_logic_interpreter.py` | 複雑な単一化のテスト |
| `test_unification_with_numbers` | `tests/runtime/test_logic_interpreter.py` | 数値を含む単一化のテスト |
| `test_occurs_check` | `tests/runtime/test_logic_interpreter.py` | 発生チェックのテスト |
| `test_occurs_check_list_cycle` | `tests/runtime/test_logic_interpreter.py` | リスト循環の発生チェック |
| `test_occurs_check_complex` | `tests/runtime/test_logic_interpreter.py` | 複雑な発生チェックのテスト: X = f(Y), Y = g(X) |
| `test_occurs_check_toggle` | `tests/runtime/test_logic_interpreter.py` | 発生チェックの有無での単一化結果の違いを確認 |
| `test_variable_renaming` | `tests/runtime/test_logic_interpreter.py` | 変数リネームのテスト |
| `test_variable_renaming_consistency` | `tests/runtime/test_logic_interpreter.py` | 変数リネームの一貫性テスト：ルール内で同じ変数は同じ新名にリネームされる |
| `test_rename_variables_no_recursion` | `tests/runtime/test_logic_interpreter.py` | 深い構造でも再帰せずに変数リネームできることを確認 |
| `test_goal_resolution` | `tests/runtime/test_logic_interpreter.py` | ゴール解決のテスト |
| `test_goal_resolution_with_variables` | `tests/runtime/test_logic_interpreter.py` | 変数を含むゴール解決のテスト |
| `test_backtracking` | `tests/runtime/test_logic_interpreter.py` | バックトラッキングのテスト |
| `test_rule_application` | `tests/runtime/test_logic_interpreter.py` | ルール適用のテスト |
| `test_dereference` | `tests/runtime/test_logic_interpreter.py` | 間接参照のテスト |
| `test_dereference_complex_chain` | `tests/runtime/test_logic_interpreter.py` | 複雑な変数チェーンの間接参照テスト（項を含む） |
| `test_dereference_term` | `tests/runtime/test_logic_interpreter.py` | 項の引数を間接参照して新しい項を構築するテスト |
| `test_partial_dereference` | `tests/runtime/test_logic_interpreter.py` | 部分的間接参照テスト：項内の変数が一部のみ束縛されている場合 |
| `test_circular_reference_detection` | `tests/runtime/test_logic_interpreter.py` | 循環参照のテスト：X=Y, Y=X の単一化と参照解決 |
| `test_unification_failure_rollback` | `tests/runtime/test_logic_interpreter.py` | 単一化失敗時の環境ロールバックテスト |
| `test_complex_term_unification` | `tests/runtime/test_logic_interpreter.py` | 複雑な項の単一化テスト（ネストした複合項） |
| `test_deep_term_unification_stack` | `tests/runtime/test_logic_interpreter.py` | 深い複合項の単一化テスト（スタック化の回帰防止） |
| `test_list_unification` | `tests/runtime/test_logic_interpreter.py` | リスト単一化テスト（ドットペア表記をTermで模擬） |
| `test_cut_operation` | `tests/runtime/test_logic_interpreter.py` | カット演算のテスト |
| `test_built_in_predicates` | `tests/runtime/test_logic_interpreter.py` | 組み込み述語のテスト |
| `test_negation_as_failure` | `tests/runtime/test_logic_interpreter.py` | 失敗による否定のテスト |
| `test_meta_predicates` | `tests/runtime/test_logic_interpreter.py` | メタ述語のテスト |

### tests/runtime/test_math_interpreter.py

| テストケース | テストのファイルパス | 確認内容 |
| --- | --- | --- |
| `test_basic_arithmetic` | `tests/runtime/test_math_interpreter.py` | 基本的な算術演算のテスト |
| `test_complex_expressions` | `tests/runtime/test_math_interpreter.py` | 複雑な式の評価テスト |
| `test_comparison_operations` | `tests/runtime/test_math_interpreter.py` | 比較演算のテスト |
| `test_mathematical_functions` | `tests/runtime/test_math_interpreter.py` | 数学関数のテスト |
| `test_variable_evaluation` | `tests/runtime/test_math_interpreter.py` | 変数を含む式の評価テスト |
| `test_type_checking` | `tests/runtime/test_math_interpreter.py` | 型チェックのテスト |
| `test_error_handling` | `tests/runtime/test_math_interpreter.py` | エラーハンドリングのテスト |
| `test_symptom_score_calculation` | `tests/runtime/test_math_interpreter.py` | 症状マッチスコア計算ロジックのテスト |
| `test_bitwise_operations` | `tests/runtime/test_math_interpreter.py` | ビット単位演算のテスト |
| `test_advanced_operations` | `tests/runtime/test_math_interpreter.py` | 高度な演算のテスト |
| `test_unary_operations` | `tests/runtime/test_math_interpreter.py` | 単項演算のテスト |
| `test_nested_variable_resolution` | `tests/runtime/test_math_interpreter.py` | ネストした変数解決のテスト |
| `test_floating_point_operations` | `tests/runtime/test_math_interpreter.py` | 浮動小数点演算のテスト |
| `test_mixed_integer_float_operations` | `tests/runtime/test_math_interpreter.py` | 整数と浮動小数点の混合演算テスト |
| `test_comparison_with_variables` | `tests/runtime/test_math_interpreter.py` | 変数を含む比較のテスト |
| `test_function_arity_validation` | `tests/runtime/test_math_interpreter.py` | 関数のアリティ検証テスト |

### tests/runtime/test_meta_predicates.py

| テストケース | テストのファイルパス | 確認内容 |
| --- | --- | --- |
| `test_findall_simple_goal_one_solution` | `tests/runtime/test_meta_predicates.py` | a. Simple goal with one solution. |
| `test_findall_goal_multiple_solutions` | `tests/runtime/test_meta_predicates.py` | b. Goal with multiple solutions. |
| `test_findall_goal_no_solutions` | `tests/runtime/test_meta_predicates.py` | c. Goal with no solutions (e.g., using fail). |
| `test_findall_goal_duplicate_solutions` | `tests/runtime/test_meta_predicates.py` | d. Goal with duplicate solutions. |
| `test_findall_template_multiple_variables` | `tests/runtime/test_meta_predicates.py` | e. Template with multiple variables. |
| `test_findall_complex_goal_conjunction` | `tests/runtime/test_meta_predicates.py` | f. Complex goal (conjunction of sub-goals). |
| `test_findall_goal_throws_exception` | `tests/runtime/test_meta_predicates.py` | g. Goal that throws an exception. findall/3 should re-throw. |
| `test_findall_goal_not_callable_variable` | `tests/runtime/test_meta_predicates.py` | h. Goal that is not a callable term (uninstantiated variable). |
| `test_findall_goal_not_callable_number` | `tests/runtime/test_meta_predicates.py` | h. Goal that is not a callable term (number). |
| `test_findall_with_cut` | `tests/runtime/test_meta_predicates.py` | i. Goal involving cut (!). |
| `test_findall_order_of_solutions` | `tests/runtime/test_meta_predicates.py` | j. Ensure the order of solutions is consistent. (Same as test_findall_goal_multiple_solutions) |
| `test_findall_template_vars_not_in_goal` | `tests/runtime/test_meta_predicates.py` | Test template variables not bound by the goal. |
| `test_findall_empty_goal_list` | `tests/runtime/test_meta_predicates.py` | Test findall with an empty list as goal (should fail or type error). |
| `test_findall_uninstantiated_template_var_in_goal` | `tests/runtime/test_meta_predicates.py` | Test findall where a variable in the template is instantiated by the goal. |

### tests/runtime/test_multiple_input.py

| テストケース | テストのファイルパス | 確認内容 |
| --- | --- | --- |
| `test_valid_two_numbers` | `tests/runtime/test_multiple_input.py` | 正常な2つの数値入力のテスト |
| `test_first_input_invalid_then_valid` | `tests/runtime/test_multiple_input.py` | 1つ目の入力が無効、再入力で有効な値のテスト |
| `test_second_input_invalid_then_valid` | `tests/runtime/test_multiple_input.py` | 2つ目の入力が無効、再入力で有効な値のテスト |
| `test_both_inputs_invalid_then_valid` | `tests/runtime/test_multiple_input.py` | 両方の入力が無効、それぞれ再入力で有効な値のテスト |
| `test_negative_numbers` | `tests/runtime/test_multiple_input.py` | 負の数値の入力テスト |
| `test_decimal_numbers` | `tests/runtime/test_multiple_input.py` | 小数点数の入力テスト |
| `test_zero_values` | `tests/runtime/test_multiple_input.py` | ゼロ値の入力テスト |
| `test_large_numbers` | `tests/runtime/test_multiple_input.py` | 大きな数値の入力テスト |
| `test_multiple_invalid_attempts` | `tests/runtime/test_multiple_input.py` | 複数回の無効入力後に有効入力のテスト |
| `test_input_prompts_appear` | `tests/runtime/test_multiple_input.py` | 入力プロンプトが正しく表示されることのテスト |
| `test_individual_predicates` | `tests/runtime/test_multiple_input.py` | 個別の述語のテスト |
| `test_validation_predicate_direct` | `tests/runtime/test_multiple_input.py` | validate_number述語の直接テスト |

### tests/runtime/test_peek_char.py

| テストケース | テストのファイルパス | 確認内容 |
| --- | --- | --- |
| `test_basic_functionality` | `tests/runtime/test_peek_char.py` | 基本機能の動作確認 |
| `test_peek_char_basic` | `tests/runtime/test_peek_char.py` | 基本的なpeek_char動作 |
| `test_peek_char_at_eof` | `tests/runtime/test_peek_char.py` | EOF時のpeek_char動作 |
| `test_peek_char_empty_stream` | `tests/runtime/test_peek_char.py` | 空ストリームでのpeek |
| `test_peek_char_multibyte` | `tests/runtime/test_peek_char.py` | マルチバイト文字のpeek |
| `test_at_end_of_stream_progression` | `tests/runtime/test_peek_char.py` | at_end_of_streamの状態変化 |
| `test_supports_peek_operations` | `tests/runtime/test_peek_char.py` | peek操作サポート確認 |
| `test_get_stream_status` | `tests/runtime/test_peek_char.py` | ストリーム状態情報の取得 |
| `test_peek_char_unification_success` | `tests/runtime/test_peek_char.py` | peek_char/1の成功ケース |
| `test_peek_char_unification_failure` | `tests/runtime/test_peek_char.py` | peek_char/1の失敗ケース |
| `test_peek_char_eof` | `tests/runtime/test_peek_char.py` | EOF時のpeek_char/1 |
| `test_peek_char_mixed_operations` | `tests/runtime/test_peek_char.py` | peek_charとget_charの混在操作 |
| `test_at_end_of_stream_false` | `tests/runtime/test_peek_char.py` | データがある場合の動作 |
| `test_at_end_of_stream_true` | `tests/runtime/test_peek_char.py` | EOFの場合の動作 |
| `test_at_end_of_stream_progression` | `tests/runtime/test_peek_char.py` | 読み取り進行中のEOF状態変化 |
| `test_conditional_reading` | `tests/runtime/test_peek_char.py` | 条件付き読み取りパターン |

### tests/runtime/test_recursive_rules.py

| テストケース | テストのファイルパス | 確認内容 |
| --- | --- | --- |
| `test_member_predicate` | `tests/runtime/test_recursive_rules.py` | 再帰ルールで定義したmember/2の成功・失敗・複数解を確認。 |
| `test_ancestor_predicate` | `tests/runtime/test_recursive_rules.py` | ancestor/2の再帰定義で世代をまたぐ解が得られることを確認。 |
| `test_peano_addition` | `tests/runtime/test_recursive_rules.py` | ペアノ算術の加算ルールで計算結果が得られることを確認。 |
| `test_left_recursion_problem_naive_ancestor` | `tests/runtime/test_recursive_rules.py` | 左再帰のancestor_lr/2で期待解が得られるか（ループ耐性）を確認。 |

### tests/test_japanese_functor_support.py

| テストケース | テストのファイルパス | 確認内容 |
| --- | --- | --- |
| `test_functor_mapper_basic_functionality` | `tests/test_japanese_functor_support.py` | FunctorMapper基本機能テスト |
| `test_scanner_integration` | `tests/test_japanese_functor_support.py` | Scanner統合テスト |
| `test_variable_vs_functor_distinction` | `tests/test_japanese_functor_support.py` | 変数とファンクターの区別テスト |
| `test_parser_integration` | `tests/test_japanese_functor_support.py` | Parser統合テスト |
| `test_runtime_integration` | `tests/test_japanese_functor_support.py` | Runtime統合テスト |
| `test_collision_avoidance` | `tests/test_japanese_functor_support.py` | 衝突回避機能テスト |
| `test_unicode_character_sets` | `tests/test_japanese_functor_support.py` | 多言語Unicode文字セットテスト |
| `test_performance_large_scale` | `tests/test_japanese_functor_support.py` | 大規模マッピング性能テスト |
| `test_mapping_consistency` | `tests/test_japanese_functor_support.py` | マッピングの一貫性テスト |
| `test_complex_japanese_expressions` | `tests/test_japanese_functor_support.py` | 複雑な日本語表現テスト |

### tests/tools/test_explain_tool.py

| テストケース | テストのファイルパス | 確認内容 |
| --- | --- | --- |
| `test_explain_tool_initialization` | `tests/tools/test_explain_tool.py` | ExplainToolの初期化テスト |
| `test_explain_simple_fact_query` | `tests/tools/test_explain_tool.py` | 単純な事実クエリの説明テスト |
| `test_explain_rule_query` | `tests/tools/test_explain_tool.py` | ルールクエリの説明テスト |
| `test_explain_with_tree_format` | `tests/tools/test_explain_tool.py` | ツリー形式での説明テスト |
| `test_explain_with_json_format` | `tests/tools/test_explain_tool.py` | JSON形式での説明テスト |
| `test_explain_with_depth_limit` | `tests/tools/test_explain_tool.py` | 深度制限付きの説明テスト |
| `test_explain_nonexistent_predicate` | `tests/tools/test_explain_tool.py` | 存在しない述語の説明テスト |
| `test_explain_invalid_query` | `tests/tools/test_explain_tool.py` | 無効なクエリの説明テスト |
| `test_explain_with_invalid_format` | `tests/tools/test_explain_tool.py` | 無効な形式指定の説明テスト |
| `test_parse_full_command` | `tests/tools/test_explain_tool.py` | 'parse_explain_command' with all arguments |
| `test_parse_command_with_default_depth` | `tests/tools/test_explain_tool.py` | 'parse_explain_command' with default depth |
| `test_parse_command_with_default_format_and_depth` | `tests/tools/test_explain_tool.py` | 'parse_explain_command' with default format and depth |
| `test_parse_command_with_unquoted_format` | `tests/tools/test_explain_tool.py` | 'parse_explain_command' with unquoted format type |
| `test_parse_invalid_command_format` | `tests/tools/test_explain_tool.py` | 'parse_explain_command' with an invalid format |

### tests/tools/test_search_tool.py

| テストケース | テストのファイルパス | 確認内容 |
| --- | --- | --- |
| `test_search_tool_initialization` | `tests/tools/test_search_tool.py` | SearchToolの初期化テスト |
| `test_search_predicate_exact_match` | `tests/tools/test_search_tool.py` | 述語名での完全一致検索テスト |
| `test_search_predicate_partial_match` | `tests/tools/test_search_tool.py` | 述語名での部分一致検索テスト |
| `test_search_argument_match` | `tests/tools/test_search_tool.py` | 引数での検索テスト |
| `test_search_full_text_match` | `tests/tools/test_search_tool.py` | 全文検索テスト |
| `test_search_with_limit` | `tests/tools/test_search_tool.py` | 検索結果数制限のテスト |
| `test_search_nonexistent_pattern` | `tests/tools/test_search_tool.py` | 存在しないパターンの検索テスト |
| `test_search_empty_pattern` | `tests/tools/test_search_tool.py` | 空パターンの検索テスト |
| `test_search_invalid_type` | `tests/tools/test_search_tool.py` | 無効な検索タイプのテスト |
| `test_format_results_text` | `tests/tools/test_search_tool.py` | 検索結果のテキスト形式フォーマットテスト |
| `test_format_results_json` | `tests/tools/test_search_tool.py` | 検索結果のJSON形式フォーマットテスト |
| `test_format_results_table` | `tests/tools/test_search_tool.py` | 検索結果のテーブル形式フォーマットテスト |
| `test_get_search_statistics` | `tests/tools/test_search_tool.py` | 検索エンジン統計情報の取得テスト |
| `test_rebuild_index` | `tests/tools/test_search_tool.py` | インデックス再構築テスト |
| `test_search_after_index_rebuild` | `tests/tools/test_search_tool.py` | インデックス再構築後の検索テスト |
| `test_search_complex_pattern` | `tests/tools/test_search_tool.py` | 複雑なパターンの検索テスト |
| `test_search_case_sensitivity` | `tests/tools/test_search_tool.py` | 大文字小文字の扱いテスト |
| `test_parse_search_full_command` | `tests/tools/test_search_tool.py` | 'parse_search_command' with all arguments |
| `test_parse_search_command_with_default_limit` | `tests/tools/test_search_tool.py` | 'parse_search_command' with default limit |
| `test_parse_search_command_with_default_type_and_limit` | `tests/tools/test_search_tool.py` | 'parse_search_command' with default type and limit |
| `test_parse_search_invalid_command_format` | `tests/tools/test_search_tool.py` | 'parse_search_command' with an invalid format |

### tests/tools/test_validate_tool.py

| テストケース | テストのファイルパス | 確認内容 |
| --- | --- | --- |
| `test_validate_tool_initialization` | `tests/tools/test_validate_tool.py` | ValidateToolの初期化テスト |
| `test_validate_all_checks` | `tests/tools/test_validate_tool.py` | 全ての検証の実行テスト |
| `test_validate_conflicts_only` | `tests/tools/test_validate_tool.py` | 矛盾検証のみのテスト |
| `test_validate_unreachable_only` | `tests/tools/test_validate_tool.py` | 到達可能性検証のみのテスト |
| `test_validate_undefined_only` | `tests/tools/test_validate_tool.py` | 未定義述語検証のみのテスト |
| `test_validate_with_detailed_analysis` | `tests/tools/test_validate_tool.py` | 詳細解析付きの検証テスト |
| `test_format_results_text` | `tests/tools/test_validate_tool.py` | 検証結果のテキスト形式フォーマットテスト |
| `test_format_results_json` | `tests/tools/test_validate_tool.py` | 検証結果のJSON形式フォーマットテスト |
| `test_format_results_detailed` | `tests/tools/test_validate_tool.py` | 検証結果の詳細形式フォーマットテスト |
| `test_format_error_result` | `tests/tools/test_validate_tool.py` | エラー結果のフォーマットテスト |
| `test_get_validation_statistics` | `tests/tools/test_validate_tool.py` | 検証エンジン統計情報の取得テスト |
| `test_rebuild_analysis` | `tests/tools/test_validate_tool.py` | 解析データ再構築テスト |
| `test_validate_empty_runtime` | `tests/tools/test_validate_tool.py` | 空のランタイムでの検証テスト |
| `test_validate_invalid_check_type` | `tests/tools/test_validate_tool.py` | 無効な検証タイプのテスト |
| `test_issue_severity_levels` | `tests/tools/test_validate_tool.py` | 問題の重要度レベルのテスト |
| `test_issue_details` | `tests/tools/test_validate_tool.py` | 問題の詳細情報テスト |
| `test_analysis_performance` | `tests/tools/test_validate_tool.py` | 解析性能のテスト |
| `test_validation_with_complex_rules` | `tests/tools/test_validate_tool.py` | 複雑なルールでの検証テスト |

### tests/unified_input/test_integration.py

| テストケース | テストのファイルパス | 確認内容 |
| --- | --- | --- |
| `test_get_char_with_unified_input` | `tests/unified_input/test_integration.py` | get_char述語と統一入力システムの統合 |
| `test_read_line_with_unified_input` | `tests/unified_input/test_integration.py` | read_line述語と統一入力システムの統合 |
| `test_multiple_predicates_same_runtime` | `tests/unified_input/test_integration.py` | 同一Runtime上での複数述語実行 |
| `test_single_thread_vs_multi_thread_consistency` | `tests/unified_input/test_integration.py` | デフォルト/明示有効化の一貫性 |
| `test_threaded_execution_with_delay` | `tests/unified_input/test_integration.py` | 遅延ありスレッド実行（真の継続実行確認） |
| `test_concurrent_predicate_execution` | `tests/unified_input/test_integration.py` | 複数述語の並行実行（スレッド安全性） |
| `test_handler_error_predicate_failure` | `tests/unified_input/test_integration.py` | InputHandlerエラー時の述語失敗 |
| `test_unification_failure` | `tests/unified_input/test_integration.py` | 統一化失敗時の処理 |
| `test_threading_error_recovery` | `tests/unified_input/test_integration.py` | スレッドエラーからの回復 |
| `test_runtime_default_configuration` | `tests/unified_input/test_integration.py` | Runtimeのデフォルト設定 |
| `test_runtime_threaded_mode_enable` | `tests/unified_input/test_integration.py` | Runtime真の継続実行モード有効化 |
| `test_mixed_predicate_sequence` | `tests/unified_input/test_integration.py` | 混在述語シーケンス実行 |
| `test_threaded_mixed_sequence` | `tests/unified_input/test_integration.py` | スレッド化混在シーケンス |
| `test_mode_switching_during_execution` | `tests/unified_input/test_integration.py` | 実行中のスレッド有効化が冪等であることを確認 |

### tests/unified_input/test_io_manager_integration.py

| テストケース | テストのファイルパス | 確認内容 |
| --- | --- | --- |
| `test_request_input_char_line_peek` | `tests/unified_input/test_io_manager_integration.py` | request_inputのchar/peek_char/line取得が正しく動くことを確認。 |

### tests/unified_input/test_io_predicate_base.py

| テストケース | テストのファイルパス | 確認内容 |
| --- | --- | --- |
| `test_argument_validation_success` | `tests/unified_input/test_io_predicate_base.py` | 引数数検証：正常ケース |
| `test_argument_validation_failure` | `tests/unified_input/test_io_predicate_base.py` | 引数数検証：異常ケース |
| `test_prompt_generation` | `tests/unified_input/test_io_predicate_base.py` | プロンプト文字列生成 |
| `test_eof_handling` | `tests/unified_input/test_io_predicate_base.py` | EOF処理 |
| `test_number_conversion_success` | `tests/unified_input/test_io_predicate_base.py` | 数値変換：成功ケース |
| `test_number_conversion_failure` | `tests/unified_input/test_io_predicate_base.py` | 数値変換：失敗ケース |
| `test_get_char_conversion` | `tests/unified_input/test_io_predicate_base.py` | get_char述語のPrologターム変換 |
| `test_read_line_conversion` | `tests/unified_input/test_io_predicate_base.py` | read_line述語のPrologターム変換 |
| `test_request_input_call` | `tests/unified_input/test_io_predicate_base.py` | 統一入力システム呼び出し |
| `test_unify_with_argument` | `tests/unified_input/test_io_predicate_base.py` | 引数との統一化 |
| `test_execute_template_method` | `tests/unified_input/test_io_predicate_base.py` | execute()テンプレートメソッドの動作 |
| `test_execute_with_io_error` | `tests/unified_input/test_io_predicate_base.py` | execute()でIOエラーが発生した場合 |
| `test_execute_with_unification_failure` | `tests/unified_input/test_io_predicate_base.py` | execute()で統一化が失敗した場合 |
| `test_multiple_predicates_same_runtime` | `tests/unified_input/test_io_predicate_base.py` | 同一Runtime上で複数述語を実行 |

### tests/unified_input/test_unified_input_system.py

| テストケース | テストのファイルパス | 確認内容 |
| --- | --- | --- |
| `test_initial_state` | `tests/unified_input/test_unified_input_system.py` | 初期状態のテスト |
| `test_enable_disable` | `tests/unified_input/test_unified_input_system.py` | 有効化・無効化のテスト |
| `test_request_input_not_enabled` | `tests/unified_input/test_unified_input_system.py` | 未有効化状態での入力要求 |
| `test_request_input_success` | `tests/unified_input/test_unified_input_system.py` | 入力要求成功ケース |
| `test_request_input_with_additional_params` | `tests/unified_input/test_unified_input_system.py` | 追加パラメータ付き入力要求 |
| `test_request_input_handler_error` | `tests/unified_input/test_unified_input_system.py` | InputHandlerエラー時の処理 |
| `test_multiple_requests` | `tests/unified_input/test_unified_input_system.py` | 複数の入力要求 |
| `test_initial_state` | `tests/unified_input/test_unified_input_system.py` | 初期状態のテスト |
| `test_set_input_handler` | `tests/unified_input/test_unified_input_system.py` | 入力ハンドラ設定 |
| `test_threading_mode_toggle` | `tests/unified_input/test_unified_input_system.py` | スレッドモード切り替え |
| `test_single_thread_mode_request` | `tests/unified_input/test_unified_input_system.py` | シングルスレッドモード入力要求 |
| `test_multi_thread_mode_request` | `tests/unified_input/test_unified_input_system.py` | マルチスレッドモード入力要求 |
| `test_request_without_handler` | `tests/unified_input/test_unified_input_system.py` | ハンドラ未設定での入力要求 |
| `test_fallback_stream` | `tests/unified_input/test_unified_input_system.py` | フォールバックストリーム使用 |
| `test_handler_error_fallback` | `tests/unified_input/test_unified_input_system.py` | ハンドラエラー時のフォールバック |
| `test_statistics_collection` | `tests/unified_input/test_unified_input_system.py` | 統計情報収集 |
| `test_concurrent_requests` | `tests/unified_input/test_unified_input_system.py` | 並行入力要求（マルチスレッドモード） |
| `test_shutdown_cleanup` | `tests/unified_input/test_unified_input_system.py` | シャットダウン時のクリーンアップ |
| `test_input_event_creation` | `tests/unified_input/test_unified_input_system.py` | InputEvent作成 |
| `test_input_request_response_matching` | `tests/unified_input/test_unified_input_system.py` | InputRequestとInputResponseのID照合 |

### tests/util/test_functor_mapper.py

| テストケース | テストのファイルパス | 確認内容 |
| --- | --- | --- |
| `test_needs_mapping_japanese_functors` | `tests/util/test_functor_mapper.py` | 日本語ファンクターのマッピング必要性テスト |
| `test_needs_mapping_unicode_functors` | `tests/util/test_functor_mapper.py` | Unicode文字のマッピング必要性テスト |
| `test_needs_mapping_unsafe_characters` | `tests/util/test_functor_mapper.py` | 安全でない文字のマッピング必要性テスト |
| `test_mapping_generation_consistency` | `tests/util/test_functor_mapper.py` | マッピング生成の一貫性テスト |
| `test_non_ascii_passthrough` | `tests/util/test_functor_mapper.py` | 非マッピング対象のパススルーテスト |
| `test_existing_functor_collision_avoidance` | `tests/util/test_functor_mapper.py` | 既存ファンクターとの衝突回避テスト |
| `test_register_existing_functors` | `tests/util/test_functor_mapper.py` | 既存ファンクター動的登録テスト |
| `test_extract_functors_from_string` | `tests/util/test_functor_mapper.py` | 文字列からのファンクター抽出テスト |
| `test_clear_mapping` | `tests/util/test_functor_mapper.py` | マッピングクリアテスト |
| `test_large_scale_mapping_performance` | `tests/util/test_functor_mapper.py` | 大規模マッピングの性能テスト |
| `test_mixed_character_sets` | `tests/util/test_functor_mapper.py` | 混在文字セットのテスト |

### tests/validation/test_analyzers.py

| テストケース | テストのファイルパス | 確認内容 |
| --- | --- | --- |
| `test_conflict_analyzer_initialization` | `tests/validation/test_analyzers.py` | ConflictAnalyzerの初期化テスト |
| `test_analyze_no_conflicts` | `tests/validation/test_analyzers.py` | 矛盾なしの場合のテスト |
| `test_analyze_with_conflicts` | `tests/validation/test_analyzers.py` | 矛盾ありの場合のテスト |
| `test_reachability_analyzer_initialization` | `tests/validation/test_analyzers.py` | ReachabilityAnalyzerの初期化テスト |
| `test_get_entry_points` | `tests/validation/test_analyzers.py` | エントリーポイント特定のテスト |
| `test_is_entry_point` | `tests/validation/test_analyzers.py` | エントリーポイント判定のテスト |
| `test_should_ignore_unreachable` | `tests/validation/test_analyzers.py` | 到達不可能述語の無視判定テスト |
| `test_analyze_reachability` | `tests/validation/test_analyzers.py` | 到達可能性解析のテスト |
| `test_undefined_analyzer_initialization` | `tests/validation/test_analyzers.py` | UndefinedAnalyzerの初期化テスト |
| `test_collect_all_references` | `tests/validation/test_analyzers.py` | 全参照収集のテスト |
| `test_determine_severity` | `tests/validation/test_analyzers.py` | 重要度決定のテスト |
| `test_suggest_fix` | `tests/validation/test_analyzers.py` | 修正提案のテスト |
| `test_find_similar_predicates` | `tests/validation/test_analyzers.py` | 類似述語検索のテスト |
| `test_is_similar_name` | `tests/validation/test_analyzers.py` | 名前類似性判定のテスト |
| `test_analyze_undefined_predicates` | `tests/validation/test_analyzers.py` | 未定義述語解析のテスト |
| `test_all_analyzers_run_without_error` | `tests/validation/test_analyzers.py` | 全アナライザーがエラーなしで実行されるテスト |
| `test_analyzers_find_different_issues` | `tests/validation/test_analyzers.py` | 各アナライザーが異なる種類の問題を発見するテスト |
| `test_analyzer_performance_with_large_dataset` | `tests/validation/test_analyzers.py` | 大規模データセットでのアナライザー性能テスト |

### tests/validation/test_validation_result.py

| テストケース | テストのファイルパス | 確認内容 |
| --- | --- | --- |
| `test_validation_issue_creation` | `tests/validation/test_validation_result.py` | ValidationIssueの作成テスト |
| `test_validation_issue_to_dict` | `tests/validation/test_validation_result.py` | ValidationIssueの辞書変換テスト |
| `test_validation_issue_without_optional_fields` | `tests/validation/test_validation_result.py` | オプションフィールドなしのValidationIssueテスト |
| `test_validation_issue_severity_validation` | `tests/validation/test_validation_result.py` | 重要度の検証テスト |
| `test_validation_result_creation` | `tests/validation/test_validation_result.py` | ValidationResultの作成テスト |
| `test_validation_result_empty` | `tests/validation/test_validation_result.py` | 空のValidationResultテスト |
| `test_has_errors_method` | `tests/validation/test_validation_result.py` | has_errors()メソッドのテスト |
| `test_has_warnings_method` | `tests/validation/test_validation_result.py` | has_warnings()メソッドのテスト |
| `test_get_error_count_method` | `tests/validation/test_validation_result.py` | get_error_count()メソッドのテスト |
| `test_get_warning_count_method` | `tests/validation/test_validation_result.py` | get_warning_count()メソッドのテスト |
| `test_get_info_count_method` | `tests/validation/test_validation_result.py` | get_info_count()メソッドのテスト |
| `test_summary_property` | `tests/validation/test_validation_result.py` | summaryプロパティのテスト |
| `test_validation_result_with_large_dataset` | `tests/validation/test_validation_result.py` | 大量データでのValidationResultテスト |

### tests/cli/test_interactive_repl_commands.py.disabled

| テストケース | テストのファイルパス | 確認内容 |
| --- | --- | --- |
| `test_explain_command_basic` | `tests/cli/test_interactive_repl_commands.py.disabled` | 基本的な:explainコマンドのテスト |
| `test_explain_command_with_format` | `tests/cli/test_interactive_repl_commands.py.disabled` | フォーマット指定付き:explainコマンドのテスト |
| `test_explain_command_with_depth` | `tests/cli/test_interactive_repl_commands.py.disabled` | 深度指定付き:explainコマンドのテスト |
| `test_explain_command_no_args` | `tests/cli/test_interactive_repl_commands.py.disabled` | 引数なし:explainコマンドのテスト |
| `test_search_command_basic` | `tests/cli/test_interactive_repl_commands.py.disabled` | 基本的な:searchコマンドのテスト |
| `test_search_command_with_type_and_limit` | `tests/cli/test_interactive_repl_commands.py.disabled` | タイプと制限指定付き:searchコマンドのテスト |
| `test_search_command_no_args` | `tests/cli/test_interactive_repl_commands.py.disabled` | 引数なし:searchコマンドのテスト |
| `test_search_stats_command` | `tests/cli/test_interactive_repl_commands.py.disabled` | :search_statsコマンドのテスト |
| `test_rebuild_index_command` | `tests/cli/test_interactive_repl_commands.py.disabled` | :rebuild_indexコマンドのテスト |
| `test_validate_command_basic` | `tests/cli/test_interactive_repl_commands.py.disabled` | 基本的な:validateコマンドのテスト |
| `test_validate_command_conflicts_only` | `tests/cli/test_interactive_repl_commands.py.disabled` | 矛盾検証のみ:validateコマンドのテスト |
| `test_validate_command_detailed` | `tests/cli/test_interactive_repl_commands.py.disabled` | 詳細検証:validateコマンドのテスト |
| `test_validate_command_invalid_type` | `tests/cli/test_interactive_repl_commands.py.disabled` | 無効なタイプ指定:validateコマンドのテスト |
| `test_validate_stats_command` | `tests/cli/test_interactive_repl_commands.py.disabled` | :validate_statsコマンドのテスト |
| `test_help_command_includes_new_commands` | `tests/cli/test_interactive_repl_commands.py.disabled` | :helpコマンドに新しいコマンドが含まれることのテスト |
| `test_commands_without_runtime` | `tests/cli/test_interactive_repl_commands.py.disabled` | ランタイム未初期化時のコマンドテスト |
| `test_command_error_handling` | `tests/cli/test_interactive_repl_commands.py.disabled` | コマンドエラーハンドリングのテスト |
| `test_sequential_commands` | `tests/cli/test_interactive_repl_commands.py.disabled` | 連続コマンド実行のテスト |
| `test_command_with_japanese_input` | `tests/cli/test_interactive_repl_commands.py.disabled` | 日本語入力を含むコマンドのテスト |
| `test_repl_state_consistency` | `tests/cli/test_interactive_repl_commands.py.disabled` | REPL状態の一貫性テスト |

## 重複・類似の可能性（概要）
- 単一化や変数解決は、`tests/core/test_variable_dereferencing.py` と `tests/runtime/test_logic_interpreter.py` の双方で詳細に扱われており、解釈レイヤー違いで重複傾向があります。
- 日本語対応は、`tests/parser/test_scanner.py` / `tests/parser/test_parser.py` / `tests/test_japanese_functor_support.py` / `tests/util/test_functor_mapper.py` で重複してカバーしています。
- I/O周辺は `tests/runtime/test_io_predicates.py` と `tests/unified_input/test_integration.py`、`tests/unified_input/test_unified_input_system.py` で重複して統合検証しています。
- 動的述語は `tests/runtime/test_dynamic_predicates.py` と `tests/runtime/test_interpreter.py` の双方で asserta/assertz/retract を検証しています。
- リスト操作は `tests/runtime/test_list_operations.py` と `tests/runtime/test_interpreter.py`、`tests/runtime/test_logic_interpreter.py` の複数レイヤーで重複検証されています。

## 備考
- `tests/cli/test_interactive_repl_commands.py.disabled` は拡張子が `.disabled` のため通常のテスト収集対象外ですが、参考として記載しています。