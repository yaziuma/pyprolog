"""
統一入力システム統合テスト

IOPredicate、UnifiedInputSystem、IOManagerの統合動作と
Runtime統合、真の継続実行をテストする。
"""

import time
from unittest.mock import Mock
from typing import Optional

# テスト用のインポート
from tests.unified_input.test_io_predicate_base import (
    TestGetCharPredicate,
    TestReadLinePredicate,
    BindingEnvironment,
    Atom,
    Number,
)
from pyprolog.runtime.unified_input_system import (
    InputHandler,
    InputEvent,
    ContinuationHandle,
)
from pyprolog.runtime.io_manager import IOManager


class MockRuntime:
    """テスト用Runtime"""

    def __init__(self):
        self.io_manager = IOManager()
        self.logic_interpreter = Mock()

        # デフォルトで統一化は成功
        self.logic_interpreter.unify.return_value = (True, BindingEnvironment())

    def enable_threaded_input(self):
        """真の継続実行モードを有効化"""
        self.io_manager.enable_threading()

    def set_custom_input_handler(self, handler: InputHandler):
        """カスタム入力ハンドラを設定"""
        self.io_manager.set_input_handler(handler)


class IntegrationTestInputHandler(InputHandler):
    """統合テスト用InputHandler"""

    def __init__(self, input_sequence=None):
        """
        Args:
            input_sequence: 入力シーケンス（リスト）。順次返される
        """
        self.input_sequence = input_sequence or ["a", "hello", "5"]
        self.current_index = 0
        self.call_history = []
        self.delay_seconds = 0  # 遅延シミュレーション用

    def set_delay(self, seconds: float):
        """入力処理に遅延を設定（スレッド動作確認用）"""
        self.delay_seconds = seconds

    def handle_input_request(
        self, event: InputEvent, continuation: ContinuationHandle
    ) -> Optional[str]:
        self.call_history.append(event)

        # 遅延シミュレーション
        if self.delay_seconds > 0:
            time.sleep(self.delay_seconds)

        # 入力シーケンスから次の値を返す
        if self.current_index < len(self.input_sequence):
            value = self.input_sequence[self.current_index]
            self.current_index += 1
        else:
            value = None
        continuation.resume(value)
        return value


class TestIOPredicateIntegration:
    """IOPredicate統合テスト"""

    def test_get_char_with_unified_input(self):
        """get_char述語と統一入力システムの統合"""
        # 設定
        runtime = MockRuntime()
        handler = IntegrationTestInputHandler(["5", "a", ""])
        runtime.set_custom_input_handler(handler)

        predicate = TestGetCharPredicate("X")
        env = BindingEnvironment()

        # 1回目: 数字文字
        results = list(predicate.execute(runtime, env))
        assert len(results) == 1

        # 統一化が数値で呼ばれることを確認
        runtime.logic_interpreter.unify.assert_called_with("X", Number(5), env)

        # 2回目: アルファベット文字
        runtime.logic_interpreter.unify.reset_mock()
        results = list(predicate.execute(runtime, env))
        assert len(results) == 1

        runtime.logic_interpreter.unify.assert_called_with("X", Atom("a"), env)

        # 3回目: EOF
        runtime.logic_interpreter.unify.reset_mock()
        results = list(predicate.execute(runtime, env))
        assert len(results) == 1

        runtime.logic_interpreter.unify.assert_called_with(
            "X", Atom("end_of_file"), env
        )

        # InputHandlerの呼び出し履歴確認
        assert len(handler.call_history) == 3
        assert all(event.input_type == "char" for event in handler.call_history)
        assert all(event.predicate_name == "get_char" for event in handler.call_history)

    def test_read_line_with_unified_input(self):
        """read_line述語と統一入力システムの統合"""
        runtime = MockRuntime()
        handler = IntegrationTestInputHandler(["123", "hello", None])
        runtime.set_custom_input_handler(handler)

        predicate = TestReadLinePredicate("X")
        env = BindingEnvironment()

        # 1回目: 数値文字列
        results = list(predicate.execute(runtime, env))
        assert len(results) == 1

        runtime.logic_interpreter.unify.assert_called_with("X", Number(123), env)

        # 2回目: 一般文字列
        runtime.logic_interpreter.unify.reset_mock()
        results = list(predicate.execute(runtime, env))
        assert len(results) == 1

        runtime.logic_interpreter.unify.assert_called_with("X", Atom("hello"), env)

        # 3回目: EOF (None)
        runtime.logic_interpreter.unify.reset_mock()
        results = list(predicate.execute(runtime, env))
        assert len(results) == 1

        runtime.logic_interpreter.unify.assert_called_with(
            "X", Atom("end_of_file"), env
        )

    def test_multiple_predicates_same_runtime(self):
        """同一Runtime上での複数述語実行"""
        runtime = MockRuntime()
        handler = IntegrationTestInputHandler(["x", "test_line"])
        runtime.set_custom_input_handler(handler)

        get_char = TestGetCharPredicate("X")
        read_line = TestReadLinePredicate("Y")
        env = BindingEnvironment()

        # get_char実行
        char_results = list(get_char.execute(runtime, env))
        assert len(char_results) == 1

        # read_line実行
        line_results = list(read_line.execute(runtime, env))
        assert len(line_results) == 1

        # 両方の述語で統一化が呼ばれる
        assert runtime.logic_interpreter.unify.call_count == 2

        # InputHandlerの呼び出し履歴
        assert len(handler.call_history) == 2
        assert handler.call_history[0].input_type == "char"
        assert handler.call_history[1].input_type == "line"


