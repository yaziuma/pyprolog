# prolog/runtime/io_streams.py
from abc import ABC, abstractmethod
import sys
from typing import List, Optional  # For Python list type hint in StringStream
from ..core.stream_errors import StreamOperationError, StreamStatus
from .stream_buffer import StreamBuffer
from .input_handlers import create_platform_handler

# To use 'PrologType' as a type hint, it would typically be imported:
# from prolog.core.types import PrologType
# However, to avoid potential circular dependencies at this stage of module creation,
# we can use it as a string literal in type hints: 'PrologType'.


class IOStream(ABC):
    """
    Abstract base class for Prolog I/O streams.
    Defines the interface for reading and writing characters and terms.
    """

    @abstractmethod
    def read_char(self) -> str:
        """
        Reads a single character from the stream.
        Returns the character read.
        Should raise an appropriate exception on EOF or error.
        """
        pass

    @abstractmethod
    def read_line(self) -> Optional[str]:
        """
        Reads a line from the stream (up to and including newline).
        Returns the line without the newline character.
        Returns None on EOF.
        """
        pass

    @abstractmethod
    def write_char(self, char: str) -> None:
        """
        Writes a single character to the stream.
        """
        pass

    @abstractmethod
    def read_term(self) -> "PrologType":
        """
        Reads a Prolog term from the stream.
        Returns the Prolog term.
        Should handle parsing and raise appropriate exceptions on syntax error or EOF.
        """
        pass

    @abstractmethod
    def write_term(self, term: "PrologType") -> None:
        """
        Writes a Prolog term to the stream.
        Should handle term serialization.
        """
        pass

    def peek_char(self) -> str:
        """
        次の文字を非破壊的に取得

        Returns:
            str: 次の文字 (EOF時は空文字列)

        Raises:
            StreamOperationError: ストリームが操作をサポートしない
        """
        raise StreamOperationError("peek_char", type(self).__name__)

    def at_end_of_stream(self) -> bool:
        """
        EOF状態を非破壊的に確認

        Returns:
            bool: True=EOF到達, False=データあり

        Raises:
            StreamOperationError: ストリーム状態取得不可
        """
        raise StreamOperationError("at_end_of_stream", type(self).__name__)

    def supports_peek_operations(self) -> bool:
        """
        peek系操作のサポート状況確認

        Returns:
            bool: True=サポート, False=非サポート
        """
        return False

    def get_stream_status(self) -> StreamStatus:
        """
        詳細なストリーム状態取得

        Returns:
            StreamStatus: 状態情報オブジェクト
        """
        return StreamStatus(
            at_eof=True,
            has_data_available=False,
            supports_peek=False,
            buffer_size=0,
            buffered_chars=0,
            buffer_position=0,
            stream_type=type(self).__name__,
            encoding="utf-8",
            last_operation="unknown",
            has_errors=False,
            error_message=None,
        )


class ConsoleStream(IOStream):
    """
    Concrete IOStream implementation for standard console I/O.
    """

    def __init__(self):
        super().__init__()
        # No specific initialization needed for stdin/stdout if using sys directly.
        self._last_operation = "init"

    def write_char(self, char: str) -> None:
        sys.stdout.write(char)
        sys.stdout.flush()

    def read_char(self) -> str:
        # sys.stdin.read(1) can be blocking and platform-dependent for raw char reads.
        # For simple line-buffered input or when input is redirected from a file, it's okay.
        # Returns empty string "" on EOF.
        return sys.stdin.read(1)

    def read_line(self) -> Optional[str]:
        # Read a line from stdin, strip the newline character
        try:
            line = sys.stdin.readline()
            if line == "":  # EOF
                return None
            if line.endswith("\n"):
                return line[:-1]
            return line
        except EOFError:
            return None

    def read_term(self) -> "PrologType":
        # This will require a parser integrated with the stream.
        raise NotImplementedError("ConsoleStream.read_term() is not yet implemented.")

    def write_term(self, term: "PrologType") -> None:
        # This will require a term serializer.
        raise NotImplementedError("ConsoleStream.write_term() is not yet implemented.")

    def get_stream_status(self) -> StreamStatus:
        return StreamStatus(
            at_eof=False,  # Console stream never really reaches EOF in typical usage
            has_data_available=False,  # Cannot reliably determine without blocking
            supports_peek=False,
            buffer_size=0,
            buffered_chars=0,
            buffer_position=0,
            stream_type="ConsoleStream",
            encoding="utf-8",
            last_operation=getattr(self, "_last_operation", "init"),
            has_errors=False,
            error_message=None,
        )


