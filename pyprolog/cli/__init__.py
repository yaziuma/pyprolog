# pyprolog/cli/__init__.py
from .prolog import main

__all__ = ["REPL", "main"]


def __getattr__(name: str):
    if name == "REPL":
        from .repl import REPL

        return REPL
    raise AttributeError(name)
