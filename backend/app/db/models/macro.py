from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, JSON, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MacroSeries(Base):
    """A named macro/geopolitical data series definition (policy rate, KIBOR, CPI, etc.)."""

    __tablename__ = "macro_series"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(150))
    source: Mapped[str] = mapped_column(String(20))  # SBP | PBS | other
    frequency: Mapped[str] = mapped_column(String(20))  # daily | monthly | quarterly | annual
    unit: Mapped[str] = mapped_column(String(20))

    observations: Mapped[list["MacroObservation"]] = relationship(back_populates="series")


class MacroObservation(Base):
    """A single published data point for a macro series, with its own publication timestamp."""

    __tablename__ = "macro_observation"

    id: Mapped[int] = mapped_column(primary_key=True)
    macro_series_id: Mapped[int] = mapped_column(ForeignKey("macro_series.id"), index=True)
    period: Mapped[date] = mapped_column(Date, index=True)
    value: Mapped[float] = mapped_column(Numeric(18, 4))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    series: Mapped[MacroSeries] = relationship(back_populates="observations")


class SectorRiskSnapshot(Base):
    """Analyst-maintained structured risk panel (Overall Risk / Geopolitical / Economy / IMF / Currency).

    Deliberately not auto-generated: these are editorial judgments, evidence class
    "analyst_interpretation", refreshed on a defined cadence rather than computed live.
    """

    __tablename__ = "sector_risk_snapshot"

    id: Mapped[int] = mapped_column(primary_key=True)
    sector_id: Mapped[int | None] = mapped_column(ForeignKey("sector.id"), nullable=True)
    as_of_date: Mapped[date] = mapped_column(Date, index=True)
    overall_risk: Mapped[str] = mapped_column(String(20))  # low | moderate | elevated | high
    geopolitical: Mapped[str] = mapped_column(String(30))
    economy: Mapped[str] = mapped_column(String(30))
    imf_program: Mapped[str] = mapped_column(String(30))
    currency_pkr: Mapped[str] = mapped_column(String(30))
    key_positives: Mapped[list[str]] = mapped_column(JSON, default=list)
    key_negatives: Mapped[list[str]] = mapped_column(JSON, default=list)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
