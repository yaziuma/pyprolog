#!/usr/bin/env python3
"""
PyProlog計算処理サンプル
算術演算、比較演算、複雑な数式の評価例
"""

from pyprolog import Runtime
from pyprolog.core.errors import PrologError
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

def basic_arithmetic():
    """基本的な算術演算の例"""
    print("=== 基本的な算術演算 ===")
    
    runtime = Runtime()
    
    # 基本的な算術演算
    test_cases = [
        ("X is 3 + 4", "加算"),
        ("X is 10 - 3", "減算"),
        ("X is 5 * 6", "乗算"),
        ("X is 15 / 3", "除算"),
        ("X is 2 ** 3", "べき乗"),
        ("X is 17 mod 5", "剰余"),
        ("X is 17 // 5", "整数除算"),
    ]
    
    for query, description in test_cases:
        try:
            results = runtime.query(query)
            if results:
                x_var = safe_get_variable(results[0], 'X')
                print(f"{description}: {query} -> X = {x_var}")
            else:
                print(f"{description}: {query} -> 解なし")
        except PrologError as e:
            print(f"{description}: {query} -> エラー: {e}")
    print()

def comparison_operations():
    """比較演算の例"""
    print("=== 比較演算 ===")
    
    runtime = Runtime()
    
    # 比較演算のテストケース
    test_cases = [
        ("5 =:= 5", "算術等価（真）"),
        ("5 =:= 6", "算術等価（偽）"),
        ("7 > 3", "大なり（真）"),
        ("3 > 7", "大なり（偽）"),
        ("5 =< 5", "以下（真）"),
        ("6 =< 5", "以下（偽）"),
        ("2 + 3 =:= 5", "式の等価（真）"),
        ("3 * 4 > 10", "式の比較（真）"),
    ]
    
    for query, description in test_cases:
        try:
            results = runtime.query(query)
            success = len(results) > 0
            print(f"{description}: {query} -> {success}")
        except PrologError as e:
            print(f"{description}: {query} -> エラー: {e}")
    print()

def complex_arithmetic():
    """複雑な算術式の例"""
    print("=== 複雑な算術式 ===")
    
    runtime = Runtime()
    
    # 複雑な算術式
    test_cases = [
        ("X is (3 + 4) * 2", "括弧付き計算"),
        ("X is 2 + 3 * 4", "演算子優先度"),
        ("X is 2 ** 3 + 1", "べき乗と加算"),
        ("X is sqrt(16)", "平方根（未実装の場合エラー）"),
        ("X is abs(-5)", "絶対値（未実装の場合エラー）"),
    ]
    
    for query, description in test_cases:
        try:
            results = runtime.query(query)
            if results:
                x_var = safe_get_variable(results[0], 'X')
                print(f"{description}: {query} -> X = {x_var}")
            else:
                print(f"{description}: {query} -> 解なし")
        except PrologError as e:
            print(f"{description}: {query} -> エラー: {e}")
    print()

def mathematical_rules():
    """数学ルールファイルを使った計算"""
    print("=== 数学ルールファイルを使った計算 ===")
    
    runtime = Runtime()
    
    # math_rules.plファイルを読み込み
    try:
        success = runtime.consult("sample_usage/math_rules.pl")
        if not success:
            print("math_rules.plの読み込みに失敗しました")
            return
        print("math_rules.plを読み込みました")
    except Exception as e:
        print(f"ファイル読み込みエラー: {e}")
        return
    
    # フィボナッチ数列
    print("\nフィボナッチ数列:")
    for i in range(8):
        try:
            results = runtime.query(f"fibonacci({i}, F)")
            if results:
                f_var = safe_get_variable(results[0], 'F')
                print(f"  fibonacci({i}) = {f_var}")
        except Exception as e:
            print(f"  fibonacci({i}) = エラー: {e}")
    
    # 階乗計算
    print("\n階乗計算:")
    for i in range(1, 6):
        try:
            results = runtime.query(f"factorial({i}, F)")
            if results:
                f_var = safe_get_variable(results[0], 'F')
                print(f"  {i}! = {f_var}")
        except Exception as e:
            print(f"  {i}! = エラー: {e}")
    
    # 最大公約数
    print("\n最大公約数:")
    gcd_tests = [(48, 18), (100, 25), (17, 13)]
    for x, y in gcd_tests:
        try:
            results = runtime.query(f"gcd({x}, {y}, G)")
            if results:
                g_var = safe_get_variable(results[0], 'G')
                print(f"  gcd({x}, {y}) = {g_var}")
        except Exception as e:
            print(f"  gcd({x}, {y}) = エラー: {e}")
    
    print()

def variable_arithmetic():
    """変数を含む算術処理"""
    print("=== 変数を含む算術処理 ===")
    
    runtime = Runtime()
    
    # 変数に値を束縛してから計算
    print("段階的な計算:")
    try:
        results = runtime.query("X = 10, Y = 5, Z is X + Y")
        if results:
            result = results[0]
            x_var = safe_get_variable(result, 'X')
            y_var = safe_get_variable(result, 'Y')
            z_var = safe_get_variable(result, 'Z')
            
            print(f"  X = {x_var}, Y = {y_var}, Z = X + Y = {z_var}")
    except Exception as e:
        print(f"  エラー: {e}")
    
    # 条件付き計算
    print("\n条件付き計算:")
    try:
        results = runtime.query("X = 15, Y = 7, X > Y, Z is X - Y")
        if results:
            result = results[0]
            x_var = safe_get_variable(result, 'X')
            y_var = safe_get_variable(result, 'Y')
            z_var = safe_get_variable(result, 'Z')
            
            print(f"  X = {x_var}, Y = {y_var}, X > Y なので Z = X - Y = {z_var}")
    except Exception as e:
        print(f"  エラー: {e}")
    
    print()

def temperature_conversion():
    """温度変換の例（math_rules.plから）"""
    print("=== 温度変換 ===")
    
    runtime = Runtime()
    
    # ルールを直接追加
    runtime.add_rule("celsius_to_fahrenheit(C, F) :- F is C * 9 / 5 + 32.")
    runtime.add_rule("fahrenheit_to_celsius(F, C) :- C is (F - 32) * 5 / 9.")
    
    # 摂氏から華氏へ
    celsius_temps = [0, 20, 37, 100]
    print("摂氏から華氏への変換:")
    for c in celsius_temps:
        try:
            results = runtime.query(f"celsius_to_fahrenheit({c}, F)")
            if results:
                f_var = safe_get_variable(results[0], 'F')
                print(f"  {c}°C = {f_var}°F")
        except Exception as e:
            print(f"  {c}°C = エラー: {e}")
    
    # 華氏から摂氏へ
    fahrenheit_temps = [32, 68, 98.6, 212]
    print("\n華氏から摂氏への変換:")
    for f in fahrenheit_temps:
        try:
            results = runtime.query(f"fahrenheit_to_celsius({f}, C)")
            if results:
                c_var = safe_get_variable(results[0], 'C')
                print(f"  {f}°F = {c_var}°C")
        except Exception as e:
            print(f"  {f}°F = エラー: {e}")
    
    print()

def main():
    """メイン関数"""
    print("PyProlog計算処理サンプル")
    print("=" * 50)
    print()
    
    basic_arithmetic()
    comparison_operations()
    complex_arithmetic()
    mathematical_rules()
    variable_arithmetic()
    temperature_conversion()
    
    print("計算処理サンプルが完了しました。")

if __name__ == "__main__":
    main()