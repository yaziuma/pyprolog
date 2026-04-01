from pathlib import Path

from pyprolog.core.errors import ScriptRegistrationError


def validate_absolute_python_path(raw_path: str) -> Path:
    path = Path(raw_path)
    if not path.is_absolute():
        raise ScriptRegistrationError("absolute path required")
    if path.suffix != ".py":
        raise ScriptRegistrationError("only .py allowed")
    if not path.exists() or not path.is_file():
        raise ScriptRegistrationError("script not found")
    return path.resolve()
