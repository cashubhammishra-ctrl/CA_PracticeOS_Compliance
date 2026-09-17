"""
Streamlit demo UI wiring all 3 agents + the Tally connector into one place.
Calls the agent classes directly in-process (no separate FastAPI server needed
for this demo UI, though src/main.py exposes the same functionality over HTTP
for the deployed backend).
"""
import csv
import io
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "connectors"))

from agents.compliance import CHECKLISTS, ComplianceAgent
from agents.drafting import DraftingAgent
from agents.onboarding import OnboardingAgent
from schema import CLIENT_MASTER_HEADERS, to_client_master_row
from tally_connector import TallyConnector

st.set_page_config(
    page_title="CA PracticeOS Compliance — AI Agent Layer",
    page_icon="⚖️",
    layout="wide",
)

# ---- Branding: match the L1 app's navy/gold identity ----------------------
st.markdown(
    """
    <style>
    :root {
        --navy: #0b1f3a; --blue: #123f73; --gold: #c9a227; --gold2: #e8d08a;
        --green: #16845b; --red: #c62828; --orange: #b76e00;
    }
    .block-container { padding-top: 1.5rem; max-width: 1100px; }
    .hero {
        background: linear-gradient(120deg, var(--navy), var(--blue));
        color: #fff; padding: 26px 32px; border-radius: 14px;
        margin-bottom: 22px; box-shadow: 0 4px 18px rgba(11,31,58,.18);
    }
    .hero h1 { margin: 0; font-size: 26px; font-weight: 800; }
    .hero .gold { color: var(--gold2); }
    .hero p { margin: 8px 0 0; color: #cfdcec; font-size: 14px; }
    .headline-chip {
        display: inline-block; margin-top: 10px; padding: 5px 12px;
        border-radius: 999px; background: rgba(232,208,138,.18);
        border: 1px solid var(--gold2); color: var(--gold2);
        font-size: 12px; font-weight: 700; letter-spacing: .3px;
    }
    div[data-testid="stTabs"] button[role="tab"] {
        font-weight: 700; font-size: 14.5px; padding: 10px 16px;
    }
    div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        color: var(--blue); border-bottom-color: var(--gold) !important;
    }
    .card {
        background: #fff; border: 1px solid #d9e2ec; border-radius: 12px;
        padding: 18px 20px; box-shadow: 0 2px 8px rgba(16,24,40,.04);
        margin-bottom: 14px;
    }
    .badge {
        display: inline-block; padding: 5px 14px; border-radius: 999px;
        font-weight: 800; font-size: 14px; letter-spacing: .2px;
    }
    .badge.green { background: #e7f6ef; color: var(--green); }
    .badge.red { background: #fdecec; color: var(--red); }
    .badge.blue { background: #e9f1fb; color: var(--blue); }
    .source-tag {
        display: inline-block; padding: 3px 10px; border-radius: 999px;
        font-size: 12px; font-weight: 700; background: #eef4fb; color: var(--blue);
    }
    .clause-row {
        border-bottom: 1px solid #edf1f5; padding: 10px 2px; font-size: 14px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <h1>CA PracticeOS <span class="gold">Compliance</span> — AI Agent Layer</h1>
      <p>AICA Level 2 capstone · onboarding, drafting and compliance agents wired
      together, plus a Tally connector — built on top of the CA PracticeOS
      Compliance L1 document engine.</p>
      <span class="headline-chip">★ Agent 3 (Compliance) is the headline feature</span>
    </div>
    """,
    unsafe_allow_html=True,
)


def status_badge(overall: str) -> str:
    if overall == "PASS":
        return '<span class="badge green">✅ PASS</span>'
    return '<span class="badge red">❌ FAIL</span>'


@st.cache_resource
def get_onboarding_agent():
    return OnboardingAgent()


@st.cache_resource
def get_compliance_agent():
    return ComplianceAgent()


@st.cache_resource
def get_drafting_agent():
    return DraftingAgent()


@st.cache_resource
def get_tally_connector():
    connector = TallyConnector()
    connector.authenticate({"company": "Techno Traders Ltd"})
    return connector


tab1, tab2, tab3, tab4 = st.tabs([
    "🧾  Agent 1 · Onboarding",
    "✅  Agent 3 · Compliance",
    "🔗  Agent 2 → 3 · Drafting + Compliance",
    "📊  Tally Connector",
])

# ---- Agent 1: Onboarding ---------------------------------------------------
with tab1:
    st.subheader("Client Onboarding")
    st.caption("Photo or PDF of a PAN card / GST certificate → a validated Client Master row.")

    with st.container(border=True):
        uploaded = st.file_uploader("Upload a PAN card or GST certificate", type=["png", "jpg", "jpeg", "pdf"])
        run = st.button("Extract client details", type="primary", key="extract_btn", disabled=not uploaded)

    if uploaded and run:
        suffix = Path(uploaded.name).suffix
        tmp_path = Path(f"_tmp_upload{suffix}")
        tmp_path.write_bytes(uploaded.getvalue())
        try:
            with st.spinner("Running Agent 1 (perceive → reason → act → validate)..."):
                result = get_onboarding_agent().run(str(tmp_path))
        finally:
            tmp_path.unlink(missing_ok=True)

        row = result["row"]
        with st.container(border=True):
            cols = st.columns(3)
            cols[0].metric("Client", row["name"] or "—")
            cols[1].metric("Entity Type", row["entity"] or "—")
            cols[2].metric("State", row["state"] or "—")
            cols = st.columns(3)
            cols[0].metric("PAN", row["pan"] or "—")
            cols[1].metric("GSTIN", row["gstin"] or "—")
            cols[2].metric("SEZ", "Yes" if row["sez"] else "No")

            if result["valid"]:
                st.success("✅ Validated against the Client Master schema — ready to import.")
            else:
                st.warning(f"Validation issues: {result['issues']}")

        with st.expander("Raw extraction JSON"):
            st.json(result)

        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(CLIENT_MASTER_HEADERS)
        writer.writerow(to_client_master_row(row))
        st.download_button(
            "⬇ Download Client Master CSV row",
            buf.getvalue(),
            file_name="client_master_row.csv",
            mime="text/csv",
        )

