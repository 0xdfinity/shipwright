"""Shipwright agent loop: the model reads code, edits files and runs the test
suite via tool calls until the suite passes or the step budget runs out.

Model calls go through Nebius Token Factory's OpenAI-compatible API, serving an
NVIDIA Nemotron open model by default."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Callable

from .sandbox import Sandbox, SandboxError

DEFAULT_MODEL = "nvidia/nemotron-3-super-120b-a12b"
DEFAULT_BASE_URL = "https://api.tokenfactory.nebius.com/v1/"

SYSTEM_PROMPT = """You are Shipwright, a careful coding agent. You are fixing a Python project.
Work in this loop: inspect the files, run the tests, make the smallest correct edit, re-run the tests.
Use the tools. Never claim tests pass unless run_tests returned passed=true in this session.
When the suite passes, reply with a short plain-text summary of what you changed and why."""

TOOLS = [
    {"type": "function", "function": {
        "name": "list_files", "description": "List project files (relative paths).",
        "parameters": {"type": "object", "properties": {}, "additionalProperties": False}}},
    {"type": "function", "function": {
        "name": "read_file", "description": "Read a project file.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}},
                       "required": ["path"], "additionalProperties": False}}},
    {"type": "function", "function": {
        "name": "write_file", "description": "Overwrite a project file with full new content.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
                       "required": ["path", "content"], "additionalProperties": False}}},
    {"type": "function", "function": {
        "name": "run_tests", "description": "Run the pytest suite for the project and return the result.",
        "parameters": {"type": "object", "properties": {}, "additionalProperties": False}}},
]


@dataclass
class Event:
    kind: str  # "tool" | "text" | "tests" | "done" | "error"
    data: dict = field(default_factory=dict)


def make_client(api_key: str | None = None, base_url: str | None = None):
    from openai import OpenAI  # imported lazily so tests run without the SDK call path
    key = api_key or os.environ.get("NEBIUS_API_KEY")
    if not key:
        raise RuntimeError("NEBIUS_API_KEY is not set")
    return OpenAI(base_url=base_url or os.environ.get("NEBIUS_BASE_URL", DEFAULT_BASE_URL), api_key=key)


def run_agent(goal: str, sandbox: Sandbox, client, model: str = DEFAULT_MODEL,
              max_steps: int = 12, on_event: Callable[[Event], None] | None = None) -> dict:
    """Run the fix loop. Returns {"status": "passed"|"failed"|"step_limit", "steps": n, "summary": str}."""
    emit = on_event or (lambda e: None)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Goal: {goal}\nStart by listing files and running the tests."},
    ]
    tests_ever_passed = False

    for step in range(1, max_steps + 1):
        resp = client.chat.completions.create(model=model, messages=messages, tools=TOOLS, temperature=0.2)
        msg = resp.choices[0].message
        messages.append({"role": "assistant", "content": msg.content or "", **(
            {"tool_calls": [tc.model_dump() for tc in msg.tool_calls]} if msg.tool_calls else {})})

        if not msg.tool_calls:
            summary = (msg.content or "").strip()
            status = "passed" if tests_ever_passed else "failed"
            emit(Event("done", {"status": status, "steps": step, "summary": summary}))
            return {"status": status, "steps": step, "summary": summary}

        for tc in msg.tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments or "{}")
                result = dispatch(name, args, sandbox)
                if name == "run_tests" and result["passed"]:
                    tests_ever_passed = True
                    # Stop early the moment the suite is green; the model's last words are the summary.
            except (SandboxError, KeyError, TypeError, json.JSONDecodeError) as exc:
                result = {"error": str(exc)}
            emit(Event("tool", {"name": name, "result_preview": json.dumps(result)[:300]}))
            messages.append({"role": "tool", "tool_call_id": tc.id,
                             "content": json.dumps(result)[:8000]})

    emit(Event("done", {"status": "step_limit", "steps": max_steps, "summary": ""}))
    return {"status": "step_limit", "steps": max_steps, "summary": ""}


def dispatch(name: str, args: dict, sandbox: Sandbox) -> dict:
    if name == "list_files":
        return {"files": sandbox.list_files()}
    if name == "read_file":
        return {"path": args["path"], "content": sandbox.read_file(args["path"])}
    if name == "write_file":
        return {"result": sandbox.write_file(args["path"], args["content"])}
    if name == "run_tests":
        return sandbox.run_tests()
    raise KeyError(f"unknown tool: {name}")
