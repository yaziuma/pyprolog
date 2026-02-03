# pyprologテストケース全分析 (631件)

生成日時: 2026-02-03
分析方法: pytest --collect-only + カテゴリ別実行検証

## エグゼクティブサマリー

### 実行結果
- **総テスト数**: 631件
- **確認済みPASS**: 443件以上（個別カテゴリ実行で全てPASS）
- **実行成功率**: 極めて高い（個別実行で全カテゴリPASS）
- **問題**: 全体一括実行時にハング発生（おそらくunified_input系のIO待機）

### テスト分布
1. **ランタイムテスト** (274件, 43.4%): インタープリタコア機能
2. **コアデータ型** (85件, 13.5%): 基本データ構造とバインディング
3. **統合テスト** (54件, 8.6%): エンドツーエンドシナリオ
4. **開発ツール** (53件, 8.4%): explain, search, validate
5. **統合入力システム** (49件, 7.8%): IO管理
6. **パーサー** (41件, 6.5%): 字句・構文解析
7. **バリデーション** (31件, 4.9%): 静的解析
8. **日本語サポート** (16件, 2.5%): 日本語変数名対応
9. その他 (28件, 4.4%)

### カテゴリ別内訳
- **runtime**: 274件 (43.4%)
- **core**: 85件 (13.5%)
- **integration**: 54件 (8.6%)
- **tools**: 53件 (8.4%)
- **unified_input**: 49件 (7.8%)
- **parser**: 41件 (6.5%)
- **validation**: 31件 (4.9%)
- **japanese**: 16件 (2.5%)
- **util**: 11件 (1.7%)
- **トップレベル**: 10件 (1.6%)
- **benchmark_guardrails**: 7件 (1.1%)

## カテゴリ別詳細

### ランタイム (274件)

#### test_arithmetic_edge_cases.py (19件)
- **変数系** (1件)
  - `test_variable_with_edge_values`
- **機能系** (16件)
  - `test_large_numbers`
  - `test_very_small_numbers`
  - `test_floating_point_precision`
  - `test_infinity_handling`
  - `test_negative_infinity`
  - `test_nan_handling`
  - `test_division_by_zero_variants`
  - `test_overflow_underflow`
  - `test_negative_zero`
  - `test_special_float_values`
  - ...他6件
- **算術系** (1件)
  - `test_nested_arithmetic_edge_cases`
- **複雑な系** (1件)
  - `test_complex_precision_scenarios`

#### test_built_in_unification.py (8件)
- **リスト系** (1件)
  - `test_non_unifiable_lists`
- **変数系** (2件)
  - `test_non_unifiable_variable_ground`
  - `test_non_unifiable_variables_unbound`
- **機能系** (5件)
  - `test_non_unifiable_atoms`
  - `test_non_unifiable_compound_terms_args`
  - `test_non_unifiable_compound_terms_structure`
  - `test_non_unifiable_numbers`
  - `test_non_unifiable_with_occurs_check_implication`

#### test_clause_indexing.py (4件)
- **変数系** (1件)
  - `test_fallback_for_variable_arg0`
- **機能系** (3件)
  - `test_cut_order_preserved_with_arg0_indexing`
  - `test_secondary_index_preserves_consult_order`
  - `test_secondary_index_miss_falls_back_to_primary`

#### test_dynamic_predicates.py (7件)
- **ルール系** (2件)
  - `test_asserta_rule`
  - `test_assertz_rule`
- **不正な系** (1件)
  - `test_assert_invalid_clause`
- **変数系** (2件)
  - `test_assert_uninstantiated_variable`
  - `test_assert_with_variables`
- **機能系** (2件)
  - `test_asserta_fact`
  - `test_assertz_fact`

#### test_enhanced_runtime.py (10件)
- **エラー系** (1件)
  - `test_error_handling`
- **基本的な系** (1件)
  - `test_medical_kb_basic`
- **機能系** (4件)
  - `test_initialization`
  - `test_trace_functionality`
  - `test_enhanced_runtime_inheritance`
  - `test_minimal_diagnosis_approach`
- **統合系** (1件)
  - `test_enhanced_runtime_integration`
- **複雑な系** (1件)
  - `test_complex_predicate_calls`
