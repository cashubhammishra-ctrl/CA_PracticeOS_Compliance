"""
Streamlit demo UI wiring all 3 agents + the Tally connector into one place.
Calls the agent classes directly in-process (no separate FastAPI server needed
for this demo UI, though src/main.py exposes the same functionality over HTTP
for the deployed backend).
"""
import csv
import io
import json
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

st.set_page_config(page_title="CA PracticeOS Compliance - AI Agent Layer", layout="wide")
st.title("CA PracticeOS Compliance — AI Agent Layer")
st.caption(
    "AICA Level 2 capstone demo. Agent 3 (Compliance) is the product's headline "
    "feature — see the Compliance and Drafting → Compliance tabs."
)


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
    "Agent 1 · Onboarding",
    "Agent 3 · Compliance",
    "Agent 2 → Agent 3 · Drafting + Compliance",
    "Tally Connector",
])

# ---- Agent 1: Onboarding ---------------------------------------------------
with tab1:
    st.subheader("Client Onboarding — photo/PDF of a PAN card or GST certificate")
    uploaded = st.file_uploader("Upload a PAN card or GST certificate", type=["png", "jpg", "jpeg", "pdf"])
    if uploaded and st.button("Extract client details", key="extract_btn"):
        suffix = Path(uploaded.name).suffix
        tmp_path = Path(f"_tmp_upload{suffix}")
        tmp_path.write_bytes(uploaded.getvalue())
        try:
            with st.spinner("Running Agent 1 (perceive → reason → act → validate)..."):
                result = get_onboarding_agent().run(str(tmp_path))
        finally:
            tmp_path.unlink(missing_ok=True)

        st.json(result)
        if result["valid"]:
            st.success("Validated against the Client Master schema — ready to import.")
        else:
            st.warning(f"Validation issues: {result['issues']}")

        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(CLIENT_MASTER_HEADERS)
        writer.writerow(to_client_master_row(result["row"]))
        st.download_button(
            "Download Client Master CSV row",
            buf.getvalue(),
            file_name="client_master_row.csv",
            mime="text/csv",
        )

# ---- Agent 3: Compliance ---------------------------------------------------
with tab2:
    st.subheader("Compliance Checklist — headline / protected-priority feature")
    doc_type = st.selectbox("Document type (leave as Auto-detect if unsure)", ["Auto-detect"] + list(CHECKLISTS.keys()))
    draft_text = st.text_area("Paste the drafted document text", height=300)
    if st.button("Run compliance check") and draft_text.strip():
        with st.spinner("Running Agent 3 (perceive → reason → self-check → act)..."):
            result = get_compliance_agent().run(
                draft_text, None if doc_type == "Auto-detect" else doc_type
            )
        badge = "✅ PASS" if result["overall"] == "PASS" else "❌ FAIL"
        st.markdown(f"### {badge} — {result['document_type']}")
        if result["missing"]:
            st.error(f"Missing clauses: {', '.join(result['missing'])}")
        if result["needs_review"]:
            st.warning(f"Needs human review: {', '.join(result['needs_review'])}")
        for item in result["items"]:
            icon = {"present": "✅", "absent": "❌", "needs_review": "⚠️"}[item["status"]]
            with st.expander(f"{icon} {item['name']}"):
                st.write(f"**Reason:** {item['reason']}")
                if item["evidence"]:
                    st.write(f"**Evidence:** _{item['evidence']}_")

# ---- Agent 2 -> Agent 3 pipeline -------------------------------------------
with tab3:
    st.subheader("Drafting → Compliance — the connected pipeline")
    instruction = st.text_input(
        "Describe the document in one line",
        value="Prepare an engagement letter for ABC Pvt Ltd for tax audit AY 2025-26, fees Rs 50,000",
    )
    if st.button("Draft and check") and instruction.strip():
        with st.spinner("Agent 2 drafting..."):
            draft = get_drafting_agent().run(instruction)
        st.markdown(f"**Agent 2 output:** {draft['doc_type']} for {draft['client_name']}")
        st.text_area("Drafted document", draft["draft_text"], height=250)

        with st.spinner("Feeding the draft straight into Agent 3..."):
            compliance = get_compliance_agent().run(draft["draft_text"], draft["doc_type"])
        badge = "✅ PASS" if compliance["overall"] == "PASS" else "❌ FAIL"
        st.markdown(f"### Agent 3 result: {badge}")
        if compliance["missing"]:
            st.error(f"Missing clauses: {', '.join(compliance['missing'])}")
        if compliance["needs_review"]:
            st.warning(f"Needs human review: {', '.join(compliance['needs_review'])}")

# ---- Tally connector --------------------------------------------------------
with tab4:
    st.subheader("Tally Connector")
    st.caption(
        "Live when TALLY_MCP_COMMAND is configured and this app runs on the same "
        "machine as Tally Prime; otherwise falls back to a cached real data pull "
        "(see connectors/connector_setup.md for why)."
    )
    connector = get_tally_connector()
    if st.button("Fetch clients (companies)"):
        clients = connector.fetch_clients()
        source = clients[0]["source"] if clients else "n/a"
        st.info(f"Data source: **{source}**")
        st.json(clients)
    if st.button("Fetch receivable invoices for Techno Traders Ltd"):
        invoices = connector.fetch_invoices("Techno Traders Ltd")
        source = invoices[0]["source"] if invoices else "n/a"
        st.info(f"Data source: **{source}**")
        st.dataframe(invoices)
