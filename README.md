# CA PracticeOS Compliance — AI Agent Layer

AICA Level 2 capstone. See [CLAUDE.md](CLAUDE.md) for the full build plan, session schedule, and priority rules.

**Submission docs:** [project_summary.pdf](project_summary.pdf) (problem, architecture,
L1→L2 evolution, proof points, learnings) · [VIDEO_SCRIPT.md](VIDEO_SCRIPT.md) (the
condensed 5–6 min submission-cut talking points) ·
[FULL_APP_WALKTHROUGH_SCRIPT.md](FULL_APP_WALKTHROUGH_SCRIPT.md) (comprehensive
section-by-section script covering the entire L1 platform + L2 agent layer, for a
longer demo or to decide what to cut into the short version) · `prompts/*.md` (all 3
agent prompts, documented) · [connectors/connector_setup.md](connectors/connector_setup.md)
(Tally MCP setup and its local-only limitation).

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

Try Agent 2 (Drafting) from the CLI against a one-line instruction:

```bash
python src/agents/drafting.py "Prepare an engagement letter for ABC Pvt Ltd for tax audit AY 2025-26, fees Rs 50,000"
```

Or run the full Agent 2 → Agent 3 pipeline (drafts a document, then immediately
compliance-checks its own output) against 4 sample prompts:

```bash
python src/run_agent2_then_agent3.py
```

Try the Tally connector (falls back to cached sample data unless
`TALLY_MCP_COMMAND` is configured — see `connectors/connector_setup.md`):

```bash
python connectors/tally_connector.py
```

Run the Streamlit demo UI (wires all 3 agents + the Tally connector together):

```bash
streamlit run src/streamlit_app.py
```

## Deploying (Render)

The FastAPI backend and the Streamlit demo both deploy from this one repo via
`render.yaml`. Tally stays in cached-fallback mode on the cloud deployment —
see `connectors/connector_setup.md` for why that's the correct behavior, not
a bug.

1. Create a GitHub repo (can be empty) and push this project to it:
   ```bash
   git remote add origin <your-github-repo-url>
   git push -u origin master
   ```
