from __future__ import annotations

import json
import os
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
BASE = ROOT / "proof_cases"

from shipwright.agent import DEFAULT_MODEL, make_client, run_agent
from shipwright.sandbox import Sandbox

CASES = {
    "logic": {
        "files": {
            "calc.py": "def apply_discount(price_cents, percent):\n    return price_cents * (100 + percent) // 100\n",
            "test_calc.py": "from calc import apply_discount\n\ndef test_discount():\n    assert apply_discount(10000, 20) == 8000\n\ndef test_zero_percent():\n    assert apply_discount(145, 0) == 145\n",
        },
        "goal": "Fix the discount calculation so percent reduces the price correctly.",
    },
    "off_by_one": {
        "files": {
            "sequence.py": "def take_first(items, count):\n    return items[:count - 1]\n",
            "test_sequence.py": "from sequence import take_first\n\ndef test_take_requested_count():\n    assert take_first(['a', 'b', 'c'], 2) == ['a', 'b']\n\ndef test_all_items():\n    assert take_first(['x'], 1) == ['x']\n",
        },
        "goal": "Fix take_first so it returns the requested number of items, including the boundary case.",
    },
    "edge_case": {
        "files": {
            "median.py": "def median(values):\n    values = sorted(values)\n    n = len(values)\n    return values[n // 2]\n",
            "test_median.py": "import pytest\nfrom median import median\n\ndef test_even_length_averages_middle_values():\n    assert median([1, 3, 2, 4]) == 2.5\n\ndef test_odd_length():\n    assert median([9, 1, 5]) == 5\n\ndef test_empty_is_explicit_error():\n    with pytest.raises(ValueError):\n        median([])\n",
        },
        "goal": "Fix median for even-length inputs and make empty input raise ValueError.",
    },
    "import_bug": {
        "files": {
            "text_tools.py": "from collections import Sequence\n\ndef normalize_words(text):\n    return [word.strip().lower() for word in text.split()]\n",
            "test_text_tools.py": "from text_tools import normalize_words\n\ndef test_normalize():\n    assert normalize_words('  Red  BLUE ') == ['red', 'blue']\n",
        },
        "goal": "Fix the import/runtime problem so normalize_words can be imported and works.",
    },
}


def create_case(name: str, spec: dict) -> Path:
    root = BASE / name
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    for rel, content in spec["files"].items():
        (root / rel).write_text(content, encoding="utf-8")
    return root


def main() -> int:
    if not os.environ.get("NEBIUS_API_KEY"):
        print("NEBIUS_API_KEY is not set", file=sys.stderr)
        return 2
    client = make_client()
    records = []
    for name, spec in CASES.items():
        root = create_case(name, spec)
        sandbox = Sandbox(root)
        before = sandbox.run_tests()
        before["output"] = before["output"].replace(str(root), name)
        started = time.monotonic()
        events = []
        result = run_agent(spec["goal"], sandbox, client, model=DEFAULT_MODEL, max_steps=12, on_event=events.append)
        elapsed = round(time.monotonic() - started, 2)
        after = sandbox.run_tests()
        record = {
            "case": name,
            "model": DEFAULT_MODEL,
            "steps": result.get("steps"),
            "elapsed_seconds": elapsed,
            "before": before,
            "after": after,
            "status": result.get("status"),
            "summary": result.get("summary", ""),
            "tool_events": [{"name": e.data.get("name"), "preview": e.data.get("result_preview", "")[:160]} for e in events if e.kind == "tool"],
        }
        records.append(record)
        print(json.dumps(record, ensure_ascii=False))
        if result.get("status") != "passed" or not after.get("passed"):
            print(f"FAILED CASE: {name}", file=sys.stderr)
            (BASE / "results.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
            return 1
    (BASE / "results.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
