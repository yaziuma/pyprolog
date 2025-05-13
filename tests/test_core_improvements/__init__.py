# This file makes Python treat the directory as a package.

# Test File Execution Priority (based on original class groups):
#
# --- 0. スキャナーとパーサーの最小限テスト ---
#   test_tokenizer_parser.py
#
# --- 1. Basic Parsing, Types, and Simple Predicates ---
#   test_basic_parsing.py
#
# --- 1.5. 結合と単一化テスト ---
#   test_conjunction.py
#
# --- 2. List Processing ---
#   test_list_processing.py
#
# --- 2.5. より詳細なリスト操作テスト ---
#   test_advanced_lists.py
#
# --- 3. Arithmetic and 'is' Predicate ---
#   test_arithmetic.py
#
# --- 3.5. より詳細な算術演算テスト ---
#   test_advanced_arithmetic.py
#
# --- 4. Cut Operator ---
#   test_cut_operator.py
#
# --- 4.5. 制御フロー構造テスト ---
#   (Tests originally in TestControlFlowStructures are now in test_advanced_recursion.py)
#
# --- 5. Recursion (Non-list specific, or more complex) ---
#   test_recursion.py
#
# --- 5.5. より詳細な再帰テスト ---
#   test_advanced_recursion.py (also contains tests from original "4.5. 制御フロー構造テスト")
