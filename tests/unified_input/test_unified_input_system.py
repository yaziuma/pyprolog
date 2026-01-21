"""
UnifiedInputSystemのテスト

統一入力システムの中央制御、InputHandlerルーティング、
シングル/マルチスレッドモード切り替えをテストする。
"""

import pytest
import threading
import time
import uuid
from unittest.mock import Mock
from typing import Optional, Dict, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod


# テスト用のデータ構造とクラス（実装前のテスト用）
@dataclass
class InputEvent:
    """入力要求イベント"""

    input_type: str
    predicate_name: str
    args: Dict[str, Any]
    timestamp: float
    event_id: str
    context: Optional[Dict] = None


@dataclass
class InputRequest:
    """スレッド間通信用入力要求"""

    input_type: str
    predicate_name: str
    prompt: str
    timestamp: float
    event_id: str
    additional_params: Dict[str, Any]


@dataclass
class InputResponse:
    """スレッド間通信用入力応答"""

    value: Optional[str]
    timestamp: float
    event_id: str
    success: bool = True
    error_message: Optional[str] = None


class InputHandler(ABC):
    """入力ハンドラインターフェース"""

    @abstractmethod
    def handle_input_request(self, event: InputEvent) -> Optional[str]:
        pass


# ThreadingController実装（設計に基づく）
class ThreadingController:
    """スレッド間通信制御"""

    def __init__(self):
        # 同期プリミティブ
        self.input_event = threading.Event()
        self.response_event = threading.Event()
        self.state_lock = threading.Lock()
        self.request_lock = threading.Lock()  # 要求排他制御

        # データ交換
        self.input_request: Optional[InputRequest] = None
        self.input_response: Optional[InputResponse] = None

        # スレッド管理
        self.input_thread: Optional[threading.Thread] = None
        self.input_handler: Optional[InputHandler] = None

        # 制御フラグ
        self.enabled = False
        self.shutdown_flag = threading.Event()

    def enable(self, input_handler: InputHandler):
        """スレッド間通信を有効化"""
        if self.enabled:
            return

        self.input_handler = input_handler

        # 入力処理スレッド開始
        self.input_thread = threading.Thread(
            target=self._input_processing_loop, daemon=True, name="unified-input-thread"
        )
        self.input_thread.start()

        self.enabled = True

    def disable(self):
        """スレッド間通信を無効化"""
        if not self.enabled:
            return

        self.shutdown_flag.set()
        self.input_event.set()

        if self.input_thread and self.input_thread.is_alive():
            self.input_thread.join(timeout=1.0)

        self.enabled = False

    def request_input(
        self, input_type: str, predicate_name: str, prompt: str, **kwargs
    ) -> Optional[str]:
        """入力要求（ブロッキング）"""
        if not self.enabled:
            raise RuntimeError("ThreadingController not enabled")

        # 複数要求の順次処理を保証する排他制御
        with self.request_lock:
            # 要求データ設定
            event_id = str(uuid.uuid4())
            with self.state_lock:
                self.input_request = InputRequest(
                    input_type=input_type,
                    predicate_name=predicate_name,
                    prompt=prompt,
                    timestamp=time.time(),
                    event_id=event_id,
                    additional_params=kwargs,
                )
                self.input_response = None

            # 入力処理スレッドに通知
            self.input_event.set()

            # 応答待ち（テスト用に短いタイムアウト）
            response_received = self.response_event.wait(timeout=5.0)

            if not response_received:
                return None

            # 応答取得
            with self.state_lock:
                response = self.input_response
                self.input_response = None
                self.response_event.clear()

        if response and response.success:
            return response.value
        else:
            return None

    def _input_processing_loop(self):
        """入力処理スレッドのメインループ"""
        while not self.shutdown_flag.is_set():
            if not self.input_event.wait(timeout=0.1):
                continue

            if self.shutdown_flag.is_set():
                break

            self.input_event.clear()

            # 要求データ取得
            with self.state_lock:
                request = self.input_request
                if request is None:
                    continue

            # InputHandlerに処理委譲
            try:
                event = InputEvent(
                    input_type=request.input_type,
                    predicate_name=request.predicate_name,
                    args={"prompt": request.prompt, **request.additional_params},
                    timestamp=request.timestamp,
                    event_id=request.event_id,
                )

                input_value = self.input_handler.handle_input_request(event)

                response = InputResponse(
                    value=input_value,
                    timestamp=time.time(),
                    event_id=request.event_id,
                    success=True,
                )

            except Exception as e:
                response = InputResponse(
                    value=None,
                    timestamp=time.time(),
                    event_id=request.event_id,
                    success=False,
                    error_message=str(e),
                )

            # Prologスレッドに応答
            with self.state_lock:
                self.input_response = response

            self.response_event.set()


