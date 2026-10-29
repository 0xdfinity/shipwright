# Shipwright demo video script (target 2:30, limit 3:00, public YouTube)

0:00 to 0:15. Hook (screen: terminal, red test output)
"This project has three bugs and three failing tests. I'm going to hand it to an AI agent running on Nebius, and it will fix it on its own."

0:15 to 0:35. The problem
"Coding agents often claim the code works without proving it. Shipwright runs the real test suite after every edit and only reports success when the tests say so."

0:35 to 1:05. Architecture (screen: diagram or code view of agent.py)
"The model is NVIDIA Nemotron 3 Super, served on Nebius Token Factory through the OpenAI-compatible API. It gets four tools: list files, read, write, and run tests. The sandbox keeps every file change inside the project."

1:05 to 2:05. Live run (screen: terminal, real time, no cuts)
Run: python -m shipwright demo_project "make the failing tests in test_shop.py pass"
Narrate the tool calls as they appear: list_files, run_tests (red), read_file, write_file, run_tests (green).
"Watch it read the code, run the tests, see them fail, make an edit, and run them again."

2:05 to 2:30. Result (screen: final status line and the pytest green line)
"Status passed. Three bugs fixed, all tests green, and the agent only said done after the suite passed."

2:30 to 2:50. Where Nebius and NVIDIA fit
"Token Factory gave us the Nemotron endpoint with tool calling, no GPU setup. Swapping to the Nano model is a single flag."

2:50 to 3:00. Close
"Shipwright. Point it at a broken repo, and it ships a fix with proof."

Production notes for Canva/screen recording: 1080p, dark terminal, large font. Show the on-screen text for each step. Upload to YouTube as public, and keep it under 3:00.
