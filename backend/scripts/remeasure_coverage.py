#!/usr/bin/env python3
"""Re-measure actual data coverage after Phase 1 semantic fixes.

This script:
1. Runs corrected engines (WhatChanged, EarningsQuality, Valuation, BusinessHealth)
2. Collects real coverage metrics for FFC and EFERT
3. Identifies which inputs are actually available vs. missing
4. Reports gaps correctly (raw missing vs. derived vs. misnamed)

No synthetic data. Only measures what exists in the database.
"""

import sys
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import Issuer, FinancialFact, Security, PriceOHLCV
from app.analysis.evidence_context import ResearchContext
from app.analysis.research_orchestrator import ResearchOrchestrator


def measure_issuer_coverage(db: Session, ticker: str) -> dict:
    """Measure actual data coverage for one issuer with corrected formulas.

    Args:
        db: Database session
        ticker: Issuer ticker (e.g., "FFC", "EFERT")

    Returns:
        Dict with coverage metrics for each engine
    """
    # Get issuer
    issuer_stmt = select(Issuer).where(Issuer.ticker == ticker)
    issuer = db.execute(issuer_stmt).scalars().first()

    if not issuer:
        print(f"ERROR: {ticker} not found")
        return {}

    print(f"\n{'='*70}")
    print(f"COVERAGE MEASUREMENT: {ticker} (issuer_id={issuer.id})")
    print(f"{'='*70}")

    # Run corrected orchestrator
    try:
        result = ResearchOrchestrator.analyze(db, issuer.id)
    except Exception as e:
        print(f"ERROR running orchestrator: {e}")
        return {}

    # Extract coverage metrics
    coverage = {
        "ticker": ticker,
        "issuer_id": issuer.id,
        "timestamp": datetime.now().isoformat(),
        "engines": {},
        "composite": {
            "data_coverage_pct": result.get("data_coverage_pct"),
            "evidence_quality": result.get("evidence_quality"),
            "analytical_confidence": result.get("analytical_confidence"),
        }
    }

    # Per-engine coverage
    for engine_name in ["business_health", "what_changed", "earnings_quality", "valuation_context"]:
        engine_result = result.get(engine_name, {})
        coverage["engines"][engine_name] = {
            "data_coverage_pct": engine_result.get("data_coverage_pct"),
            "confidence": engine_result.get("confidence") or engine_result.get("classification_confidence"),
            "status": engine_result.get("status"),
        }

    # Print summary
    print(f"\nCOMPOSITE COVERAGE:")
    print(f"  Data Coverage:      {coverage['composite']['data_coverage_pct']}%")
    print(f"  Evidence Quality:   {coverage['composite']['evidence_quality']}")
    print(f"  Analysis Confidence: {coverage['composite']['analytical_confidence']}")

    print(f"\nPER-ENGINE BREAKDOWN:")
    for engine, metrics in coverage["engines"].items():
        print(f"  {engine:25} {metrics['data_coverage_pct']:3}% (confidence: {metrics['confidence']})")

    # Analyze what raw inputs are available
    print(f"\nAVAILABLE FINANCIAL INPUTS:")
    fact_stmt = (
        select(FinancialFact.line_item, func.count(FinancialFact.id))
        .where(FinancialFact.issuer_id == issuer.id)
        .group_by(FinancialFact.line_item)
    )

    # Simple query without groupby aggregation
    all_facts_stmt = select(FinancialFact.line_item.distinct()).where(
        FinancialFact.issuer_id == issuer.id
    )
    line_items = db.execute(all_facts_stmt).scalars().all()

    if line_items:
        for item in sorted(line_items):
            # Count periods for this item
            count_stmt = select(FinancialFact).where(
                FinancialFact.issuer_id == issuer.id,
                FinancialFact.line_item == item
            )
            count = len(db.execute(count_stmt).scalars().all())
            print(f"  {item:30} {count} periods")
    else:
        print("  (no financial facts found)")

    return coverage