- **述語系** (2件)
  - `test_builtin_predicates`
  - `test_builtin_predicates_initialization`

#### test_exception_propagation.py (8件)
- **例外系** (5件)
  - `test_direct_get_char_exception`
  - `test_nested_predicate_exception`
  - `test_deeper_nesting_exception`
  - `test_direct_read_line_exception`
  - `test_nested_read_line_exception`
- **機能系** (3件)
  - `test_mixed_io_operations`
  - `test_mixed_io_read_line_then_get_char`
  - `test_deeply_nested_read_line`

#### test_execution_frames.py (28件)
- **作成系** (1件)
  - `test_choice_point_creation`
- **機能系** (25件)
  - `test_frame_type_values`
  - `test_goal_frame_initialization`
  - `test_goal_frame_can_backtrack`
  - `test_goal_frame_step_returns_none_when_exhausted`
  - `test_goal_seq_frame_initialization`
  - `test_goal_seq_frame_advancement`
  - `test_goal_seq_frame_step_completion`
  - `test_goal_seq_frame_step_not_done`
  - `test_goal_seq_frame_cannot_backtrack`
  - `test_disjunction_can_backtrack`
  - ...他15件
- **演算子系** (1件)
  - `test_operator_frame_initialization`
- **複雑な系** (1件)
  - `test_execution_state_complex_workflow`

#### test_export_facts.py (12件)
- **ルール系** (1件)
  - `test_export_facts_only_facts_not_rules`
- **不正な系** (2件)
  - `test_export_facts_invalid_file_path`
  - `test_export_facts_invalid_predicate_format`
- **基本的な系** (3件)
  - `test_export_facts_csv_basic`
  - `test_export_facts_json_basic`
  - `test_export_facts_tsv_basic`
- **機能系** (4件)
  - `test_export_facts_with_japanese_data`
  - `test_export_facts_file_overwrite`
  - `test_export_facts_large_dataset`
  - `test_export_facts_unicode_handling`
- **複雑な系** (1件)
  - `test_export_facts_with_complex_terms`
- **述語系** (1件)
  - `test_export_facts_nonexistent_predicate`

#### test_interpreter.py (31件)
- **エラー系** (1件)
  - `test_error_handling`
- **クエリ系** (1件)
  - `test_query_parsing`
- **リスト系** (1件)
  - `test_list_operations`
- **ルール系** (2件)
  - `test_rule_resolution`
  - `test_recursive_rules`
- **例外系** (1件)
  - `test_exception_handling`
- **単一化系** (1件)
  - `test_built_in_unification`
- **基本的な系** (2件)
  - `test_basic_fact_queries`
  - `test_performance_basic`
- **変数系** (1件)
  - `test_variable_unification`
- **機能系** (16件)
  - `test_comparison_operations`
  - `test_logical_operations`
  - `test_control_flow`
  - `test_negation_as_failure`
  - `test_cut_behavior`
  - `test_multiple_solutions`
  - `test_memory_management`
  - `test_goal_stack_management`
  - `test_built_in_comparison`
  - `test_io_operations`
  - ...他6件
- **算術系** (2件)
  - `test_arithmetic_operations`
  - `test_built_in_arithmetic`
- **述語系** (3件)
  - `test_builtin_predicates`
  - `test_meta_predicates`
  - `test_dynamic_predicates`

#### test_io_infrastructure.py (9件)
- **機能系** (9件)
  - `test_string_stream_read`
  - `test_string_stream_write`
  - `test_string_stream_write_with_external_buffer`
  - `test_string_stream_reset_input`
  - `test_string_stream_clear_output`
  - `test_io_manager_default_streams`
  - `test_io_manager_set_input_handler_and_request_input`
  - `test_io_manager_write_char`
  - `test_runtime_has_io_manager`

#### test_io_predicates.py (19件)
- **変数系** (2件)
  - `test_get_char_variable`
  - `test_read_line_variable`
- **機能系** (17件)
  - `test_get_char_multiple_calls`
  - `test_get_char_match_atom_success`
  - `test_get_char_mismatch_atom_failure`
  - `test_get_char_eof`
  - `test_get_char_eof_multiple_reads`
  - `test_get_char_already_bound_success`
  - `test_get_char_already_bound_fail`
  - `test_read_line_multiple_lines`
  - `test_read_line_empty_line`
  - `test_read_line_without_newline`
  - ...他7件

