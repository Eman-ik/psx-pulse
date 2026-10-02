#!/usr/bin/env python
"""Test intelligence engines against real issuer data."""

import sys
import traceback
from app.db.session import SessionLocal
from app.db.models import Issuer, Security, FinancialFact
from sqlalchemy import select

# Get FFC issuer_id
db = SessionLocal()
ffc_security = db.execute(
    select(Security).where(Security.symbol == 'FFC')
).scalar_one_or_none()

if not ffc_security:
    print("FFC not found")
    sys.exit(1)

issuer_id = ffc_security.issuer_id
issuer = db.execute(select(Issuer).where(Issuer.id == issuer_id)).scalar()
print(f"Testing on: {issuer.name} (issuer_id={issuer_id})")

# Check what facts we have
facts = db.execute(
    select(FinancialFact.line_item)
    .where(FinancialFact.issuer_id == issuer_id)
    .distinct()
    .order_by(FinancialFact.line_item)
).scalars().all()

print(f"\nAvailable metrics ({len(facts)} unique):")
for i, fact in enumerate(sorted(facts)):
    print(f"  {fact}")
    if i >= 14:
        print(f"  ... and {len(facts) - 15} more")
        break

# Get period summary
periods = db.execute(
    select(FinancialFact.period_end)
    .where(FinancialFact.issuer_id == issuer_id)
    .distinct()
    .order_by(FinancialFact.period_end.desc())
).scalars().all()

print(f"\nAvailable periods ({len(periods)} total):")
for period in periods[:5]:
    print(f"  {period.isoformat()}")
if len(periods) > 5:
    print(f"  ... and {len(periods) - 5} more")

# Now test Business Health Engine
print("\n" + "="*70)
print("TEST 1: Business Health Engine")
print("="*70)

try:
    from app.analysis.business_health import BusinessHealthEngine
    result = BusinessHealthEngine.analyze(db, issuer_id)

    print(f"Status: {result.get('status', 'UNKNOWN')}")
    print(f"Overall: {result.get('overall', 'N/A')}")
    print(f"\nNarrative:")
    print(result.get('narrative', 'No narrative'))

    print(f"\nComponents:")
    for key, val in result.get('components', {}).items():
        print(f"  {key}: {val}")

    print("\n✅ PASSED")
except Exception as e:
    print(f"❌ FAILED: {e}")
    traceback.print_exc()

# Test What Changed Engine
print("\n" + "="*70)
print("TEST 2: What Changed Engine")
print("="*70)

try:
    from app.analysis.what_changed import WhatChangedEngine
    result = WhatChangedEngine.analyze(db, issuer_id)

    print(f"Status: {result.get('status', 'UNKNOWN')}")
    print(f"Periods: {result.get('periods', {})}")

    print(f"\nPositive changes: {len(result.get('positive_changes', []))}")
    for change in result.get('positive_changes', []):
        print(f"  ✓ {change}")

    print(f"\nNegative changes: {len(result.get('negative_changes', []))}")
    for change in result.get('negative_changes', []):
        print(f"  ✗ {change}")

    print(f"\nInterpretation:")
    print(result.get('interpretation', 'N/A'))

    print("\n✅ PASSED")
except Exception as e:
    print(f"❌ FAILED: {e}")
    traceback.print_exc()

# Test Earnings Quality Engine
print("\n" + "="*70)
print("TEST 3: Earnings Quality Engine")
print("="*70)

try:
    from app.analysis.earnings_quality import EarningsQualityEngine
    result = EarningsQualityEngine.analyze(db, issuer_id)

    print(f"Status: {result.get('status', 'UNKNOWN')}")
    print(f"Quality: {result.get('quality', 'UNKNOWN')}")
    print(f"Score: {result.get('quality_score', 'N/A')}/100")

    print(f"\nIssues: {len(result.get('issues', []))}")
    for issue in result.get('issues', []):
        print(f"  ⚠️  {issue}")

    print(f"\nPositive indicators: {len(result.get('positive_indicators', []))}")
    for indicator in result.get('positive_indicators', []):
        print(f"  ✓ {indicator}")

    print(f"\nNarrative:")
    print(result.get('narrative', 'N/A'))

    print("\n✅ PASSED")
except Exception as e:
    print(f"❌ FAILED: {e}")
    traceback.print_exc()

# Test Bull/Bear Case
print("\n" + "="*70)
print("TEST 4: Bull/Bear Case Engine")
print("="*70)

try:
    from app.analysis.bull_bear_case import BullBearCaseEngine
    result = BullBearCaseEngine.analyze(db, issuer_id)

    print(f"Bull case drivers: {len(result.get('bull_case', {}).get('drivers', []))}")
    for driver in result.get('bull_case', {}).get('drivers', []):
        print(f"  🚀 {driver}")

    print(f"\nBull thesis:")
    print(result.get('bull_case', {}).get('thesis', 'N/A'))

    print(f"\nBear case drivers: {len(result.get('bear_case', {}).get('drivers', []))}")
    for driver in result.get('bear_case', {}).get('drivers', []):
        print(f"  ⚠️  {driver}")

    print(f"\nBear thesis:")
    print(result.get('bear_case', {}).get('thesis', 'N/A'))

    print(f"\nCritical debate:")
    print(result.get('critical_debate', 'N/A'))

    print("\n✅ PASSED")
