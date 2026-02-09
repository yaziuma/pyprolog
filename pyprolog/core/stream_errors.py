# pyprolog/core/stream_errors.py
from dataclasses import dataclass

from .errors import PrologError


class StreamError(PrologError):
    """ストリーム関連エラーの基底クラス"""

    pass


class StreamOperationError(StreamError):
    """ストリーム操作エラー"""

    def __init__(self, message: str, stream_type: str = None):
        super().__init__(message)
        self.stream_type = stream_type


class StreamBufferError(StreamError):
    """バッファ関連エラー"""

    pass


class StreamCapabilityError(StreamError):
    """ストリーム能力不足エラー"""

    def __init__(self, operation: str, stream_type: str):
        super().__init__(f"Operation '{operation}' not supported by {stream_type}")
        self.operation = operation
        self.stream_type = stream_type


@dataclass
class StreamStatus:
    """ストリーム状態情報"""

    # 基本状態
    at_eof: bool
    has_data_available: bool
    supports_peek: bool

    # バッファ情報
    buffer_size: int
    buffered_chars: int
    buffer_position: int

    # メタデータ
    stream_type: str
    encoding: str
    last_operation: str

    # エラー状態
    has_errors: bool
    error_message: str | None
