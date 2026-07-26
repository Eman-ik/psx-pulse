from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Sector(Base):
    """PSX sector classification (e.g. Fertilizer). Identity master root for sector grouping."""

    __tablename__ = "sector"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    psx_sector_code: Mapped[str | None] = mapped_column(String(20), nullable=True)

    issuers: Mapped[list["Issuer"]] = relationship(back_populates="sector")


class Issuer(Base):
    """A company/legal entity that may list one or more securities. Supports parent/subsidiary graph."""

    __tablename__ = "issuer"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    short_name: Mapped[str | None] = mapped_column(String(60), nullable=True)
    sector_id: Mapped[int | None] = mapped_column(ForeignKey("sector.id"), nullable=True)
    ultimate_parent_issuer_id: Mapped[int | None] = mapped_column(ForeignKey("issuer.id"), nullable=True)
    incorporation_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_conglomerate: Mapped[bool] = mapped_column(Boolean, default=False)

    sector: Mapped[Sector | None] = relationship(back_populates="issuers")
    parent: Mapped["Issuer | None"] = relationship(remote_side="Issuer.id")
    securities: Mapped[list["Security"]] = relationship(back_populates="issuer")


class Security(Base):
    """A single listed instrument (usually ordinary shares) belonging to an issuer."""

    __tablename__ = "security"

    id: Mapped[int] = mapped_column(primary_key=True)
    issuer_id: Mapped[int] = mapped_column(ForeignKey("issuer.id"), index=True)
    symbol: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    security_type: Mapped[str] = mapped_column(String(40), default="ordinary_share")
    listing_status: Mapped[str] = mapped_column(String(20), default="listed")
    listing_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    free_float_pct: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    issuer: Mapped[Issuer] = relationship(back_populates="securities")
    ticker_history: Mapped[list["TickerHistory"]] = relationship(back_populates="security")


class TickerHistory(Base):
    """Ticker/symbol changes over time, required to keep historical price series correctly identified."""

    __tablename__ = "ticker_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    security_id: Mapped[int] = mapped_column(ForeignKey("security.id"), index=True)
    old_symbol: Mapped[str] = mapped_column(String(20))
    new_symbol: Mapped[str] = mapped_column(String(20))
    effective_date: Mapped[date] = mapped_column(Date)
    reason: Mapped[str | None] = mapped_column(String(200), nullable=True)

    security: Mapped[Security] = relationship(back_populates="ticker_history")


class Person(Base):
    """A director/officer/sponsor referenced by governance and ownership data."""

    __tablename__ = "person"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(150), index=True)


class BoardMembership(Base):
    """Links a person to an issuer's board/management with tenure, for governance tracking."""

    __tablename__ = "board_membership"

    id: Mapped[int] = mapped_column(primary_key=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("person.id"), index=True)
    issuer_id: Mapped[int] = mapped_column(ForeignKey("issuer.id"), index=True)
    role: Mapped[str] = mapped_column(String(100))
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_independent: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
