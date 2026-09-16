# Video script / talking points — CA PracticeOS Compliance AI Agent Layer

Target length: 5–6 minutes, face + screen. Record Wednesday morning (23 Sep),
not the night before. This is talking points to speak from, not a word-for-word
script — sound natural.

**Framing rule (do not skip): open by calling this a compliance product and
lead the whole demo with Agent 3.** Agent 1, Agent 2, and the Tally connector
are supporting pieces, in that order of importance. If time runs short, cut
detail from Agent 2 or the connector first — never shorten the Agent 3 segment.

---

## 0. Cold open (face, ~20s)

> "This is CA PracticeOS Compliance — and I want to be upfront about what it
> is: it's a compliance product. Last term I built the document engine — the
> part of a CA firm's workflow that drafts engagement letters, certificates,
> fee notes. What I've built this term is the part that actually checks that
> work — an AI agent that reads a drafted document and tells you, clause by
> clause, whether it's compliant before it goes out the door. That's the
> headline feature. Everything else in this demo supports it."

## 1. Agent 3 — Compliance (screen, ~90s) — LEAD WITH THIS

- Open the Streamlit "Agent 3 · Compliance" tab (or the Drafting → Compliance
  tab — pick whichever demos better live).
- Paste the **complete engagement letter** sample → run the check → show the
  clean PASS with all 5 clauses evidenced.
- Then paste the **engagement letter missing fees/limitations** sample → run
  it again → show the FAIL with the exact two missing clauses called out.
- **Say out loud, explicitly**: "Notice the agent isn't just doing one LLM
  call and printing the answer. It perceives the document, reasons about each
  mandatory clause with evidence, then runs a second, independent self-check
  pass on its own verdicts before deciding — extract, validate, then act.
  That's what makes this agentic, not a chatbot wrapper."
- **The strongest beat, don't cut this**: run the Agent 2 → Agent 3 pipeline
  live on "Prepare an engagement letter for ABC Pvt Ltd for tax audit AY
  2025-26, fees Rs 50,000" and show it **fail on a missing Limitations
  clause**. Say: "This isn't a rigged test case — this is the firm's own
  engagement letter template from last term's build. The compliance agent
  just caught a real gap in paperwork the firm has been using. That's the
  whole pitch for why this product exists."

## 2. Agent 1 — Onboarding (screen, ~60s)

- Upload one of the sample PAN or GST certificate images.
- Show the extracted JSON: name, entity type, PAN, GSTIN, address, state —
  and point out it validated PAN/GSTIN format and cross-checked that the
  GSTIN embeds the same PAN.
- Download the CSV, then switch to the L1 app (`CA_PracticeOS_Compliance.html`)
  and actually import it through "Upload / Update Client Master" — show the
  client appear in the table. Say: "A photo goes in, a validated row in the
  firm's existing client database comes out — no manual retyping."

## 3. Agent 2 — Drafting (screen, ~45s)

- Type a one-line instruction into the Drafting tab (a different one from
  the Agent 3 demo, e.g. the Net Worth Certificate or fee note prompt).
- Show the filled draft appear, then point out the compliance result under
  it. Say: "One line of plain English becomes a structured draft, and it's
  immediately checked — you can see where it's genuinely incomplete, like
  this fee note where the GST hasn't been computed yet, because that number
  legitimately isn't known from a one-liner. The agent is honest about what
  it doesn't know."

## 4. Tally connector (screen, ~30s)

- Open the Tally Connector tab, fetch clients or receivable invoices.
- Say: "This connects via ICAI's Tally Prime MCP server — the exact module
  the course covers. Tally itself only runs locally, so in this cloud demo
  you're seeing a real cached pull from a live connection rather than a live
  call — that's a genuine constraint of Tally's architecture, not a shortcut
  I took. On a CA's own machine, this same code talks to Tally live." Show
  the `"source"` field in the JSON output as proof this is disclosed
  honestly, not hidden.
- One sentence on roadmap: "Zoho Books and SAP would plug into the same
  connector interface — that's designed for, not built, in this timeline."

## 5. Close (face, ~20s)

> "So: an onboarding agent, a drafting agent, and — the one that matters
> most — a compliance agent that actually validates the firm's own
> paperwork against real professional requirements. Built on top of last
> term's document engine, connected to Tally, and it's honest everywhere it
> has a limitation instead of faking it. That's CA PracticeOS Compliance."

---

## B-roll / cutaway shots to have ready

- `examples/outputs/agent3/` JSON files, for a quick zoom-in on the evidence
  quotes if there's time.
- The architecture diagram in `CLAUDE.md` Section 3, screenshotted, as a
  5-second establishing shot before the demo starts.

## Things to say explicitly (the video brief calls these out)

- "compliance product" — in the first 20 seconds.
- "extracts → validates → then acts" — during the Agent 3 segment, narrating
  the agentic loop out loud.
- Name the honest limitation on Tally before anyone can call it out as a bug.