class TestThreadedExecution:
    """スレッド化実行テスト"""

    def test_single_thread_vs_multi_thread_consistency(self):
        """デフォルト/明示有効化の一貫性"""
        # デフォルト設定
        runtime1 = MockRuntime()
        handler1 = IntegrationTestInputHandler(["single"])
        runtime1.set_custom_input_handler(handler1)

        predicate1 = TestReadLinePredicate("X")
        single_results = list(predicate1.execute(runtime1, BindingEnvironment()))

        # 明示的にスレッド有効化（冪等）
        runtime2 = MockRuntime()
        handler2 = IntegrationTestInputHandler(["multi"])
        runtime2.set_custom_input_handler(handler2)
        runtime2.enable_threaded_input()

        try:
            predicate2 = TestReadLinePredicate("X")
            multi_results = list(predicate2.execute(runtime2, BindingEnvironment()))

            # 結果の一貫性確認
            assert len(single_results) == len(multi_results)

        finally:
            runtime2.io_manager.shutdown()

    def test_threaded_execution_with_delay(self):
        """遅延ありスレッド実行（真の継続実行確認）"""
        runtime = MockRuntime()
        handler = IntegrationTestInputHandler(["delayed_input"])
        handler.set_delay(0.1)  # 100ms遅延

        runtime.set_custom_input_handler(handler)
        runtime.enable_threaded_input()

        try:
            predicate = TestReadLinePredicate("X")
            env = BindingEnvironment()

            # 実行時間測定
            start_time = time.time()
            results = list(predicate.execute(runtime, env))
            end_time = time.time()

            # 遅延が発生していることを確認
            execution_time = end_time - start_time
            assert execution_time >= 0.1

            # 正常に結果が得られることを確認
            assert len(results) == 1

            # 統一化が正しく呼ばれることを確認
            runtime.logic_interpreter.unify.assert_called_once_with(
                "X", Atom("delayed_input"), env
            )

        finally:
            runtime.io_manager.shutdown()

    def test_concurrent_predicate_execution(self):
        """複数述語の並行実行（スレッド安全性）"""
        runtime = MockRuntime()
        handler = IntegrationTestInputHandler(["input1", "input2", "input3", "input4"])
        handler.set_delay(0.05)  # 50ms遅延

        runtime.set_custom_input_handler(handler)
        runtime.enable_threaded_input()

        try:
            predicates = [
                TestReadLinePredicate("X1"),
                TestReadLinePredicate("X2"),
                TestReadLinePredicate("X3"),
                TestReadLinePredicate("X4"),
            ]

            # 並行実行用の関数
            def execute_predicate(pred, env):
                return list(pred.execute(runtime, env))

            # 複数スレッドで並行実行
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                futures = []
                for pred in predicates:
                    future = executor.submit(
                        execute_predicate, pred, BindingEnvironment()
                    )
                    futures.append(future)

                # 全ての結果を取得
                results = []
                for future in concurrent.futures.as_completed(futures, timeout=5.0):
                    result = future.result()
                    results.append(result)

            # 全ての述語が成功
            assert len(results) == 4
            assert all(len(result) == 1 for result in results)

            # 統一化が正しい回数呼ばれる
            assert runtime.logic_interpreter.unify.call_count == 4

        finally:
            runtime.io_manager.shutdown()


