"""DB models for the PSX Analyst Agent (Blueprint Section 13.3).

AnalystRun: one row per invocation — tracks status, version identifiers, and errors.
AnalystPacket: the structured output of a completed run, keyed scalars + full JSON.

is_approved on AnalystPacket is the Human Review Interrupt gate (Blueprint Section 5).
A packet is readable internally regardless of approval status; the gate prevents
any future public distribution path from reading unapproved research.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

HEALTH_CLASSIFICATIONS = (
    "genuinely_healthy",
    "healthy_but_cyclical",
    "improving",
    "surface_level_strength",
    "deteriorating",
    "financially_fragile",
    "insufficient_evidence",
)

RESEARCH_STANCES = ("positive", "neutral", "negative", "watch", "insufficient_evidence")


class AnalystRun(Base):
    """Tracks each invocation of the PSX Analyst Agent for an issuer.

    status lifecycle: pending → running → complete | failed | blocked
    blocked = required data is missing for a critical module
    failed = runtime error (see error_message)
    """

    __tablename__ = "analyst_run"

    id: Mapped[int] = mapped_column(primary_key=True)
    issuer_id: Mapped[int] = mapped_column(ForeignKey("issuer.id"), index=True)
    symbol: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    prompt_version: Mapped[str] = mapped_column(String(40), default="psx-analyst-v1")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AnalystPacket(Base):
    """The structured output of a completed analyst run.

    packet_json stores the full PSXAnalystPacket (Blueprint Section 12).
    Key scalar fields are extracted as columns so the review queue can filter
    without parsing JSON on every row.

    is_approved: human review gate — must be True before any public-facing
    distribution path reads this packet. Internal display (the Analyst Workbench
    tab) always reads regardless, with a disclaimer.
    """

    __tablename__ = "analyst_packet"

    id: Mapped[int] = mapped_column(primary_key=True)
    analyst_run_id: Mapped[int] = mapped_column(ForeignKey("analyst_run.id"), unique=True, index=True)
    issuer_id: Mapped[int] = mapped_column(ForeignKey("issuer.id"), index=True)
    research_posture: Mapped[str] = mapped_column(String(30))
    business_health: Mapped[str] = mapped_column(String(40))
    confidence: Mapped[str] = mapped_column(String(10))
    one_sentence_view: Mapped[str | None] = mapped_column(String(500), nullable=True)
    decision_hinge: Mapped[str | None] = mapped_column(String(500), nullable=True)
    packet_json: Mapped[dict] = mapped_column(JSON)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
