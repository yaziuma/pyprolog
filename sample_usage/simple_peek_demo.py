#!/usr/bin/env python3
"""
PyProlog 非ブロッキング入力機能 簡単なデモ

peek_char/1 と at_end_of_stream/0 述語の基本的な使用例を示します。
"""

from pyprolog.runtime.interpreter import Runtime
from pyprolog.runtime.io_streams import StringStream
from pyprolog.core.types import Variable


def demo_basic_functionality():
    """基本機能のデモ"""
    print("=== PyProlog 非ブロッキング入力機能デモ ===\n")

    runtime = Runtime()

    # 1. 基本的な peek_char 操作
    print("1. 基本的な peek_char/1 操作:")
    runtime.io_manager.set_input_stream(StringStream("hello"))

    # 先読み
    peek_result = runtime.query("peek_char(X)")
    print(f"   peek_char(X): X = {peek_result[0][Variable('X')]}")

    # 同じ文字がもう一度取得される
    peek_again = runtime.query("peek_char(Y)")
    print(f"   peek_char(Y): Y = {peek_again[0][Variable('Y')]}")
    print("   → ストリーム位置は変更されません")

    # 実際に消費
    consume_result = runtime.query("get_char(Z)")
    print(f"   get_char(Z): Z = {consume_result[0][Variable('Z')]}")

    # 次の文字
    next_peek = runtime.query("peek_char(W)")
    print(f"   次の peek_char(W): W = {next_peek[0][Variable('W')]}")

    print()

    # 2. EOF状態の確認
    print("2. at_end_of_stream/0 の使用:")

    # まだデータがある場合
    eof_result = runtime.query("at_end_of_stream")
    print(f"   データあり時: at_end_of_stream = {len(eof_result) > 0}")

    # 全て読み取り
    while not runtime.query("at_end_of_stream"):
        char_result = runtime.query("get_char(_)")
        if not char_result:
            break

    # EOF確認
    eof_after = runtime.query("at_end_of_stream")
    print(f"   全読み取り後: at_end_of_stream = {len(eof_after) > 0}")

    print()


def demo_conditional_reading():
    """条件付き読み取りのデモ（簡単版）"""
    print("3. 条件付き読み取りのデモ:")

    runtime = Runtime()

    # 基本的な文字確認ルール
    runtime.add_rule("""
    read_if_not_eof(Char) :-
        \\+ at_end_of_stream,
        get_char(Char).
    """)

    # テストケース1: データあり
    print("   データがある場合:")
    runtime.io_manager.set_input_stream(StringStream("abc"))

    result1 = runtime.query("read_if_not_eof(C1)")
    if result1:
        print(f"   読み取り成功: C1 = {result1[0][Variable('C1')]}")

    result2 = runtime.query("read_if_not_eof(C2)")
    if result2:
        print(f"   読み取り成功: C2 = {result2[0][Variable('C2')]}")

    # テストケース2: EOF
    print("   EOF の場合:")
    runtime.io_manager.set_input_stream(StringStream(""))

    result3 = runtime.query("read_if_not_eof(C3)")
    if result3:
        print(f"   読み取り成功: C3 = {result3[0][Variable('C3')]}")
    else:
        print("   読み取り失敗（EOF のため）")

    print()


def demo_peek_sequence():
    """連続 peek 操作のデモ"""
    print("4. 連続 peek 操作のデモ:")

    runtime = Runtime()
    runtime.io_manager.set_input_stream(StringStream("hello"))

    # 5回 peek して同じ文字が返ることを確認
    for i in range(5):
        peek_result = runtime.query("peek_char(X)")
        if peek_result:
            char = peek_result[0][Variable("X")]
            print(f"   peek #{i + 1}: {char}")

    # 一度読み取って次の文字に移動
    runtime.query("get_char(_)")
    peek_result = runtime.query("peek_char(Y)")
    if peek_result:
        char = peek_result[0][Variable("Y")]
        print(f"   文字消費後の peek: {char}")

    print()


def demo_japanese_support():
    """日本語文字サポートのデモ"""
    print("5. 日本語文字サポートのデモ:")

    runtime = Runtime()
    runtime.io_manager.set_input_stream(StringStream("こんにちは"))

    # 日本語文字を一つずつpeek & read
    chars = []
    while not runtime.query("at_end_of_stream"):
        # peek
        peek_result = runtime.query("peek_char(P)")
        if peek_result:
            char = peek_result[0][Variable("P")]
            print(f"   peek: '{char}'")
            chars.append(char)

        # read
        runtime.query("get_char(_)")

    print(f"   読み取った文字: {''.join(chars)}")

    print()


def main():
    """メイン実行関数"""
    try:
        demo_basic_functionality()
        demo_conditional_reading()
        demo_peek_sequence()
        demo_japanese_support()

        print("=" * 50)
        print("✅ デモ完了!")
        print("\n新機能により可能になったこと:")
        print("• 非破壊的な文字先読み (peek_char/1)")
        print("• EOF状態の確認 (at_end_of_stream/0)")
        print("• 入力待ちによるブロックの回避")
        print("• より柔軟な入力処理パターン")

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
