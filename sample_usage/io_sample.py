#!/usr/bin/env python3
"""
PyPrologI/O機能サンプル
入出力ストリーム管理、ファイルとの連携、対話的処理
"""

from prolog import Runtime
from prolog.core.errors import PrologError
from prolog.runtime.io_streams import StringStream, ConsoleStream

def demonstrate_string_stream_input():
    """文字列ストリームからの入力"""
    print("=== 文字列ストリームからの入力 ===")
    
    runtime = Runtime()
    
    # 入力データを準備
    input_data = "hello\nworld\ntest\nend\n"
    input_stream = StringStream(input_data)
    runtime.io_manager.set_input_stream(input_stream)
    
    print(f"入力データ: {repr(input_data)}")
    print("文字を順次読み込み:")
    
    # 文字を1つずつ読み込み
    chars_read = []
    for i in range(10):  # 最大10文字
        try:
            results = runtime.query("get_char(C)")
            if results:
                char = None
                for var_name, value in results[0].items():
                    if str(var_name) == 'C' or (hasattr(var_name, 'name') and var_name.name == 'C'):
                        char = value
                        break
                
                if char:
                    chars_read.append(char)
                    if char == '\n':
                        print(f"  {i+1}: '\\n' (改行)")
                    else:
                        print(f"  {i+1}: '{char}'")
                    
                    # 'end'まで読んだら終了
                    if len(chars_read) >= 3 and ''.join(chars_read[-3:]) == 'end':
                        print("  'end'を検出したため終了")
                        break
            else:
                print(f"  {i+1}: 読み込み失敗")
                break
                
        except Exception as e:
            print(f"  {i+1}: エラー - {e}")
            break
    
    print(f"読み込んだ文字: {chars_read}")
    print()

def demonstrate_string_stream_output():
    """文字列ストリームへの出力"""
    print("=== 文字列ストリームへの出力 ===")
    
    runtime = Runtime()
    
    # 出力バッファを準備
    output_buffer = []
    output_stream = StringStream("", output_buffer)
    runtime.io_manager.set_output_stream(output_stream)
    
    print("出力ストリームを設定しました")
    print("注意: write/1述語は実装状況により動作しない可能性があります")
    
    # 出力テスト（write述語が実装されている場合）
    try:
        # writeが実装されていれば動作
        runtime.query("write('Hello, World!')")
        runtime.query("write('\\n')")
        runtime.query("write('PyProlog I/O Test')")
        
        print("出力結果:")
        print(f"  バッファ内容: {output_buffer}")
        
    except Exception as e:
        print(f"出力テストでエラーが発生しました: {e}")
        print("これは write/1 述語が未実装の場合の正常な動作です")
    
    print()

def demonstrate_interactive_io():
    """対話的I/O処理"""
    print("=== 対話的I/O処理 ===")
    
    runtime = Runtime()
    
    # 対話シナリオをシミュレート
    conversation_data = "y\nn\ny\nquit\n"
    input_stream = StringStream(conversation_data)
    runtime.io_manager.set_input_stream(input_stream)
    
    print(f"対話データ: {repr(conversation_data)}")
    print("対話的な yes/no 判定:")
    
    # yes/no判定のルールを追加
    runtime.add_rule("yes_answer(y).")
    runtime.add_rule("yes_answer(yes).")
    runtime.add_rule("no_answer(n).")
    runtime.add_rule("no_answer(no).")
    runtime.add_rule("quit_command(quit).")
    runtime.add_rule("quit_command(exit).")
    
    questions = [
        "コーヒーは好きですか？",
        "プログラミングは楽しいですか？", 
        "Prologを学びたいですか？",
        "続行しますか？"
    ]
    
    for i, question in enumerate(questions):
        print(f"\n質問 {i+1}: {question}")
        try:
            # 文字を読み込み
            results = runtime.query("get_char(C)")
            if results:
                char = None
                for var_name, value in results[0].items():
                    if str(var_name) == 'C' or (hasattr(var_name, 'name') and var_name.name == 'C'):
                        char = value
                        break
                
                if char:
                    print(f"  入力: '{char}'")
                    
                    # 入力を判定
                    if char == 'y':
                        yes_results = runtime.query(f"yes_answer({char})")
                        if yes_results:
                            print("  回答: はい")
                    elif char == 'n':
                        no_results = runtime.query(f"no_answer({char})")
                        if no_results:
                            print("  回答: いいえ")
                    else:
                        print("  回答: 不明な入力")
                    
                    # 改行文字をスキップ
                    runtime.query("get_char(_)")  # 改行文字を読み飛ばし
                    
        except Exception as e:
            print(f"  エラー: {e}")
            break
    
    print()