#### test_iterative_execution.py (14件)
- **エラー系** (1件)
  - `test_undefined_predicate_raises_error`
- **単一化系** (1件)
  - `test_conjunction_with_unification`
- **単純な系** (4件)
  - `test_simple_atom_goal`
  - `test_simple_unification`
  - `test_simple_conjunction`
  - `test_simple_disjunction`
- **機能系** (8件)
  - `test_failing_goal`
  - `test_conjunction_with_failure`
  - `test_disjunction_left_succeeds`
  - `test_disjunction_right_succeeds`
  - `test_negation_of_failure`
  - `test_negation_of_success`
  - `test_nested_conjunction`
  - `test_conjunction_and_disjunction`

#### test_list_operations.py (6件)
- **リスト系** (2件)
  - `test_member_list_argument_types`
  - `test_member_element_and_list_vars`
- **機能系** (2件)
  - `test_member_inspection_mode`
  - `test_member_generation_mode`
- **複雑な系** (1件)
  - `test_member_complex_elements`
- **述語系** (1件)
  - `test_append_predicate`

#### test_listing_predicates.py (10件)
- **リスト系** (7件)
  - `test_listing_one_predicate_person_2`
  - `test_listing_one_predicate_parent_2`
  - `test_listing_one_predicate_nonexistent`
  - `test_listing_empty_knowledge_base`
  - `test_listing_with_japanese_predicates`
  - `test_listing_with_numbers_and_variables`
  - `test_listing_with_special_characters`
- **不正な系** (1件)
  - `test_listing_one_predicate_invalid_format`
- **基本的な系** (1件)
  - `test_listing_zero_predicate_basic`
- **複雑な系** (1件)
  - `test_listing_with_complex_rules`

#### test_logic_interpreter.py (27件)
- **リスト系** (2件)
  - `test_occurs_check_list_cycle`
  - `test_list_unification`
- **ルール系** (1件)
  - `test_rule_application`
- **単一化系** (3件)
  - `test_unification_with_numbers`
  - `test_unification_failure_rollback`
  - `test_deep_term_unification_stack`
- **基本的な系** (1件)
  - `test_unification_basic`
- **変数系** (4件)
  - `test_variable_renaming`
  - `test_variable_renaming_consistency`
  - `test_rename_variables_no_recursion`
  - `test_goal_resolution_with_variables`
- **機能系** (10件)
  - `test_occurs_check`
  - `test_occurs_check_toggle`
  - `test_goal_resolution`
  - `test_backtracking`
  - `test_dereference`
  - `test_dereference_term`
  - `test_partial_dereference`
  - `test_circular_reference_detection`
  - `test_cut_operation`
  - `test_negation_as_failure`
- **複雑な系** (4件)
  - `test_unification_complex`
  - `test_occurs_check_complex`
  - `test_dereference_complex_chain`
  - `test_complex_term_unification`
- **述語系** (2件)
  - `test_built_in_predicates`
  - `test_meta_predicates`

#### test_math_interpreter.py (16件)
- **エラー系** (1件)
  - `test_error_handling`
- **基本的な系** (1件)
  - `test_basic_arithmetic`
- **変数系** (3件)
  - `test_variable_evaluation`
  - `test_nested_variable_resolution`
  - `test_comparison_with_variables`
- **機能系** (10件)
  - `test_comparison_operations`
  - `test_mathematical_functions`
  - `test_type_checking`
  - `test_symptom_score_calculation`
  - `test_bitwise_operations`
  - `test_advanced_operations`
  - `test_unary_operations`
  - `test_floating_point_operations`
  - `test_mixed_integer_float_operations`
  - `test_function_arity_validation`
- **複雑な系** (1件)
  - `test_complex_expressions`

#### test_meta_predicates.py (14件)
- **リスト系** (1件)
  - `test_findall_empty_goal_list`
- **例外系** (1件)
  - `test_findall_goal_throws_exception`
- **単純な系** (1件)
  - `test_findall_simple_goal_one_solution`