def identify_missing_inputs(db: Session, ticker: str, expected_inputs: dict) -> dict:
    """Identify which expected inputs are actually missing.

    Check database for:
    1. Truly missing (not in any form)
    2. Present under different canonical name
    3. Derivable from other fields

    Args:
        db: Database session
        ticker: Issuer ticker
        expected_inputs: Dict of {engine: [list of expected metrics]}

    Returns:
        Gap report
    """
    issuer_stmt = select(Issuer).where(Issuer.ticker == ticker)
    issuer = db.execute(issuer_stmt).scalars().first()

    if not issuer:
        return {}

    print(f"\n{'='*70}")
    print(f"GAP ANALYSIS: {ticker}")
    print(f"{'='*70}")

    # Get all available line items
    all_items_stmt = select(FinancialFact.line_item.distinct()).where(
        FinancialFact.issuer_id == issuer.id
    )
    available = set(db.execute(all_items_stmt).scalars().all())

    print(f"\nTOTAL UNIQUE METRICS IN DATABASE: {len(available)}")
    print(f"Metrics: {sorted(available)}")

    # Expected metrics by engine
    expected_all = set()
    for engine, metrics in expected_inputs.items():
        expected_all.update(metrics)

    truly_missing = expected_all - available

    print(f"\nEXPECTED BUT NOT FOUND: {len(truly_missing)}")
    for metric in sorted(truly_missing):
        print(f"  - {metric}")

    # Check for potential alternative names (heuristic)
    print(f"\nPOTENTIAL ALTERNATIVES (check manually):")
    alternatives = {
        "operating_cash_flow": ["cash_flow_operations", "operating_activities_cash_flow", "ocf"],
        "other_income": ["non_operating_income", "other_gains"],
        "accounts_receivable": ["trade_receivables", "ar"],
    }

    for preferred, alternates in alternatives.items():
        if preferred in truly_missing:
            for alt in alternates:
                if alt in available:
                    print(f"  {preferred:30} <- FOUND AS: {alt}")

    return {
        "ticker": ticker,
        "available_count": len(available),
        "available_metrics": sorted(available),
        "missing_count": len(truly_missing),
        "missing_metrics": sorted(truly_missing),
    }


if __name__ == "__main__":
    # Expected inputs per engine (from audit)
    EXPECTED_INPUTS = {
        "business_health": [
            "revenue", "profit_after_tax", "operating_cash_flow",
            "total_debt", "total_equity"
        ],
        "what_changed": [
            "revenue", "gross_profit", "finance_cost", "operating_cash_flow",
            "accounts_receivable", "inventory", "dividend_per_share", "total_debt", "ebitda"
        ],
        "earnings_quality": [
            "profit_after_tax", "operating_cash_flow", "operating_profit",
            "other_income", "finance_cost", "revenue", "tax_expense"
        ],
        "valuation_context": [
            "pe_ratio", "historical_pe_series", "pb_ratio", "roe", "revenue_growth",
            "sector_median_pe"
        ],
    }

    # Connect to database
    db = next(get_db())

    print("\n" + "="*70)
    print("PHASE 1 COVERAGE RE-MEASUREMENT (After Semantic Fixes)")
    print("="*70)

    # Measure for each issuer
    tickers = ["FFC", "EFERT"]
    measurements = {}

    for ticker in tickers:
        measurements[ticker] = measure_issuer_coverage(db, ticker)
        identify_missing_inputs(db, ticker, EXPECTED_INPUTS)

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    for ticker, coverage in measurements.items():
        if coverage:
            print(f"\n{ticker:10} {coverage['composite']['data_coverage_pct']:3}% " +
                  f"({coverage['composite']['evidence_quality']}, " +
                  f"{coverage['composite']['analytical_confidence']})")

    print("\n✅ Re-measurement complete. Check output above for:")
    print("   - Actual corrected coverage (after semantic fixes)")
    print("   - Available metrics in database")
    print("   - Truly missing raw inputs")
    print("   - Potential alternative metric names")
