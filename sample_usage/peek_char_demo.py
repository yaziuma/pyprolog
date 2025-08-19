#!/usr/bin/env python3
"""
PyProlog 非ブロッキング入力機能デモ

peek_char/1 と at_end_of_stream/0 述語の使用例を示します。
これらの述語により、入力待ちによるブロックを避けながら
条件付きの入力処理が可能になります。
"""

from pyprolog.runtime.interpreter import Runtime
from pyprolog.runtime.io_streams import StringStream
from pyprolog.core.types import Variable


def demo_basic_peek_operations():
    """基本的な peek 操作のデモ"""
    print("=== 基本的な peek 操作のデモ ===")

    runtime = Runtime()
    runtime.io_manager.set_input_stream(StringStream("hello world"))

    # 1. peek_char/1: 非破壊的先読み
    print("1. peek_char/1 を使用した非破壊的先読み:")
    peek_result = runtime.query("peek_char(X)")
    print(f"   peek_char(X): X = {peek_result[0][Variable('X')]}")

    # 同じ文字がもう一度取得される
    peek_again = runtime.query("peek_char(Y)")
    print(f"   peek_char(Y): Y = {peek_again[0][Variable('Y')]}")
    print("   → ストリーム位置は変更されません")

    # 2. 実際の文字消費
    print("\n2. 実際の文字消費:")
    consume_result = runtime.query("get_char(Z)")
    print(f"   get_char(Z): Z = {consume_result[0][Variable('Z')]}")

    # 次の文字をpeek
    next_peek = runtime.query("peek_char(W)")
    print(f"   次の peek_char(W): W = {next_peek[0][Variable('W')]}")

    # 3. EOF確認
    print("\n3. EOF状態の確認:")
    eof_result = runtime.query("at_end_of_stream")
    print(f"   at_end_of_stream: {len(eof_result) > 0} (まだデータあり)")


def demo_conditional_reading():
    """条件付き読み取りのデモ"""
    print("\n\n=== 条件付き読み取りのデモ ===")

    runtime = Runtime()

    # 数字判定ルールを追加
    runtime.add_rule("""
    read_if_digit(Char) :-
        peek_char(Next),
        Next >= '0',
        Next =< '9',
        get_char(Char).
    """)

    # 文字判定ルールを追加
    runtime.add_rule("""
    read_if_letter(Char) :-
        peek_char(Next),
        Next >= 'a',
        Next =< 'z',
        get_char(Char).
    """)

    # テストケース1: 数字から始まる入力
    print("1. 数字から始まる入力 ('5abc'):")
    runtime.io_manager.set_input_stream(StringStream("5abc"))

    digit_result = runtime.query("read_if_digit(D)")
    if digit_result:
        print(f"   数字読み取り成功: D = {digit_result[0][Variable('D')]}")
    else:
        print("   数字読み取り失敗")

    letter_result = runtime.query("read_if_letter(L)")
    if letter_result:
        print(f"   文字読み取り成功: L = {letter_result[0][Variable('L')]}")
    else:
        print("   文字読み取り失敗")

    # テストケース2: 文字から始まる入力
    print("\n2. 文字から始まる入力 ('abc5'):")
    runtime.io_manager.set_input_stream(StringStream("abc5"))

    digit_result = runtime.query("read_if_digit(D2)")
    if digit_result:
        print(f"   数字読み取り成功: D2 = {digit_result[0][Variable('D2')]}")
    else:
        print("   数字読み取り失敗")

    letter_result = runtime.query("read_if_letter(L2)")
    if letter_result:
        print(f"   文字読み取り成功: L2 = {letter_result[0][Variable('L2')]}")
    else:
        print("   文字読み取り失敗")