class TestErrorHandling:
    """エラーハンドリング統合テスト"""

    def test_handler_error_predicate_failure(self):
        """InputHandlerエラー時の述語失敗"""
        runtime = MockRuntime()

        # エラーハンドラ
        class ErrorHandler(InputHandler):
            def handle_input_request(
                self, event: InputEvent, continuation: ContinuationHandle
            ) -> Optional[str]:
                raise Exception("Input error")

        runtime.set_custom_input_handler(ErrorHandler())

        predicate = TestGetCharPredicate("X")
        env = BindingEnvironment()

        # 述語実行（エラーにより失敗）
        results = list(predicate.execute(runtime, env))

        # 述語失敗（空のリスト）
        assert len(results) == 0

        # 統一化は呼ばれない
        runtime.logic_interpreter.unify.assert_not_called()

    def test_unification_failure(self):
        """統一化失敗時の処理"""
        runtime = MockRuntime()
        handler = IntegrationTestInputHandler(["test"])
        runtime.set_custom_input_handler(handler)

        # 統一化を失敗させる
        runtime.logic_interpreter.unify.return_value = (False, None)

        predicate = TestReadLinePredicate("X")
        env = BindingEnvironment()

        # 述語実行
        results = list(predicate.execute(runtime, env))

        # 統一化失敗により述語失敗
        assert len(results) == 0

        # InputHandlerは呼ばれている
        assert len(handler.call_history) == 1

        # 統一化は呼ばれている
        runtime.logic_interpreter.unify.assert_called_once_with("X", Atom("test"), env)

    def test_threading_error_recovery(self):
        """スレッドエラーからの回復"""
        runtime = MockRuntime()

        # 最初はエラー、その後成功するハンドラ
        class RecoveryHandler(InputHandler):
            def __init__(self):
                self.call_count = 0

            def handle_input_request(
                self, event: InputEvent, continuation: ContinuationHandle
            ) -> Optional[str]:
                self.call_count += 1
                if self.call_count == 1:
                    raise Exception("First call error")
                else:
                    continuation.resume("recovered")
                    return "recovered"

        handler = RecoveryHandler()
        runtime.set_custom_input_handler(handler)
        runtime.enable_threaded_input()

        try:
            predicate1 = TestReadLinePredicate("X1")
            predicate2 = TestReadLinePredicate("X2")

            # 1回目: エラーにより述語失敗
            results1 = list(predicate1.execute(runtime, BindingEnvironment()))
            assert len(results1) == 0

            # 2回目: 回復して成功
            results2 = list(predicate2.execute(runtime, BindingEnvironment()))
            assert len(results2) == 1

        finally:
            runtime.io_manager.shutdown()


class TestRuntimeIntegration:
    """Runtime統合テスト"""

    def test_runtime_default_configuration(self):
        """Runtimeのデフォルト設定"""
        runtime = MockRuntime()

        # デフォルトでスレッドモードが有効
        assert runtime.io_manager.unified_input.threading_enabled

    def test_runtime_threaded_mode_enable(self):
        """Runtime真の継続実行モード有効化"""
        runtime = MockRuntime()
        handler = IntegrationTestInputHandler(["runtime_test"])

        runtime.set_custom_input_handler(handler)
        runtime.enable_threaded_input()

        try:
            # スレッドモードが有効化されることを確認
            assert runtime.io_manager.unified_input.threading_enabled

            # 述語実行
            predicate = TestReadLinePredicate("X")
            results = list(predicate.execute(runtime, BindingEnvironment()))

            assert len(results) == 1
            assert len(handler.call_history) == 1

        finally:
            runtime.io_manager.shutdown()


