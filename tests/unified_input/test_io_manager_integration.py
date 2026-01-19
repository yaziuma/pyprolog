"""
IOManager統合テスト

統一入力システムのrequest_input経由の基本動作を確認する。
"""

from pyprolog.runtime.io_manager import IOManager
from pyprolog.runtime.io_streams import StringStream
from pyprolog.runtime.unified_input_system import StreamInputHandler


def test_request_input_char_line_peek():
    manager = IOManager()
    manager.set_input_handler(StreamInputHandler(StringStream("ab\ncd\n")))

    assert manager.request_input("char", "get_char") == "a"
    assert manager.request_input("peek_char", "peek_char", non_destructive=True) == "b"
    assert manager.request_input("line", "read_line") == "b"
    assert manager.request_input("line", "read_line") == "cd"
