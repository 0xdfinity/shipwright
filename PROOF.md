# Shipwright proof run

Four isolated Python projects were created with planted defects, then passed through the unchanged `shipwright.agent.run_agent` loop on Nebius Token Factory using `nvidia/nemotron-3-super-120b-a12b`. Every case started with failing tests and ended with a passing agent status plus a fresh pytest pass. Times are measured wall time for the agent call, including model API latency, rounded to 0.01 seconds. Steps are the model-call step count reported by the existing agent loop.

| Scenario | Starting failure | Model steps | Agent wall time | Tests before | Tests after | Fix |
|---|---|---:|---:|---|---|---|
| Logic error | discount adds the percentage, yielding 12,000 instead of 8,000 cents | 6 | 5.85 s | red, 1 failed / 1 passed | green, 2 passed | subtract the percentage before applying the price factor |
| Off-by-one | `count - 1` slice omits a requested item, including an empty result for count 1 | 6 | 5.03 s | red, 2 failed | green, 2 passed | use `items[:count]` |
| Missing edge cases | even-length median returns one middle value; empty input raises `IndexError` | 6 | 4.80 s | red, 2 failed / 1 passed | green, 3 passed | average the two middle values and explicitly raise `ValueError` for empty input |
| Import bug | `from collections import Sequence` fails during test collection on Python 3.13 | 7 | 10.21 s | red, collection error | green, 1 passed | remove the unused, invalid import |

## Reproduce

From the repository root, install dependencies, provide a Nebius Token Factory API key, and run:

```bash
pip install -r requirements.txt
export NEBIUS_API_KEY=your_key
python scripts/run_proof.py
```

The runner recreates the four projects in `proof_cases/`, records each red-before result, executes the agent and captures its tool-call previews, then independently reruns pytest. Raw run data is saved at `proof_cases/results.json`. The measured outcomes above came from the live run on October 29, 2026.

## Offline tests

```bash
python -m pytest -q tests
```

The offline suite uses a scripted fake model to verify the loop, sandbox path guard, real pytest execution, and error handling. Current result: 5 passed.
