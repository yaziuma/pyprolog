#!/usr/bin/env python3
# logging標準の遅延フォーマットに変換。debugが無効なら repr が起きない
# 使い方
# 
# 1. まず dry-run（差分表示のみ）
# uv run python scripts/convert_fstring_logging.py --root pyprolog --dry-run
# 
# 2. 実際に書き換え（バックアップなし。gitで管理）
# uv run python scripts/convert_fstring_logging.py --root pyprolog --write
# 
# 3. 特定ファイルだけ
# uv run python scripts/convert_fstring_logging.py --files pyprolog/runtime/logic_interpreter.py --write

"""
Convert logging calls like:

    logger.debug(f"unify: {a} {b}")

into:

    logger.debug("unify: %r %r", a, b)

Safe-only policy:
- Only converts when the first argument is a simple f-string (JoinedStr)
- No format_spec inside FormattedValue (e.g., {x:.2f} is skipped)
- Only conversions:
    - default or !r  -> %r
    - !s            -> %s
  Anything else is skipped.
- Skips if the logging call already has extra positional args (besides the first message)
  or keyword args (to avoid changing semantics).

Python 3.9+ recommended (uses ast.unparse). For 3.8, you can swap unparse with astor.
"""

from __future__ import annotations

import argparse
import ast
import difflib
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple


LOG_METHODS = {"debug", "info", "warning", "error", "exception", "critical"}

# 実行範囲は scripts/ から ../pyprolog 配下に固定
BASE_ROOT = (Path(__file__).resolve().parent / ".." / "pyprolog").resolve()


@dataclass
class Change:
    path: Path
    before: str
    after: str
    conversions: int
    skipped: int


def _escape_percent(s: str) -> str:
    # printf-style formatting uses % for placeholders; literal % must be escaped.
    return s.replace("%", "%%")


def _joinedstr_to_percent(joined: ast.JoinedStr) -> Optional[Tuple[str, List[ast.AST]]]:
    """
    Convert an ast.JoinedStr into (format_string, args) for logging % formatting.

    Returns None if it contains unsupported features.
    """
    fmt_parts: List[str] = []
    fmt_args: List[ast.AST] = []

    for v in joined.values:
        if isinstance(v, ast.Constant) and isinstance(v.value, str):
            fmt_parts.append(_escape_percent(v.value))
            continue

        if isinstance(v, ast.FormattedValue):
            # Reject format_spec like {x:.2f}
            if v.format_spec is not None:
                return None

            # Handle conversion:
            # -1 = default, ord('r') = !r, ord('s') = !s, ord('a') = !a
            conv = v.conversion
            if conv == -1 or conv == ord("r"):
                fmt_parts.append("%r")
                fmt_args.append(v.value)
                continue
            if conv == ord("s"):
                fmt_parts.append("%s")
                fmt_args.append(v.value)
                continue

            # !a or other conversions: skip (safe-only)
            return None

        # Any other node types inside f-string: skip
        return None

    return ("".join(fmt_parts), fmt_args)


class LoggingFStringTransformer(ast.NodeTransformer):
    def __init__(self, source: str):
        self.source = source
        self.conversions = 0
        self.skipped = 0

    def visit_Call(self, node: ast.Call) -> ast.AST:
        self.generic_visit(node)

        # Match: <something>.<log_method>(...)
        if not isinstance(node.func, ast.Attribute):
            return node
        if node.func.attr not in LOG_METHODS:
            return node

        # Must have at least 1 positional arg
        if not node.args:
            return node

        # Only convert if the first arg is an f-string JoinedStr
        first = node.args[0]
        if not isinstance(first, ast.JoinedStr):
            return node

        # Safe-only: skip if there are already extra args or any kwargs
        # Because: logger.debug(f"...{x}...", y) changes meaning.
        if len(node.args) != 1 or node.keywords:
            self.skipped += 1
            return node

        converted = _joinedstr_to_percent(first)
        if converted is None:
            self.skipped += 1
            return node

        fmt, fmt_args = converted

        new_args: List[ast.AST] = [ast.Constant(value=fmt), *fmt_args]
        new_call = ast.Call(
            func=node.func,
            args=new_args,
            keywords=[],
        )
        ast.copy_location(new_call, node)
        ast.fix_missing_locations(new_call)

        self.conversions += 1
        return new_call


def transform_source(src: str, filename: str) -> Tuple[str, int, int]:
    """
    Returns (new_source, conversions, skipped)
    """
    tree = ast.parse(src, filename=filename)
    tr = LoggingFStringTransformer(src)
    new_tree = tr.visit(tree)
    ast.fix_missing_locations(new_tree)

    # ast.unparse normalizes formatting; that's acceptable for an automated refactor.
    new_src = ast.unparse(new_tree) + ("\n" if not src.endswith("\n") else "")
    return new_src, tr.conversions, tr.skipped


def iter_py_files(root: Path) -> List[Path]:
    return [p for p in root.rglob("*.py") if p.is_file()]


def print_diff(path: Path, before: str, after: str) -> None:
    diff = difflib.unified_diff(
        before.splitlines(keepends=True),
        after.splitlines(keepends=True),
        fromfile=str(path),
        tofile=str(path),
    )
    for line in diff:
        print(line, end="")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=str, default=".", help="Root directory to scan (recursive)")
    ap.add_argument("--files", nargs="*", help="Specific files to process (overrides --root)")
    ap.add_argument("--dry-run", action="store_true", help="Show diffs but do not write")
    ap.add_argument("--write", action="store_true", help="Write changes in place (no .bak; rely on git)")
    args = ap.parse_args()

    if args.write and args.dry_run:
        raise SystemExit("Choose either --dry-run or --write, not both.")
    if not args.write and not args.dry_run:
        # Default to dry-run to be safe
        args.dry_run = True

    # pyprolog専用: 実行範囲を scripts/ から ../pyprolog 配下に限定
    if not BASE_ROOT.exists():
        raise SystemExit(f"Base root not found: {BASE_ROOT}")

    paths: List[Path]
    if args.files:
        # 明示指定は base_root 配下のみ許可
        paths = []
        for f in args.files:
            p = (
                Path(f).resolve()
                if Path(f).is_absolute()
                else (BASE_ROOT / f).resolve()
            )
            if not str(p).startswith(str(BASE_ROOT)):
                raise SystemExit(f"File out of scope: {p}")
            if p.exists() and p.is_file():
                paths.append(p)
        if not paths:
            raise SystemExit("No valid files under base root.")
    else:
        # root 引数は base_root からの相対として解釈
        root_path = (BASE_ROOT / args.root).resolve()
        if not str(root_path).startswith(str(BASE_ROOT)):
            raise SystemExit(f"Root out of scope: {root_path}")
        paths = iter_py_files(root_path)

    total_conv = 0
    total_skip = 0
    touched = 0

    for path in paths:
        if not path.exists() or not path.is_file():
            continue

        before = path.read_text(encoding="utf-8")
        after, conv, skip = transform_source(before, filename=str(path))
        total_conv += conv
        total_skip += skip

        if after != before and conv > 0:
            touched += 1
            if args.dry_run:
                print_diff(path, before, after)
            else:
                path.write_text(after, encoding="utf-8")

    mode = "DRY-RUN" if args.dry_run else "WRITE"
    print(f"\n[{mode}] files_scanned={len(paths)} touched={touched} conversions={total_conv} skipped={total_skip}")


if __name__ == "__main__":
    main()
