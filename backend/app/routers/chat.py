"""
Multi-agent chat router
─────────────────────────────────────────────────────────────────────────────
Request flow:
  1. Orchestrator agent  — decides which tools to call and in what order
  2. Triage subagent     — dedicated LLM call; structured JSON signal extraction
  3. Research tool       — deterministic vector search over incident embeddings
  4. Deployment tool     — deterministic recent-deployment lookup (conditional)
  5. Responder agent     — final streaming synthesis using all gathered context

SSE event types emitted to the client
  {"agent": "<name>", "status": "running"|"done", "label": "<human label>"}
  {"delta": "<text chunk>"}
  {"done": true, "citations": [...]}
"""

import json
import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from app.db.models import Incident
from app.deps import APIKeyDep, DBDep
from app.services import llm, rag
from app.services.connectors import deployments, logs

router = APIRouter(dependencies=[APIKeyDep])

# Human-readable labels shown in the UI while each agent is active
AGENT_LABELS: dict[str, str] = {
    "orchestrator":            "Orchestrator dispatching agents…",
    "triage_incident":         "Triage agent analysing incident signals…",
    "search_similar_incidents":"Research agent searching knowledge base…",
    "analyze_deployment_context": "Deployment agent checking recent changes…",
    "signal_complete":         "Orchestrator completing investigation…",
    "responder":               "Responder synthesising findings…",
}


class ChatRequest(BaseModel):
    message: str
    incident_id: str | None = None
    conversation_history: list[dict] = []


@router.post("/chat")
async def chat(body: ChatRequest, db: AsyncSession = DBDep) -> StreamingResponse:

    # ── 1. Fetch the selected incident ──────────────────────────────────────
    current: Incident | None = None
    if body.incident_id:
        try:
            uid = uuid.UUID(body.incident_id)
        except ValueError:
            uid = None
        if uid is not None:
            current = await db.get(Incident, uid)

    # ── 2. Build raw context strings ────────────────────────────────────────
    if current is not None:
        log_text = (
            (current.log_snapshot or "")
            + "\n"
            + logs.get_logs(current.service, str(current.id))
        )
        metrics_text = current.metrics_summary or ""
        svc = current.service
        incident_context = (
            f"Incident: {current.title}  |  Severity: {current.severity}  "
            f"|  Status: {current.status}\n"
            f"Service: {current.service}  |  Deployment ref: {current.deployment_ref or 'N/A'}\n"
            f"Description: {current.description}"
        )
    else:
        log_text = "No specific incident selected."
        metrics_text = ""
        svc = "unknown"
        incident_context = "No specific incident selected."

    dep_data = deployments.get_recent_deployments(svc)

    # ── 3. Shared state for the orchestration loop ───────────────────────────
    gathered: dict = {
        "triage":    None,
        "similar":   [],
        "citations": [],
        "dep_data":  dep_data,
    }

    async def execute_tool(name: str, tool_input: dict) -> dict:
        """Dispatch a tool call requested by the Orchestrator agent."""

        if name == "triage_incident":
            result = await llm.run_triage_agent(
                tool_input.get("focus_query", body.message),
                log_text,
                metrics_text,
            )
            gathered["triage"] = result
            return result

        if name == "search_similar_incidents":
            query = tool_input.get("query", body.message)
            similar = await rag.retrieve_similar(query, db, top_k=3)
            gathered["similar"] = similar
            gathered["citations"] = [
                {"id": str(i.id), "title": i.title, "severity": i.severity}
                for i in similar
            ]
            return {
                "incidents": [
                    {
                        "id": str(i.id),
                        "title": i.title,
                        "severity": i.severity,
                        "status": i.status,
                        "service": i.service,
                        "resolution": i.resolution or "Unresolved",
                    }
                    for i in similar
                ]
            }

        if name == "analyze_deployment_context":
            svc_name = tool_input.get("service", svc)
            data = deployments.get_recent_deployments(svc_name)
            gathered["dep_data"] = data
            return {"deployments": data}

        if name == "signal_complete":
            return {"status": "acknowledged"}

        return {"error": f"Unknown tool: {name}"}

    # ── 4. SSE generator ─────────────────────────────────────────────────────
    async def event_gen() -> AsyncIterator[str]:

        def sse(payload: dict) -> str:
            return f"data: {json.dumps(payload)}\n\n"

        # ── Orchestrator tool-use loop ──
        yield sse({"agent": "orchestrator", "status": "running",
                   "label": AGENT_LABELS["orchestrator"]})

        messages: list[dict] = [
            {"role": "user", "content": f"{incident_context}\n\n{body.message}"}
        ]
        done_gathering = False

        for _round in range(6):                        # safety cap: 6 rounds max
            content_blocks, stop_reason = await llm.orchestrator_step(messages)
            messages.append({"role": "assistant", "content": content_blocks})

            if stop_reason != "tool_use":
                break                                  # end_turn or error → stop

            tool_results: list[dict] = []
            for block in content_blocks:
                if block.type != "tool_use":
                    continue

                tool_name = block.name
                yield sse({
                    "agent": tool_name,
                    "status": "running",
                    "label": AGENT_LABELS.get(tool_name, tool_name),
                })

                result = await execute_tool(tool_name, block.input)

                yield sse({"agent": tool_name, "status": "done", "label": ""})

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result, default=str),
                })

                if tool_name == "signal_complete":
                    done_gathering = True

            messages.append({"role": "user", "content": tool_results})

            if done_gathering:
                break

        yield sse({"agent": "orchestrator", "status": "done", "label": ""})

        # ── Responder agent (streaming) ──
        yield sse({"agent": "responder", "status": "running",
                   "label": AGENT_LABELS["responder"]})

        triage_text = (
            json.dumps(gathered["triage"], indent=2)
            if gathered["triage"] else "Not available."
        )
        similar_text = "\n\n".join([
            f"[INC-{i.id}] {i.title} ({i.severity}, {i.status})\n"
            f"Service: {i.service}\n"
            f"Description: {i.description}\n"
            f"Resolution: {i.resolution or 'Unresolved'}"
            for i in gathered["similar"]
        ]) or "No similar incidents found in the knowledge base."

        dep_context = json.dumps(gathered["dep_data"], indent=2)

        responder_ctx = (
            "<context>\n"
            "## Triage Assessment  (from Triage Agent)\n"
            f"{triage_text}\n\n"
            "## Similar Historical Incidents  (from Research Agent)\n"
            f"{similar_text}\n\n"
            "## Recent Deployments\n"
            f"{dep_context}\n\n"
            "## Current Logs\n"
            f"{log_text}\n"
            "</context>"
        )

        responder_messages = body.conversation_history + [
            {"role": "user", "content": responder_ctx + "\n\n" + body.message}
        ]

        async for chunk in llm.stream_response(responder_messages):
            yield sse({"delta": chunk})

        yield sse({"agent": "responder", "status": "done", "label": ""})
        yield sse({"done": True, "citations": gathered["citations"]})

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={
            "X-Accel-Buffering": "no",
            "Cache-Control": "no-cache",
        },
    )
