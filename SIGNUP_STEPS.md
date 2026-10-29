# Nebius Token Factory: signup steps (the user must do these)

Shipwright runs on Nebius Token Factory with an NVIDIA Nemotron open model. You need an API key, which only you can create.

1. Go to https://tokenfactory.nebius.com and create an account (Google or GitHub login works).
2. Optional but recommended: apply for builder credits at https://dev.nebius.com/builders. Approval can take a while, so apply first.
3. In the Token Factory console, open the API keys section and create a key. Copy it.
4. In the project folder, copy .env.example to .env and paste the key after NEBIUS_API_KEY=. Do not commit .env.
5. Verify the key:
   export NEBIUS_API_KEY=your_key_here
   python -m shipwright.live_check
   Expected output: model=nvidia/nemotron-3-super-120b-a12b reply='ready'
6. Fix the demo end to end:
   python -m shipwright demo_project "make the failing tests in test_shop.py pass"

Troubleshooting: a 401 means the key is wrong or has no credits. A connection error usually means the base URL is wrong; it must end in /v1.
