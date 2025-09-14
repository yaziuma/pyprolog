"""
統一入力システム（Unified Input System）

統一入力システムの中央制御、InputHandlerルーティング、
ThreadingControllerによる真の継続実行を提供する。
"""

import threading
import time
import uuid
from typing import Optional, Dict, Any, TYPE_CHECKING
from dataclasses import dataclass
from abc import ABC, abstractmethod
import logging

if TYPE_CHECKING:
    from pyprolog.runtime.io_streams import IOStream

logger = logging.getLogger(__name__)


@dataclass
class InputEvent:
    """
    入力要求イベント
    
    統一入力システム内で使用される入力要求の標準化されたデータ構造
    """
    input_type: str                    # "char", "line", "peek_char" etc.
    predicate_name: str               # "get_char", "read_line" etc.
    args: Dict[str, Any]              # 追加パラメータ
    timestamp: float                  # 要求時刻
    event_id: str                     # 一意識別子
    context: Optional[Dict] = None    # 実行コンテキスト情報


@dataclass  
class InputRequest:
    """
    スレッド間通信用入力要求
    
    Prologスレッドから入力処理スレッドへの要求データ
    """
    input_type: str
    predicate_name: str
    prompt: str
    timestamp: float
    event_id: str
    additional_params: Dict[str, Any]


@dataclass
class InputResponse:
    """
    スレッド間通信用入力応答
    
    入力処理スレッドからPrologスレッドへの応答データ
    """
    value: Optional[str]              # 入力値（None = EOF）
    timestamp: float                  # 応答時刻
    event_id: str                     # 対応する要求のID
    success: bool = True              # 成功フラグ
    error_message: Optional[str] = None  # エラー時のメッセージ


class InputHandler(ABC):
    """
    入力ハンドラインターフェース
    
    利用者が実装する統一入力処理インターフェース
    """
    
    @abstractmethod
    def handle_input_request(self, event: InputEvent) -> Optional[str]:
        """
        入力要求処理
        
        Args:
            event: 入力要求イベント
            
        Returns:
            Optional[str]: 入力値（None = EOF）
        """
        pass


class StandardInputHandler(InputHandler):
    """
    標準入力ハンドラ
    
    デフォルトの標準入力処理を提供
    """
    
    def handle_input_request(self, event: InputEvent) -> Optional[str]:
        """
        標準入力による入力処理
        
        Args:
            event: 入力要求イベント
            
        Returns:
            Optional[str]: 入力値（None = EOF）
        """
        prompt = event.args.get("prompt", f"{event.predicate_name}: ")
        try:
            if event.input_type == "char":
                # 文字入力の場合
                line = input(prompt)
                return line[0] if line else ""
            else:
                # 行入力の場合
                return input(prompt)
        except (EOFError, KeyboardInterrupt):
            return None


class StreamInputHandler(InputHandler):
    """
    ストリームベース入力ハンドラ
    
    テスト用途やファイル入力に使用
    """
    
    def __init__(self, stream):
        """
        Args:
            stream: IOStreamインターフェースを持つストリーム
        """
        self.stream = stream
    
    def handle_input_request(self, event: InputEvent) -> Optional[str]:
        """
        ストリームからの入力処理
        
        Args:
            event: 入力要求イベント
            
        Returns:
            Optional[str]: 入力値（None = EOF）
        """
        try:
            if event.input_type == "char":
                # 文字入力の場合
                char = self.stream.read_char()
                return char if char else None
            elif event.input_type == "peek_char":
                # 先読み文字入力の場合
                char = self.stream.peek_char()
                return char if char else None
            else:
                # 行入力の場合
                line = self.stream.read_line()
                return line
        except Exception:
            # ストリームエラー時はEOFとして扱う
            return None


