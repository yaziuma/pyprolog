#!/usr/bin/python3

import argparse
import sys

from pyprolog.runtime.interpreter import Runtime


def start(input_path: str, unsafe_mode: bool = False) -> Runtime:
    try:
        runtime = Runtime(unsafe_mode=unsafe_mode)
        runtime.consult(input_path)
    except Exception as e:
        print(f"Error loading rules: {e}")
        sys.exit()

    if runtime is None:
        print("Failed to compile Prolog rules")
        sys.exit()
    return runtime


def main():
    from .repl import run_repl

    ap = argparse.ArgumentParser(
        prog="prolog",
        usage="%(prog)s [options] path",
        description="Simple Prolog interpreter",
    )
    ap.add_argument("Path", type=str, help="Path to file with Prolog rules")
    ap.add_argument(
        "--explain", action="store_true", help="Enable query explanation mode"
    )
    ap.add_argument("--trace-depth", type=int, help="Maximum trace depth")
    ap.add_argument(
        "--trace-format",
        choices=["text", "tree", "json"],
        default="text",
        help="Trace output format",
    )
    ap.add_argument(
        "--unsafe",
        action="store_true",
        help="Enable unsafe external Python execution predicates",
    )
    args = ap.parse_args()
    input_path = args.Path

    # Pass args to repl for explain functionality
    if args.explain:
        run_repl(start(input_path, unsafe_mode=args.unsafe), explain_mode=True, args=args)
    else:
        run_repl(start(input_path, unsafe_mode=args.unsafe))


if __name__ == "__main__":
    main()