def demo_parser_pattern():
    """パーサー実装パターンのデモ"""
    print("\n\n=== パーサー実装パターンのデモ ===")

    runtime = Runtime()

    # トークン種別判定ルール
    runtime.add_rule("""
    token_type(number) :-
        peek_char(C),
        C >= '0',
        C =< '9'.
        
    token_type(letter) :-
        peek_char(C),
        C >= 'a',
        C =< 'z'.
        
    token_type(space) :-
        peek_char(' ').
        
    token_type(eof) :-
        at_end_of_stream.
    """)

    # 空白スキップルール
    runtime.add_rule("""
    skip_spaces :-
        peek_char(' '),
        get_char(_),
        skip_spaces.
        
    skip_spaces :-
        peek_char(C),
        C \\= ' '.
    """)

    # テスト用入力
    test_inputs = ["123abc", "abc123", "   hello", ""]

    for i, test_input in enumerate(test_inputs, 1):
        print(f"{i}. 入力 '{test_input}':")
        runtime.io_manager.set_input_stream(StringStream(test_input))

        # 空白スキップ
        runtime.query("skip_spaces")

        # トークン種別判定
        token_results = []
        for token_type in ["number", "letter", "space", "eof"]:
            result = runtime.query(f"token_type({token_type})")
            if result:
                token_results.append(token_type)

        if token_results:
            print(f"   検出されたトークン: {', '.join(token_results)}")
        else:
            print("   トークンが検出されませんでした")


def demo_eof_handling():
    """EOF処理のデモ"""
    print("\n\n=== EOF処理のデモ ===")

    runtime = Runtime()

    # 入力を全て読み取るルール
    runtime.add_rule("""
    read_all_chars([]) :-
        at_end_of_stream.
        
    read_all_chars([H|T]) :-
        \\+ at_end_of_stream,
        get_char(H),
        read_all_chars(T).
    """)

    test_inputs = ["hi", "a", ""]

    for i, test_input in enumerate(test_inputs, 1):
        print(f"{i}. 入力 '{test_input}':")
        runtime.io_manager.set_input_stream(StringStream(test_input))

        # EOF確認
        eof_before = runtime.query("at_end_of_stream")
        print(f"   読み取り前のEOF状態: {len(eof_before) > 0}")

        # 全文字読み取り
        all_chars = runtime.query("read_all_chars(Chars)")
        if all_chars:
            chars = all_chars[0][Variable("Chars")]
            print(f"   読み取った文字: {chars}")

        # EOF確認
        eof_after = runtime.query("at_end_of_stream")
        print(f"   読み取り後のEOF状態: {len(eof_after) > 0}")


def demo_japanese_support():
    """日本語文字サポートのデモ"""
    print("\n\n=== 日本語文字サポートのデモ ===")

    runtime = Runtime()

    # 日本語文字の判定ルール
    runtime.add_rule("""
    is_hiragana(Char) :-
        peek_char(Char),
        Char >= 'あ',
        Char =< 'ん'.
    """)

    # テスト用日本語入力
    test_input = "こんにちは世界"
    print(f"入力: '{test_input}'")

    runtime.io_manager.set_input_stream(StringStream(test_input))

    # 各文字をpeekして表示
    for i in range(len(test_input)):
        peek_result = runtime.query("peek_char(C)")
        if peek_result:
            char = peek_result[0][Variable("C")]
            print(f"   位置 {i}: '{char}'")

            # ひらがな判定
            hiragana_result = runtime.query("is_hiragana(C)")
            is_hiragana = len(hiragana_result) > 0
            print(f"        ひらがな: {is_hiragana}")

        # 文字を消費
        runtime.query("get_char(_)")


def main():
    """メイン実行関数"""
    print("PyProlog 非ブロッキング入力機能デモ")
    print("=" * 50)

    try:
        demo_basic_peek_operations()
        demo_conditional_reading()
        demo_parser_pattern()
        demo_eof_handling()
        demo_japanese_support()

        print("\n" + "=" * 50)
        print("デモ完了！")
        print("\n新機能により以下が可能になりました：")
        print("• 非破壊的な文字先読み (peek_char/1)")
        print("• EOF状態の非破壊的確認 (at_end_of_stream/0)")
        print("• 条件付き入力処理")
        print("• パーサー・トークナイザーの実装")
        print("• 入力待ちによるブロックの回避")

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
