# tests/runtime/test_io_infrastructure.py
import pytest
from pyprolog.runtime.io_streams import StringStream, ConsoleStream, IOStream
from pyprolog.runtime.io_manager import IOManager
from pyprolog.runtime.interpreter import Runtime # Assuming Runtime is in interpreter

# Test StringStream
def test_string_stream_read():
    """Test reading characters from StringStream."""
    stream = StringStream("abc")
    assert stream.read_char() == 'a'
    assert stream.read_char() == 'b'
    assert stream.read_char() == 'c'
    assert stream.read_char() == ""  # EOF
    assert stream.read_char() == ""  # Stays EOF

def test_string_stream_write():
    """Test writing characters to StringStream's internal buffer."""
    stream = StringStream()
    stream.write_char('x')
    stream.write_char('y')
    assert stream.output_buffer == ['x', 'y']
    assert stream.get_output_string() == "xy"

def test_string_stream_write_with_external_buffer():
    """Test writing to StringStream with an externally provided buffer."""
    my_buffer = []
    stream = StringStream(output_buffer=my_buffer)
    stream.write_char('z')
    stream.write_char('a')
    assert my_buffer == ['z', 'a']
    assert stream.get_output_string() == "za" # Also check internal helper

def test_string_stream_reset_input():
    """Test resetting the input string in StringStream."""
    stream = StringStream("abc")
    assert stream.read_char() == 'a'
    stream.reset_input("xyz")
    assert stream.read_char() == 'x'
    assert stream.read_char() == 'y'
    assert stream.read_char() == 'z'
    assert stream.read_char() == ""

def test_string_stream_clear_output():
    """Test clearing the output buffer in StringStream."""
    stream = StringStream()
    stream.write_char('x')
    assert stream.get_output_string() == "x"
    stream.clear_output_buffer()
    assert stream.get_output_string() == ""
    assert stream.output_buffer == []


# Test IOManager Stream Management
def test_io_manager_default_streams():
    """Test that IOManager defaults to ConsoleStream."""
    manager = IOManager()
    assert isinstance(manager.get_input_stream(), ConsoleStream)
    assert isinstance(manager.get_output_stream(), ConsoleStream)

def test_io_manager_set_get_streams():
    """Test setting and getting streams in IOManager."""
    manager = IOManager()
    input_s = StringStream("test")
    output_s = StringStream()

    manager.set_input_stream(input_s)
    manager.set_output_stream(output_s)

    assert manager.get_input_stream() is input_s
    assert manager.get_output_stream() is output_s

# Test IOManager Character I/O
def test_io_manager_read_char():
    """Test read_char_from_current in IOManager."""
    manager = IOManager()
    manager.set_input_stream(StringStream("hello"))
    assert manager.read_char_from_current() == 'h'
    assert manager.read_char_from_current() == 'e'
    assert manager.read_char_from_current() == 'l'
    assert manager.read_char_from_current() == 'l'
    assert manager.read_char_from_current() == 'o'
    assert manager.read_char_from_current() == "" # EOF

def test_io_manager_write_char():
    """Test write_char_to_current in IOManager."""
    manager = IOManager()
    test_buffer = []
    manager.set_output_stream(StringStream(output_buffer=test_buffer))

    manager.write_char_to_current('w')
    manager.write_char_to_current('o')

    assert test_buffer == ['w', 'o']
    # Verify through the stream's own method too
    assert isinstance(manager.get_output_stream(), StringStream)
    current_output_stream = manager.get_output_stream()
    if isinstance(current_output_stream, StringStream): # type guard for mypy
        assert current_output_stream.get_output_string() == "wo"


# Test Runtime IOManager Integration
def test_runtime_has_io_manager():
    """Test that a Runtime instance has an IOManager."""
    runtime_instance = Runtime() # Assuming default constructor is fine
    assert isinstance(runtime_instance.io_manager, IOManager)
    # Also check if default streams are ConsoleStream via runtime's IOManager
    assert isinstance(runtime_instance.io_manager.get_input_stream(), ConsoleStream)
    assert isinstance(runtime_instance.io_manager.get_output_stream(), ConsoleStream)

# Note: ConsoleStream read_char and write_char are hard to test in automated unit tests
# without mocking sys.stdin and sys.stdout, which is beyond the scope of "basic" tests here.
# Their direct functionality relies on the system's console.
# We are testing that IOManager *uses* ConsoleStream by default.

# Placeholder for PrologType for type hinting if not using string literals
# This would normally come from e.g. from pyprolog.core.types import PrologType
# For now, the io_streams.py uses 'PrologType' as a string.
PrologType = None