2. Create a free account at [render.com](https://render.com) and connect your
   GitHub account.
3. In the Render dashboard: **New +** → **Blueprint**, select this repo.
   Render reads `render.yaml` automatically and proposes two services:
   `ca-practiceos-backend` (FastAPI) and `ca-practiceos-streamlit` (demo UI).
4. When prompted, set the `ANTHROPIC_API_KEY` environment variable on **both**
   services to your real key (never commit it — `render.yaml` intentionally
   leaves it as `sync: false` so Render asks for it instead of reading `.env`).
5. Deploy. Once live, put both URLs in `deployment_link.txt`.

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

- **Sat 19 Sep** — **Agent 2 (Drafting) built, and connected to Agent 3 end to
  end.** `src/agents/drafting.py` turns one plain-English instruction into a
  filled draft as a perceive → reason → act loop: one Claude call extracts
  `doc_type`, `client_name`, and a flexible `fields` dict, then a template
  renderer for that document type (all 6 types, mirroring the L1 app's own
  `generate*()` section structure and firm defaults `NSSJ & Co.` / `CA Shubham
  Mishra`) fills in the draft. Deliberately does **not** add a Limitations
  clause to the Engagement Letter template that the L1 app's own generator
  doesn't have — see `prompts/drafting_agent.md` for why.

  **Pipeline proven end to end** (`src/run_agent2_then_agent3.py` and the new
  `/api/drafting/generate-and-check` endpoint): Agent 2's draft feeds straight
  into Agent 3 with no manual step in between. Ran against 4 sample
  instructions — every one produced a real, non-contrived finding: the
  engagement letter drafted from "tax audit AY 2025-26, fees Rs 50,000" fails
  on the missing Limitations clause (a genuine gap in the firm's own standard
  template, not a synthetic test case); the net worth certificate and fee note
  correctly fail because their one-liners didn't supply asset/liability
  figures or a GST-computed total, so the template's placeholder fields are
  correctly caught as incomplete.

  Two bugs fixed along the way: `format_inr()` couldn't parse fee strings like
  "Rs 50,000" or "Rs 15,000 plus GST" (only handled bare numbers), silently
  rendering fees as blank — fixed by stripping all non-numeric characters
  before parsing. Also refined Agent 3's self-check heuristic to be
  asymmetric: it now only downgrades an LLM's "present" verdict to
  `needs_review` (catching over-claiming), and no longer second-guesses an
  "absent" verdict, because a blank Net Worth Certificate template still
  contains the words "Assets"/"Liabilities" in its column headers, so a
  symmetric keyword check was flagging every blank template as merely
  "uncertain" instead of cleanly failing it. Prompt documented in
  `prompts/drafting_agent.md`.

- **Sun 20 Sep** — **Tally connector built, all 3 agents + connector wired into
  one Streamlit UI, Agent 1's CSV import proven live in the L1 app, and full
  deployment config prepared.**

  - **Researched the real ICAI Tally Prime MCP Server** (not guessed): it's a
    local Node.js process, distributed as a zip from ai.icai.org, that talks
    to Tally Prime over its own XML gateway on port 9000 and is launched by
    the MCP client as a local subprocess over stdio. This means **a
    cloud-deployed backend genuinely cannot reach a user's local Tally
    instance** — a real infrastructure constraint, not a gap in the code.
  - `connectors/base_connector.py` — the exact `BaseConnector` ABC from
    CLAUDE.md Section 2A. `connectors/tally_connector.py` implements it with a
    real MCP stdio client (using the official `mcp` Python SDK) for local use,
    falling back honestly to a cached real data pull
    (`examples/outputs/sample_tally_pull.json`, refreshed today with live
    ledger, voucher, and receivables data pulled from a working Tally MCP
    connection) whenever the live path isn't reachable — every result is
    tagged `"source": "live"` or `"source": "cached_fallback"`, nothing is
    silently faked. Full setup/limitation writeup in
    `connectors/connector_setup.md`. Zoho/SAP remain unbuilt, as scoped.
  - `src/streamlit_app.py` — one UI with tabs for all 3 agents plus the Tally
    connector, including a live Agent 2 → Agent 3 tab. Verified working in a
    real browser session (not just import-checked): every tab exercised live,
    including the Drafting → Compliance tab reproducing Saturday's Limitations
    finding and the Tally tab correctly reporting `cached_fallback`.
  - **Agent 1's CSV import tested live against the actual L1 app**
    (`CA_PracticeOS_Compliance.html`, served locally and driven in a real
    browser): generated a fresh CSV from a sample GST certificate, imported it
    through the app's real "Upload / Update Client Master" flow (dispatched a
    real `File` via the actual file input, not simulated), and confirmed
    "RIVERSTONE TRADERS PRIVATE LIMITED" appeared correctly in the Client
    Master table with the right entity type, PAN, and GSTIN — the L1 → L2
    bridge this capstone is built around now has an end-to-end proof, not
    just a schema-matching claim.
  - **Deployment prepared, not yet live**: `render.yaml` (Blueprint for both
    the FastAPI backend and the Streamlit demo, `ANTHROPIC_API_KEY` deliberately
    left as `sync: false` rather than committed) plus step-by-step GitHub +
    Render setup instructions added to this README. Actually creating the
    GitHub repo and Render account needs the user's own login, so that's
    queued for a near-term session once those are set up — `deployment_link.txt`
    is scaffolded and ready to fill in.

