import json
from pathlib import Path
from typing import AsyncIterator

import anthropic

from app.config import settings

client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

CHAT_SYSTEM = (Path(__file__).parent.parent / "prompts/chat_system.txt").read_text()
RCA_SYSTEM = (Path(__file__).parent.parent / "prompts/rca_system.txt").read_text()


MODEL = "claude-sonnet-4-6"


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