class ThreadingController:
    """
    スレッド間通信制御
    
    Prologスレッドと入力処理スレッドの同期制御を担当
    """
    
    def __init__(self):
        # 同期プリミティブ
        self.input_event = threading.Event()      # 入力要求通知
        self.response_event = threading.Event()   # 応答通知  
        self.state_lock = threading.Lock()        # 状態保護
        self.request_lock = threading.Lock()      # 要求排他制御
        
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
        """
        スレッド間通信を有効化
        
        Args:
            input_handler: 入力処理ハンドラ
        """
        if self.enabled:
            return
            
        self.input_handler = input_handler
        
        # 入力処理スレッド開始
        self.input_thread = threading.Thread(
            target=self._input_processing_loop,
            daemon=True,
            name="unified-input-thread"
        )
        self.input_thread.start()
        
        self.enabled = True
        logger.info("ThreadingController enabled")
    
    def disable(self):
        """スレッド間通信を無効化"""
        if not self.enabled:
            return
            
        self.shutdown_flag.set()
        self.input_event.set()  # スレッド終了のための通知
        
        if self.input_thread and self.input_thread.is_alive():
            self.input_thread.join(timeout=1.0)
            
        self.enabled = False
        self.shutdown_flag.clear()  # 次回有効化のためリセット
        logger.info("ThreadingController disabled")
    
    def request_input(
        self, 
        input_type: str, 
        predicate_name: str,
        prompt: str,
        **kwargs
    ) -> Optional[str]:
        """
        入力要求（ブロッキング）
        
        【重要】ここで真の継続実行が実現される。
        このメソッド呼び出しでPrologスレッドがブロックし、
        入力完了まで待機。しかしスタックフレームは完全保持。
        
        Args:
            input_type: 入力タイプ
            predicate_name: 述語名
            prompt: プロンプト文字列
            **kwargs: 追加パラメータ
            
        Returns:
            Optional[str]: 入力値（None = EOF）
        """
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
                    additional_params=kwargs
                )
                self.input_response = None
            
            # 入力処理スレッドに通知
            self.input_event.set()
            
            # 【重要】ここでPrologスレッドブロッキング
            # スタックフレーム・ローカル変数は完全保持
            response_received = self.response_event.wait(timeout=300.0)  # 5分タイムアウト
            
            if not response_received:
                logger.error(f"Input request timeout: {predicate_name}")
                return None
            
            # 応答取得
            with self.state_lock:
                response = self.input_response
                self.input_response = None
                self.response_event.clear()
            
            if response and response.success:
                return response.value
            else:
                logger.error(f"Input request failed: {response.error_message if response else 'No response'}")
                return None
    
    def _input_processing_loop(self):
        """
        入力処理スレッドのメインループ
        
        Prologスレッドからの入力要求を待機し、
        InputHandlerに処理を委譲する。
        """
        logger.info("Input processing thread started")
        
        while not self.shutdown_flag.is_set():
            # 入力要求待ち
            if not self.input_event.wait(timeout=1.0):
                continue  # タイムアウト → ループ継続
            
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
                    event_id=request.event_id
                )
                
                input_value = self.input_handler.handle_input_request(event)
                
                # 成功応答
                response = InputResponse(
                    value=input_value,
                    timestamp=time.time(),
                    event_id=request.event_id,
                    success=True
                )
                
            except Exception as e:
                logger.error(f"InputHandler error: {e}")
                
                # エラー応答  
                response = InputResponse(
                    value=None,
                    timestamp=time.time(),
                    event_id=request.event_id,
                    success=False,
                    error_message=str(e)
                )
            
            # Prologスレッドに応答
            with self.state_lock:
                self.input_response = response
            
            self.response_event.set()
        
        logger.info("Input processing thread stopped")


