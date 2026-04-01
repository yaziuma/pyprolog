import subprocess
from dataclasses import dataclass

from pyprolog.core.errors import ExternalExecutionError


@dataclass(slots=True)
class ExecutionResult:
    exit_code: int
    stdout: str
    stderr: str


class ExternalPythonExecutor:
    def __init__(self, python_executable: str, timeout_seconds: int) -> None:
        self.python_executable = python_executable
        self.timeout_seconds = timeout_seconds

    def execute(self, script_path: str, args: list[str]) -> ExecutionResult:
        command = [self.python_executable, script_path, *args]
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                shell=False,
                stdin=subprocess.DEVNULL,
                timeout=self.timeout_seconds,
                check=False,
            )
        except FileNotFoundError as exc:
            raise ExternalExecutionError("python executable not found") from exc
        except subprocess.TimeoutExpired as exc:
            raise ExternalExecutionError("timeout") from exc

        return ExecutionResult(
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
