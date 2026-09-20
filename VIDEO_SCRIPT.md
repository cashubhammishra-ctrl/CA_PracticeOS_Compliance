# Video script / talking points — CA PracticeOS Compliance

Target length: 5–6 minutes, face + screen. Record the morning of submission day,
not the night before. This is talking points to speak from, not a
word-for-word script — sound natural.

**Everything in this demo happens inside ONE app** — `CA_PracticeOS_Compliance.html`,
publicly hosted, installable as a PWA, with its own login/signup and the AI
agent layer built directly in (not a separate Streamlit tool). That
consolidation is itself worth saying out loud once, briefly, in the close.

**Framing rule (do not skip): open by calling this a compliance product and
lead the whole demo with Agent 3.** Agent 1, Agent 2, and the Tally connector
are supporting pieces, in that order of importance. If time runs short, cut
detail from Agent 2 or the connector first — never shorten the Agent 3
segment.

**Live link for the demo:**
`https://cashubhammishra-ctrl.github.io/CA_PracticeOS_Compliance/CA_PracticeOS_Compliance.html`

---

## 0. Cold open (face, ~20s)

> "This is CA PracticeOS Compliance — and I want to be upfront about what it
> is: it's a compliance product. Last term I built the document engine — the
> part of a CA firm's workflow that drafts engagement letters, certificates,
> fee notes. What I've built this term is the part that actually checks that
> work — an AI agent that reads a drafted document and tells you, clause by
> clause, whether it's compliant before it goes out the door. That's the
> headline feature. Everything else in this demo — including a full
> multi-firm login system and a working Tally connector — supports it."

## 1. The app itself, briefly (screen, ~25s)

- Open the live public link (not localhost — say so). Show the login screen.
- Say: "This isn't running on my laptop for this demo — it's a real,
  publicly hosted web app anyone can open, and it installs as an app on
  desktop or mobile through the browser's own Install prompt. It also has
  real authentication: a firm signs up, I get an email approval request, and
  once I approve them they can log in and start working — with their own
  isolated data, separate from every other firm using the app."
- Log in on camera (use a pre-approved test account so you're not waiting on
  email mid-recording).

## 2. Agent 3 — Compliance (screen, ~90s) — LEAD WITH THIS

- From the sidebar, open **🤖 AI Agents** → scroll to **Agent 3 — Compliance
  Checklist**.
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

## 3. Agent 1 — Onboarding (screen, ~50s)

- Same **AI Agents** page, scroll to **Agent 1 — Onboarding**.
- Upload one of the sample PAN or GST certificate images.
- Show the extracted JSON: name, entity type, PAN, GSTIN, address, state —
  and point out it validated PAN/GSTIN format and cross-checked that the
  GSTIN embeds the same PAN.
- Click through to add it as a real client — show it land straight in
  **Client Master**, no manual retyping, no separate app to switch to.

## 4. Agent 2 — Drafting (screen, ~35s)

- Scroll to **Agent 2 — Drafting**.
- Type a one-line instruction (a different one from the Agent 3 demo, e.g.
  the Net Worth Certificate prompt).
- Show the filled draft appear, then point out the compliance result under
  it. Say: "One line of plain English becomes a structured draft, and it's
  immediately checked — you can see where it's genuinely incomplete, like a
  fee note where the GST hasn't been computed yet, because that number
  legitimately isn't known from a one-liner. The agent is honest about what
  it doesn't know."

## 5. Tally connector (screen, ~30s)

- Open **📊 Tally Connector** in the sidebar.
- Say: "This connects directly to Tally Prime's own XML/HTTP gateway,
  browser to desktop — no separate backend hop for this part. Tally only
  runs on a local machine, so in this cloud demo you're seeing [a live pull
  against my own running Tally instance / a cached sample response — pick
  whichever is true on the day], and that's disclosed honestly rather than
  hidden." Show a real fetch — clients, ledgers, or receivables.
- One sentence on roadmap: "Zoho Books and SAP would plug into the same kind
  of connector — that's designed for, not built, in this timeline."

## 6. Team & multi-tenancy — the SaaS layer (screen, ~30s)

- Open **👥 Team Members**.
- Say: "Because this is meant to be used commercially, not just
  demonstrated, I built proper multi-firm support: an admin approves new
  firms by email, and each firm's admin can then add their own preparers,
  reviewers, and approvers — role-based, and completely isolated from every
  other firm's data on the same app." Add one team member live if time
  allows.

## 7. Close (face, ~20s)

> "So: a real compliance-checking agent as the headline feature, an
> onboarding agent, a drafting agent, a live Tally connector, and all of it
> sitting inside one publicly hosted, installable, multi-firm application —
> not a prototype running on my laptop. Built on top of last term's document
> engine, and honest everywhere it has a limitation instead of faking it.
> That's CA PracticeOS Compliance."

---

## B-roll / cutaway shots to have ready

- `examples/outputs/agent3/` JSON files, for a quick zoom-in on the evidence
  quotes if there's time.
- The PWA "Install app" prompt in the browser address bar — a 3-second shot
  is enough, don't dwell on it.
- The admin-approval email arriving, if you can time a real signup to land
  during recording (optional — don't gamble the whole take on this).

## Things to say explicitly (the video brief calls these out)

- "compliance product" — in the first 20 seconds.
- "extracts → validates → then acts" — during the Agent 3 segment, narrating
  the agentic loop out loud.
- Name the honest limitation on Tally before anyone can call it out as a bug.
- "publicly hosted" / "not running on my laptop" — once, early, while
  showing the live link.

## Practical recording notes

- **Use a pre-approved test login** so you're not waiting on a real email
  mid-take. Have its password ready to type without looking it up on camera.
- **Pre-load the sample documents** (`examples/inputs/`) in a scratch text
  file so you can paste, not type, during the Agent 3 segment — typing a
  full engagement letter on camera burns your time budget.
- If GitHub Pages or Render is slow to respond because of a cold start,
  **open the live link 2–3 minutes before you start recording** so the free
  backend has already spun up.
- Keep this under 6 minutes. If you're running long, cut Team Members (§6)
  entirely before cutting anything from Agent 3.
