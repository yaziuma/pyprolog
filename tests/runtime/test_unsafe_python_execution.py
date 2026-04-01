import textwrap
from pathlib import Path

import pytest

from pyprolog.cli.prolog import start
from pyprolog.core.errors import (
    InvalidCliArgsError,
    ScriptRegistrationError,
    UnsafeModeError,
)
from pyprolog.core.types import Atom, Number, Variable
from pyprolog.runtime.interpreter import Runtime


def _write_script(path: Path, content: str) -> Path:
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    return path


def _write_program(path: Path, content: str) -> Path:
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    return path


def test_py_register_rejected_when_unsafe_mode_disabled(tmp_path: Path) -> None:
    script_path = _write_script(
        tmp_path / "echo_args.py",
        """
        import sys
        print("|".join(sys.argv[1:]))
        """,
    )
    runtime = Runtime()

    with pytest.raises(UnsafeModeError):
        runtime.query(f"py_register(echo_args, '{script_path}').")


def test_py_register_requires_absolute_path(tmp_path: Path) -> None:
    _write_script(
        tmp_path / "echo_args.py",
        """
        print("ok")
        """,
    )
    runtime = Runtime(unsafe_mode=True)

    with pytest.raises(ScriptRegistrationError):
        runtime.query("py_register(echo_args, 'relative.py').")


def test_py_call_executes_registered_script_with_cli_args_only(
    tmp_path: Path,
) -> None:
    script_path = _write_script(
        tmp_path / "echo_args.py",
        """
        import sys

        def main() -> int:
            args = sys.argv[1:]
            print("|".join(args))
            print("stderr:" + "|".join(args), file=sys.stderr)
            return 0

        if __name__ == "__main__":
            raise SystemExit(main())
        """,
    )
    runtime = Runtime(unsafe_mode=True)

    assert runtime.query(f"py_register(echo_args, '{script_path}').") == [{}]
    assert runtime.add_rule(
        'run_task(TaskId, Exit, Out, Err) :- py_call(echo_args, ["--task-id", TaskId, "日本語"], Exit, Out, Err).'
    )

    solutions = runtime.query("run_task('task-001', Exit, Out, Err).")

    assert len(solutions) == 1
    solution = solutions[0]
    assert solution[Variable("Exit")] == Number(0)
    assert solution[Variable("Out")] == Atom("--task-id|task-001|日本語\n")
    assert solution[Variable("Err")] == Atom("stderr:--task-id|task-001|日本語\n")


def test_py_registered_and_py_unregister_manage_registry(tmp_path: Path) -> None:
    script_path = _write_script(
        tmp_path / "simple.py",
        """
        print("ok")
        """,
    )
    runtime = Runtime(unsafe_mode=True)

    runtime.query(f"py_register(simple, '{script_path}').")
    registered = runtime.query("py_registered(Name, Path).")

    assert len(registered) == 1
    assert registered[0][Variable("Name")] == Atom("simple")
    assert registered[0][Variable("Path")] == Atom(str(script_path.resolve()))

    assert runtime.query("py_unregister(simple).") == [{}]
    assert runtime.query("py_registered(Name, Path).") == []


def test_py_call_rejects_invalid_args_shape(tmp_path: Path) -> None:
    script_path = _write_script(
        tmp_path / "echo_args.py",
        """
        print("ok")
        """,
    )
    runtime = Runtime(unsafe_mode=True)
    runtime.query(f"py_register(echo_args, '{script_path}').")

    with pytest.raises(InvalidCliArgsError):
        runtime.query("py_call(echo_args, X, Exit, Out, Err).")

    with pytest.raises(InvalidCliArgsError):
        runtime.query("py_call(echo_args, [foo(bar)], Exit, Out, Err).")

    with pytest.raises(InvalidCliArgsError):
        runtime.query("py_call(echo_args, [[a]], Exit, Out, Err).")


def test_py_call_does_not_provide_stdin(tmp_path: Path) -> None:
    script_path = _write_script(
        tmp_path / "needs_input.py",
        """
        import sys

        def main() -> int:
            try:
                input()
            except EOFError:
                print("stdin-disabled", file=sys.stderr)
                return 1
            print("unexpected-stdin")
            return 0

        if __name__ == "__main__":
            raise SystemExit(main())
        """,
    )
    runtime = Runtime(unsafe_mode=True)
    runtime.query(f"py_register(needs_input, '{script_path}').")

    solutions = runtime.query("py_call(needs_input, [], Exit, Out, Err).")

    assert len(solutions) == 1
    solution = solutions[0]
    assert solution[Variable("Exit")] == Number(1)
    assert solution[Variable("Out")] == Atom("")
    assert solution[Variable("Err")] == Atom("stdin-disabled\n")


def test_consult_applies_py_register_directive(tmp_path: Path) -> None:
    script_path = _write_script(
        tmp_path / "echo_args.py",
        """
        import sys
        print("|".join(sys.argv[1:]))
        """,
    )
    program_path = _write_program(
        tmp_path / "workflow.pl",
        f"""
        :- py_register(echo_args, "{script_path}").

        run(Exit, Out, Err) :-
            py_call(echo_args, ["--mode", fast], Exit, Out, Err).
        """,
    )
    runtime = Runtime(unsafe_mode=True)

    assert runtime.consult(str(program_path))
    solutions = runtime.query("run(Exit, Out, Err).")

    assert len(solutions) == 1
    solution = solutions[0]
    assert solution[Variable("Exit")] == Number(0)
    assert solution[Variable("Out")] == Atom("--mode|fast\n")
    assert solution[Variable("Err")] == Atom("")


def test_cli_start_honors_unsafe_mode_for_directives(tmp_path: Path) -> None:
    script_path = _write_script(
        tmp_path / "echo_args.py",
        """
        print("ok")
        """,
    )
    program_path = _write_program(
        tmp_path / "workflow.pl",
        f"""
        :- py_register(echo_args, '{script_path}').
        """,
    )

    runtime = start(str(program_path), unsafe_mode=True)
    solutions = runtime.query("py_registered(Name, Path).")

    assert len(solutions) == 1
    assert solutions[0][Variable("Name")] == Atom("echo_args")