class TestComplexScenarios:
    """複雑なシナリオテスト"""

    def test_mixed_predicate_sequence(self):
        """混在述語シーケンス実行"""
        runtime = MockRuntime()
        handler = IntegrationTestInputHandler(
            [
                "a",  # get_char用
                "hello",  # read_line用
                "5",  # get_char用
                "world",  # read_line用
            ]
        )
        runtime.set_custom_input_handler(handler)

        # 述語シーケンス
        predicates = [
            TestGetCharPredicate("A"),
            TestReadLinePredicate("B"),
            TestGetCharPredicate("C"),
            TestReadLinePredicate("D"),
        ]

        env = BindingEnvironment()

        # 順次実行
        for i, predicate in enumerate(predicates):
            runtime.logic_interpreter.unify.reset_mock()
            results = list(predicate.execute(runtime, env))

            assert len(results) == 1

            # 適切な値で統一化が呼ばれることを確認
            if i == 0:  # get_char: "a"
                runtime.logic_interpreter.unify.assert_called_with("A", Atom("a"), env)
            elif i == 1:  # read_line: "hello"
                runtime.logic_interpreter.unify.assert_called_with(
                    "B", Atom("hello"), env
                )
            elif i == 2:  # get_char: "5"
                runtime.logic_interpreter.unify.assert_called_with("C", Number(5), env)
            elif i == 3:  # read_line: "world"
                runtime.logic_interpreter.unify.assert_called_with(
                    "D", Atom("world"), env
                )

        # 全入力が消費されたことを確認
        assert handler.current_index == len(handler.input_sequence)

    def test_threaded_mixed_sequence(self):
        """スレッド化混在シーケンス"""
        runtime = MockRuntime()
        handler = IntegrationTestInputHandler(["t1", "t2", "t3"])
        handler.set_delay(0.02)  # 短い遅延

        runtime.set_custom_input_handler(handler)
        runtime.enable_threaded_input()

        try:
            predicates = [
                TestReadLinePredicate("X1"),
                TestReadLinePredicate("X2"),
                TestReadLinePredicate("X3"),
            ]

            # 順次実行（各々でスレッドブロッキング発生）
            all_results = []
            for predicate in predicates:
                results = list(predicate.execute(runtime, BindingEnvironment()))
                all_results.extend(results)

            # 全て成功
            assert len(all_results) == 3

            # 統一化が正しく呼ばれる
            assert runtime.logic_interpreter.unify.call_count == 3

            # InputHandlerが適切に呼ばれる
            assert len(handler.call_history) == 3

        finally:
            runtime.io_manager.shutdown()

    def test_mode_switching_during_execution(self):
        """実行中のスレッド有効化が冪等であることを確認"""
        runtime = MockRuntime()
        handler = IntegrationTestInputHandler(["mode1", "mode2", "mode3"])
        runtime.set_custom_input_handler(handler)

        # デフォルトで1回実行
        predicate1 = TestReadLinePredicate("X1")
        results1 = list(predicate1.execute(runtime, BindingEnvironment()))
        assert len(results1) == 1
        assert runtime.io_manager.unified_input.threading_enabled

        # スレッドモードを再度有効化（冪等）
        runtime.enable_threaded_input()

        try:
            predicate2 = TestReadLinePredicate("X2")
            results2 = list(predicate2.execute(runtime, BindingEnvironment()))
            assert len(results2) == 1
            assert runtime.io_manager.unified_input.threading_enabled
            
            predicate3 = TestReadLinePredicate("X3")
            results3 = list(predicate3.execute(runtime, BindingEnvironment()))
            assert len(results3) == 1
            assert runtime.io_manager.unified_input.threading_enabled

        finally:
            runtime.io_manager.shutdown()

        # 全ての実行が成功
        assert len(handler.call_history) == 3
