import json
import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from app.db.models import Incident
from app.deps import APIKeyDep, DBDep
from app.services import llm, rag
from app.services.connectors import deployments, logs

router = APIRouter(dependencies=[APIKeyDep])


class ChatRequest(BaseModel):
    message: str
    incident_id: str | None = None
    conversation_history: list[dict] = []


def _format_similar(inc_list: list[Incident]) -> str:
    blocks: list[str] = []
    for inc in inc_list:
        res = inc.resolution or "Unresolved"
        blocks.append(
            f"[INC-{inc.id}] {inc.title} (severity: {inc.severity}, status: {inc.status})\n"
            f"Service: {inc.service}\n"
            f"Description: {inc.description}\n"
            f"Resolution: {res}"
        )
    return "\n\n".join(blocks)


@router.post("/chat")
async def chat(body: ChatRequest, db: AsyncSession = DBDep) -> StreamingResponse:
    similar = await rag.retrieve_similar(body.message, db)
    current: Incident | None = None
    if body.incident_id:
        try:
            uid = uuid.UUID(body.incident_id)
        except ValueError:
            uid = None
        if uid is not None:
            current = await db.get(Incident, uid)

    if current is not None:
        log_block = (current.log_snapshot or "") + "\n" + logs.get_logs(current.service, str(current.id))
        svc = current.service
    elif body.incident_id:
        log_block = "No specific incident selected"
        svc = "unknown"
    else:
        log_block = "No specific incident selected"
        svc = "unknown"

    dep_list = deployments.get_recent_deployments(svc)
    dep_text = json.dumps(dep_list, indent=2)

    context = f"""<context>
## Similar historical incidents
{_format_similar(similar)}

## Current incident logs
{log_block}

## Recent deployments for {svc}
{dep_text}
</context>"""

    messages = body.conversation_history + [
        {"role": "user", "content": context + "\n\n" + body.message}
    ]

    citations = [{"id": str(inc.id), "title": inc.title, "severity": inc.severity} for inc in similar]

    async def event_gen() -> AsyncIterator[str]:
        async for chunk in llm.stream_chat(messages):
            yield f"data: {json.dumps({'delta': chunk})}\n\n"
        yield f"data: {json.dumps({'done': True, 'citations': citations})}\n\n"

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={
            "X-Accel-Buffering": "no",
            "Cache-Control": "no-cache",
        },
    )
