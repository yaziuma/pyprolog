# prolog/__init__.py
from prolog.parser import Parser, Scanner # Adjusted for new structure
from prolog.runtime.interpreter import Runtime
from prolog.core.types import Rule, Conjunction, Variable, Term # Adjusted for new structure
from prolog.core.errors import InterpreterError, ScannerError, ParserError # Adjusted for new structure

# 後方互換性のためのエイリアス (必要に応じて追加)
# from prolog.core.types import Variable, Term # Already imported above
# from prolog.core.errors import InterpreterError, ScannerError, ParserError # Already imported above

# 既存のエクスポートを維持
__all__ = [
    'Parser', 'Runtime', 'Rule', 'Conjunction', 'Scanner',
    'Variable', 'Term', 'InterpreterError', 'ScannerError', 'ParserError'
]
