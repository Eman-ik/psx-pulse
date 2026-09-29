"""The v1 coverage universe: fertilizer and cement, and how deeply each name is covered.

Scope is two PSX sectors, not an index slice. That means the universe is defined by PSX's
own sector taxonomy (psxdata.symbols().sector_name) rather than a hand-maintained ticker
list, so a new listing or a reclassification shows up on the next rebuild instead of being
silently missing forever.

Three things have to be filtered out of a raw sector query before it is a universe of
companies, and each one is a different kind of wrong:

  * Non-common-equity lines. Preference shares and rights (AGLNCPS, POWERPS, FLYNGR1) carry
    their own symbols and would otherwise appear as extra "companies" with nonsense ratios.
  * Stale symbol records. PSX keeps a symbols() row long after the company behind it stops
    trading. ENGRO still shows up under FERTILIZER although Engro Corporation restructured
    into Engro Holdings (ENGROH, now classified under investment companies); FFBL still shows
    up although it merged into FFC in Dec 2024. Both return zero price bars.
  * Instruments that are not equities at all (is_debt / is_gem / is_etf).

After filtering, the live counts reconcile exactly against psxdata.sectors()' own
advance/decline/unchanged totals for each sector -- 5 fertilizer and 18 cement on the day
this was written. That reconciliation is the cheapest available check that the filter is
neither dropping real companies nor inventing them, so build_universe() performs it.

## Coverage tiers

  FULL        -- fundamentals traceable to a specific source document. Ratios and
                 narrative are safe to render.
  UNVERIFIED  -- fundamentals exist in the DB but were never checked against the
                 underlying PDF. Must NOT reach a user-facing ratio or narrative.
  PRICE_ONLY  -- prices and announcements ingest fine, no fundamentals entered yet.

## The quarantine note

app/ingestion/manual_financials_seed_cement.py opens with its own "DATA VERIFICATION
REQUIRED" warning: its balance-sheet figures were recalled from model training data, not
read off annual reports. Its per-company `source_label` strings nonetheless read like real
citations ("Bestway Cement Annual Report FY2022-FY2024"), so nothing downstream can tell
those rows apart from the genuinely-sourced fertilizer rows by inspection. That is exactly
the failure mode worth spending code on: UNVERIFIED_FUNDAMENTALS below is the explicit list
that keeps them out of user-facing surfaces until someone opens the PDFs.

With scope narrowed to these two sectors, that quarantine covers 10 of the 18 cement
companies -- i.e. most of half the product. Verifying them is the critical path, not a
cleanup task.

Promoting a symbol from UNVERIFIED to FULL means: open the annual report, check every line
item, fix what is wrong, rewrite source_label to cite the verified document, then move the
symbol between the two frozensets here. It is deliberately a code change, not a config flag.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

logger = logging.getLogger(__name__)

SECTORS = ("FERTILIZER", "CEMENT")

SNAPSHOT_PATH = Path(__file__).resolve().parent.parent / "data" / "universe_snapshot.json"

# PSX appends an ex-marker to a symbol on its ex-dividend/bonus/rights date: LUCK trades as
# LUCKXD that day. These forms appear in indices() but never in the symbols() master list, so
# ingesting one raw either fails to resolve or mints a phantom Security that will never match
# the real company's fundamentals.
EX_MARKER_SUFFIXES = ("XD", "XB", "XR", "XBR")

# Preference-share and rights suffixes. These are separate tradable lines on the same issuer
# and are not the common equity this product researches. JVDCPS (Javedan preference) is not
# listed here because PSX classifies Javedan under PROPERTY, so it never enters this universe
# in the first place -- only the stale JVDCR1 rights line is misfiled under CEMENT.
NON_COMMON_EQUITY_SUFFIXES = ("NCPS", "CPS", "PS", "R1", "R2")

# In symbols() with a sector, but the company behind the symbol no longer trades. Each entry
# has to say why, because "returns no price data" alone does not distinguish a dead company
# from a broken fetch, and treating the second as the first silently shrinks the universe.
KNOWN_INACTIVE: dict[str, str] = {
    "ENGRO": "Engro Corporation restructured into Engro Holdings (ENGROH), which PSX now "
             "classifies under investment companies, not fertilizer.",
    "FFBL": "Merged into FFC in Dec 2024 per its own Scheme-of-Arrangement announcements. "
            "Historical data stays in the DB; the symbol is not a current company.",
    "LPCL": "Lafarge Pakistan Cement -- no price history returned; symbol record outlived the "
            "listing.",
    "PAKCEM": "Pakcem Limited -- no price history returned; symbol record outlived the listing.",
    "ZELP": "Zeal Pak Cement Factory -- long dormant, no price history returned.",
}

# Fundamentals traceable to a specific source document, entered from analyst material the
# user supplied. See manual_financials_seed.py's module docstring for per-company provenance.
VERIFIED_FUNDAMENTALS = frozenset({"FFC", "EFERT", "FATIMA"})

# Present in the DB, never checked against the underlying annual report. Read the quarantine
# note above before touching this. Do not render these as ratios or feed them to a narrative.
UNVERIFIED_FUNDAMENTALS = frozenset(
    {"LUCK", "MLCF", "DGKC", "CHCC", "BWCL", "ACPL", "FCCL", "KOHC", "DCL", "GWLC"}
)

TIER_FULL = "full"
TIER_UNVERIFIED = "unverified"
TIER_PRICE_ONLY = "price_only"


@dataclass(frozen=True)
class UniverseEntry:
    """One company in the v1 universe, as of the snapshot date."""

    symbol: str
    name: str
    sector: str
    coverage_tier: str
    # Index weight when the company is a KSE-100 constituent, else None. Most of the cement
    # sector is not in the index, so this annotates rather than defines membership.
    index_weight: float | None = None

    @property
    def has_renderable_fundamentals(self) -> bool:
        return self.coverage_tier == TIER_FULL


def normalize_symbol(raw: str, known_symbols: set[str] | None = None) -> str:
    """Strips a PSX ex-dividend/bonus/rights marker off a symbol.

    Only strips when the stripped form is a real symbol and the raw form is not, so a
    legitimate ticker that happens to end in "XD" survives intact. When `known_symbols`
    is not supplied this falls back to suffix-stripping alone, which is the looser rule --
    pass the psxdata.symbols() master list whenever you have it.
    """
    symbol = raw.strip().upper()
    if known_symbols is not None and symbol in known_symbols:
        return symbol

    for suffix in EX_MARKER_SUFFIXES:
        if not symbol.endswith(suffix) or len(symbol) <= len(suffix):
            continue
        stripped = symbol[: -len(suffix)]
        if known_symbols is None or stripped in known_symbols:
            return stripped
    return symbol


def is_common_equity(symbol: str) -> bool:
    """False for preference-share and rights lines, which are not the common equity."""
    upper = symbol.strip().upper()
    return not any(
        upper.endswith(suffix) and len(upper) > len(suffix)
        for suffix in NON_COMMON_EQUITY_SUFFIXES
    )


def coverage_tier(symbol: str) -> str:
    """Coverage tier for an already-normalized symbol."""
    if symbol in VERIFIED_FUNDAMENTALS:
        return TIER_FULL
    if symbol in UNVERIFIED_FUNDAMENTALS:
        return TIER_UNVERIFIED
    return TIER_PRICE_ONLY


def build_universe(sectors: tuple[str, ...] = SECTORS) -> list[UniverseEntry]:
    """Fetches the live symbol master and returns the common equities in `sectors`.

    Cross-checks each sector's resulting count against psxdata.sectors()' own
    advance/decline/unchanged total for that sector and logs a warning on any mismatch. A
    mismatch means the filters here have drifted from what PSX considers the sector -- worth
    knowing immediately, but not worth refusing to build over, since PSX's summary counts
    only the names that traded that session.

    Network call. Raises on an empty fetch rather than quietly writing an empty universe.
    """
    import psxdata  # imported lazily: this module is also read by code with no network

    master = psxdata.symbols()
    if master is None or len(master) == 0:
        raise RuntimeError("psxdata.symbols() returned no rows")

    equities = master[(~master["is_debt"]) & (~master["is_gem"]) & (~master["is_etf"])]
    index_weights = _kse100_weights()

    entries: list[UniverseEntry] = []
    for sector in sectors:
        rows = equities[equities["sector_name"].astype(str).str.upper() == sector.upper()]
        for _, row in rows.iterrows():
            symbol = str(row["symbol"]).strip().upper()

            if not is_common_equity(symbol):
                logger.info("Skipping %s (%s): not common equity", symbol, sector)
                continue
            if symbol in KNOWN_INACTIVE:
                logger.info("Skipping %s (%s): %s", symbol, sector, KNOWN_INACTIVE[symbol])
                continue

            entries.append(
                UniverseEntry(
                    symbol=symbol,
                    name=str(row["name"]).strip(),
                    sector=sector.upper(),
                    coverage_tier=coverage_tier(symbol),
                    index_weight=index_weights.get(symbol),
                )
            )

        _reconcile_against_psx_summary(sector, sum(1 for e in entries if e.sector == sector.upper()))

    return entries


def _kse100_weights() -> dict[str, float]:
    """KSE-100 weight per symbol, for annotation. Empty dict if the index fetch fails."""
    import psxdata

    try:
        constituents = psxdata.indices("KSE100")
        known = {str(s).strip().upper() for s in psxdata.symbols()["symbol"]}
        return {
            normalize_symbol(str(row["symbol"]), known): float(row["idx_weight"])
            for _, row in constituents.iterrows()
        }
    except Exception as exc:  # noqa: BLE001 -- annotation only, never worth failing the build
        logger.warning("Could not load KSE-100 weights, leaving them unset: %s", exc)
        return {}


def _reconcile_against_psx_summary(sector: str, counted: int) -> None:
    """Logs a warning when our filtered count disagrees with PSX's own sector summary."""
    import psxdata

    try:
        summary = psxdata.sectors()
        row = summary[summary["sector_name"].astype(str).str.upper() == sector.upper()]
        if row.empty:
            logger.warning("No PSX sector summary row for %s; skipping reconciliation", sector)
            return
        traded = int(row.iloc[0][["advance", "decline", "unchanged"]].fillna(0).sum())
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not reconcile %s against the PSX sector summary: %s", sector, exc)
        return

    if traded != counted:
        logger.warning(
            "%s: built %d companies but PSX's summary shows %d traded this session. "
            "Expected when a name did not trade; investigate if the gap is large or persistent.",
            sector, counted, traded,
        )
    else:
        logger.info("%s: %d companies, reconciles with PSX's sector summary", sector, counted)