except Exception as e:
    print(f"❌ FAILED: {e}")
    traceback.print_exc()

# Test Red Flags
print("\n" + "="*70)
print("TEST 5: Red Flags Engine")
print("="*70)

try:
    from app.analysis.red_flags import RedFlagEngine
    result = RedFlagEngine.detect(db, issuer_id)

    print(f"Flags detected: {result.get('flags_detected', 0)}")
    print(f"Recommendation: {result.get('recommendation', 'N/A')}")

    severity = result.get('severity_summary', {})
    print(f"  High: {severity.get('high', 0)}, Medium: {severity.get('medium', 0)}, Low: {severity.get('low', 0)}")

    print(f"\nFlags:")
    for flag in result.get('flags', []):
        print(f"  [{flag.get('severity', 'UNKNOWN').upper()}] {flag.get('title', 'No title')}")
        print(f"    {flag.get('detail', 'No detail')}")

    if not result.get('flags'):
        print("  ✓ No financial red flags detected")

    print("\n✅ PASSED")
except Exception as e:
    print(f"❌ FAILED: {e}")
    traceback.print_exc()

# Test Risk Engine
print("\n" + "="*70)
print("TEST 6: Risk Engine")
print("="*70)

try:
    from app.analysis.risk_engine import RiskEngine
    result = RiskEngine.analyze(db, issuer_id)

    summary = result.get('summary', {})
    print(f"Risk summary: {summary.get('high', 0)} high, {summary.get('medium', 0)} medium, {summary.get('low', 0)} low")
    print(f"Recommendation: {result.get('recommendation', 'N/A')}")

    print(f"\nTop 3 risks:")
    for risk in result.get('high_priority_risks', []):
        print(f"  {risk.get('title', 'No title')}")
        print(f"    Category: {risk.get('category', 'N/A')}")
        print(f"    Probability: {risk.get('probability', 'N/A')}")

    print("\n✅ PASSED")
except Exception as e:
    print(f"❌ FAILED: {e}")
    traceback.print_exc()

# Test Catalyst Engine
print("\n" + "="*70)
print("TEST 7: Catalyst Engine")
print("="*70)

try:
    from app.analysis.catalyst_engine import CatalystEngine
    result = CatalystEngine.analyze(db, issuer_id)

    summary = result.get('summary', {})
    print(f"Catalysts: {summary.get('known_dated', 0)} known+dated, {summary.get('known_undated', 0)} known+undated, "
          f"{summary.get('possible', 0)} possible, {summary.get('speculative', 0)} speculative")

    most_sig = result.get('most_significant')
    if most_sig:
        print(f"\nMost significant: {most_sig.get('event', 'N/A')}")

    print("\n✅ PASSED")
except Exception as e:
    print(f"❌ FAILED: {e}")
    traceback.print_exc()

# Test Valuation Context
print("\n" + "="*70)
print("TEST 8: Valuation Context Engine")
print("="*70)

try:
    from app.analysis.valuation_context import ValuationContextEngine
    result = ValuationContextEngine.analyze(db, issuer_id)

    print(f"Assessment: {result.get('assessment', 'UNKNOWN')}")
    print(f"\nInterpretation:")
    print(result.get('interpretation', 'N/A'))

    multiples = result.get('multiples', {})
    print(f"\nMultiples:")
    print(f"  Current P/E: {multiples.get('current_pe', 'N/A')}")
    print(f"  Historical median P/E: {multiples.get('historical_median_pe', 'N/A')}")
    print(f"  Discount/Premium: {multiples.get('discount_premium_pct', 'N/A'):.1f}%" if multiples.get('discount_premium_pct') else "  Discount/Premium: N/A")

    print("\n✅ PASSED")
except Exception as e:
    print(f"❌ FAILED: {e}")
    traceback.print_exc()

# Test What to Watch
print("\n" + "="*70)
print("TEST 9: What to Watch Engine")
print("="*70)

try:
    from app.analysis.what_to_watch import WhatToWatchEngine
    result = WhatToWatchEngine.analyze(db, issuer_id)

    print(f"Title: {result.get('title', 'N/A')}")

    metrics = result.get('watch_metrics', [])
    print(f"\nWatch metrics: {len(metrics)}")
    for metric in metrics[:5]:
        print(f"  {metric.get('priority', '?')}. {metric.get('metric', 'Unknown')}: {metric.get('current', 'N/A')}")

    invalidation = result.get('thesis_invalidation_triggers', [])
    print(f"\nInvalidation triggers: {len(invalidation)}")
    for trigger in invalidation[:3]:
        print(f"  ⚠️  {trigger}")

    print("\n✅ PASSED")
except Exception as e:
    print(f"❌ FAILED: {e}")
    traceback.print_exc()

print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print("All engines tested against FFC (Fauji Fertilizer)")
print("Check output above for any failures")
db.close()
