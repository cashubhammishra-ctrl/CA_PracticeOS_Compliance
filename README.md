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

Run the backend:

```bash
cd src
uvicorn main:app --reload --port 8010
```

Try Agent 1 (Onboarding) from the CLI against a sample document:

```bash
python src/agents/onboarding.py examples/inputs/sample_pan_individual_01.png
```

Or batch-run it against every sample onboarding document:

```bash
python src/run_agent1_on_samples.py
```

## Status (updated each session)

- **Wed 16 Sep** — Repo initialized, virtualenv + `src/requirements.txt` installed, 8 sample
  documents collected in `examples/inputs/` (4 mock PAN/GST images, 3 sample engagement
  letters — one complete, two with deliberately missing mandatory clauses — and one Net
  Worth Certificate missing UDIN/membership number), sample drafting prompts collected.
  Tally MCP connection verified live against company "Techno Traders Ltd" (see
  `examples/outputs/sample_tally_pull.json` for a cached fallback pull).
  `ANTHROPIC_API_KEY` set in `.env` and `src/test_claude_api.py` runs successfully
  ("API connection OK"). Setup complete.

- **Thu 17 Sep** — FastAPI backend running (`src/main.py`: `/health`,
  `/api/onboarding/extract`, `/api/onboarding/extract-csv`). Agent 1 (Onboarding)
  built (`src/agents/onboarding.py`) as a perceive → reason → act → validate loop:
  perceives images directly, extracts text from text-layer PDFs via `pdfplumber`,
  and rasterizes scanned/photographed PDFs (via pdfplumber's pdfium backend) for a
  vision call when there's no real text layer. Output is normalized and validated
  against the exact Client Master schema from `CA_PracticeOS_Compliance.html`
  (`src/schema.py`: PAN/GSTIN regex checks, PAN-in-GSTIN cross-check, entity-type
  whitelist, state inferred from GSTIN code). Tested against all 6 sample
  PAN/GST fixtures (4 images + text-layer PDF + scanned PDF) — all extract
  correctly and pass validation; results saved in `examples/outputs/agent1/`.
  CSV export endpoint confirmed byte-for-byte compatible with the L1 app's
  "Upload Client Master" template headers. Prompt documented in
  `prompts/onboarding_agent.md`.
