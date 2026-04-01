import sys
from dataclasses import dataclass


@dataclass(slots=True)
class RuntimeConfig:
    unsafe_mode: bool = False
    python_executable: str = sys.executable
    exec_timeout_seconds: int = 30
