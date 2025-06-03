#!/usr/bin/env python3
"""
PyPrologファイル読み込みサンプル
Prologファイルの読み込み、複数ファイルの統合、エラーハンドリング
"""

from prolog import Runtime
from prolog.core.errors import PrologError
import os

def demonstrate_single_file_loading():
    """単一ファイルの読み込み"""
    print("=== 単一ファイル読み込み ===")
    
    runtime = Runtime()
    
    # family.plファイルの読み込み
    family_file = "sample_usage/family.pl"
    print(f"ファイル読み込み: {family_file}")
    
    try:
        if os.path.exists(family_file):
            success = runtime.consult(family_file)
            if success:
                print("✓ ファイル読み込み成功")
                
                # 読み込まれたデータをテスト
                print("\n読み込まれたデータのテスト:")
                test_queries = [
                    "parent(tom, bob)",
                    "parent(X, Y)",
                    "father(tom, bob)"
                ]
                
                for query in test_queries:
                    results = runtime.query(query)
                    print(f"  {query}: {len(results)}件の解")
                    
            else:
                print("✗ ファイル読み込み失敗")
        else:
            print(f"✗ ファイルが見つかりません: {family_file}")
            
    except Exception as e:
        print(f"✗ エラー: {e}")
    
    print()

def demonstrate_multiple_file_loading():
    """複数ファイルの読み込み"""
    print("=== 複数ファイル読み込み ===")
    
    runtime = Runtime()
    
    files_to_load = [
        "sample_usage/family.pl",
        "sample_usage/math_rules.pl"
    ]
    
    loaded_files = []
    failed_files = []
    
    for filepath in files_to_load:
        print(f"読み込み中: {filepath}")
        try:
            if os.path.exists(filepath):
                success = runtime.consult(filepath)
                if success:
                    print(f"  ✓ 成功")
                    loaded_files.append(filepath)
                else:
                    print(f"  ✗ 失敗")
                    failed_files.append(filepath)
            else:
                print(f"  ✗ ファイルが存在しません")
                failed_files.append(filepath)
        except Exception as e:
            print(f"  ✗ エラー: {e}")
            failed_files.append(filepath)
    
    print(f"\n読み込み結果:")
    print(f"  成功: {len(loaded_files)}ファイル")
    print(f"  失敗: {len(failed_files)}ファイル")
    
    # 複数ファイルからのデータを使った統合クエリ
    if len(loaded_files) >= 2:
        print("\n統合クエリテスト:")
        try:
            # 家族関係のクエリ
            results = runtime.query("parent(X, Y)")
            print(f"  親子関係: {len(results)}件")
            
            # 数学計算のクエリ
            results = runtime.query("factorial(5, F)")
            if results:
                f_var = None
                for var_name, value in results[0].items():
                    if str(var_name) == 'F' or (hasattr(var_name, 'name') and var_name.name == 'F'):
                        f_var = value
                        break
                print(f"  5の階乗: {f_var}")
            else:
                print("  5の階乗: 計算失敗")
                
        except Exception as e:
            print(f"  統合クエリエラー: {e}")
    
    print()

def demonstrate_error_handling():
    """エラーハンドリング"""
    print("=== エラーハンドリング ===")
    
    runtime = Runtime()
    
    # 存在しないファイルの読み込み
    print("存在しないファイルの読み込みテスト:")
    non_existent_file = "sample_usage/non_existent.pl"
    try:
        success = runtime.consult(non_existent_file)
        print(f"  結果: {success}")
    except Exception as e:
        print(f"  エラー: {e}")
    
    # 不正な構文を含むファイルのシミュレーション
    print("\n構文エラーのシミュレーション:")
    try:
        # 直接不正な構文を追加してエラーをテスト
        runtime.add_rule("invalid syntax here")
        print("  構文エラーが検出されませんでした")
    except PrologError as e:
        print(f"  ✓ 構文エラーを正しく検出: {e}")
    except Exception as e:
        print(f"  予期しないエラー: {e}")
    
    print()

