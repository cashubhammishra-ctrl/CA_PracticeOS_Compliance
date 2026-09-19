"""
Signup (admin-approval-gated), login, session check, and team-member
management endpoints. Mounted into main.py under /api/auth and /api/team.
"""
from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

import auth
from db import get_db
from models import Client, Tenant, User

router = APIRouter()


# ---- request/response schemas ------------------------------------------
class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    firm_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AddTeamMemberRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str  # Preparer / Reviewer / Approver / Admin


# ---- auth dependency ------------------------------------------------------
def current_user(authorization: str = Header(default=""), db: Session = Depends(get_db)) -> User:
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing or invalid Authorization header")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = auth.decode_session_token(token)
    except Exception:
        raise HTTPException(401, "Invalid or expired session")
    user = db.get(User, payload["user_id"])
    if not user or user.status != "approved":
        raise HTTPException(401, "Account not found or not approved")
    return user


# ---- signup / approval flow -------------------------------------------
@router.post("/api/auth/signup")
def signup(payload: SignupRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(400, "An account with this email already exists")

    tenant = Tenant(firm_name=payload.firm_name)
    db.add(tenant)
    db.flush()

    user = User(
        tenant_id=tenant.id,
        email=payload.email,
        password_hash=auth.hash_password(payload.password),
        name=payload.name,
        role="Admin",
        is_tenant_admin=True,
        status="pending",
    )
    db.add(user)
    db.commit()

    background_tasks.add_task(
        auth.send_approval_request_email, payload.name, payload.email, payload.firm_name, user.approval_token
    )
    return {"message": "Access request submitted. You'll be able to log in once the admin approves your request."}


@router.get("/api/auth/approve", response_class=HTMLResponse)
def approve(token: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.approval_token == token).first()
    if not user:
        return HTMLResponse("<h2>Invalid or already-used approval link.</h2>", status_code=404)
    user.status = "approved"
    db.commit()
    return HTMLResponse(f"<h2>Approved {user.email} ({user.name}). They can now log in.</h2>")


@router.get("/api/auth/reject", response_class=HTMLResponse)
def reject(token: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.approval_token == token).first()
    if not user:
        return HTMLResponse("<h2>Invalid or already-used link.</h2>", status_code=404)
    user.status = "rejected"
    db.commit()
    return HTMLResponse(f"<h2>Rejected the request from {user.email}.</h2>")


# ---- login / session ------------------------------------------------------
@router.post("/api/auth/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not auth.verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Incorrect email or password")
    if user.status == "pending":
        raise HTTPException(403, "Your access request is still pending admin approval")
    if user.status == "rejected":
        raise HTTPException(403, "Your access request was not approved")

    token = auth.create_session_token(user.id, user.tenant_id, user.role, user.is_tenant_admin)
    return {
        "token": token,
        "user": {
            "name": user.name, "email": user.email, "role": user.role,
            "is_tenant_admin": user.is_tenant_admin, "firm_name": user.tenant.firm_name,
        },
    }


@router.get("/api/auth/me")
def me(user: User = Depends(current_user)):
    return {
        "name": user.name, "email": user.email, "role": user.role,
        "is_tenant_admin": user.is_tenant_admin, "firm_name": user.tenant.firm_name,
    }


# ---- team management (tenant admin only) -------------------------------
@router.post("/api/team/add")
def add_team_member(payload: AddTeamMemberRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if not user.is_tenant_admin:
        raise HTTPException(403, "Only the firm admin can add team members")
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(400, "An account with this email already exists")
    member = User(
        tenant_id=user.tenant_id,
        email=payload.email,
        password_hash=auth.hash_password(payload.password),
        name=payload.name,
        role=payload.role,
        is_tenant_admin=False,
        status="approved",  # added directly by the firm's own admin - no separate approval needed
    )
    db.add(member)
    db.commit()
    return {"message": f"Added {member.name} ({member.role})."}


@router.get("/api/team/list")
def list_team(user: User = Depends(current_user), db: Session = Depends(get_db)):
    members = db.query(User).filter(User.tenant_id == user.tenant_id).all()
    return [{"name": m.name, "email": m.email, "role": m.role, "is_tenant_admin": m.is_tenant_admin} for m in members]


# ---- tenant-scoped client data (replaces localStorage for logged-in use) --
class ClientPayload(BaseModel):
    name: str
    entity: str = "Individual"
    pan: str = ""
    gstin: str = ""
    cin: str = ""
    contact: str = ""
    mobile: str = ""
    email: str = ""
    address: str = ""
    state: str = "Delhi"
    sez: bool = False


@router.get("/api/clients")
def list_clients(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.query(Client).filter(Client.tenant_id == user.tenant_id).all()
    return [
        {
            "id": c.id, "name": c.name, "entity": c.entity, "pan": c.pan, "gstin": c.gstin,
            "cin": c.cin, "contact": c.contact, "mobile": c.mobile, "email": c.email,
            "address": c.address, "state": c.state, "sez": c.sez,
        }
        for c in rows
    ]


@router.post("/api/clients")
def add_client(payload: ClientPayload, user: User = Depends(current_user), db: Session = Depends(get_db)):
    existing = None
    if payload.pan:
        existing = db.query(Client).filter(Client.tenant_id == user.tenant_id, Client.pan == payload.pan).first()
    if existing:
        for field, value in payload.model_dump().items():
            setattr(existing, field, value)
        db.commit()
        return {"id": existing.id, "action": "updated"}
    client = Client(tenant_id=user.tenant_id, **payload.model_dump())
    db.add(client)
    db.commit()
    return {"id": client.id, "action": "created"}
