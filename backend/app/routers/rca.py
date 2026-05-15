import json
import re
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Incident, RcaReport
from app.deps import APIKeyDep, DBDep
from app.services import llm, rag
from app.services.connectors import logs

router = APIRouter(dependencies=[APIKeyDep])


class RcaGenerateRequest(BaseModel):
    incident_id: str


def _strip_json_fences(raw: str) -> str:
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE | re.MULTILINE)
    text = re.sub(r"\s*```$", "", text, flags=re.MULTILINE)
    return text.strip()


@router.post("/rca/generate")
async def generate_rca(body: RcaGenerateRequest, db: AsyncSession = DBDep) -> dict:
    try:
        uid = uuid.UUID(body.incident_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid incident id") from exc

    incident = await db.get(Incident, uid)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    similar = await rag.retrieve_similar(
        f"{incident.title}\n{incident.description or ''}",
        db,
    )
    connector_logs = logs.get_logs(incident.service, str(incident.id))

    similar_text = "\n\n".join(
        f"[INC-{s.id}] {s.title} ({s.severity}, {s.status}): {s.description}"
        for s in similar
    )

    user_prompt = f"""Generate an RCA for this incident:

Title: {incident.title}
Severity: {incident.severity}
Service: {incident.service}
Description: {incident.description or ''}
Log snapshot:
{incident.log_snapshot or ''}
Metrics: {incident.metrics_summary or ''}
Deployment ref: {incident.deployment_ref or ''}

Connector log tail:
{connector_logs}

Similar past incidents:
{similar_text}
"""

    raw = await llm.complete([{"role": "user", "content": user_prompt}], system=llm.RCA_SYSTEM)
    data = json.loads(_strip_json_fences(raw))

    await db.execute(delete(RcaReport).where(RcaReport.incident_id == incident.id))
    report = RcaReport(
        incident_id=incident.id,
        timeline=data.get("timeline"),
        root_cause=data.get("root_cause"),
        impacted_systems=data.get("impacted_systems"),
        resolution_steps=data.get("resolution_steps"),
        recommendations=data.get("recommendations"),
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    return {
        "id": str(report.id),
        "incident_id": str(report.incident_id),
        "timeline": report.timeline or "",
        "root_cause": report.root_cause or "",
        "impacted_systems": report.impacted_systems or "",
        "resolution_steps": report.resolution_steps or "",
        "recommendations": report.recommendations or "",
        "generated_by": report.generated_by,
        "created_at": report.created_at.isoformat() if report.created_at else "",
    }