# UnifiedInputSystem実装（設計に基づく）
class UnifiedInputSystem:
    """統一入力システム"""

    def __init__(self):
        self.threading_controller = ThreadingController()
        self.input_handler: Optional[InputHandler] = None
        self.fallback_stream = None

        # 実行モード
        self.threading_enabled = False

        # 統計・監視
        self.request_count = 0
        self.error_count = 0
        self.start_time = time.time()

    def set_input_handler(self, handler: InputHandler):
        """入力ハンドラを設定"""
        self.input_handler = handler

        if self.threading_enabled:
            self.threading_controller.enable(handler)

    def set_fallback_stream(self, stream):
        """フォールバック用IOStreamを設定"""
        self.fallback_stream = stream

    def enable_threading(self):
        """マルチスレッドモードを有効化"""
        if self.threading_enabled:
            return

        self.threading_enabled = True

        if self.input_handler:
            self.threading_controller.enable(self.input_handler)

    def disable_threading(self):
        """シングルスレッドモードに切り替え"""
        if not self.threading_enabled:
            return

        self.threading_controller.disable()
        self.threading_enabled = False

    def request_input(
        self, input_type: str, predicate_name: str, prompt: str = "", **kwargs
    ) -> Optional[str]:
        """統一入力要求（メインAPI）"""
        self.request_count += 1

        if self.threading_enabled:
            # マルチスレッドモード
            try:
                return self.threading_controller.request_input(
                    input_type, predicate_name, prompt, **kwargs
                )
            except Exception:
                self.error_count += 1
                return self._fallback_input(prompt)
        else:
            # シングルスレッドモード - 例外をそのまま通す
            return self._request_input_sync(
                input_type, predicate_name, prompt, **kwargs
            )

    def _request_input_sync(
        self, input_type: str, predicate_name: str, prompt: str, **kwargs
    ) -> Optional[str]:
        """シングルスレッド同期入力処理"""
        if not self.input_handler:
            self.error_count += 1
            return self._fallback_input(prompt)

        try:
            event = InputEvent(
                input_type=input_type,
                predicate_name=predicate_name,
                args={"prompt": prompt, **kwargs},
                timestamp=time.time(),
                event_id=str(uuid.uuid4()),
            )

            return self.input_handler.handle_input_request(event)
        except Exception:
            self.error_count += 1
            return self._fallback_input(prompt)

    def _fallback_input(self, prompt: str) -> Optional[str]:
        """フォールバック入力処理"""
        if self.fallback_stream and hasattr(self.fallback_stream, "read_line"):
            return self.fallback_stream.read_line()
        else:
            # テスト環境では標準入力を使わない
            return None

    def get_statistics(self) -> Dict[str, Any]:
        """統計情報取得"""
        uptime = time.time() - self.start_time
        return {
            "threading_enabled": self.threading_enabled,
            "request_count": self.request_count,
            "error_count": self.error_count,
            "error_rate": self.error_count / max(self.request_count, 1),
            "uptime_seconds": uptime,
            "handler_configured": self.input_handler is not None,
            "fallback_configured": self.fallback_stream is not None,
        }

    def shutdown(self):
        """システムシャットダウン"""
        if self.threading_enabled:
            self.threading_controller.disable()
            self.threading_enabled = False


# テスト用InputHandler実装
class TestInputHandler(InputHandler):
    """テスト用InputHandler"""

    __test__ = False

    def __init__(self, responses=None):
        self.responses = responses or {}
        self.call_history = []
        self.default_response = "test_input"

    def handle_input_request(self, event: InputEvent) -> Optional[str]:
        self.call_history.append(event)

        # 特定の入力タイプに対する応答
        response = self.responses.get(event.input_type, self.default_response)

        if callable(response):
            return response(event)
        else:
            return response


class ErrorInputHandler(InputHandler):
    """エラーを発生させるテスト用InputHandler"""

    def handle_input_request(self, event: InputEvent) -> Optional[str]:
        raise Exception("Test handler error")


