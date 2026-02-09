# pyprolog/runtime/input_handlers.py
import platform
import sys
from abc import ABC, abstractmethod

from ..core.stream_errors import StreamCapabilityError


class InputHandler(ABC):
    """入力ハンドラー抽象基底クラス"""

    @abstractmethod
    def is_input_available(self) -> bool:
        """入力が利用可能かチェック"""
        pass

    @abstractmethod
    def read_char_nonblocking(self) -> str:
        """非ブロッキング文字読み込み"""
        pass

    @abstractmethod
    def read_char_blocking(self) -> str:
        """ブロッキング文字読み込み"""
        pass


class UnixInputHandler(InputHandler):
    """Unix系システム用入力ハンドラー"""

    def is_input_available(self) -> bool:
        """select()による入力判定"""
        try:
            import select

            ready, _, _ = select.select([sys.stdin], [], [], 0.0)
            return bool(ready)
        except ImportError:
            # selectがサポートされていない環境
            return False

    def read_char_nonblocking(self) -> str:
        """非ブロッキング読み込み"""
        if self.is_input_available():
            return sys.stdin.read(1)
        return ""

    def read_char_blocking(self) -> str:
        """通常のブロッキング読み込み"""
        return sys.stdin.read(1)


class WindowsInputHandler(InputHandler):
    """Windows用入力ハンドラー"""

    def __init__(self):
        try:
            import msvcrt

            self._msvcrt = msvcrt
        except ImportError:
            raise StreamCapabilityError(
                "Windows input handler requires msvcrt", "WindowsInputHandler"
            )

    def is_input_available(self) -> bool:
        """msvcrt.kbhit()による入力判定"""
        return self._msvcrt.kbhit()

    def read_char_nonblocking(self) -> str:
        """非ブロッキング読み込み"""
        if self.is_input_available():
            char_bytes = self._msvcrt.getch()
            # バイト文字列をUTF-8でデコード（エラーは無視）
            return char_bytes.decode("utf-8", errors="ignore")
        return ""

    def read_char_blocking(self) -> str:
        """ブロッキング読み込み"""
        char_bytes = self._msvcrt.getch()
        return char_bytes.decode("utf-8", errors="ignore")


def create_platform_handler() -> InputHandler:
    """プラットフォーム固有ハンドラー作成"""
    if platform.system() == "Windows":
        return WindowsInputHandler()
    else:
        return UnixInputHandler()
