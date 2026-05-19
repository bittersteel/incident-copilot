import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ApprovalRequest, Incident, RcaReport
from app.deps import APIKeyDep, DBDep

router = APIRouter(dependencies=[APIKeyDep], prefix="/incidents")


def _incident_dict(inc: Incident) -> dict:
    return {
        "id": str(inc.id),
        "title": inc.title,
        "severity": inc.severity,
        "status": inc.status,
        "service": inc.service,
        "environment": inc.environment,
        "description": inc.description or "",
        "log_snapshot": inc.log_snapshot,
        "metrics_summary": inc.metrics_summary,
        "deployment_ref": inc.deployment_ref,
        "resolution": inc.resolution,
        "started_at": inc.started_at.isoformat() if inc.started_at else None,
        "resolved_at": inc.resolved_at.isoformat() if inc.resolved_at else None,
        "created_at": inc.created_at.isoformat() if inc.created_at else "",
    }


def _rca_dict(r: RcaReport) -> dict:
    return {
        "id": str(r.id),
        "incident_id": str(r.incident_id),
        "timeline": r.timeline or "",
        "root_cause": r.root_cause or "",
        "impacted_systems": r.impacted_systems or "",
        "resolution_steps": r.resolution_steps or "",
        "recommendations": r.recommendations or "",
        "generated_by": r.generated_by,
        "created_at": r.created_at.isoformat() if r.created_at else "",
    }


def _approval_dict(a: ApprovalRequest) -> dict:
    return {
        "id": str(a.id),
        "incident_id": str(a.incident_id),
        "action_type": a.action_type,
        "action_payload": a.action_payload or {},
        "status": a.status,
        "requested_by": a.requested_by,
        "reviewed_by": a.reviewed_by,
        "created_at": a.created_at.isoformat() if a.created_at else "",
        "reviewed_at": a.reviewed_at.isoformat() if a.reviewed_at else None,
    }


@router.get("")
async def list_incidents(db: AsyncSession = DBDep) -> list[dict]:
    result = await db.scalars(
        select(Incident).order_by(Incident.created_at.desc()).limit(50)
    )
    return [_incident_dict(i) for i in result.all()]


@router.get("/{incident_id}")
async def get_incident(incident_id: str, db: AsyncSession = DBDep) -> dict:
    try:
        uid = uuid.UUID(incident_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid incident id") from exc
    inc = await db.get(Incident, uid)
    if inc is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    rca = await db.scalar(select(RcaReport).where(RcaReport.incident_id == inc.id))
    out = {"incident": _incident_dict(inc)}
    if rca is not None:
        out["rca_report"] = _rca_dict(rca)
    return out


class ApproveCreate(BaseModel):
    action_type: str
    action_payload: dict = Field(default_factory=dict)


@router.post("/{incident_id}/approve")
async def create_approval(
    incident_id: str,
    body: ApproveCreate,
    db: AsyncSession = DBDep,
) -> dict:
    try:
        uid = uuid.UUID(incident_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid incident id") from exc
    inc = await db.get(Incident, uid)
    if inc is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    req = ApprovalRequest(
        incident_id=inc.id,
        action_type=body.action_type,
        action_payload=body.action_payload,
    )
    db.add(req)
    await db.commit()
    await db.refresh(req)
    return _approval_dict(req)


class ApprovePatch(BaseModel):
    status: str
    reviewed_by: str


@router.patch("/{incident_id}/approve/{approval_id}")
async def update_approval(
    incident_id: str,
    approval_id: str,
    body: ApprovePatch,
    db: AsyncSession = DBDep,
) -> dict:
    if body.status not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="status must be approved or rejected")
    try:
        iid = uuid.UUID(incident_id)
        aid = uuid.UUID(approval_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid id") from exc
    req = await db.get(ApprovalRequest, aid)
    if req is None or req.incident_id != iid:
        raise HTTPException(status_code=404, detail="Approval request not found")
    req.status = body.status
    req.reviewed_by = body.reviewed_by
    req.reviewed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(req)
    return _approval_dict(req)
