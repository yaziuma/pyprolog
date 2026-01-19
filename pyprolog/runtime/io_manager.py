# pyprolog/runtime/io_manager.py
from .io_streams import IOStream, ConsoleStream
from .unified_input_system import UnifiedInputSystem, InputHandler, StandardInputHandler
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class IOManager:
    """
    入出力管理クラス（継続駆動統一入力システム）

    全ての入力要求は継続ハンドル前提の UnifiedInputSystem を経由し、
    旧同期フォールバックは撤去された構成です。
    """

    def __init__(self) -> None:
        """
        IOManagerを初期化し、統一入力システムを統合
        """
        self._current_output_stream: IOStream = ConsoleStream()
        self.unified_input = UnifiedInputSystem()

        self._setup_default_unified_input()
        self.enable_threading()

    def _setup_default_unified_input(self):
        """デフォルト統一入力ハンドラの設定"""
        default_handler = StandardInputHandler()
        self.unified_input.set_input_handler(default_handler)

    # ========================================================================
    # 新規API（統一入力システム）
    # ========================================================================

    def request_input(
        self, input_type: str, predicate_name: str, prompt: str = "", **kwargs
    ) -> Optional[str]:
        """
        統一入力要求API

        継続ハンドルベースの UnifiedInputSystem を直接呼び出します。
        例外はそのままプロセス実行側へ伝播します。

        Args:
            input_type: 入力タイプ ("char", "line", "peek_char" etc.)
            predicate_name: 呼び出し元述語名
            prompt: プロンプト文字列
            **kwargs: 追加パラメータ

        Returns:
            Optional[str]: 入力値（None = EOF）
        """
        try:
            return self.unified_input.request_input(
                input_type, predicate_name, prompt, **kwargs
            )
        except Exception:
            logger.exception("Unified input failed")
            raise

    def set_input_handler(self, handler: InputHandler):
        """
        統一入力ハンドラを設定

        Args:
            handler: InputHandlerの実装
        """
        self.unified_input.set_input_handler(handler)

    def enable_threading(self):
        """
        マルチスレッドモード（真の継続実行）を有効化

        この呼び出し後、全ての入力要求で真の継続実行が使用される。
        """
        self.unified_input.enable_threading()
        logger.info("IOManager: Threading mode enabled")

    def disable_threading(self):
        """シングルスレッドモードに切り替え"""
        self.unified_input.disable_threading()
        logger.info("IOManager: Threading mode disabled")

    # ========================================================================
    # 出力系API（変更なし）
    # ========================================================================

    def write_char_to_current(self, char: str) -> None:
        """現在の出力ストリームに文字を書き込み"""
        self._current_output_stream.write_char(char)

    def write_string_to_current(self, string: str):
        """現在の出力ストリームに文字列を書き込み"""
        if hasattr(self._current_output_stream, "write"):
            self._current_output_stream.write(string)
        else:
            # 文字列を文字ごとに書き込み
            for char in string:
                self.write_char_to_current(char)

    # ========================================================================
    # ストリーム管理API
    # ========================================================================

    def set_output_stream(self, stream: IOStream) -> None:
        """現在の出力ストリームを設定"""
        self._current_output_stream = stream

    def get_output_stream(self) -> IOStream:
        """現在の出力ストリームを取得"""
        return self._current_output_stream

    # ========================================================================
    # 統計・診断API
    # ========================================================================

    def get_input_statistics(self) -> Dict[str, Any]:
        """統一入力処理統計情報取得"""
        return self.unified_input.get_statistics()

    def shutdown(self):
        """IOManager終了処理"""
        self.unified_input.shutdown()
        logger.info("IOManager shutdown complete")
