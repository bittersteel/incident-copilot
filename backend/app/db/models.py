from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSON, UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    title: Mapped[str] = mapped_column(String(255))
    severity: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(20), server_default=text("'open'"))
    service: Mapped[str] = mapped_column(String(100))
    environment: Mapped[str] = mapped_column(String(50), server_default=text("'production'"))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    log_snapshot: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metrics_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    deployment_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    resolution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class IncidentEmbedding(Base):
    __tablename__ = "incident_embeddings"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    incident_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=False,
    )
    embedding: Mapped[list[float]] = mapped_column(Vector(1024))
    embed_model: Mapped[str] = mapped_column(String(64), server_default=text("'voyage-3'"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class RcaReport(Base):
    __tablename__ = "rca_reports"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    incident_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("incidents.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    timeline: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    root_cause: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    impacted_systems: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolution_steps: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recommendations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    generated_by: Mapped[str] = mapped_column(
        String(64),
        server_default=text("'claude-sonnet-4-6'"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    incident_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=False,
    )
    action_type: Mapped[str] = mapped_column(String(100))
    action_payload: Mapped[dict[str, Any]] = mapped_column(JSON, server_default=text("'{}'::jsonb"))
    status: Mapped[str] = mapped_column(String(20), server_default=text("'pending'"))
    requested_by: Mapped[str] = mapped_column(String(100), server_default=text("'system'"))
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