- **変数系** (2件)
  - `test_findall_template_multiple_variables`
  - `test_findall_goal_not_callable_variable`
- **機能系** (8件)
  - `test_findall_goal_multiple_solutions`
  - `test_findall_goal_no_solutions`
  - `test_findall_goal_duplicate_solutions`
  - `test_findall_goal_not_callable_number`
  - `test_findall_with_cut`
  - `test_findall_order_of_solutions`
  - `test_findall_template_vars_not_in_goal`
  - `test_findall_uninstantiated_template_var_in_goal`
- **複雑な系** (1件)
  - `test_findall_complex_goal_conjunction`

#### test_multiple_input.py (12件)
- **不正な系** (4件)
  - `test_first_input_invalid_then_valid`
  - `test_second_input_invalid_then_valid`
  - `test_both_inputs_invalid_then_valid`
  - `test_multiple_invalid_attempts`
- **機能系** (6件)
  - `test_valid_two_numbers`
  - `test_negative_numbers`
  - `test_decimal_numbers`
  - `test_zero_values`
  - `test_large_numbers`
  - `test_input_prompts_appear`
- **述語系** (2件)
  - `test_individual_predicates`
  - `test_validation_predicate_direct`

#### test_peek_char.py (16件)
- **単一化系** (2件)
  - `test_peek_char_unification_success`
  - `test_peek_char_unification_failure`
- **基本的な系** (2件)
  - `test_peek_char_basic`
  - `test_basic_functionality`
- **機能系** (12件)
  - `test_peek_char_at_eof`
  - `test_peek_char_empty_stream`
  - `test_peek_char_multibyte`
  - `test_at_end_of_stream_progression`
  - `test_supports_peek_operations`
  - `test_get_stream_status`
  - `test_peek_char_eof`
  - `test_peek_char_mixed_operations`
  - `test_at_end_of_stream_false`
  - `test_at_end_of_stream_true`
  - ...他2件

#### test_recursive_rules.py (4件)
- **機能系** (2件)
  - `test_peano_addition`
  - `test_left_recursion_problem_naive_ancestor`
- **述語系** (2件)
  - `test_member_predicate`
  - `test_ancestor_predicate`

### コアデータ型 (85件)

#### test_binding_environment.py (11件)
- **バインディング系** (2件)
  - `test_binding_conflicts`
  - `test_term_binding`
- **変数系** (3件)
  - `test_variable_shadowing`
  - `test_variable_scoping`
  - `test_variable_to_variable_binding`
- **機能系** (6件)
  - `test_bind_and_get_value`
  - `test_parent_environment_inheritance`
  - `test_copy_environment`
  - `test_copy_with_parent_environment`
  - `test_empty_environment`
  - `test_environment_representation`

#### test_merge_bindings.py (15件)
- **バインディング系** (6件)
  - `test_merge_binding_environments`
  - `test_merge_dict_with_binding_environment`
  - `test_bindings_to_dict`
  - `test_dict_to_binding_environment`
  - `test_empty_bindings_conversion`
  - `test_apply_substitution_with_binding_environment`
- **変数系** (1件)
  - `test_merge_variable_with_concrete_value`
- **機能系** (7件)
  - `test_merge_dictionaries`
  - `test_merge_conflicting_dictionaries`
  - `test_merge_with_none`
  - `test_conflict_resolution`
  - `test_mixed_merging`
  - `test_nested_environment_conversion`
  - `test_apply_substitution_with_dict`
- **複雑な系** (1件)
  - `test_apply_substitution_complex_terms`

#### test_new_operators.py (14件)
- **ルール系** (2件)
  - `test_rule_with_new_operators`
  - `test_rule_with_alt_operator`
- **機能系** (3件)
  - `test_not_equal_mixed_types`
  - `test_not_equal_alt_mixed_types`
  - `test_compound_expressions`
- **演算子系** (9件)
  - `test_not_equal_operator_different_atoms`
  - `test_not_equal_operator_same_atoms`
  - `test_not_equal_operator_different_numbers`
  - `test_not_equal_operator_same_numbers`
  - `test_not_equal_alt_operator_different_atoms`
  - `test_not_equal_alt_operator_same_atoms`
  - `test_not_equal_alt_operator_different_numbers`
  - `test_not_equal_alt_operator_same_numbers`
  - `test_comparison_with_traditional_operator`

