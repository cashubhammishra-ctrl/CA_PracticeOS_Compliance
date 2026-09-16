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

Try Agent 3 (Compliance) from the CLI against a sample drafted document:

```bash
python src/agents/compliance.py examples/inputs/sample_engagement_letter_complete.txt
```

Or batch-run it against all 4 sample drafts (see
`examples/inputs/compliance_test_expectations.md` for expected results):

```bash
python src/run_agent3_on_samples.py
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

- **Fri 18 Sep** — **Agent 3 (Compliance) built and working — protected-priority
  headline feature.** `src/agents/compliance.py` checks a drafted document's text
  against a mandatory-clause checklist for its document type (6 document types
  defined in `CHECKLISTS`, derived from the L1 app's own `generate*()` templates),
  as a perceive → reason → self-check → act loop:
  - **Perceive**: strips HTML if present, classifies document type by title-line
    match (falls back to an LLM classification call for anything unrecognized).
  - **Reason**: one Claude call checks every mandatory clause at once, returning
    present/absent + a quoted evidence snippet + reason per clause.
  - **Self-check**: a keyword heuristic cross-checks each verdict and downgrades it
    to `needs_review` if the LLM's present/absent call disagrees with what's
    actually in the text — a genuine second opinion, not just a JSON wrapper
    around one model call.
  - **Act**: compiles the overall PASS/FAIL verdict, the missing-clause list, and
    anything flagged for human review.

  Tested against all 4 sample drafted documents in `examples/inputs/` (see
  `compliance_test_expectations.md`): the complete engagement letter passes
  cleanly, and all three deliberately-broken drafts fail with exactly the
  clauses that were removed called out (fees + limitations; scope +
  responsibilities + limitations; UDIN + membership number) — zero false
  positives or false negatives. One tuning fix along the way: the "scope"
  clause's self-check keyword list included "engage", which false-triggered on
  every letter's boilerplate opening ("...appointing [firm] to provide
  professional services...") — narrowed to `scope`/`objective`/`deliverable`.
  Wired into FastAPI (`/api/compliance/check`, `/api/compliance/check-file`,
  `/api/compliance/document-types`) and verified live. Prompt documented in
  `prompts/compliance_agent.md`.
