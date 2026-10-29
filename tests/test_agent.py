"""Offline tests: the agent loop, sandbox safety and the CLI wiring, using a scripted fake model.
Run with: python -m pytest -q   (from hackathon-nebius/)"""
import json
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

from shipwright.agent import run_agent
from shipwright.sandbox import Sandbox, SandboxError

DEMO = Path(__file__).resolve().parent.parent / "demo_project"


def tool_call(cid, name, args):
    return SimpleNamespace(id=cid, type="function",
                           function=SimpleNamespace(name=name, arguments=json.dumps(args)),
                           model_dump=lambda: {"id": cid, "type": "function",
                                               "function": {"name": name, "arguments": json.dumps(args)}})


def reply(content="", calls=None):
    msg = SimpleNamespace(content=content, tool_calls=calls)
    return SimpleNamespace(choices=[SimpleNamespace(message=msg)])


class ScriptedClient:
    """Stands in for the OpenAI client: returns queued replies in order."""
    def __init__(self, replies):
        self.replies = list(replies)
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        return self.replies.pop(0)


@pytest.fixture
def project(tmp_path):
    dest = tmp_path / "proj"
    shutil.copytree(DEMO, dest)
    # Keep sandbox failure tests meaningful even if the demo source is repaired.
    (dest / "shop.py").write_text(
        """def slugify(title):
    return title

def apply_discount(price_cents, percent):
    return price_cents * (100 + percent) // 100

def median(values):
    values = sorted(values)
    return values[len(values) // 2]
""",
        encoding="utf-8",
    )
    return dest


def fixed_shop(project):
    (project / "shop.py").write_text(
        'def slugify(title):\n    return "-".join(title.strip().lower().split())\n\n'
        'def apply_discount(price_cents, percent):\n    return price_cents * (100 - percent) // 100\n\n'
        'def median(values):\n    v = sorted(values)\n    n = len(v)\n'
        '    return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2\n')


def test_sandbox_blocks_path_escape(project):
    sb = Sandbox(project)
    with pytest.raises(SandboxError):
        sb.resolve("../../etc/passwd")


def test_sandbox_runs_real_tests_and_detects_failure(project):
    sb = Sandbox(project)
    res = sb.run_tests()
    assert res["passed"] is False
    assert "failed" in res["output"].lower()


def test_agent_fixes_project_end_to_end(project):
    fixed_shop(project)
    client = ScriptedClient([
        reply(calls=[tool_call("1", "list_files", {})]),
        reply(calls=[tool_call("2", "run_tests", {})]),
        reply("All three bugs fixed. Tests green."),
    ])
    events = []
    out = run_agent("fix shop.py", Sandbox(project), client, on_event=events.append)
    assert out["status"] == "passed"
    assert out["steps"] == 3
    assert any(e.kind == "tool" and e.data["name"] == "run_tests" for e in events)


def test_agent_reports_failed_if_tests_never_pass(project):
    client = ScriptedClient([
        reply(calls=[tool_call("1", "run_tests", {})]),
        reply("Done, I think it works."),
    ])
    out = run_agent("fix", Sandbox(project), client)
    assert out["status"] == "failed"


def test_agent_survives_bad_tool_arguments(project):
    client = ScriptedClient([
        reply(calls=[tool_call("1", "read_file", {"path": "../../secret"})]),
        reply("Could not read that file."),
    ])
    out = run_agent("fix", Sandbox(project), client)
    assert out["status"] == "failed"
    assert out["steps"] == 2
