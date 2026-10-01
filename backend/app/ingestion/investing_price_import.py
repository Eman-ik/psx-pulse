"""Bulk daily OHLCV import from user-provided investing.com CSV exports.

The user is supplying price history manually for now (see 2026-08-04 scope-expansion decision)
rather than having it scraped, to sidestep both PSX's scrape load and investing.com's own ToS on
automated collection -- a future scraper against investing.com is a separate, later piece of work
and needs the same source_registry.yaml documentation treatment as PSX's own licensing caveat.

Files arrive as "<Company Name> Stock Price History.csv" (investing.com's standard export name),
nested under sector folders, with columns: Date, Price(=close), Open, High, Low, Vol., Change %.
There is no ticker symbol in the file at all -- only a free-text company name -- so each file has
to be fuzzy-matched to an existing Issuer.name before we know which Security it belongs to. A wrong
match would silently attach one company's prices to a different company, which is worse than no
data at all, so this runs in two phases: match_files() (pure, no DB writes, returns match+score for
review) and import_matched() (writes, only call with matches you've actually reviewed).
"""

import csv
import difflib
import logging
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import IngestionRun, Issuer, PriceOHLCV, Security
from app.ingestion.runs import ingestion_run

logger = logging.getLogger(__name__)

_SUFFIX_RE = re.compile(r"stock price history\s*(\(\d+\))?\s*$", re.IGNORECASE)
_CORP_WORDS_RE = re.compile(
    r"\b(limited|ltd|pakistan|company|co|corporation|corp|the|industries|industry)\b",
    re.IGNORECASE,
)
_PUNCT_RE = re.compile(r"[^a-z0-9]+")


def _normalize(name: str) -> str:
    name = _CORP_WORDS_RE.sub(" ", name.lower())
    name = _PUNCT_RE.sub(" ", name)
    return " ".join(name.split())


def _company_name_from_filename(path: Path) -> str:
    stem = path.stem
    stem = _SUFFIX_RE.sub("", stem).strip()
    return stem


@dataclass
class FileMatch:
    path: Path
    file_company_name: str
    issuer_name: str | None
    symbol: str | None
    score: float


# Cases plain text-similarity can't resolve correctly even against the full candidate pool --
# either because the real-world rename/rebrand shares no vocabulary with the old name (Pervez
# Ahmed Securities -> Pervez Ahmed Consultancy Services, confirmed via the company's own PSX
# history: it exited brokerage and rebranded after the 2012 demutualization reforms), or because
# two share classes only differ by a trailing letter that normalization treats as noise (PIA
# Holding's Class A/B). Checked individually against the DB, not guessed.
MANUAL_OVERRIDES: dict[str, str] = {
    "pervez ahmed securities": "PASL",
    "pia holding a": "PIAHCLA",
    "pia holding b": "PIAHCLB",
    # Mari Petroleum Company Limited was renamed Mari Energies Limited in 2024 -- shares no
    # vocabulary with the old name, so text similarity keeps preferring "Pakistan Petroleum"
    # (PPL, a real but different company) over the actual match. Key is post-_normalize() form
    # (corp-suffix words like "Company" are stripped before comparison).
    "mari petroleum": "MARI",
}

# Files with no real counterpart in the seeded universe, or genuinely ambiguous ones where the
# best text match is a data artifact rather than the real company -- checked individually against
# the DB, not guessed. Excluded rather than force-matched:
#  - "Ghani Gases Ltd": no such entity exists among the seeded issuers at all (checked: every
#    "Ghani*" issuer is Chemical/Glass/Dairies/Automobile, none Gases) -- likely never separately
#    PSX-listed, or not present in psxdata's symbol table.
#  - "Waves Singer": best text match is WAVESR1 ("Waves Singer Pakistan Limited (R)"), a stale
#    rights-issue-looking record from the full-market seed, not a real 20-year tradable security --
#    plausibly the historical name of today's Waves Corporation (WAVES) before rebrand, but not
#    confirmed, so left for manual review rather than attaching 20 years of prices to the wrong
#    record either way.
SKIP_FILES: set[str] = {
    "ghani gases",
    "waves singer",
}


