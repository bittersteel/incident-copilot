import anthropic
import json
from pathlib import Path
from typing import AsyncIterator

from app.config import settings

client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

_PROMPTS = Path(__file__).parent.parent / "prompts"
CHAT_SYSTEM        = (_PROMPTS / "chat_system.txt").read_text()
RCA_SYSTEM         = (_PROMPTS / "rca_system.txt").read_text()
ORCHESTRATOR_SYSTEM = (_PROMPTS / "orchestrator_system.txt").read_text()
TRIAGE_SYSTEM      = (_PROMPTS / "triage_system.txt").read_text()
RESPONDER_SYSTEM   = (_PROMPTS / "responder_system.txt").read_text()

MODEL = "claude-sonnet-4-6"

# ---------------------------------------------------------------------------
# Tool definitions for the Orchestrator agent
# ---------------------------------------------------------------------------
ORCHESTRATOR_TOOLS: list[dict] = [
    {
        "name": "triage_incident",
        "description": (
            "Analyse the current incident's logs, metrics, and description. "
            "Returns a structured JSON assessment including incident class, key signals, "
            "suspected root cause, and an optimised knowledge-base search query. "
            "ALWAYS call this first."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "focus_query": {
                    "type": "string",
                    "description": (
                        "A concise description of what to focus the triage on, "
                        "e.g. 'JWT key rotation mismatch causing auth 401s in user-service'"
                    ),
                }
            },
            "required": ["focus_query"],
        },
    },
    {
        "name": "search_similar_incidents",
        "description": (
            "Search the historical incident knowledge base using semantic similarity. "
            "Returns up to 3 past incidents with their resolutions. "
            "Call after triage and use its search_query field for best results."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Semantic search query based on triage findings",
                }
            },
            "required": ["query"],
        },
    },
    {
        "name": "analyze_deployment_context",
        "description": (
            "Retrieve and analyse recent deployments for a service. "
            "Call this when triage returns deployment_correlated=true."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "service": {
                    "type": "string",
                    "description": "Service name to retrieve deployment history for",
                }
            },
            "required": ["service"],
        },
    },
    {
        "name": "signal_complete",
        "description": (
            "Signal that all needed context has been gathered. "
            "The framework will generate the final synthesised response. "
            "This must always be your last tool call."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]


# ---------------------------------------------------------------------------
# Original single-agent helpers (kept for RCA and fallback use)
# ---------------------------------------------------------------------------

async def stream_chat(messages: list[dict], system: str = CHAT_SYSTEM) -> AsyncIterator[str]:
    async with client.messages.stream(
        model=MODEL,
        max_tokens=1024,
        system=system,
        messages=messages,
    ) as stream:
        async for text in stream.text_stream:
            yield text


async def complete(messages: list[dict], system: str = RCA_SYSTEM) -> str:
    response = await client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=system,
        messages=messages,
    )
    return response.content[0].text


# ---------------------------------------------------------------------------
# Multi-agent helpers
# ---------------------------------------------------------------------------

async def run_triage_agent(focus_query: str, logs: str, metrics: str) -> dict:
    """
    Triage subagent — a dedicated LLM call that returns structured JSON.
    This is Agent #2 in the pipeline (invoked by the orchestrator tool handler).
    """
    response = await client.messages.create(
        model=MODEL,
        max_tokens=512,
        system=TRIAGE_SYSTEM,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Focus: {focus_query}\n\n"
                    f"Logs:\n{logs}\n\n"
                    f"Metrics: {metrics}"
                ),
            }
        ],
    )
    text = response.content[0].text.strip()

    # Strip code fences if Claude added them
    if "```" in text:
        if "```json" in text:
            text = text.split("```json", 1)[1].split("```", 1)[0]
        else:
            text = text.split("```", 1)[1].split("```", 1)[0]
        text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "raw_triage": text,
            "incident_class": "other",
            "confidence": "low",
            "affected_layers": [],
            "key_signals": [],
            "suspected_root_cause": "Triage output could not be parsed.",
            "deployment_correlated": False,
            "affected_service": "unknown",
            "search_query": focus_query,
        }


async def orchestrator_step(messages: list[dict]) -> tuple[list, str]:
    """
    Single round of the Orchestrator agent's tool-use loop.
    Returns (content_blocks, stop_reason).
    """
    response = await client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=ORCHESTRATOR_SYSTEM,
        tools=ORCHESTRATOR_TOOLS,
        messages=messages,
    )
    return response.content, response.stop_reason


async def stream_response(
    messages: list[dict],
    system: str = RESPONDER_SYSTEM,
) -> AsyncIterator[str]:
    """
    Responder agent — final streaming synthesis call.
    This is Agent #3 (or #4 when deployment analysis is included).
    """
    async with client.messages.stream(
        model=MODEL,
        max_tokens=1500,
        system=system,
        messages=messages,
    ) as stream:
        async for text in stream.text_stream:
            yield text
