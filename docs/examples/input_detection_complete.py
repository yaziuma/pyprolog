#!/usr/bin/env python3
"""
PyProlog入力待ち検知の完全な実装例

このファイルは docs/入力待ち検知ガイド.md で説明されている
全ての方法を実際に動作する形で実装しています。
"""

import threading
import time
import queue
import asyncio
import concurrent.futures
from pyprolog.runtime.interpreter import Runtime
from pyprolog.runtime.io_streams import IOStream


# =============================================================================
# 方法1: カスタムストリーム方式 (最も実用的)
# =============================================================================


class InputDetectionStream(IOStream):
    """入力待ちを検知し、外部に通知するストリーム"""

    def __init__(self, input_callback=None, output_callback=None):
        self.input_callback = input_callback
        self.output_callback = output_callback
        self.input_history = []
        self.output_history = []

    def read_line(self):
        """行入力待ちを検知"""
        print("📥 [検知] 行入力要求を検知しました")

        if self.input_callback:
            result = self.input_callback("line_input_needed")
            if result:
                self.input_history.append(result)
                print(f"✅ [提供] 入力値: {result}")
                return result

        # デフォルト: 標準入力
        value = input("🎯 入力してください: ")
        self.input_history.append(value)
        return value

    def read_char(self):
        """文字入力待ちを検知"""
        print("📥 [検知] 文字入力要求を検知しました")

        if self.input_callback:
            result = self.input_callback("char_input_needed")
            if result:
                return result[0] if result else "x"

        value = input("🎯 文字を入力: ")
        return value[0] if value else "x"

    def write_char(self, char):
        if self.output_callback:
            self.output_callback(char)
        else:
            print(char, end="")
        self.output_history.append(char)

    def write_term(self, term):
        text = str(term)
        if self.output_callback:
            self.output_callback(text)
        else:
            print(text, end="")
        self.output_history.append(text)

    # その他の必須メソッド
    def read_term(self):
        pass

    def peek_char(self):
        return "x"

    def at_end_of_stream(self):
        return False


# =============================================================================
# 方法2: 監視スレッド方式
# =============================================================================