#### test_operators.py (14件)
- **機能系** (2件)
  - `test_token_type_mapping`
  - `test_singleton_pattern`
- **演算子系** (12件)
  - `test_builtin_operators_registration`
  - `test_operator_precedence`
  - `test_operator_associativity`
  - `test_operator_types`
  - `test_user_defined_operators`
  - `test_operators_by_type`
  - `test_operators_by_precedence`
  - `test_operator_arity`
  - `test_operator_symbols_sorted`
  - `test_operator_info_validation`
  - ...他2件

#### test_types.py (16件)
- **リスト系** (5件)
  - `test_list_term_conversion`
  - `test_empty_list_representation`
  - `test_tail_list_representation`
  - `test_nested_list_representation`
  - `test_list_hashing`
- **作成系** (6件)
  - `test_atom_creation_and_equality`
  - `test_variable_creation_and_equality`
  - `test_number_creation_and_operations`
  - `test_string_creation_and_operations`
  - `test_term_creation_and_structure`
  - `test_rule_and_fact_creation`
- **単純な系** (1件)
  - `test_simple_list_representation`
- **機能系** (2件)
  - `test_nested_terms`
  - `test_mixed_data_types`
- **等価性系** (1件)
  - `test_list_equality`
- **複雑な系** (1件)
  - `test_rule_with_complex_body`

#### test_variable_dereferencing.py (15件)
- **バインディング系** (1件)
  - `test_binding_update_dereferencing`
- **リスト系** (1件)
  - `test_dereferencing_in_list_context`
- **単純な系** (1件)
  - `test_simple_dereferencing`
- **参照解決系** (5件)
  - `test_chain_dereferencing`
  - `test_partial_dereferencing`
  - `test_mixed_type_dereferencing`
  - `test_dereferencing_with_occurs_check`
  - `test_dereferencing_performance`
- **変数系** (2件)
  - `test_unbound_variable_handling`
  - `test_nested_variable_chains`
- **機能系** (4件)
  - `test_circular_reference_detection`
  - `test_multi_level_chain`
  - `test_self_reference`
  - `test_environment_isolation`
- **複雑な系** (1件)
  - `test_complex_term_dereferencing`

### 統合テスト (54件)

#### test_end_to_end.py (40件)
- **エラー系** (1件)
  - `test_error_recovery`
- **クエリ系** (1件)
  - `test_query_parsing`
- **リスト系** (1件)
  - `test_list_operations`
- **ルール系** (1件)
  - `test_recursive_rules`
- **例外系** (1件)
  - `test_exception_handling`
- **単純な系** (1件)
  - `test_simple_queries`
- **基本的な系** (1件)
  - `test_performance_basic`
- **変数系** (1件)
  - `test_variable_scoping`
- **機能系** (22件)
  - `test_cut_behavior`
  - `test_negation_as_failure`
  - `test_runtime_state_management`
  - `test_comprehensive_scenario`
  - `test_multiple_solutions`
  - `test_constraint_satisfaction`
  - `test_database_operations`
  - `test_module_system`
  - `test_io_operations`
  - `test_term_inspection`
  - ...他12件
- **演算子系** (1件)
  - `test_operator_definitions`
- **算術系** (1件)
  - `test_arithmetic_integration`
- **統合系** (4件)
  - `test_memory_management_integration`
  - `test_parser_integration`
  - `test_type_checking_integration`
  - `test_edge_case_integration`
- **複雑な系** (2件)
  - `test_complex_queries`
  - `test_complex_unification`
- **述語系** (2件)
  - `test_meta_predicates`
  - `test_built_in_predicates`

#### test_fixed_medical.py (2件)
- **機能系** (2件)
  - `test_english_diagnosis_system`
  - `test_working_medical_diagnosis`

#### test_listing_export_integration.py (12件)
- **エラー系** (1件)
  - `test_error_recovery_in_mixed_operations`