def match_files(db: Session, root_dirs: list[Path], min_score: float = 0.55) -> list[FileMatch]:
    """Finds every 'Stock Price History' CSV under root_dirs and proposes an Issuer match.

    Read-only. Deliberately permissive on min_score (0.55) so borderline matches surface for
    human review rather than being silently dropped -- but nothing gets written until
    import_matched() is called with the reviewed subset.

    Matches against ALL issuers, not just currently-active ones: a company that later delisted,
    merged, or went quiet (e.g. First Dawood Investment Bank, Imperial Sugar) still deserves its
    real historical prices attached to the right Issuer, not silently excluded from the candidate
    pool and mismatched onto some unrelated active company as the next-best text match.
    """
    issuers = list(db.execute(select(Issuer).join(Security)).scalars().unique())
    issuer_norms = [(iss, _normalize(iss.name)) for iss in issuers]

    csv_files: list[Path] = []
    for root in root_dirs:
        csv_files.extend(sorted(root.rglob("*Stock Price History*.csv")))

    issuers_by_symbol = {sec.symbol: iss for iss in issuers for sec in iss.securities}

    results: list[FileMatch] = []
    for path in csv_files:
        file_name = _company_name_from_filename(path)
        file_norm = _normalize(file_name)

        if file_norm in SKIP_FILES:
            results.append(FileMatch(path, file_name, None, None, 0.0))
            continue

        if file_norm in MANUAL_OVERRIDES:
            symbol = MANUAL_OVERRIDES[file_norm]
            override_issuer = issuers_by_symbol.get(symbol)
            issuer_name = override_issuer.name if override_issuer else None
            results.append(FileMatch(path, file_name, issuer_name, symbol, 1.0))
            continue

        best_issuer: Issuer | None = None
        best_score = 0.0
        for issuer, issuer_norm in issuer_norms:
            score = difflib.SequenceMatcher(None, file_norm, issuer_norm).ratio()
            if score > best_score:
                best_score = score
                best_issuer = issuer

        if best_issuer is not None and best_score >= min_score:
            symbol = best_issuer.securities[0].symbol if best_issuer.securities else None
            results.append(FileMatch(path, file_name, best_issuer.name, symbol, best_score))
        else:
            results.append(FileMatch(path, file_name, None, None, best_score))

    return results


def _parse_volume(raw: str) -> int | None:
    raw = raw.strip()
    if not raw or raw == "-":
        return None
    multiplier = 1
    if raw[-1] in ("K", "k"):
        multiplier = 1_000
        raw = raw[:-1]
    elif raw[-1] in ("M", "m"):
        multiplier = 1_000_000
        raw = raw[:-1]
    elif raw[-1] in ("B", "b"):
        multiplier = 1_000_000_000
        raw = raw[:-1]
    try:
        return int(float(raw.replace(",", "")) * multiplier)
    except ValueError:
        return None


def _parse_row(row: dict[str, str]) -> dict | None:
    try:
        trade_date = datetime.strptime(row["Date"].strip(), "%m/%d/%Y").date()
        open_ = float(row["Open"].replace(",", ""))
        high = float(row["High"].replace(",", ""))
        low = float(row["Low"].replace(",", ""))
        close = float(row["Price"].replace(",", ""))
    except (KeyError, ValueError) as exc:
        logger.warning("Unparseable row %s: %s", row, exc)
        return None

    # Same spirit as psxdata's own OHLC-constraint flagging in psx_prices.py -- better a gap
    # than a silently wrong bar.
    if not (low <= open_ <= high and low <= close <= high and low <= high):
        return None

    return {
        "trade_date": trade_date,
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": _parse_volume(row.get("Vol.", "")),
    }