class TestThreadingController:
    """ThreadingControllerのテスト"""

    def test_initial_state(self):
        """初期状態のテスト"""
        controller = ThreadingController()
        assert not controller.enabled
        assert controller.input_handler is None
        assert controller.input_thread is None

    def test_enable_disable(self):
        """有効化・無効化のテスト"""
        controller = ThreadingController()
        handler = TestInputHandler()

        # 有効化
        controller.enable(handler)
        assert controller.enabled
        assert controller.input_handler == handler
        assert controller.input_thread is not None
        assert controller.input_thread.is_alive()

        # 無効化
        controller.disable()
        assert not controller.enabled

        # スレッドが終了するまで少し待つ
        time.sleep(0.1)
        if controller.input_thread:
            assert not controller.input_thread.is_alive()

    def test_request_input_not_enabled(self):
        """未有効化状態での入力要求"""
        controller = ThreadingController()

        with pytest.raises(RuntimeError, match="ThreadingController not enabled"):
            controller.request_input("char", "get_char", "test: ")

    def test_request_input_success(self):
        """入力要求成功ケース"""
        controller = ThreadingController()
        handler = TestInputHandler({"char": "a"})

        controller.enable(handler)

        try:
            result = controller.request_input("char", "get_char", "文字入力: ")

            assert result == "a"
            assert len(handler.call_history) == 1

            event = handler.call_history[0]
            assert event.input_type == "char"
            assert event.predicate_name == "get_char"
            assert event.args["prompt"] == "文字入力: "

        finally:
            controller.disable()

    def test_request_input_with_additional_params(self):
        """追加パラメータ付き入力要求"""
        controller = ThreadingController()

        def custom_handler(event):
            # 追加パラメータをチェック
            assert event.args.get("non_destructive") == True
            assert event.args.get("timeout") == 10.0
            return "peek_result"

        handler = TestInputHandler({"peek_char": custom_handler})
        controller.enable(handler)

        try:
            result = controller.request_input(
                "peek_char", "peek_char", "peek: ", non_destructive=True, timeout=10.0
            )

            assert result == "peek_result"

        finally:
            controller.disable()

    def test_request_input_handler_error(self):
        """InputHandlerエラー時の処理"""
        controller = ThreadingController()
        handler = ErrorInputHandler()

        controller.enable(handler)

        try:
            result = controller.request_input("char", "get_char", "test: ")

            # エラー時はNoneが返される
            assert result is None

        finally:
            controller.disable()

    def test_multiple_requests(self):
        """複数の入力要求"""
        controller = ThreadingController()
        handler = TestInputHandler({"char": "x", "line": "hello world"})

        controller.enable(handler)

        try:
            # 1回目：文字入力
            result1 = controller.request_input("char", "get_char", "char: ")
            assert result1 == "x"

            # 2回目：行入力
            result2 = controller.request_input("line", "read_line", "line: ")
            assert result2 == "hello world"

            # 呼び出し履歴確認
            assert len(handler.call_history) == 2
            assert handler.call_history[0].input_type == "char"
            assert handler.call_history[1].input_type == "line"

        finally:
            controller.disable()


