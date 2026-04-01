from pathlib import Path

from pyprolog.core.errors import ScriptNotRegisteredError, ScriptRegistrationError


class PythonScriptRegistry:
    def __init__(self) -> None:
        self._entries: dict[str, str] = {}

    def register(self, name: str, path: Path) -> None:
        if name in self._entries:
            raise ScriptRegistrationError(f"duplicate script registration: {name}")
        self._entries[name] = str(path)

    def unregister(self, name: str) -> None:
        if name not in self._entries:
            raise ScriptNotRegisteredError(f"script not registered: {name}")
        del self._entries[name]

    def resolve(self, name: str) -> str:
        if name not in self._entries:
            raise ScriptNotRegisteredError(f"script not registered: {name}")
        return self._entries[name]

    def items(self) -> list[tuple[str, str]]:
        return list(self._entries.items())