- **リスト系** (5件)
  - `test_listing_shows_all_predicates`
  - `test_listing_specific_predicates`
  - `test_listing_and_export_consistency`
  - `test_listing_after_dynamic_changes`
  - `test_large_knowledge_base_listing`
- **機能系** (3件)
  - `test_export_facts_only_exports_facts`
  - `test_export_after_dynamic_changes`
  - `test_large_dataset_export`
- **統合系** (1件)
  - `test_japanese_integration`
- **複雑な系** (1件)
  - `test_complex_query_integration`
- **述語系** (1件)
  - `test_multiple_predicate_export`

### 開発ツール (53件)

#### test_explain_tool.py (14件)
- **クエリ系** (1件)
  - `test_explain_rule_query`
- **不正な系** (3件)
  - `test_explain_invalid_query`
  - `test_explain_with_invalid_format`
  - `test_parse_invalid_command_format`
- **単純な系** (1件)
  - `test_explain_simple_fact_query`
- **機能系** (8件)
  - `test_explain_tool_initialization`
  - `test_explain_with_tree_format`
  - `test_explain_with_json_format`
  - `test_explain_with_depth_limit`
  - `test_parse_full_command`
  - `test_parse_command_with_default_depth`
  - `test_parse_command_with_default_format_and_depth`
  - `test_parse_command_with_unquoted_format`
- **述語系** (1件)
  - `test_explain_nonexistent_predicate`

#### test_search_tool.py (21件)
- **不正な系** (2件)
  - `test_search_invalid_type`
  - `test_parse_search_invalid_command_format`
- **機能系** (16件)
  - `test_search_tool_initialization`
  - `test_search_argument_match`
  - `test_search_full_text_match`
  - `test_search_with_limit`
  - `test_search_nonexistent_pattern`
  - `test_search_empty_pattern`
  - `test_format_results_text`
  - `test_format_results_json`
  - `test_format_results_table`
  - `test_get_search_statistics`
  - ...他6件
- **複雑な系** (1件)
  - `test_search_complex_pattern`
- **述語系** (2件)
  - `test_search_predicate_exact_match`
  - `test_search_predicate_partial_match`

#### test_validate_tool.py (18件)
- **エラー系** (1件)
  - `test_format_error_result`
- **不正な系** (1件)
  - `test_validate_invalid_check_type`
- **機能系** (15件)
  - `test_validate_tool_initialization`
  - `test_validate_all_checks`
  - `test_validate_conflicts_only`
  - `test_validate_unreachable_only`
  - `test_validate_undefined_only`
  - `test_validate_with_detailed_analysis`
  - `test_format_results_text`
  - `test_format_results_json`
  - `test_format_results_detailed`
  - `test_get_validation_statistics`
  - ...他5件
- **複雑な系** (1件)
  - `test_validation_with_complex_rules`

### 統合入力システム (49件)

#### test_integration.py (14件)
- **エラー系** (2件)
  - `test_handler_error_predicate_failure`
  - `test_threading_error_recovery`
- **単一化系** (1件)
  - `test_unification_failure`
- **機能系** (8件)
  - `test_get_char_with_unified_input`
  - `test_read_line_with_unified_input`
  - `test_single_thread_vs_multi_thread_consistency`
  - `test_threaded_execution_with_delay`
  - `test_runtime_default_configuration`
  - `test_runtime_threaded_mode_enable`
  - `test_threaded_mixed_sequence`
  - `test_mode_switching_during_execution`
- **述語系** (3件)
  - `test_multiple_predicates_same_runtime`
  - `test_concurrent_predicate_execution`
  - `test_mixed_predicate_sequence`

#### test_io_manager_integration.py (1件)
- **機能系** (1件)
  - `test_request_input_char_line_peek`

#### test_io_predicate_base.py (14件)
- **エラー系** (1件)
  - `test_execute_with_io_error`
- **単一化系** (1件)
  - `test_execute_with_unification_failure`
- **機能系** (11件)
  - `test_argument_validation_success`
  - `test_argument_validation_failure`
  - `test_prompt_generation`
  - `test_eof_handling`
  - `test_number_conversion_success`
  - `test_number_conversion_failure`
  - `test_get_char_conversion`
  - `test_read_line_conversion`
  - `test_request_input_call`
  - `test_unify_with_argument`
  - ...他1件