def demonstrate_file_simulation():
    """ファイル操作のシミュレーション"""
    print("=== ファイル操作のシミュレーション ===")
    
    runtime = Runtime()
    
    # ファイル内容をシミュレート
    file_content = """fact(apple, fruit).
fact(carrot, vegetable).
fact(salmon, fish).
query(X, fruit).
"""
    
    input_stream = StringStream(file_content)
    runtime.io_manager.set_input_stream(input_stream)
    
    print("ファイル内容のシミュレーション:")
    print(file_content)
    
    # ファイルからデータを読み込んで処理
    print("ファイルからのデータ読み込み処理:")
    
    # 事前にルールを定義
    runtime.add_rule("process_fact(Item, Type) :- fact(Item, Type).")
    runtime.add_rule("answer_query(Item, Type) :- query(Item, Type), fact(Item, Type).")
    
    # ファイル内容に対応するファクトを手動で追加（実際のファイル読み込みをシミュレート）
    simulated_facts = [
        "fact(apple, fruit).",
        "fact(carrot, vegetable).",
        "fact(salmon, fish)."
    ]
    
    print("シミュレートされたファクトの追加:")
    for fact in simulated_facts:
        runtime.add_rule(fact)
        print(f"  + {fact}")
    
    # クエリの実行
    print("\nクエリの実行:")
    queries = [
        ("fact(X, fruit)", "果物の検索"),
        ("fact(X, vegetable)", "野菜の検索"),
        ("process_fact(apple, Type)", "りんごの分類"),
        ("answer_query(X, fruit)", "果物クエリの回答")
    ]
    
    for query, description in queries:
        try:
            results = runtime.query(query)
            print(f"  {description}: {len(results)}件")
            for result in results:
                var_strs = []
                for var_name, value in result.items():
                    var_strs.append(f"{var_name}={value}")
                if var_strs:
                    print(f"    - {', '.join(var_strs)}")
        except Exception as e:
            print(f"  {description}: エラー - {e}")
    
    print()

def demonstrate_stream_switching():
    """ストリームの切り替え"""
    print("=== ストリームの切り替え ===")
    
    runtime = Runtime()
    
    # 複数の入力ストリームを準備
    stream1_data = "stream1\ndata1\n"
    stream2_data = "stream2\ndata2\n"
    
    stream1 = StringStream(stream1_data)
    stream2 = StringStream(stream2_data)
    
    print("ストリーム1のデータ:", repr(stream1_data))
    print("ストリーム2のデータ:", repr(stream2_data))
    
    # ストリーム1から読み込み
    print("\nストリーム1から読み込み:")
    runtime.io_manager.set_input_stream(stream1)
    
    for i in range(3):
        try:
            results = runtime.query("get_char(C)")
            if results:
                char = None
                for var_name, value in results[0].items():
                    if str(var_name) == 'C' or (hasattr(var_name, 'name') and var_name.name == 'C'):
                        char = value
                        break
                if char:
                    if char == '\n':
                        print(f"  文字 {i+1}: '\\n'")
                    else:
                        print(f"  文字 {i+1}: '{char}'")
        except Exception as e:
            print(f"  読み込みエラー: {e}")
            break
    
    # ストリーム2に切り替え
    print("\nストリーム2に切り替え:")
    runtime.io_manager.set_input_stream(stream2)
    
    for i in range(3):
        try:
            results = runtime.query("get_char(C)")
            if results:
                char = None
                for var_name, value in results[0].items():
                    if str(var_name) == 'C' or (hasattr(var_name, 'name') and var_name.name == 'C'):
                        char = value
                        break
                if char:
                    if char == '\n':
                        print(f"  文字 {i+1}: '\\n'")
                    else:
                        print(f"  文字 {i+1}: '{char}'")
        except Exception as e:
            print(f"  読み込みエラー: {e}")
            break
    
    print()

def demonstrate_error_handling():
    """I/Oエラーハンドリング"""
    print("=== I/Oエラーハンドリング ===")
    
    runtime = Runtime()
    
    # 空のストリームでEOFテスト
    print("空ストリームでのEOFテスト:")
    empty_stream = StringStream("")
    runtime.io_manager.set_input_stream(empty_stream)
    
    try:
        results = runtime.query("get_char(C)")
        if results:
            char = None
            for var_name, value in results[0].items():
                if str(var_name) == 'C' or (hasattr(var_name, 'name') and var_name.name == 'C'):
                    char = value
                    break
            print(f"  読み込み結果: {char}")
        else:
            print("  読み込み失敗: 解なし")
    except Exception as e:
        print(f"  EOFエラー: {e}")
    
    # 不正な文字マッチング
    print("\n不正な文字マッチングテスト:")
    test_stream = StringStream("a")
    runtime.io_manager.set_input_stream(test_stream)
    
    try:
        # 'a'を読み込むが'b'とマッチさせようとする
        results = runtime.query("get_char(b)")
        if results:
            print("  予期しない成功")
        else:
            print("  正常: マッチ失敗")
    except Exception as e:
        print(f"  マッチエラー: {e}")
    
    print()

def main():
    """メイン関数"""
    print("PyPrologI/O機能サンプル")
    print("=" * 50)
    print()
    
    demonstrate_string_stream_input()
    demonstrate_string_stream_output()
    demonstrate_interactive_io()
    demonstrate_file_simulation()
    demonstrate_stream_switching()
    demonstrate_error_handling()
    
    print("I/O機能サンプルが完了しました。")

if __name__ == "__main__":
    main()