class PrologExecutionMonitor:
    """Prolog実行を監視して入力待ちを検知"""

    def __init__(self):
        self.runtime = None
        self.monitoring = False
        self.input_waiting = False
        self.event_log = []

    def setup_runtime(self):
        """監視機能付きランタイムをセットアップ"""
        self.runtime = Runtime()

        stream = InputDetectionStream(
            input_callback=self._on_input_needed, output_callback=self._on_output
        )

        self.runtime.io_manager.set_input_stream(stream)
        self.runtime.io_manager.set_output_stream(stream)

        return self.runtime

    def _on_input_needed(self, input_type):
        """入力待ち検知ハンドラ"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"🔍 [{timestamp}] 監視: 入力待ち検知 - {input_type}")

        self.input_waiting = True
        self._log_event("INPUT_DETECTED", input_type)

        # 外部システムから入力取得
        result = self._get_monitored_input(input_type)

        self.input_waiting = False
        self._log_event("INPUT_PROVIDED", result)

        return result

    def _log_event(self, event_type, data):
        """イベントログ記録"""
        self.event_log.append(
            {"timestamp": time.time(), "type": event_type, "data": data}
        )

    def _get_monitored_input(self, input_type):
        """監視下での入力取得"""
        # 実際のアプリケーションでは、ここで外部システム
        # (GUI、Web API、データベース等) から入力を取得

        test_inputs = {
            "line_input_needed": ["監視テスト1", "監視テスト2", "監視テスト3"],
            "char_input_needed": ["y", "n", "a"],
        }

        if input_type in test_inputs and test_inputs[input_type]:
            return test_inputs[input_type].pop(0)

        return f"default_{input_type[:4]}"

    def _on_output(self, text):
        """出力監視ハンドラ"""
        print(text, end="")
        self._log_event("OUTPUT", text)

    def execute_query_with_monitoring(self, query, program_file=None):
        """監視機能付きクエリ実行"""
        if program_file:
            self.runtime.consult(program_file)

        print(f"🚀 [監視開始] クエリ実行: {query}")
        self.monitoring = True
        self.event_log.clear()

        try:
            results = self.runtime.query(query)
            return results
        finally:
            self.monitoring = False
            self.input_waiting = False
            print(f"🏁 [監視終了] クエリ完了")

    def get_monitoring_report(self):
        """監視レポート生成"""
        input_events = [e for e in self.event_log if e["type"] == "INPUT_DETECTED"]
        output_events = [e for e in self.event_log if e["type"] == "OUTPUT"]

        return {
            "total_events": len(self.event_log),
            "input_detections": len(input_events),
            "output_events": len(output_events),
            "timeline": self.event_log,
        }


# =============================================================================
# 方法3: 非同期実行方式
# =============================================================================


class AsyncPrologExecutor:
    """非同期Prolog実行・入力待ち検知"""

    def __init__(self):
        self.runtime = None
        self.input_event = None
        self.input_queue = None
        self.current_input_type = None
        self.async_event_log = []

    async def setup_async_runtime(self):
        """非同期対応ランタイムセットアップ"""
        self.runtime = Runtime()
        self.input_event = asyncio.Event()
        self.input_queue = asyncio.Queue()

        stream = AsyncInputDetectionStream(self)
        self.runtime.io_manager.set_input_stream(stream)
        self.runtime.io_manager.set_output_stream(stream)

    async def execute_query_async(self, query, program_file=None, timeout=30.0):
        """非同期クエリ実行"""
        if program_file:
            self.runtime.consult(program_file)

        print(f"🚀 [非同期開始] クエリ実行: {query}")

        # 別スレッドでProlog実行
        loop = asyncio.get_event_loop()

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(self._execute_sync, query)

            start_time = time.time()

            # 入力待ち監視ループ
            while not future.done():
                if time.time() - start_time > timeout:
                    print("⏰ [タイムアウト] クエリ実行がタイムアウトしました")
                    break

                try:
                    # 短時間で入力イベント確認
                    await asyncio.wait_for(self.input_event.wait(), timeout=0.01)

                    await self._log_async_event(
                        "INPUT_DETECTED", self.current_input_type
                    )
                    print(f"⚡ [非同期検知] 入力待ち: {self.current_input_type}")

                    # 非同期で入力処理
                    input_value = await self._handle_input_async()
                    await self.input_queue.put(input_value)
                    await self._log_async_event("INPUT_PROVIDED", input_value)

                    self.input_event.clear()

                except asyncio.TimeoutError:
                    continue  # タイムアウト = まだ実行中

            try:
                result = future.result(timeout=1.0)
                print(f"🏁 [非同期完了] クエリ実行完了")
                return result
            except concurrent.futures.TimeoutError:
                print("⚠️ [警告] クエリ結果の取得がタイムアウトしました")
                return []

    def _execute_sync(self, query):
        """同期的なクエリ実行（スレッドプール内）"""
        return self.runtime.query(query)

    async def _handle_input_async(self):
        """非同期入力処理"""
        if self.current_input_type == "line_input_needed":
            return await self._get_async_line_input()
        elif self.current_input_type == "char_input_needed":
            return await self._get_async_char_input()

        return "async_default"

    async def _get_async_line_input(self):
        """非同期行入力"""
        # 実際の実装では:
        # - WebSocketからの入力待ち
        # - HTTP APIポーリング
        # - 非同期ファイル読み込み
        # 等を行います

        await asyncio.sleep(0.1)  # 模擬遅延
        async_inputs = ["非同期入力1", "非同期入力2", "非同期入力3"]

        return async_inputs.pop(0) if async_inputs else "async_default_line"

    async def _get_async_char_input(self):
        """非同期文字入力"""
        await asyncio.sleep(0.1)
        return "x"

    async def _log_async_event(self, event_type, data):
        """非同期イベントログ"""
        self.async_event_log.append(
            {"timestamp": time.time(), "type": event_type, "data": data}
        )


class AsyncInputDetectionStream(IOStream):
    """非同期入力検知ストリーム"""

    def __init__(self, executor):
        self.executor = executor

    def read_line(self):
        """非同期入力待ち通知（同期メソッド内）"""
        self.executor.current_input_type = "line_input_needed"

        # イベント設定（非同期側で検知）
        try:
            loop = asyncio.get_event_loop()
            asyncio.run_coroutine_threadsafe(self._set_input_event(), loop)

            # 入力結果を同期的に取得
            future = asyncio.run_coroutine_threadsafe(
                self.executor.input_queue.get(), loop
            )
            return future.result(timeout=10.0)

        except (concurrent.futures.TimeoutError, RuntimeError):
            print("⚠️ 非同期入力取得に失敗、フォールバック")
            return "fallback_input"

    async def _set_input_event(self):
        """入力イベント設定"""
        if self.executor.input_event:
            self.executor.input_event.set()

    def read_char(self):
        """非同期文字入力待ち"""
        self.executor.current_input_type = "char_input_needed"

        try:
            loop = asyncio.get_event_loop()
            asyncio.run_coroutine_threadsafe(self._set_input_event(), loop)

            future = asyncio.run_coroutine_threadsafe(
                self.executor.input_queue.get(), loop
            )
            result = future.result(timeout=10.0)
            return result[0] if result else "x"

        except (concurrent.futures.TimeoutError, RuntimeError):
            return "x"

    # その他の必須メソッド
    def write_char(self, char):
        print(char, end="")

    def write_term(self, term):
        print(str(term), end="")

    def read_term(self):
        pass

    def peek_char(self):
        return "x"

    def at_end_of_stream(self):
        return False


# =============================================================================
# テスト・デモプログラム
# =============================================================================


def test_method1_custom_stream():
    """方法1: カスタムストリーム方式のテスト"""
    print("\n" + "=" * 60)
    print("🧪 テスト1: カスタムストリーム方式")
    print("=" * 60)

    # 入力コールバック定義
    test_inputs = ["テスト値1", "テスト値2", "テスト値3"]
    input_index = 0

    def input_handler(input_type):
        nonlocal input_index
        if input_index < len(test_inputs):
            value = test_inputs[input_index]
            input_index += 1
            print(f"🎯 [コールバック] {input_type} -> {value}")
            return value
        return "default"

    # ランタイム設定
    runtime = Runtime()
    stream = InputDetectionStream(input_callback=input_handler)
    runtime.io_manager.set_input_stream(stream)
    runtime.io_manager.set_output_stream(stream)

    # テスト用Prologプログラム
    runtime.add_rule("""
    test_interaction :-
        write('名前を入力: '),
        read_line(Name),
        write('年齢を入力: '),
        read_line(Age),
        write('確認: '),
        read_line(Confirm),
        write('結果: '), write(Name), write(' ('), write(Age), write(') - '), write(Confirm), nl.
    """)

    # 実行
    results = runtime.query("test_interaction.")

    print(f"✅ 実行結果: {'成功' if results else '失敗'}")
    print(f"📝 入力履歴: {stream.input_history}")
    print(f"📤 出力履歴: {''.join(stream.output_history)}")

    return len(results) > 0


def test_method2_monitoring():
    """方法2: 監視スレッド方式のテスト"""
    print("\n" + "=" * 60)
    print("🧪 テスト2: 監視スレッド方式")
    print("=" * 60)

    # 監視システム初期化
    monitor = PrologExecutionMonitor()
    runtime = monitor.setup_runtime()

    # テスト用プログラム
    runtime.add_rule("""
    monitored_calc :-
        write('数値A: '),
        read_line(A),
        write('数値B: '),
        read_line(B),
        C is A + B,
        write('A + B = '), write(C), nl.
    """)

    # 監視実行
    results = monitor.execute_query_with_monitoring("monitored_calc.")

    # 監視レポート
    report = monitor.get_monitoring_report()
    print(f"✅ 実行結果: {'成功' if results else '失敗'}")
    print(f"📊 総イベント数: {report['total_events']}")
    print(f"📥 入力検知回数: {report['input_detections']}")
    print(f"📤 出力イベント数: {report['output_events']}")

    return len(results) > 0


async def test_method3_async():
    """方法3: 非同期実行方式のテスト"""
    print("\n" + "=" * 60)
    print("🧪 テスト3: 非同期実行方式")
    print("=" * 60)

    # 非同期実行システム初期化
    executor = AsyncPrologExecutor()
    await executor.setup_async_runtime()

    # テスト用プログラム
    executor.runtime.add_rule("""
    async_test :-
        write('非同期入力1: '),
        read_line(X),
        write('非同期入力2: '),
        read_line(Y),
        write('結果: '), write(X), write(' & '), write(Y), nl.
    """)

    # 非同期実行
    results = await executor.execute_query_async("async_test.", timeout=15.0)

    print(f"✅ 実行結果: {'成功' if results else '失敗'}")
    print(f"📊 非同期ログ: {len(executor.async_event_log)}件")

    return len(results) > 0


def demo_practical_applications():
    """実用的な応用例のデモ"""
    print("\n" + "=" * 60)
    print("🚀 実用的な応用例デモ")
    print("=" * 60)

    # 実用例1: 設定ファイルからの自動入力
    print("\n📁 例1: 設定ファイル連携")

    config_data = {"user_name": "Alice", "user_age": "30", "save_config": "yes"}

    def config_input_handler(input_type):
        if input_type == "line_input_needed":
            # 設定ファイルから順次取得
            keys = list(config_data.keys())
            if keys:
                key = keys[0]
                value = config_data.pop(key)
                print(f"📋 [設定] {key} -> {value}")
                return value
        return "config_default"

    runtime1 = Runtime()
    stream1 = InputDetectionStream(input_callback=config_input_handler)
    runtime1.io_manager.set_input_stream(stream1)
    runtime1.io_manager.set_output_stream(stream1)

    runtime1.add_rule("""
    setup_user :-
        write('ユーザー名: '),
        read_line(Name),
        write('年齢: '),
        read_line(Age),
        write('設定を保存？: '),
        read_line(Save),
        write('設定完了: '), write(Name), write(' ('), write(Age), write(') 保存='), write(Save), nl.
    """)

    results1 = runtime1.query("setup_user.")
    print(f"設定ファイル連携: {'成功' if results1 else '失敗'}")

    # 実用例2: 時間ベース入力制御
    print("\n⏰ 例2: 時間制御入力")

    time_based_inputs = ["朝の入力", "昼の入力", "夜の入力"]

    def time_based_handler(input_type):
        current_hour = time.localtime().tm_hour
        if time_based_inputs:
            value = time_based_inputs.pop(0)
            print(f"⏰ [{current_hour:02d}時] {value}")
            return value
        return "time_default"

    runtime2 = Runtime()
    stream2 = InputDetectionStream(input_callback=time_based_handler)
    runtime2.io_manager.set_input_stream(stream2)
    runtime2.io_manager.set_output_stream(stream2)

    runtime2.add_rule("""
    time_logger :-
        write('時刻1: '),
        read_line(T1),
        write('時刻2: '),
        read_line(T2),
        write('時刻3: '),
        read_line(T3),
        write('ログ: '), write(T1), write(' | '), write(T2), write(' | '), write(T3), nl.
    """)

    results2 = runtime2.query("time_logger.")
    print(f"時間制御入力: {'成功' if results2 else '失敗'}")


async def main():
    """メイン実行関数"""
    print("PyProlog 入力待ち検知 - 完全実装例")
    print("=" * 60)

    # 各方式のテスト実行
    success1 = test_method1_custom_stream()
    success2 = test_method2_monitoring()
    success3 = await test_method3_async()

    # 実用例デモ
    demo_practical_applications()

    # 結果まとめ
    print("\n" + "=" * 60)
    print("📊 テスト結果まとめ")
    print("=" * 60)
    print(f"方法1 (カスタムストリーム): {'✅ 成功' if success1 else '❌ 失敗'}")
    print(f"方法2 (監視スレッド): {'✅ 成功' if success2 else '❌ 失敗'}")
    print(f"方法3 (非同期実行): {'✅ 成功' if success3 else '❌ 失敗'}")

    all_success = success1 and success2 and success3
    print(f"\n🎯 総合結果: {'✅ 全テスト成功' if all_success else '⚠️ 一部失敗'}")

    return all_success


if __name__ == "__main__":
    try:
        # 非同期実行
        result = asyncio.run(main())
        exit_code = 0 if result else 1
        print(f"\n🏁 プログラム終了 (終了コード: {exit_code})")
        exit(exit_code)

    except KeyboardInterrupt:
        print("\n⚠️ プログラムが中断されました")
        exit(1)

    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback

        traceback.print_exc()
        exit(1)
