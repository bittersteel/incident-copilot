import voyageai
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import Incident

voyage_client = voyageai.Client(api_key=settings.voyage_api_key)


def embed_text(texts: list[str]) -> list[list[float]]:
    result = voyage_client.embed(texts, model="voyage-3")
    return result.embeddings


async def retrieve_similar(
    query_text: str,
    db: AsyncSession,
    top_k: int = 3,
) -> list[Incident]:
    vector = embed_text([query_text])[0]
    vec_str = "[" + ",".join(str(x) for x in vector) + "]"
    rows = await db.execute(
        text("""
            SELECT i.id, i.title, i.severity, i.status, i.service,
                   i.description, i.log_snapshot, i.metrics_summary,
                   i.deployment_ref, i.resolution, i.started_at,
                   i.resolved_at, i.created_at, i.environment
            FROM incidents i
            JOIN incident_embeddings e ON e.incident_id = i.id
            ORDER BY e.embedding <=> CAST(:vec AS vector)
            LIMIT :k
        """),
        {"vec": vec_str, "k": top_k},
    )
    out: list[Incident] = []
    for r in rows.mappings().all():
        out.append(
            Incident(
                id=r["id"],
                title=r["title"],
                severity=r["severity"],
                status=r["status"],
                service=r["service"],
                environment=r["environment"],
                description=r["description"],
                log_snapshot=r["log_snapshot"],
                metrics_summary=r["metrics_summary"],
                deployment_ref=r["deployment_ref"],
                resolution=r["resolution"],
                started_at=r["started_at"],
                resolved_at=r["resolved_at"],
                created_at=r["created_at"],
            )
        )
    return out
