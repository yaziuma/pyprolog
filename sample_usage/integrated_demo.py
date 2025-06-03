#!/usr/bin/env python3
"""
PyProlog統合デモ
テキストファイル読み込み、Pythonからの動的追加、計算処理、I/Oを含む総合例
"""

from prolog import Runtime
from prolog.core.errors import PrologError
from prolog.runtime.io_streams import StringStream
import os

def print_section(title):
    """セクションタイトルを表示"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def safe_get_variable(result_dict, var_name):
    """結果辞書から変数値を安全に取得"""
    for key, value in result_dict.items():
        if str(key) == var_name or (hasattr(key, 'name') and key.name == var_name):
            return value
    return 'unknown'

def load_prolog_files(runtime):
    """Prologファイルの読み込み"""
    print_section("1. Prologファイルの読み込み")
    
    files_to_load = [
        ("sample_usage/family.pl", "家族関係データ"),
        ("sample_usage/math_rules.pl", "数学計算ルール")
    ]
    
    loaded_files = []
    for filepath, description in files_to_load:
        try:
            if os.path.exists(filepath):
                success = runtime.consult(filepath)
                if success:
                    print(f"✓ {description} ({filepath}) を読み込みました")
                    loaded_files.append(filepath)
                else:
                    print(f"✗ {description} ({filepath}) の読み込みに失敗しました")
            else:
                print(f"✗ ファイルが見つかりません: {filepath}")
        except Exception as e:
            print(f"✗ {description} ({filepath}) 読み込みエラー: {e}")
    
    return loaded_files

def add_dynamic_rules(runtime):
    """Pythonから動的にルールを追加"""
    print_section("2. 動的ルール追加")
    
    # 会社の組織構造を追加
    print("会社の組織構造を追加:")
    company_rules = [
        "employee(alice, manager, 80000).",
        "employee(bob, developer, 60000).",
        "employee(charlie, developer, 55000).",
        "employee(diana, designer, 50000).",
        "employee(eve, intern, 25000).",
        "reports_to(bob, alice).",
        "reports_to(charlie, alice).",
        "reports_to(diana, alice).",
        "reports_to(eve, bob).",
        "department(alice, management).",
        "department(bob, engineering).",
        "department(charlie, engineering).",
        "department(diana, design).",
        "department(eve, engineering).",
        # ルール定義
        "salary_range(low) :- employee(_, _, Salary), Salary < 40000.",
        "salary_range(medium) :- employee(_, _, Salary), Salary >= 40000, Salary < 70000.",
        "salary_range(high) :- employee(_, _, Salary), Salary >= 70000.",
        "team_member(X, Y) :- reports_to(X, Y).",
        "team_member(X, Z) :- reports_to(X, Y), team_member(Y, Z).",
        "can_afford(Person, Amount) :- employee(Person, _, Salary), Salary >= Amount."
    ]
    
    for rule in company_rules:
        try:
            runtime.add_rule(rule)
            print(f"  + {rule}")
        except Exception as e:
            print(f"  ✗ エラー: {rule} - {e}")
    
    print(f"\n{len(company_rules)}個のルールを追加しました。")

def demonstrate_family_queries(runtime):
    """家族関係のクエリ実行"""
    print_section("3. 家族関係クエリ")
    
    family_queries = [
        ("parent(X, Y)", "全ての親子関係", ['X', 'Y']),
        ("grandparent(X, Y)", "祖父母関係", ['X', 'Y']),
        ("sibling(X, Y)", "兄弟姉妹関係", ['X', 'Y']),
        ("ancestor(tom, X)", "tomの子孫", ['X']),
        ("older(X, Y), parent(X, Y)", "子供より年上の親", ['X', 'Y'])
    ]
    
    for query, description, variables in family_queries:
        print(f"\n{description}: {query}")
        try:
            results = runtime.query(query)
            if results:
                print(f"  結果 ({len(results)}件):")
                for i, result in enumerate(results[:5], 1):  # 最初の5件のみ表示
                    var_values = [safe_get_variable(result, var) for var in variables]
                    var_display = ", ".join(f"{var}={val}" for var, val in zip(variables, var_values))
                    print(f"    {i}. {var_display}")
                if len(results) > 5:
                    print(f"    ... 他{len(results) - 5}件")
            else:
                print("  結果: なし")
        except Exception as e:
            print(f"  エラー: {e}")

def demonstrate_math_calculations(runtime):
    """数学計算のデモンストレーション"""
    print_section("4. 数学計算")
    
    # 基本的な算術演算
    print("基本算術演算:")
    arithmetic_tests = [
        ("X is 2 ** 10", "2の10乗"),
        ("X is 100 mod 7", "100を7で割った余り"),
        ("X is sqrt(144)", "144の平方根（未実装の場合エラー）")
    ]
    
    for query, description in arithmetic_tests:
        try:
            results = runtime.query(query)
            if results:
                x_val = safe_get_variable(results[0], 'X')
                print(f"  {description}: {x_val}")
            else:
                print(f"  {description}: 解なし")
        except Exception as e:
            print(f"  {description}: エラー - {e}")
    
    # フィボナッチ数列（math_rules.plから）
    print("\nフィボナッチ数列:")
    try:
        fib_results = []
        for i in range(10):
            results = runtime.query(f"fibonacci({i}, F)")
            if results:
                f_val = safe_get_variable(results[0], 'F')
                fib_results.append(str(f_val))
            else:
                break
        if fib_results:
            print(f"  F(0) to F({len(fib_results)-1}): {', '.join(fib_results)}")
    except Exception as e:
        print(f"  フィボナッチ計算エラー: {e}")
    
    # 給与関連の計算
    print("\n給与計算:")
    salary_queries = [
        ("employee(X, _, Salary), Salary > 55000", "高給取り"),
        ("findall(Person, can_afford(Person, 50000), HighEarners)", "5万以上稼げる人"),
        ("employee(alice, _, AliceSalary), employee(bob, _, BobSalary), Diff is AliceSalary - BobSalary", "AliceとBobの給与差")
    ]
    
    for query, description in salary_queries:
        try:
            results = runtime.query(query)
            if results:
                print(f"  {description}:")
                result = results[0]
                if 'HighEarners' in str(result) or any('HighEarners' in str(k) for k in result.keys()):
                    earners = safe_get_variable(result, 'HighEarners')
                    print(f"    リスト: {earners}")
                elif 'Diff' in str(result) or any('Diff' in str(k) for k in result.keys()):
                    diff = safe_get_variable(result, 'Diff')
                    print(f"    給与差: {diff}")
                else:
                    for key, value in result.items():
                        print(f"    {key}: {value}")
        except Exception as e:
            print(f"  {description}: エラー - {e}")

def demonstrate_io_operations(runtime):
    """I/O操作のデモンストレーション"""
    print_section("5. I/O操作")
    
    # 文字列ストリームを設定
    input_data = "hello\nworld\ntest\n"
    input_stream = StringStream(input_data)
    output_buffer = []
    output_stream = StringStream("", output_buffer)
    
    runtime.io_manager.set_input_stream(input_stream)
    runtime.io_manager.set_output_stream(output_stream)
    
    print(f"入力データ: {repr(input_data)}")
    print("文字読み込みテスト:")
    
    # 文字を順次読み込み
    chars_read = []
    for i in range(5):  # 最大5文字読み込み
        try:
            results = runtime.query("get_char(C)")
            if results:
                char = safe_get_variable(results[0], 'C')
                chars_read.append(char)
                print(f"  読み込み {i+1}: '{char}'")
            else:
                print(f"  読み込み {i+1}: 失敗")
                break
        except Exception as e:
            print(f"  読み込み {i+1}: エラー - {e}")
            break
    
    print(f"読み込んだ文字: {chars_read}")

def demonstrate_advanced_queries(runtime):
    """高度なクエリの例"""
    print_section("6. 高度なクエリ")
    
    # メタ述語を使った複雑なクエリ
    print("メタ述語を使った解収集:")
    meta_queries = [
        ("findall(X, employee(X, developer, _), Developers)", "全開発者"),
        ("findall([Name, Salary], employee(Name, _, Salary), AllEmployees)", "全従業員と給与"),
        ("findall(Dept, department(_, Dept), AllDepts)", "全部署（重複あり）")
    ]
    
    for query, description in meta_queries:
        try:
            results = runtime.query(query)
            if results:
                result = results[0]
                for key, value in result.items():
                    key_str = str(key)
                    if 'Developers' in key_str or 'AllEmployees' in key_str or 'AllDepts' in key_str:
                        print(f"  {description}: {value}")
                        break
            else:
                print(f"  {description}: 解なし")
        except Exception as e:
            print(f"  {description}: エラー - {e}")
    
    # 条件分岐を使った複雑なクエリ
    print("\n条件分岐クエリ:")
    try:
        results = runtime.query("employee(X, Job, Salary), (Salary > 60000 -> Status = senior; Status = junior)")
        if results:
            print("  従業員のシニア/ジュニア判定:")
            for i, result in enumerate(results[:3], 1):
                x_val = safe_get_variable(result, 'X')
                job_val = safe_get_variable(result, 'Job')
                salary_val = safe_get_variable(result, 'Salary')
                status_val = safe_get_variable(result, 'Status')
                print(f"    {i}. {x_val} ({job_val}, {salary_val}) -> {status_val}")
    except Exception as e:
        print(f"  条件分岐エラー: {e}")

def main():
    """メイン関数"""
    print("PyProlog統合デモ")
    print("このデモでは、ファイル読み込み、動的ルール追加、計算処理、I/Oの全機能を統合して使用します。")
    
    # ランタイムを初期化
    runtime = Runtime()
    
    try:
        # 1. ファイル読み込み
        loaded_files = load_prolog_files(runtime)
        
        # 2. 動的ルール追加
        add_dynamic_rules(runtime)
        
        # 3. 家族関係クエリ（ファイルから読み込んだデータを使用）
        if any('family.pl' in f for f in loaded_files):
            demonstrate_family_queries(runtime)
        else:
            print("\n家族関係ファイルが読み込まれていないため、スキップします。")
        
        # 4. 数学計算
        demonstrate_math_calculations(runtime)
        
        # 5. I/O操作
        demonstrate_io_operations(runtime)
        
        # 6. 高度なクエリ
        demonstrate_advanced_queries(runtime)
        
        print_section("完了")
        print("統合デモが正常に完了しました。")
        print("PyPrologの主要機能（ファイル読み込み、動的ルール追加、計算処理、I/O）を")
        print("組み合わせて使用する方法を確認できました。")
        
    except Exception as e:
        print(f"\n重大なエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()