class StringStream(IOStream):
    """
    Concrete IOStream implementation for reading from and writing to strings/buffers.
    """

    def __init__(self, initial_input: str = "", output_buffer: List[str] = None):
        super().__init__()
        self.input_string = initial_input
        self.read_position = 0
        # Ensure output_buffer is a list. If None is passed, create a new list.
        self.output_buffer: List[str] = (
            output_buffer if output_buffer is not None else []
        )
        self._last_operation = "init"

    def write_char(self, char: str) -> None:
        self.output_buffer.append(char)

    def read_char(self) -> str:
        if self.read_position < len(self.input_string):
            char = self.input_string[self.read_position]
            self.read_position += 1
            return char
        else:
            return ""  # Signify EOF

    def read_line(self) -> Optional[str]:
        if self.read_position >= len(self.input_string):
            return None  # EOF - return None to distinguish from empty line

        # Find the next newline character
        newline_pos = self.input_string.find("\n", self.read_position)

        if newline_pos == -1:
            # No newline found, return rest of string
            line = self.input_string[self.read_position :]
            self.read_position = len(self.input_string)
            return line
        else:
            # Newline found, return line without newline
            line = self.input_string[self.read_position : newline_pos]
            self.read_position = newline_pos + 1  # Skip the newline
            return line

    def get_output_string(self) -> str:
        """Helper method to get the accumulated output as a single string."""
        return "".join(self.output_buffer)

    def clear_output_buffer(self) -> None:
        """Helper method to clear the output buffer."""
        self.output_buffer.clear()

    def reset_input(self, new_input_string: str = "") -> None:
        """Helper method to reset or set a new input string."""
        self.input_string = new_input_string
        self.read_position = 0

    def read_term(self) -> "PrologType":
        # This will require a parser integrated with the stream (reading from self.input_string).
        raise NotImplementedError("StringStream.read_term() is not yet implemented.")

    def write_term(self, term: "PrologType") -> None:
        # This will require a term serializer (writing to self.output_buffer).
        raise NotImplementedError("StringStream.write_term() is not yet implemented.")

    def peek_char(self) -> str:
        """実装方針: read_positionを変更せずに文字取得"""
        self._last_operation = "peek_char"
        if self.read_position < len(self.input_string):
            return self.input_string[self.read_position]
        return ""  # EOF

    def at_end_of_stream(self) -> bool:
        """実装方針: 位置と長さの比較のみ"""
        self._last_operation = "at_end_of_stream"
        return self.read_position >= len(self.input_string)

    def supports_peek_operations(self) -> bool:
        return True  # 完全サポート

    def get_stream_status(self) -> StreamStatus:
        return StreamStatus(
            at_eof=self.at_end_of_stream(),
            has_data_available=not self.at_end_of_stream(),
            supports_peek=True,
            buffer_size=len(self.input_string),
            buffered_chars=len(self.input_string) - self.read_position,
            buffer_position=self.read_position,
            stream_type="StringStream",
            encoding="utf-8",
            last_operation=getattr(self, "_last_operation", "init"),
            has_errors=False,
            error_message=None,
        )


class BufferedConsoleStream(IOStream):
    """
    バッファ付きコンソールストリーム（新規実装）
    - クロスプラットフォーム非ブロッキング読み取り
    - 循環バッファによる効率的なデータ管理
    - Windows/Unix両対応
    """

    def __init__(self, buffer_size: int = 1024):
        self.buffer = StreamBuffer(buffer_size)
        self.eof_reached = False
        self._last_operation = "init"
        self._platform_handler = create_platform_handler()

    def _fill_buffer_non_blocking(self) -> bool:
        """
        非ブロッキングでバッファを充填

        Returns:
            bool: 新しいデータを読み込めた場合True
        """
        if self.eof_reached:
            return False

        try:
            if self._platform_handler.is_input_available():
                char = self._platform_handler.read_char_nonblocking()
                if char:
                    self.buffer.put(char)
                    return True
                else:
                    self.eof_reached = True
                    return False
            return False  # 入力なし

        except Exception as e:
            raise StreamOperationError(f"Buffer fill failed: {e}")

    def peek_char(self) -> str:
        """実装方針: バッファから非破壊的読み取り"""
        self._last_operation = "peek_char"

        # バッファに文字があるかチェック
        char = self.buffer.peek()
        if char is not None:
            return char

        # バッファ充填を試行
        if self._fill_buffer_non_blocking():
            char = self.buffer.peek()
            return char if char is not None else ""

        # EOFまたは入力なし
        return ""

    def at_end_of_stream(self) -> bool:
        """実装方針: バッファ状態とEOFフラグの組み合わせ"""
        self._last_operation = "at_end_of_stream"

        if not self.buffer.is_empty():
            return False

        # バッファが空の場合、充填を試行
        self._fill_buffer_non_blocking()
        return self.eof_reached and self.buffer.is_empty()

    def read_char(self) -> str:
        """バッファ優先の文字読み取り"""
        self._last_operation = "read_char"

        # バッファから読み取り
        char = self.buffer.get()
        if char is not None:
            return char

        # バッファが空の場合はプラットフォーム固有の読み取り
        return self._platform_handler.read_char_blocking()

    def supports_peek_operations(self) -> bool:
        return True

    def get_stream_status(self) -> StreamStatus:
        return StreamStatus(
            at_eof=self.eof_reached and self.buffer.is_empty(),
            has_data_available=not self.buffer.is_empty() or not self.eof_reached,
            supports_peek=True,
            buffer_size=self.buffer.capacity,
            buffered_chars=self.buffer.size(),
            buffer_position=0,  # バッファ内位置は内部管理
            stream_type="BufferedConsoleStream",
            encoding="utf-8",
            last_operation=self._last_operation,
            has_errors=False,
            error_message=None,
        )

    def read_line(self) -> Optional[str]:
        """行読み取り（基本実装）"""
        self._last_operation = "read_line"
        line_chars = []

        while True:
            char = self.read_char()
            if char == "":
                # EOF
                if line_chars:
                    return "".join(line_chars)
                else:
                    return None
            elif char == "\n":
                # 改行文字は含めない
                return "".join(line_chars)
            else:
                line_chars.append(char)

    def write_char(self, char: str) -> None:
        """出力（コンソールストリームに委譲）"""
        sys.stdout.write(char)
        sys.stdout.flush()

    def read_term(self) -> "PrologType":
        raise NotImplementedError(
            "BufferedConsoleStream.read_term() is not yet implemented."
        )

    def write_term(self, term: "PrologType") -> None:
        raise NotImplementedError(
            "BufferedConsoleStream.write_term() is not yet implemented."
        )