def demonstrate_file_content_verification():
    """ファイル内容の検証"""
    print("=== ファイル内容の検証 ===")
    
    runtime = Runtime()
    
    # ファイルを読み込んでから内容を検証
    test_file = "sample_usage/family.pl"
    if os.path.exists(test_file):
        try:
            success = runtime.consult(test_file)
            if success:
                print(f"✓ {test_file}を読み込みました")
                
                # 期待される述語が存在するかチェック
                expected_predicates = [
                    ("parent(tom, bob)", "基本的な親子関係"),
                    ("father(X, Y)", "父親関係のルール"),
                    ("ancestor(X, Y)", "先祖関係のルール"),
                    ("age(tom, Age)", "年齢情報")
                ]
                
                print("\n述語の存在確認:")
                for query, description in expected_predicates:
                    try:
                        results = runtime.query(query)
                        if results:
                            print(f"  ✓ {description}: 解あり ({len(results)}件)")
                            if len(results) <= 3:  # 少数の場合は表示
                                for i, result in enumerate(results, 1):
                                    vars_str = ", ".join(f"{k}={v}" for k, v in result.items())
                                    if vars_str:
                                        print(f"    {i}. {vars_str}")
                        else:
                            print(f"  ✗ {description}: 解なし")
                    except Exception as e:
                        print(f"  ✗ {description}: エラー - {e}")
                        
            else:
                print(f"✗ {test_file}の読み込みに失敗")
        except Exception as e:
            print(f"✗ ファイル読み込みエラー: {e}")
    else:
        print(f"✗ テストファイルが見つかりません: {test_file}")
    
    print()

def demonstrate_incremental_loading():
    """段階的な読み込み"""
    print("=== 段階的な読み込み ===")
    
    runtime = Runtime()
    
    # 段階1: 基本データの読み込み
    print("段階1: 基本家族データの読み込み")
    try:
        runtime.consult("sample_usage/family.pl")
        results = runtime.query("parent(X, Y)")
        print(f"  親子関係: {len(results)}件")
    except Exception as e:
        print(f"  エラー: {e}")
    
    # 段階2: 追加データをPythonで挿入
    print("\n段階2: 追加データをPythonで挿入")
    additional_rules = [
        "hobby(tom, reading).",
        "hobby(mary, cooking).",
        "hobby(bob, programming).",
        "common_hobby(X, Y) :- hobby(X, H), hobby(Y, H), X \\= Y."
    ]
    
    for rule in additional_rules:
        try:
            runtime.add_rule(rule)
            print(f"  + {rule}")
        except Exception as e:
            print(f"  ✗ エラー: {rule} - {e}")
    
    # 段階3: 数学ルールの追加読み込み
    print("\n段階3: 数学ルールの追加読み込み")
    try:
        runtime.consult("sample_usage/math_rules.pl")
        results = runtime.query("factorial(4, F)")
        if results:
            f_var = None
            for var_name, value in results[0].items():
                if str(var_name) == 'F' or (hasattr(var_name, 'name') and var_name.name == 'F'):
                    f_var = value
                    break
            print(f"  4の階乗計算: {f_var}")
        else:
            print("  4の階乗計算: 失敗")
    except Exception as e:
        print(f"  エラー: {e}")
    
    # 統合テスト
    print("\n統合テスト:")
    integrated_queries = [
        ("parent(X, Y), hobby(X, H)", "親の趣味"),
        ("common_hobby(X, Y)", "共通の趣味を持つ人"),
        ("factorial(3, F), parent(X, Y)", "階乗計算と親子関係の組み合わせ")
    ]
    
    for query, description in integrated_queries:
        try:
            results = runtime.query(query)
            print(f"  {description}: {len(results)}件の解")
        except Exception as e:
            print(f"  {description}: エラー - {e}")
    
    print()

def main():
    """メイン関数"""
    print("PyPrologファイル読み込みサンプル")
    print("=" * 50)
    print()
    
    demonstrate_single_file_loading()
    demonstrate_multiple_file_loading()
    demonstrate_error_handling()
    demonstrate_file_content_verification()
    demonstrate_incremental_loading()
    
    print("ファイル読み込みサンプルが完了しました。")

if __name__ == "__main__":
    main()