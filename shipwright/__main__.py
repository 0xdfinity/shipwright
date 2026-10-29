"""Command line entry point: python -m shipwright <project_dir> "<goal>"."""
from __future__ import annotations

import argparse
import sys

from .agent import DEFAULT_MODEL, Event, make_client, run_agent
from .sandbox import Sandbox


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="shipwright", description="Fix a Python project until its tests pass.")
    p.add_argument("project", help="path to the project directory")
    p.add_argument("goal", help="what to fix, in plain language")
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--max-steps", type=int, default=12)
    args = p.parse_args(argv)

    def show(ev: Event) -> None:
        if ev.kind == "tool":
            print(f"  [tool] {ev.data['name']} -> {ev.data['result_preview'][:120]}")
        elif ev.kind == "done":
            print(f"\nstatus: {ev.data['status']} (steps: {ev.data['steps']})")
            if ev.data["summary"]:
                print(ev.data["summary"])

    result = run_agent(args.goal, Sandbox(args.project), make_client(), model=args.model,
                       max_steps=args.max_steps, on_event=show)
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
