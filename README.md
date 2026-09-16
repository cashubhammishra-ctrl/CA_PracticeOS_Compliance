# CA PracticeOS Compliance — AI Agent Layer

AICA Level 2 capstone. See [CLAUDE.md](CLAUDE.md) for the full build plan, session schedule, and priority rules.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r src/requirements.txt
copy .env.example .env        # then fill in your real ANTHROPIC_API_KEY
```

Test the Claude API connection:

```bash
python src/test_claude_api.py
```

## Status (updated each session)

- **Wed 16 Sep** — Repo initialized, virtualenv + `src/requirements.txt` installed, 8 sample
  documents collected in `examples/inputs/` (4 mock PAN/GST images, 3 sample engagement
  letters — one complete, two with deliberately missing mandatory clauses — and one Net
  Worth Certificate missing UDIN/membership number), sample drafting prompts collected.
  Tally MCP connection verified live against company "Techno Traders Ltd" (see
  `examples/outputs/sample_tally_pull.json` for a cached fallback pull).
  **Pending:** a valid `ANTHROPIC_API_KEY` — none of the strings supplied so far matched
  Anthropic's `sk-ant-...` key format, so `src/test_claude_api.py` has not been run
  successfully yet. Needed before Thursday's Agent 1 session.
