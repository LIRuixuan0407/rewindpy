from __future__ import annotations

import argparse
import sys
import webbrowser
from pathlib import Path

from .runner import run_target


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rewindpy",
        description="Run a Python script and create a rewindable local report when it crashes.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("run", help="Run a Python script under RewindPy")
    run.add_argument("target", type=Path, help="Path to the Python script")
    run.add_argument("--output", type=Path, default=Path("rewindpy-report.html"))
    run.add_argument("--max-events", type=int, default=5_000)
    run.add_argument("--open", action="store_true", dest="open_report", help="Open the report in a browser")
    return parser


def _split_target_args(argv: list[str]) -> tuple[list[str], list[str]]:
    """Split RewindPy arguments from target arguments at an explicit `--`."""
    if "--" not in argv:
        return argv, []
    separator = argv.index("--")
    return argv[:separator], argv[separator + 1 :]


def main(argv: list[str] | None = None) -> int:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    rewind_args, target_args = _split_target_args(raw_argv)
    parser = build_parser()
    args = parser.parse_args(rewind_args)

    if args.command == "run":
        try:
            exit_code = run_target(
                args.target,
                target_args,
                output=args.output,
                max_events=max(10, args.max_events),
            )
        except FileNotFoundError as exc:
            parser.error(str(exc))

        if exit_code != 0 and args.output.exists():
            report = args.output.resolve()
            print(f"\nRewindPy captured the crash: {report}", file=sys.stderr)
            if args.open_report:
                webbrowser.open(report.as_uri())
        return exit_code

    return 2
