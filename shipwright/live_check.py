"""Smoke test against the real Nebius Token Factory endpoint.
Run: NEBIUS_API_KEY=... python -m shipwright.live_check"""
import os
import sys

from .agent import DEFAULT_MODEL, make_client


def main() -> int:
    if not os.environ.get("NEBIUS_API_KEY"):
        print("NEBIUS_API_KEY is not set. See SIGNUP_STEPS.md.")
        return 2
    client = make_client()
    resp = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=[{"role": "user", "content": "Reply with the single word: ready"}],
        max_tokens=20, temperature=0,
    )
    text = resp.choices[0].message.content
    print(f"model={DEFAULT_MODEL} reply={text!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
