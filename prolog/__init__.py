# prolog/__init__.py
from prolog.parser.parser import Parser
from prolog.parser.scanner import Scanner  # Adjusted for new structure
from prolog.runtime.interpreter import Runtime
from prolog.core.types import (
    Rule,
    Variable,
    Term,
)  # Adjusted for new structure
from prolog.core.errors import (
    InterpreterError,
    ScannerError,
    ParserError,
)  # Adjusted for new structure

__all__ = [
    "Parser",
    "Runtime",
    "Rule",
    "Scanner",
    "Variable",
    "Term",
    "InterpreterError",
    "ScannerError",
    "ParserError",
]