- **述語系** (1件)
  - `test_multiple_predicates_same_runtime`

#### test_unified_input_system.py (20件)
- **エラー系** (2件)
  - `test_request_input_handler_error`
  - `test_handler_error_fallback`
- **作成系** (1件)
  - `test_input_event_creation`
- **機能系** (17件)
  - `test_initial_state`
  - `test_enable_disable`
  - `test_request_input_not_enabled`
  - `test_request_input_success`
  - `test_request_input_with_additional_params`
  - `test_multiple_requests`
  - `test_initial_state`
  - `test_set_input_handler`
  - `test_threading_mode_toggle`
  - `test_single_thread_mode_request`
  - ...他7件

### パーサー (41件)

#### test_parser.py (22件)
- **エラー系** (1件)
  - `test_parse_error_handling`
- **リスト系** (2件)
  - `test_parse_lists`
  - `test_parse_list_with_tail`
- **ルール系** (3件)
  - `test_parse_rules_and_facts`
  - `test_parse_japanese_rules`
  - `test_parse_conjunction_in_rule_body`
- **単純な系** (1件)
  - `test_parse_simple_terms`
- **変数系** (2件)
  - `test_parse_atoms_and_variables`
  - `test_parse_variables_and_atoms_distinction`
- **機能系** (9件)
  - `test_parse_numbers_and_strings`
  - `test_parse_parenthesized_expressions`
  - `test_parse_multiple_statements`
  - `test_parse_japanese_facts`
  - `test_parse_japanese_string_as_atom_in_term`
  - `test_parse_mixed_japanese_english_terms`
  - `test_parse_empty_source`
  - `test_parse_comments_ignored`
  - `test_parse_whitespace_handling`
- **演算子系** (1件)
  - `test_parse_operators_with_precedence`
- **算術系** (1件)
  - `test_parse_arithmetic_expressions`
- **複雑な系** (2件)
  - `test_parse_complex_terms`
  - `test_parse_complex_rule`

#### test_scanner.py (19件)
- **エラー系** (1件)
  - `test_error_cases`
- **リスト系** (1件)
  - `test_list_syntax`
- **基本的な系** (1件)
  - `test_basic_tokens`
- **変数系** (2件)
  - `test_variables_and_atoms`
  - `test_japanese_variable_like_atoms`
- **機能系** (12件)
  - `test_numbers_and_strings`
  - `test_special_characters`
  - `test_comments_handling`
  - `test_keywords_recognition`
  - `test_whitespace_handling`
  - `test_line_tracking`
  - `test_float_numbers`
  - `test_empty_source`
  - `test_multiline_string`
  - `test_japanese_atoms`
  - ...他2件
- **演算子系** (1件)
  - `test_operators_scanning`
- **複雑な系** (1件)
  - `test_complex_expression`

### バリデーション (31件)

#### test_analyzers.py (18件)
- **エラー系** (1件)
  - `test_all_analyzers_run_without_error`
- **機能系** (15件)
  - `test_conflict_analyzer_initialization`
  - `test_analyze_no_conflicts`
  - `test_analyze_with_conflicts`
  - `test_reachability_analyzer_initialization`
  - `test_get_entry_points`
  - `test_is_entry_point`
  - `test_should_ignore_unreachable`
  - `test_analyze_reachability`
  - `test_undefined_analyzer_initialization`
  - `test_collect_all_references`
  - ...他5件
- **述語系** (2件)
  - `test_find_similar_predicates`
  - `test_analyze_undefined_predicates`

#### test_validation_result.py (13件)
- **エラー系** (2件)
  - `test_has_errors_method`
  - `test_get_error_count_method`
- **作成系** (2件)
  - `test_validation_issue_creation`
  - `test_validation_result_creation`
- **機能系** (9件)
  - `test_validation_issue_to_dict`
  - `test_validation_issue_without_optional_fields`
  - `test_validation_issue_severity_validation`
  - `test_validation_result_empty`
  - `test_has_warnings_method`
  - `test_get_warning_count_method`
  - `test_get_info_count_method`
  - `test_summary_property`
  - `test_validation_result_with_large_dataset`

### 日本語サポート (16件)

