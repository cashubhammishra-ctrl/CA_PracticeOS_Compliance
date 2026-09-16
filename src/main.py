"""
FastAPI backend for the CA PracticeOS Compliance AI Agent Layer.
Wed 16 Sep: setup. Thu 17 Sep: this file + Agent 1 (Onboarding) endpoints.
"""
import csv
import io
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from agents.onboarding import OnboardingAgent
from schema import CLIENT_MASTER_HEADERS, to_client_master_row

app = FastAPI(title="CA PracticeOS Compliance - AI Agent Layer")

_onboarding_agent: OnboardingAgent | None = None


def get_onboarding_agent() -> OnboardingAgent:
    global _onboarding_agent
    if _onboarding_agent is None:
        _onboarding_agent = OnboardingAgent()
    return _onboarding_agent


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/onboarding/extract")
async def extract_client(file: UploadFile = File(...)):
    """Agent 1: photo/PDF of a PAN card or GST certificate -> Client Master row (JSON)."""
    suffix = Path(file.filename or "upload").suffix
    if suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".pdf"}:
        raise HTTPException(400, f"Unsupported file type: {suffix}")

    data = await file.read()
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name

    try:
        agent = get_onboarding_agent()
        result = agent.run(tmp_path)
        result["source_file"] = file.filename
        return result
    except Exception as exc:
        raise HTTPException(500, f"Extraction failed: {exc}") from exc
    finally:
        Path(tmp_path).unlink(missing_ok=True)


@app.post("/api/onboarding/extract-csv")
async def extract_client_csv(file: UploadFile = File(...)):
    """Same as /extract, but returns a one-row CSV matching the L1 app's
    Client Master import template, ready to feed straight into its
    'Upload / Update Client Master' feature."""
    suffix = Path(file.filename or "upload").suffix
    if suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".pdf"}:
        raise HTTPException(400, f"Unsupported file type: {suffix}")

    data = await file.read()
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name

    try:
        agent = get_onboarding_agent()
        result = agent.run(tmp_path)
    except Exception as exc:
        raise HTTPException(500, f"Extraction failed: {exc}") from exc
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(CLIENT_MASTER_HEADERS)
    writer.writerow(to_client_master_row(result["row"]))
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=client_master_row.csv"},
    )
