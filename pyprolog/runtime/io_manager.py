# pyprolog/runtime/io_manager.py
from .io_streams import IOStream, ConsoleStream
from .unified_input_system import UnifiedInputSystem, InputHandler, StandardInputHandler
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class IOManager:
    """
    入出力管理クラス（統一入力システム統合版）
    
    従来のIOStreamベースAPIと新しい統一入力システムの
    両方をサポートし、完全な後方互換性を提供する。
    """

    def __init__(self) -> None:
        """
        IOManagerを初期化し、統一入力システムを統合
        """
        # 従来コンポーネント（互換性のため保持）
        self._current_input_stream: IOStream = ConsoleStream()
        self._current_output_stream: IOStream = ConsoleStream()
        
        # 新規コンポーネント
        self.unified_input = UnifiedInputSystem()
        
        # 移行制御フラグ
        self._unified_input_enabled = True  # デフォルトで新方式使用
        self._fallback_to_legacy = True    # エラー時は従来方式にフォールバック
        
        # 初期設定
        self._setup_default_unified_input()
        self._setup_unified_input_fallback()

    def _setup_default_unified_input(self):
        """デフォルト統一入力ハンドラの設定"""
        default_handler = StandardInputHandler()
        self.unified_input.set_input_handler(default_handler)

    def _setup_unified_input_fallback(self):
        """統一入力システムのフォールバック設定"""
        self.unified_input.set_fallback_stream(self._current_input_stream)

    # ========================================================================
    # 新規API（統一入力システム）
    # ========================================================================

    def request_input(
        self, 
        input_type: str, 
        predicate_name: str, 
        prompt: str = "",
        **kwargs
    ) -> Optional[str]:
        """
        統一入力要求API
        
        【メインAPI】IOPredicateから呼び出される新しい統一入力API。
        設定に応じて統一入力システムまたは従来方式を使用。
        
        Args:
            input_type: 入力タイプ ("char", "line", "peek_char" etc.)
            predicate_name: 呼び出し元述語名
            prompt: プロンプト文字列
            **kwargs: 追加パラメータ
            
        Returns:
            Optional[str]: 入力値（None = EOF）
        """
        if self._unified_input_enabled:
            try:
                return self.unified_input.request_input(
                    input_type, predicate_name, prompt, **kwargs
                )
            except Exception as e:
                logger.warning(f"Unified input failed, fallback to legacy: {e}")
                if self._fallback_to_legacy:
                    return self._request_input_legacy(input_type, prompt)
                else:
                    raise
        else:
            return self._request_input_legacy(input_type, prompt)

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

    def enable_unified_input(self):
        """統一入力システムを有効化"""
        self._unified_input_enabled = True
        logger.info("IOManager: Unified input enabled")

    def disable_unified_input(self):
        """統一入力システムを無効化（従来方式のみ）"""
        self._unified_input_enabled = False
        logger.info("IOManager: Unified input disabled")

    # ========================================================================
    # 従来API（後方互換性）
    # ========================================================================

    def read_char_from_current(self) -> str:
        """
        現在の入力ストリームから文字を読み取り（従来互換API）
        
        【重要】このメソッドは既存のGetCharPredicateとの互換性のため保持。
        しかし、新しいIOPredicate統合後は使用されない。
        
        Returns:
            str: 読み取った文字（EOF時は空文字列）
        """
        if self._unified_input_enabled:
            # 統一入力システム経由で処理
            result = self.request_input("char", "get_char_legacy")
            return result if result is not None else ""
        else:
            # 従来処理
            return self._read_char_from_stream()

    def read_line_from_current(self) -> Optional[str]:
        """
        現在の入力ストリームから行を読み取り（従来互換API）
        
        Returns:
            Optional[str]: 読み取った行（EOF時はNone）
        """
        if self._unified_input_enabled:
            # 統一入力システム経由で処理
            return self.request_input("line", "read_line_legacy")
        else:
            # 従来処理
            return self._read_line_from_stream()

    def peek_char_from_current(self) -> str:
        """
        現在の入力ストリームから非破壊的文字読み取り（従来互換API）
        
        Returns:
            str: 覗き見した文字（EOF時は空文字列）
        """
        if self._unified_input_enabled:
            # 統一入力システム経由で処理
            result = self.request_input("peek_char", "peek_char_legacy", non_destructive=True)
            return result if result is not None else ""
        else:
            # 従来処理
            return self._peek_char_from_stream()

    # ========================================================================
    # 内部実装（従来処理の保持）
    # ========================================================================

    def _request_input_legacy(self, input_type: str, prompt: str) -> Optional[str]:
        """
        従来方式による入力処理
        
        統一入力システムエラー時のフォールバック処理
        """
        if input_type == "char":
            result = self._read_char_from_stream()
            return result if result else None
        elif input_type == "line":
            return self._read_line_from_stream()
        elif input_type == "peek_char":
            result = self._peek_char_from_stream()
            return result if result else None
        else:
            logger.error(f"Unknown input_type in legacy mode: {input_type}")
            return None

    def _read_char_from_stream(self) -> str:
        """従来のストリームベース文字読み取り"""
        return self._current_input_stream.read_char()

    def _read_line_from_stream(self) -> Optional[str]:
        """従来のストリームベース行読み取り"""
        return self._current_input_stream.read_line()

    def _peek_char_from_stream(self) -> str:
        """従来のストリームベース覗き見読み取り"""
        if hasattr(self._current_input_stream, 'peek_char'):
            return self._current_input_stream.peek_char()
        else:
            # peek_charが実装されていない場合は通常読み取り
            return self._read_char_from_stream()

    # ========================================================================
    # 出力系API（変更なし）
    # ========================================================================

    def write_char_to_current(self, char: str) -> None:
        """現在の出力ストリームに文字を書き込み"""
        self._current_output_stream.write_char(char)

    def write_string_to_current(self, string: str):
        """現在の出力ストリームに文字列を書き込み"""
        if hasattr(self._current_output_stream, 'write'):
            self._current_output_stream.write(string)
        else:
            # 文字列を文字ごとに書き込み
            for char in string:
                self.write_char_to_current(char)

    # ========================================================================
    # ストリーム管理API（変更なし、但し統一入力システム統合）
    # ========================================================================

    def set_input_stream(self, stream: IOStream) -> None:
        """現在の入力ストリームを設定"""
        self._current_input_stream = stream
        # 統一入力システムのフォールバックも更新
        self.unified_input.set_fallback_stream(stream)

    def set_output_stream(self, stream: IOStream) -> None:
        """現在の出力ストリームを設定"""
        self._current_output_stream = stream

    def get_input_stream(self) -> IOStream:
        """現在の入力ストリームを取得"""
        return self._current_input_stream

    def get_output_stream(self) -> IOStream:
        """現在の出力ストリームを取得"""
        return self._current_output_stream

    # ========================================================================
    # 統計・診断API
    # ========================================================================

    def get_input_statistics(self) -> Dict[str, Any]:
        """入力処理統計情報取得"""
        stats = self.unified_input.get_statistics()
        stats.update({
            "unified_input_enabled": self._unified_input_enabled,
            "fallback_to_legacy": self._fallback_to_legacy,
            "current_input_stream": str(type(self._current_input_stream).__name__),
        })
        return stats

    def shutdown(self):
        """IOManager終了処理"""
        self.unified_input.shutdown()
        logger.info("IOManager shutdown complete")