class TestUnifiedInputSystem:
    """UnifiedInputSystemのテスト"""

    def test_initial_state(self):
        """初期状態のテスト"""
        system = UnifiedInputSystem()
        assert not system.threading_enabled
        assert system.input_handler is None
        assert system.request_count == 0
        assert system.error_count == 0

    def test_set_input_handler(self):
        """入力ハンドラ設定"""
        system = UnifiedInputSystem()
        handler = TestInputHandler()

        system.set_input_handler(handler)
        assert system.input_handler == handler

    def test_threading_mode_toggle(self):
        """スレッドモード切り替え"""
        system = UnifiedInputSystem()
        handler = TestInputHandler()

        system.set_input_handler(handler)

        # スレッドモード有効化
        system.enable_threading()
        assert system.threading_enabled
        assert system.threading_controller.enabled

        # スレッドモード無効化
        system.disable_threading()
        assert not system.threading_enabled
        assert not system.threading_controller.enabled

    def test_single_thread_mode_request(self):
        """シングルスレッドモード入力要求"""
        system = UnifiedInputSystem()
        handler = TestInputHandler({"line": "single_thread_input"})

        system.set_input_handler(handler)

        result = system.request_input("line", "read_line", "入力: ")

        assert result == "single_thread_input"
        assert system.request_count == 1
        assert system.error_count == 0

        # ハンドラが正しく呼ばれたことを確認
        assert len(handler.call_history) == 1
        event = handler.call_history[0]
        assert event.input_type == "line"
        assert event.predicate_name == "read_line"

    def test_multi_thread_mode_request(self):
        """マルチスレッドモード入力要求"""
        system = UnifiedInputSystem()
        handler = TestInputHandler({"char": "multi_thread_input"})

        system.set_input_handler(handler)
        system.enable_threading()

        try:
            result = system.request_input("char", "get_char", "文字: ")

            assert result == "multi_thread_input"
            assert system.request_count == 1
            assert system.error_count == 0

        finally:
            system.shutdown()

    def test_request_without_handler(self):
        """ハンドラ未設定での入力要求"""
        system = UnifiedInputSystem()

        # フォールバックストリームも未設定
        result = system.request_input("line", "read_line", "test: ")

        # フォールバック処理により None が返される
        assert result is None
        assert system.request_count == 1
        assert system.error_count == 1

    def test_fallback_stream(self):
        """フォールバックストリーム使用"""
        system = UnifiedInputSystem()

        # モックフォールバックストリーム
        mock_stream = Mock()
        mock_stream.read_line.return_value = "fallback_input"

        system.set_fallback_stream(mock_stream)

        result = system.request_input("line", "read_line", "test: ")

        assert result == "fallback_input"
        mock_stream.read_line.assert_called_once()

    def test_handler_error_fallback(self):
        """ハンドラエラー時のフォールバック"""
        system = UnifiedInputSystem()

        # エラーハンドラとフォールバックストリーム設定
        error_handler = ErrorInputHandler()
        mock_stream = Mock()
        mock_stream.read_line.return_value = "error_fallback"

        system.set_input_handler(error_handler)
        system.set_fallback_stream(mock_stream)

        result = system.request_input("char", "get_char", "test: ")

        assert result == "error_fallback"
        assert system.error_count == 1
        mock_stream.read_line.assert_called_once()

    def test_statistics_collection(self):
        """統計情報収集"""
        system = UnifiedInputSystem()
        handler = TestInputHandler()

        system.set_input_handler(handler)

        # 初期統計
        stats = system.get_statistics()
        assert stats["request_count"] == 0
        assert stats["error_count"] == 0
        assert stats["threading_enabled"] == False
        assert stats["handler_configured"] == True

        # 成功要求
        system.request_input("line", "read_line", "test: ")

        stats = system.get_statistics()
        assert stats["request_count"] == 1
        assert stats["error_count"] == 0
        assert stats["error_rate"] == 0.0

        # エラー要求
        error_handler = ErrorInputHandler()
        system.set_input_handler(error_handler)
        system.request_input("char", "get_char", "test: ")

        stats = system.get_statistics()
        assert stats["request_count"] == 2
        assert stats["error_count"] == 1
        assert stats["error_rate"] == 0.5

    def test_concurrent_requests(self):
        """並行入力要求（マルチスレッドモード）"""
        system = UnifiedInputSystem()

        # レスポンス時間を制御するハンドラ
        def slow_handler(event):
            time.sleep(0.1)
            return f"response_{event.input_type}"

        handler = TestInputHandler({"char": slow_handler, "line": slow_handler})

        system.set_input_handler(handler)
        system.enable_threading()

        try:
            # 並行実行用の関数
            def make_request(input_type, predicate_name):
                return system.request_input(input_type, predicate_name, "test: ")

            # 複数スレッドで同時要求
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                future1 = executor.submit(make_request, "char", "get_char")
                future2 = executor.submit(make_request, "line", "read_line")

                result1 = future1.result(timeout=2.0)
                result2 = future2.result(timeout=2.0)

            # 注意: ThreadingControllerは同時に1つの要求のみ処理
            # 2番目の要求は1番目の完了後に処理される
            assert result1 in ["response_char", "response_line"]
            assert result2 in ["response_char", "response_line"]
            assert result1 != result2

        finally:
            system.shutdown()

    def test_shutdown_cleanup(self):
        """シャットダウン時のクリーンアップ"""
        system = UnifiedInputSystem()
        handler = TestInputHandler()

        system.set_input_handler(handler)
        system.enable_threading()

        # スレッドが動作中であることを確認
        assert system.threading_controller.input_thread.is_alive()

        # シャットダウン
        system.shutdown()

        # スレッドが停止することを確認
        time.sleep(0.2)
        assert not system.threading_enabled
        assert not system.threading_controller.enabled


class TestInputEventDataStructure:
    """InputEventデータ構造のテスト"""

    def test_input_event_creation(self):
        """InputEvent作成"""
        event = InputEvent(
            input_type="char",
            predicate_name="get_char",
            args={"prompt": "test: ", "timeout": 10},
            timestamp=time.time(),
            event_id="test-id-123",
        )

        assert event.input_type == "char"
        assert event.predicate_name == "get_char"
        assert event.args["prompt"] == "test: "
        assert event.args["timeout"] == 10
        assert event.event_id == "test-id-123"

    def test_input_request_response_matching(self):
        """InputRequestとInputResponseのID照合"""
        request = InputRequest(
            input_type="line",
            predicate_name="read_line",
            prompt="入力: ",
            timestamp=time.time(),
            event_id="req-123",
            additional_params={},
        )

        response = InputResponse(
            value="test_response",
            timestamp=time.time(),
            event_id="req-123",
            success=True,
        )

        # IDが一致することを確認
        assert request.event_id == response.event_id
