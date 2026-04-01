class InterpreterError(Exception):
    pass


class ScannerError(Exception):
    pass


class ParserError(Exception):
    pass


class PrologError(Exception):
    pass


class UnsafeModeError(PrologError):
    pass


class ScriptRegistrationError(PrologError):
    pass


class InvalidCliArgsError(PrologError):
    pass


class ScriptNotRegisteredError(PrologError):
    pass


class ExternalExecutionError(PrologError):
    pass


class UnificationError(Exception):
    pass


class CutException(Exception):
    """カット演算子 (!) が実行されたことを示す例外"""

    pass
