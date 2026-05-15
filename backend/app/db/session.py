from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.db.models import Base

engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def create_tables() -> None:
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(
            text("""
            CREATE INDEX IF NOT EXISTS idx_embeddings_vector
            ON incident_embeddings
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 10)
        """)
        )


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