# ---- Agent 3: Compliance ---------------------------------------------------
with tab2:
    st.subheader("Compliance Checklist")
    st.caption("The product's headline feature — checks a drafted document against its mandatory-clause checklist.")

    with st.container(border=True):
        doc_type = st.selectbox("Document type", ["Auto-detect"] + list(CHECKLISTS.keys()))
        draft_text = st.text_area("Paste the drafted document text", height=260, placeholder="Paste an engagement letter, certificate, or other drafted document here...")
        run_check = st.button("Run compliance check", type="primary", key="check_btn")

    if run_check and draft_text.strip():
        with st.spinner("Running Agent 3 (perceive → reason → self-check → act)..."):
            result = get_compliance_agent().run(
                draft_text, None if doc_type == "Auto-detect" else doc_type
            )
        with st.container(border=True):
            st.markdown(f"{status_badge(result['overall'])} &nbsp; **{result['document_type']}**", unsafe_allow_html=True)
            if result["missing"]:
                st.error(f"Missing clauses: {', '.join(result['missing'])}")
            if result["needs_review"]:
                st.warning(f"Needs human review: {', '.join(result['needs_review'])}")
            if not result["missing"] and not result["needs_review"]:
                st.success("All mandatory clauses present.")

            st.markdown("**Clause-by-clause breakdown**")
            for item in result["items"]:
                icon = {"present": "✅", "absent": "❌", "needs_review": "⚠️"}[item["status"]]
                with st.expander(f"{icon}  {item['name']}"):
                    st.write(f"**Reason:** {item['reason']}")
                    if item["evidence"]:
                        st.write(f"**Evidence:** _{item['evidence']}_")

# ---- Agent 2 -> Agent 3 pipeline -------------------------------------------
with tab3:
    st.subheader("Drafting → Compliance")
    st.caption("One plain-English instruction becomes a draft, which is immediately compliance-checked — no manual step in between.")

    with st.container(border=True):
        instruction = st.text_input(
            "Describe the document in one line",
            value="Prepare an engagement letter for ABC Pvt Ltd for tax audit AY 2025-26, fees Rs 50,000",
        )
        run_pipeline = st.button("Draft and check", type="primary", key="pipeline_btn")

    if run_pipeline and instruction.strip():
        with st.spinner("Agent 2 drafting..."):
            draft = get_drafting_agent().run(instruction)

        with st.container(border=True):
            st.markdown(f'<span class="source-tag">Agent 2</span> &nbsp; **{draft["doc_type"]}** for **{draft["client_name"]}**', unsafe_allow_html=True)
            st.text_area("Drafted document", draft["draft_text"], height=220)

        with st.spinner("Feeding the draft straight into Agent 3..."):
            compliance = get_compliance_agent().run(draft["draft_text"], draft["doc_type"])

        with st.container(border=True):
            st.markdown(f'<span class="source-tag">Agent 3</span> &nbsp; {status_badge(compliance["overall"])}', unsafe_allow_html=True)
            if compliance["missing"]:
                st.error(f"Missing clauses: {', '.join(compliance['missing'])}")
            if compliance["needs_review"]:
                st.warning(f"Needs human review: {', '.join(compliance['needs_review'])}")
            if not compliance["missing"] and not compliance["needs_review"]:
                st.success("All mandatory clauses present.")

# ---- Tally connector --------------------------------------------------------
with tab4:
    st.subheader("Tally Connector")
    st.caption(
        "Live when TALLY_MCP_COMMAND is configured and this app runs on the same "
        "machine as Tally Prime; otherwise falls back to a cached real data pull "
        "(see connectors/connector_setup.md for why)."
    )
    connector = get_tally_connector()

    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.markdown("**Companies**")
            if st.button("Fetch clients (companies)"):
                clients = connector.fetch_clients()
                source = clients[0]["source"] if clients else "n/a"
                st.markdown(f'<span class="source-tag">source: {source}</span>', unsafe_allow_html=True)
                st.json(clients)
    with col2:
        with st.container(border=True):
            st.markdown("**Receivables — Techno Traders Ltd**")
            if st.button("Fetch receivable invoices"):
                invoices = connector.fetch_invoices("Techno Traders Ltd")
                source = invoices[0]["source"] if invoices else "n/a"
                st.markdown(f'<span class="source-tag">source: {source}</span>', unsafe_allow_html=True)
                st.dataframe(invoices, use_container_width=True)