def import_one_file(db: Session, path: Path, security: Security, run: IngestionRun) -> dict[str, int]:
    """Idempotent: only inserts dates not already present for this security."""
    with open(path, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    existing_dates = set(
        db.execute(select(PriceOHLCV.trade_date).where(PriceOHLCV.security_id == security.id)).scalars().all()
    )

    inserted = skipped_existing = skipped_bad_row = 0
    for raw_row in rows:
        parsed = _parse_row(raw_row)
        if parsed is None:
            skipped_bad_row += 1
            continue
        if parsed["trade_date"] in existing_dates:
            skipped_existing += 1
            continue
        db.add(
            PriceOHLCV(
                security_id=security.id,
                trade_date=parsed["trade_date"],
                open=parsed["open"],
                high=parsed["high"],
                low=parsed["low"],
                close=parsed["close"],
                volume=parsed["volume"],
                adjusted=False,
                is_delayed=True,
                source="investing_csv",
                ingestion_run_id=run.id,
            )
        )
        existing_dates.add(parsed["trade_date"])
        inserted += 1

    if skipped_bad_row:
        run.add_error(f"{security.symbol}: {skipped_bad_row} unparseable or OHLC-inconsistent rows skipped in {path.name}")
    run.rows_inserted += inserted
    db.commit()
    return {
        "inserted": inserted,
        "skipped_existing": skipped_existing,
        "skipped_bad_row": skipped_bad_row,
        "fetched": len(rows),
    }


def import_matched(db: Session, matches: list[FileMatch]) -> dict[str, dict]:
    """Imports only matches that already have a resolved symbol -- call after reviewing
    match_files()'s output, not directly on its raw result."""
    results: dict[str, dict] = {}
    matched = [m for m in matches if m.symbol]
    with ingestion_run(
        db, "investing_csv", table="price_ohlcv", files={m.symbol: str(m.path) for m in matched}
    ) as run:
        for m in matched:
            security = db.execute(select(Security).where(Security.symbol == m.symbol)).scalar_one_or_none()
            if security is None:
                results[m.symbol] = {"error": "security not found"}
                run.add_error(f"{m.symbol}: security not found, {m.path.name} not imported")
                continue
            stats = import_one_file(db, m.path, security, run)
            results[m.symbol] = stats
            logger.info("Imported %s from %s: %s", m.symbol, m.path.name, stats)
    return results


if __name__ == "__main__":
    import sys

    from app.db.session import SessionLocal

    logging.basicConfig(level=logging.INFO)

    args = sys.argv[1:]
    write = "--write" in args
    roots = [Path(p) for p in args if p != "--write"]
    if not roots:
        print("Usage: python -m app.ingestion.investing_price_import <root_dir> [<root_dir> ...] [--write]")
        sys.exit(1)

    with SessionLocal() as session:
        matches = match_files(session, roots)
        matched = [m for m in matches if m.symbol]
        unmatched = [m for m in matches if not m.symbol]

        print(f"\n{len(matched)} matched, {len(unmatched)} unmatched (of {len(matches)} files)\n")
        print("=== MATCHED ===")
        for m in matched:
            print(f"  [{m.score:.2f}] {m.file_company_name!r} -> {m.symbol} ({m.issuer_name})")
        print("\n=== UNMATCHED (skipped) ===")
        for m in unmatched:
            print(f"  [{m.score:.2f}] {m.file_company_name!r} -> no confident match")

        if write:
            print("\n=== IMPORTING ===")
            results = import_matched(session, matched)
            total_inserted = sum(r.get("inserted", 0) for r in results.values())
            total_skipped = sum(r.get("skipped_existing", 0) for r in results.values())
            total_bad = sum(r.get("skipped_bad_row", 0) for r in results.values())
            print(f"\n{total_inserted} bars inserted, {total_skipped} already present, {total_bad} bad rows skipped, across {len(results)} securities")
        else:
            print("\n(dry run -- pass --write to actually import)")