def write_snapshot(entries: list[UniverseEntry], path: Path = SNAPSHOT_PATH) -> Path:
    """Freezes the universe to disk.

    v1 runs off this snapshot, not a live symbols() call, so the set of companies the product
    covers does not silently change under users. Re-running this is a deliberate act with a
    reviewable diff.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "sectors": list(SECTORS),
        "as_of": date.today().isoformat(),
        "count": len(entries),
        "tier_counts": tier_counts(entries),
        "sector_counts": {
            sector: sum(1 for e in entries if e.sector == sector) for sector in SECTORS
        },
        "entries": [asdict(e) for e in entries],
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def load_snapshot(path: Path = SNAPSHOT_PATH) -> list[UniverseEntry]:
    """Reads the frozen universe. Raises FileNotFoundError if nobody has built one yet."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [UniverseEntry(**entry) for entry in payload["entries"]]


def tier_counts(entries: list[UniverseEntry]) -> dict[str, int]:
    return {
        tier: sum(1 for e in entries if e.coverage_tier == tier)
        for tier in (TIER_FULL, TIER_UNVERIFIED, TIER_PRICE_ONLY)
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    universe = build_universe()
    destination = write_snapshot(universe)
    counts = tier_counts(universe)
    print(f"\nWrote {len(universe)} companies to {destination}")
    for sector in SECTORS:
        print(f"  {sector:<12} {sum(1 for e in universe if e.sector == sector)}")
    print(f"  full (renderable ratios):  {counts[TIER_FULL]}")
    print(f"  unverified (quarantined):  {counts[TIER_UNVERIFIED]}")
    print(f"  price-only:                {counts[TIER_PRICE_ONLY]}")