- **Mon 21 Sep** — **Full regression test + extra scrutiny on Agent 3, no
  regressions found, one documentation correction.** Since live deployment is
  still pending GitHub/Render account setup, "fresh browser/incognito" was
  treated as a full clean-state pass: cleared all `__pycache__`, re-ran every
  batch script (Agent 1 on all 6 onboarding fixtures, Agent 3 on all 4 drafted
  fixtures, the Agent 2 → Agent 3 pipeline on all 4 prompts) and every FastAPI
  endpoint (all 8) from a fresh server process — identical results to prior
  sessions across the board, no drift.

  **Extra scrutiny on Agent 3** (the protected headline feature), targeting
  paths never exercised before:
  - Drafted a **General Certificate** and a **Working Paper** via Agent 2 (the
    two document types Agent 3 supported but had never actually been tested
    against) and ran Agent 3 on both. The Working Paper failed on all 5
    clauses — correctly: its "Objective" and "Evidence / Exceptions" sections
    contain only generic instructional boilerplate ("Document the work
    performed...", "Supporting documents should be listed here...") rather
    than this engagement's actual content, and Agent 3 correctly refused to
    count boilerplate as substance. No bug — this is the strict behavior
    working as intended, and a stronger differentiator than simple
    keyword-presence checking.
  - Fed a **raw HTML draft** (matching the shape Agent 2/the L1 app would
    produce, with `<div class="doc">` wrappers and `<h2>` headings) directly
    into Agent 3 — `strip_html()` handled it correctly and classification and
    clause-checking both worked unaffected by the markup.
  - Fed a **completely untitled document** with no document-type marker to
    exercise the LLM classification fallback path (previously never directly
    verified) — correctly classified as a Working Paper based on content
    alone.
  - Tested a **deliberately vague fee clause** ("fees to be mutually agreed...
    prior to commencement," no amount, rate, or basis stated) against the
    Engagement Letter checklist. The model marked it **absent**, reasoning
    that deferring the fee without stating any basis doesn't satisfy what an
    engagement letter needs to state. This is stricter than an example in
    `prompts/compliance_agent.md` that suggested a vague fee mention should
    still count as present — on reflection that example was too lenient (SA
    210 expects the fee basis to actually be stated), so the doc was corrected
    to match the stricter, more correct behavior rather than "fixing" the
    code to match an outdated example.

- **Tue 22 Sep** — **Docs + video prep.** Deployment (GitHub repo + Render
  account) is still deferred to a later session at the user's choice, so
  today focused entirely on the written deliverables:
  - `project_summary.pdf` — 2-page written summary (problem, the 3
    agents + connector, architecture table, L1→L2 evolution, the same three
    proof points from this log, learnings, and an honest roadmap section for
    Zoho/SAP and the pending deployment). Generated with `reportlab`.
  - `VIDEO_SCRIPT.md` — talking points for the 5–6 minute face+screen video,
    structured to open by naming this a compliance product and lead the demo
    with Agent 3 (per CLAUDE.md's explicit framing requirement), with Agent 1,
    Agent 2, and the Tally connector as supporting segments in that priority
    order, plus the exact phrases the video brief calls out to say out loud
    ("compliance product," "extracts → validates → then acts").
  - Confirmed all 3 prompt files (`prompts/*.md`) and
    `connectors/connector_setup.md` are already complete and current from
    prior sessions — no changes needed there.
  - This README now links the submission docs at the top for discoverability.

- **Wed 17 Sep (deployment)** — **Live deployment complete and verified.**
  GitHub repo created and pushed (`cashubhammishra-ctrl/CA_PracticeOS_Compliance`).
  Render Blueprint deployed both services from `render.yaml`:
  `ca-practiceos-backend` (FastAPI) and `ca-practiceos-streamlit` (demo UI),
  both live — see `deployment_link.txt`.
  - Verified the **live** backend directly (not just locally): `/health`,
    `/api/compliance/document-types`, the full `/api/drafting/generate-and-check`
    Agent 2 → Agent 3 pipeline (reproduced the same Limitations finding as every
    local run), and `/api/onboarding/extract` (vision extraction on a real GST
    certificate image) — all correct, confirming `ANTHROPIC_API_KEY` is
    configured correctly on Render.
  - **Redesigned the Streamlit UI** after feedback that the default look
    wasn't presentable for the video: added a `.streamlit/config.toml` theme
    and branded navy/gold styling matching the L1 app (hero banner, card
    layout, colored PASS/FAIL badges, metric tiles for extracted client
    data, tab icons) instead of bare default Streamlit widgets. Verified
    live on the actual Render deployment, not just locally — including a
    full compliance check run showing the new badge/card styling working
    correctly in production.
  - Git push required Git Credential Manager login done by the user directly
    in their own terminal (this sandboxed tool can't complete an interactive
    OAuth prompt); after that one-time login, subsequent pushes from this
    session worked non-interactively using the cached credential.
  - **Streamlit UI redesigned a second time** after seeing the actual L1 app's
    dashboard: replaced the top-tab layout with a dark navy **sidebar nav**
    matching L1's pattern exactly (brand block, gold active-item highlight,
    icon-prefixed nav buttons), added a **Dashboard landing view** with KPI
    cards and "Quick jump" buttons mirroring L1's Dashboard/Quick Create
    layout. Verified live on Render.
  - **L1 app enhancement (out of L2 capstone scope, done at user's request):**
    added a **Securities / ISIN Master** to `CA_PracticeOS_Compliance.html` —
    a new sidebar section for bulk-uploading share/mutual-fund/bond holdings
    (Client PAN, Security Name, ISIN, Type, Quantity, Current Value), matched
    to an existing Client Master record by PAN then name, following the exact
    same upload/preview/commit pattern as the existing Client Master import
    (`mapSecurityImportRow`, `showSecurityImportPreview`,
    `commitPendingSecurityImport`, `renderSecurities`). Added a
    "Load from Securities / ISIN Master" button inside the Net Worth
    Certificate generator that pulls a client's holdings straight into the
    Assets table. Tested end to end in a live browser session: imported a
    client, uploaded a securities CSV, confirmed correct PAN-matching and
    Indian-currency formatting in the preview, committed the import, and
    confirmed `calcNW()` correctly summed the pulled-in holdings. Zero console
    errors throughout.