class UnifiedInputSystem:
    """
    統一入力システム
    
    入力要求の中央制御を行い、シングルスレッドモードと
    マルチスレッドモードを統一的に提供する。
    """
    
    def __init__(self):
        # コンポーネント
        self.threading_controller = ThreadingController()
        self.input_handler: Optional[InputHandler] = None
        self.fallback_stream: Optional["IOStream"] = None
        
        # 実行モード
        self.threading_enabled = False
        
        # 統計・監視
        self.request_count = 0
        self.error_count = 0
        self.start_time = time.time()
    
    def set_input_handler(self, handler: InputHandler):
        """
        入力ハンドラを設定
        
        Args:
            handler: InputHandlerの実装
        """
        self.input_handler = handler
        
        if self.threading_enabled:
            self.threading_controller.enable(handler)
    
    def set_fallback_stream(self, stream: "IOStream"):
        """
        フォールバック用IOStreamを設定
        
        Args:
            stream: フォールバック用IOStream
        """
        self.fallback_stream = stream
    
    def enable_threading(self):
        """
        マルチスレッドモード（真の継続実行）を有効化
        """
        if self.threading_enabled:
            return
            
        self.threading_enabled = True
        
        if self.input_handler:
            self.threading_controller.enable(self.input_handler)
            
        logger.info("UnifiedInputSystem threading mode enabled")
    
    def disable_threading(self):
        """
        シングルスレッドモードに切り替え
        """
        if not self.threading_enabled:
            return
            
        self.threading_controller.disable()
        self.threading_enabled = False
        
        logger.info("UnifiedInputSystem threading mode disabled")
    
    def request_input(
        self, 
        input_type: str, 
        predicate_name: str, 
        prompt: str = "",
        **kwargs
    ) -> Optional[str]:
        """
        統一入力要求（メインAPI）
        
        実行モードに応じてシングルスレッド実行または
        マルチスレッド実行を選択する。
        
        Args:
            input_type: 入力タイプ
            predicate_name: 述語名
            prompt: プロンプト文字列
            **kwargs: 追加パラメータ
            
        Returns:
            Optional[str]: 入力値（None = EOF）
        """
        self.request_count += 1
        logger.error(f"request_input called: threading_enabled={self.threading_enabled}, input_handler={self.input_handler}")
        
        if self.threading_enabled:
            # マルチスレッドモード（真の継続実行）
            try:
                return self.threading_controller.request_input(
                    input_type, predicate_name, prompt, **kwargs
                )
            except Exception as e:
                self.error_count += 1
                logger.error(f"UnifiedInputSystem threading error: {e}")
                return self._fallback_input(prompt)
        else:
            # シングルスレッドモード（従来互換）
            return self._request_input_sync(
                input_type, predicate_name, prompt, **kwargs
            )
    
    def _request_input_sync(
        self, 
        input_type: str, 
        predicate_name: str,
        prompt: str,
        **kwargs
    ) -> Optional[str]:
        """
        シングルスレッド同期入力処理
        
        従来互換モードでの入力処理。InputHandlerを直接呼び出す。
        """
        if not self.input_handler:
            self.error_count += 1
            logger.error(f"No input handler, error_count incremented to {self.error_count}")
            return self._fallback_input(prompt)
        
        try:
            event = InputEvent(
                input_type=input_type,
                predicate_name=predicate_name,
                args={"prompt": prompt, **kwargs},
                timestamp=time.time(),
                event_id=str(uuid.uuid4())
            )
            
            return self.input_handler.handle_input_request(event)
        except Exception as e:
            self.error_count += 1
            logger.error(f"InputHandler error in sync mode: {e}")
            return self._fallback_input(prompt)
    
    def _fallback_input(self, prompt: str) -> Optional[str]:
        """
        フォールバック入力処理
        
        InputHandlerが設定されていない場合や
        エラー時の代替入力処理。
        """
        if self.fallback_stream and hasattr(self.fallback_stream, 'read_line'):
            return self.fallback_stream.read_line()
        else:
            # 最終手段: 標準入力
            try:
                return input(prompt)
            except (EOFError, KeyboardInterrupt):
                return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        統計情報取得
        
        Returns:
            Dict[str, Any]: システム統計情報
        """
        uptime = time.time() - self.start_time
        return {
            "threading_enabled": self.threading_enabled,
            "request_count": self.request_count,
            "error_count": self.error_count,
            "error_rate": self.error_count / max(self.request_count, 1),
            "uptime_seconds": uptime,
            "handler_configured": self.input_handler is not None,
            "fallback_configured": self.fallback_stream is not None
        }
    
    def shutdown(self):
        """
        システムシャットダウン
        
        スレッドの適切な終了処理を行う。
        """
        if self.threading_enabled:
            self.threading_controller.disable()
            self.threading_enabled = False
            
        logger.info("UnifiedInputSystem shutdown complete")