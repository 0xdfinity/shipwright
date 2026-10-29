# Shipwright

Track: Coding and Agentic Engineering Track (verified on nebiusglobalaihackathon.devpost.com: 'build coding agents and developer tools: agents that write, run, and test code in Token Factory')

## Inspiration
Coding agents often say the code works without proving it. We wanted an agent that fixes a broken project and stops only when the real test suite passes.

## What it does
Shipwright takes a Python project and a plain-language goal. It lists the files, runs the tests, reads the failing code, makes the smallest fix, runs the tests again, and repeats until they pass. Then it reports what it changed. A run counts as passed only when the test suite itself returned green in that session.

## How we built it
- Model: NVIDIA Nemotron 3 Super 120B (open weights) on Nebius Token Factory, through its OpenAI-compatible API. We use native tool calling for the four tools (list_files, read_file, write_file, run_tests).
- Agent loop: a small Python loop that dispatches tool calls and feeds results back to the model. We wrote it from scratch to keep it auditable.
- Sandbox: every file operation is confined to the project root, and tests run under a timeout.
- Tests: 5 offline tests cover the loop, the path guard, the real pytest run and error handling, using a scripted model so the suite runs without a key.

## How NVIDIA Nemotron and Nebius Token Factory are used
- Nemotron 3 Super is the reasoning and coding model. Its tool calling and long context are what the agent loop depends on.
- Token Factory serves it behind an OpenAI-compatible endpoint, so there is no GPU or serving setup. Switching to Nemotron 3 Nano (nvidia/nemotron-3-nano-30b-a3b) is a one-flag change for a faster, cheaper loop.
- Feedback on Token Factory: the OpenAI-compatible base URL made integration a three-line change. (Add your own experience here after you run it.)

## Challenges
Keeping the agent honest. A model can declare victory without running anything, so the loop only reports passed when run_tests returned green during the run.

## Accomplishments
A working agent with a verified loop, a path-safe sandbox, and a demo project where it fixes three planted bugs.

## What we learned
Tool-calling agents are only as trustworthy as the checks outside the model. Tests are the cheapest honest judge.

## What's next
Multi-repo support, a web UI, and the Nebius Serverless Jobs deployment for long fix runs.

## Built with
Python, OpenAI Python SDK (Apache 2.0), pytest (MIT), NVIDIA Nemotron 3 Super, Nebius Token Factory.

## Links
- Public repository (MIT): [paste your GitHub or GitLab URL]
- Demo video (YouTube, under 3 min): [paste your YouTube URL]
- Working demo: run locally with the README steps, or host on Nebius Serverless (see README).
