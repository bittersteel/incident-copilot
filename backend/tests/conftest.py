import os
from unittest.mock import AsyncMock, patch

import pytest

os.environ.setdefault("ANTHROPIC_API_KEY", "test-anthropic-key")
os.environ.setdefault("VOYAGE_API_KEY", "test-voyage-key")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://copilot:copilot@localhost:5432/copilot")
os.environ.setdefault("API_KEY", "dev-secret")
os.environ.setdefault("FRONTEND_ORIGIN", "http://localhost:5173")


@pytest.fixture(autouse=True)
def _noop_lifespan_db():
    with (
        patch("app.main.create_tables", new=AsyncMock(return_value=None)),
        patch("app.main.seed_incidents", new=AsyncMock(return_value=None)),
    ):
        yield
