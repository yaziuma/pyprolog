# pyprolog/runtime/stream_buffer.py
from collections import deque
from typing import Optional
from ..core.stream_errors import StreamBufferError


class StreamBuffer:
    """
    効率的な文字バッファ管理（シングルスレッド用）
    - dequeによる効率的なデータ管理
    - peek操作の高速化
    - シンプルなインターフェース
    """

    def __init__(self, capacity: int = 1024):
        self._buffer = deque(maxlen=capacity)
        self._capacity = capacity

    def peek(self) -> Optional[str]:
        """先頭文字をpeek（位置変更なし）"""
        try:
            return self._buffer[0]
        except IndexError:
            return None

    def get(self) -> Optional[str]:
        """先頭文字を読み取り（除去）"""
        try:
            return self._buffer.popleft()
        except IndexError:
            return None

    def put(self, char: str) -> bool:
        """文字をバッファに追加"""
        try:
            self._buffer.append(char)
            return True
        except Exception as e:
            raise StreamBufferError(f"Failed to add character to buffer: {e}")

    def is_empty(self) -> bool:
        """バッファが空かチェック"""
        return len(self._buffer) == 0

    def size(self) -> int:
        """現在のバッファサイズ"""
        return len(self._buffer)

    def clear(self) -> None:
        """バッファクリア"""
        self._buffer.clear()

    @property
    def capacity(self) -> int:
        """バッファ容量を取得"""
        return self._capacity

    def is_full(self) -> bool:
        """バッファが満杯かチェック"""
        return len(self._buffer) >= self._capacity