#### test_medical_diagnosis_jp.py (16件)
- **エラー系** (1件)
  - `test_edge_cases_and_error_handling`
- **基本的な系** (2件)
  - `test_basic_disease_facts`
  - `test_basic_symptom_facts`
- **変数系** (1件)
  - `test_japanese_variable_support`
- **機能系** (11件)
  - `test_disease_symptom_relations`
  - `test_risk_factors`
  - `test_age_categories`
  - `test_season_factors`
  - `test_recommended_tests`
  - `test_emergency_level_assessment`
  - `test_symptom_match_score_calculation`
  - `test_comprehensive_patient_diagnosis`
  - `test_without_knowledge_base`
  - `test_japanese_atom_parsing`
  - ...他1件
- **述語系** (1件)
  - `test_auxiliary_predicates`

### ユーティリティ (11件)

#### test_functor_mapper.py (11件)
- **機能系** (11件)
  - `test_needs_mapping_japanese_functors`
  - `test_needs_mapping_unicode_functors`
  - `test_needs_mapping_unsafe_characters`
  - `test_mapping_generation_consistency`
  - `test_non_ascii_passthrough`
  - `test_existing_functor_collision_avoidance`
  - `test_register_existing_functors`
  - `test_extract_functors_from_string`
  - `test_clear_mapping`
  - `test_large_scale_mapping_performance`
  - ...他1件

### その他 (10件)

#### test_japanese_functor_support.py (10件)
- **基本的な系** (1件)
  - `test_functor_mapper_basic_functionality`
- **変数系** (1件)
  - `test_variable_vs_functor_distinction`
- **機能系** (4件)
  - `test_collision_avoidance`
  - `test_mapping_consistency`
  - `test_performance_large_scale`
  - `test_unicode_character_sets`
- **統合系** (3件)
  - `test_parser_integration`
  - `test_runtime_integration`
  - `test_scanner_integration`
- **複雑な系** (1件)
  - `test_complex_japanese_expressions`

### ベンチマークガードレール (7件)

#### test_guardrails_semantics.py (7件)
- **エラー系** (2件)
  - `test_guardrail_undefined_predicate_raises_existence_error`
  - `test_guardrail_undeclared_predicate_after_retract_raises_error`
- **機能系** (4件)
  - `test_guardrail_dynamic_update_and_index_consistency`
  - `test_guardrail_conjunction_solution_order_preserved`
  - `test_guardrail_retract_deletes_all_no_ghosts`
  - `test_guardrail_index_integrity_after_retract`
- **述語系** (1件)
  - `test_guardrail_dynamic_predicate_with_no_clauses_fails`

## 重複・冗長性分析
類似テスト数: 40グループ

### `end_to_end` 関連 (40件)
- test_simple_queries
- test_complex_queries
- test_recursive_rules
- test_arithmetic_integration
- test_list_operations
- ...他35件

### `interpreter` 関連 (31件)
- test_basic_fact_queries
- test_rule_resolution
- test_arithmetic_operations
- test_comparison_operations
- test_logical_operations
- ...他26件

### `execution_frames` 関連 (28件)
- test_frame_type_values
- test_goal_frame_initialization
- test_goal_frame_can_backtrack
- test_goal_frame_step_returns_none_when_exhausted
- test_goal_seq_frame_initialization
- ...他23件

### `logic_interpreter` 関連 (27件)
- test_unification_basic
- test_unification_complex
- test_unification_with_numbers
- test_occurs_check
- test_occurs_check_list_cycle
- ...他22件

### `parser` 関連 (22件)
- test_parse_atoms_and_variables
- test_parse_numbers_and_strings
- test_parse_simple_terms
- test_parse_complex_terms
- test_parse_lists
- ...他17件

## 推奨事項

### 統合可能性
- **ランタイムテスト**: 274件と多い。機能別にサブモジュール化を検討
- **統合テスト**: end_to_endが40件。シナリオ別にファイル分割推奨
- **コアテスト**: 型テストとバインディングテストに明確な重複なし（良好）

### 優先度の高い追加テスト
- パフォーマンステスト（現在7件のみ）
- エラーリカバリーシナリオ
- 大規模データセットでのストレステスト
