#!/usr/bin/env python3
"""
PyProlog基本使用例
基本的なランタイム操作とクエリ実行のサンプル
"""

from prolog import Runtime
from prolog.core.errors import PrologError
from utility import safe_get_variable
import sys
import io

# UTF-8出力の設定（Windows対応）
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer, 
        encoding='utf-8', 
        errors='replace'
    )

def basic_facts_and_queries():
    """基本的なファクトとクエリの例"""
    print("=== 基本的なファクトとクエリ ===")
    
    # ランタイムを初期化
    runtime = Runtime()
    
    # 基本的なファクトを追加
    runtime.add_rule("likes(mary, food).")
    runtime.add_rule("likes(mary, wine).")
    runtime.add_rule("likes(john, wine).")
    runtime.add_rule("likes(john, mary).")
    
    # ルールを追加
    runtime.add_rule("happy(X) :- likes(X, wine).")
    
    print("追加されたファクト:")
    print("- likes(mary, food).")
    print("- likes(mary, wine).")
    print("- likes(john, wine).")
    print("- likes(john, mary).")
    print("- happy(X) :- likes(X, wine).")
    print()
    
    # 単純なクエリ
    print("クエリ: likes(mary, food)")
    results = runtime.query("likes(mary, food)")
    print(f"結果: {len(results)} 件の解")
    print()
    
    # 変数を含むクエリ
    print("クエリ: likes(mary, X)")
    results = runtime.query("likes(mary, X)")
    print(f"結果: {len(results)} 件の解")
    for i, result in enumerate(results, 1):
        x_var = safe_get_variable(result, 'X')
        print(f"  {i}. X = {x_var}")
    print()
    
    # ルールを使ったクエリ
    print("クエリ: happy(X)")
    results = runtime.query("happy(X)")
    print(f"結果: {len(results)} 件の解")
    for i, result in enumerate(results, 1):
        x_var = safe_get_variable(result, 'X')
        print(f"  {i}. X = {x_var}")
    print()

def variable_unification_example():
    """変数の単一化の例"""
    print("=== 変数の単一化 ===")
    
    runtime = Runtime()
    
    # データを追加
    runtime.add_rule("person(tom, 25, engineer).")
    runtime.add_rule("person(mary, 30, doctor).")
    runtime.add_rule("person(bob, 35, teacher).")
    
    print("データ:")
    print("- person(tom, 25, engineer).")
    print("- person(mary, 30, doctor).")
    print("- person(bob, 35, teacher).")
    print()
    
    # 複数変数のクエリ
    print("クエリ: person(Name, Age, Job)")
    results = runtime.query("person(Name, Age, Job)")
    print(f"結果: {len(results)} 件の解")
    for i, result in enumerate(results, 1):
        name = safe_get_variable(result, 'Name')
        age = safe_get_variable(result, 'Age')
        job = safe_get_variable(result, 'Job')
        print(f"  {i}. Name={name}, Age={age}, Job={job}")
    print()
    
    # 条件付きクエリ
    print("クエリ: person(Name, Age, Job), Age > 30")
    results = runtime.query("person(Name, Age, Job), Age > 30")
    print(f"結果: {len(results)} 件の解")
    for i, result in enumerate(results, 1):
        name = safe_get_variable(result, 'Name')
        age = safe_get_variable(result, 'Age')
        job = safe_get_variable(result, 'Job')
        print(f"  {i}. Name={name}, Age={age}, Job={job}")
    print()

def list_operations_example():
    """リスト操作の例"""
    print("=== リスト操作 ===")
    
    runtime = Runtime()
    
    # memberを使った例
    print("クエリ: member(X, [1, 2, 3, 4, 5])")
    results = runtime.query("member(X, [1, 2, 3, 4, 5])")
    print(f"結果: {len(results)} 件の解")
    for i, result in enumerate(results, 1):
        x_var = safe_get_variable(result, 'X')
        print(f"  {i}. X = {x_var}")
    print()
    
    # appendを使った例
    print("クエリ: append([1, 2], [3, 4], L)")
    results = runtime.query("append([1, 2], [3, 4], L)")
    print(f"結果: {len(results)} 件の解")
    for i, result in enumerate(results, 1):
        l_var = safe_get_variable(result, 'L')
        print(f"  {i}. L = {l_var}")
    print()
    
    # appendを使ったリスト分割
    print("クエリ: append(X, Y, [a, b, c, d])")
    results = runtime.query("append(X, Y, [a, b, c, d])")
    print(f"結果: {len(results)} 件の解")
    for i, result in enumerate(results, 1):
        x_var = safe_get_variable(result, 'X')
        y_var = safe_get_variable(result, 'Y')
        print(f"  {i}. X={x_var}, Y={y_var}")
    print()

def error_handling_example():
    """エラーハンドリングの例"""
    print("=== エラーハンドリング ===")
    
    runtime = Runtime()
    
    # 正常なクエリ
    try:
        results = runtime.query("member(1, [1, 2, 3])")
        print("正常なクエリ: member(1, [1, 2, 3]) - 成功")
    except PrologError as e:
        print(f"エラー: {e}")
    
    # 存在しない述語
    try:
        results = runtime.query("undefined_predicate(X)")
        print("存在しない述語: 実行されました")
    except PrologError as e:
        print(f"存在しない述語エラー: {e}")
    
    # 構文エラー
    try:
        runtime.add_rule("invalid syntax here")
        print("構文エラー: 実行されました")
    except PrologError as e:
        print(f"構文エラー: {e}")
    
    print()

def main():
    """メイン関数"""
    print("PyProlog基本使用例")
    print("=" * 50)
    print()
    
    basic_facts_and_queries()
    variable_unification_example()
    list_operations_example()
    error_handling_example()
    
    print("基本使用例が完了しました。")

if __name__ == "__main__":
    main()