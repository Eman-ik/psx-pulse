"""Quick test of new /api/v1/research routes."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("Testing new /api/v1/research routes...\n")

# Test 1: Universe endpoint
print("1. GET /api/v1/research/universe")
response = client.get("/api/v1/research/universe")
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"   ✓ Returns universe with {data.get('count', 0)} companies")
else:
    print(f"   ✗ Error: {response.text[:200]}")
print()

# Test 2: Company analysis (FFC)
print("2. GET /api/v1/research/FFC/analysis")
response = client.get("/api/v1/research/FFC/analysis")
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"   ✓ Returns analysis for {data.get('ticker', '?')}")
    engines = data.get("intelligence", {})
    engine_names = list(engines.keys())[:5]
    print(f"   ✓ Intelligence engines: {', '.join(engine_names)}")
    if "executive_summary" in data:
        summary = data.get("executive_summary", {})
        print(f"   ✓ Executive summary: {summary.get('business_health', '?')}")
    print(f"   ✓ Confidence score: {data.get('confidence_score', '?')}")
else:
    error_msg = response.text[:300]
    print(f"   ✗ Error: {error_msg}")
print()

# Test 3: Trade check endpoint
print("3. POST /api/v1/research/trade/check")
payload = {
    "ticker": "FFC",
    "entry": 500,
    "stop": 450,
    "targets": [550, 600],
    "portfolio_value": 100000,
    "risk_percent": 1.0,
}
response = client.post("/api/v1/research/trade/check", json=payload)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"   ✓ Trade check for {data.get('ticker', '?')}")
    gates = data.get("gates", [])
    print(f"   ✓ Gates evaluated: {len(gates)}")
    if gates:
        passed = sum(1 for g in gates if g.get("status") == "pass")
        print(f"   ✓ Gates passed: {passed}/{len(gates)}")
else:
    error_msg = response.text[:300]
    print(f"   ✗ Error: {error_msg}")
print()

# Test 4: Technical Screener endpoint
print("4. GET /api/v1/research/screeners/technical")
response = client.get("/api/v1/research/screeners/technical")
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    signals = data.get("signals", [])
    print(f"   ✓ Technical screener returned {len(signals)} signals")
    if signals:
        first = signals[0]
        print(f"   ✓ Example: {first.get('symbol', '?')} (RSI: {first.get('rsi_14', '?')})")
else:
    error_msg = response.text[:300]
    print(f"   ✗ Error: {error_msg}")
print()

# Test 5: Momentum Screener
print("5. GET /api/v1/research/screeners/momentum")
response = client.get("/api/v1/research/screeners/momentum")
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    signals = data.get("signals", [])
    print(f"   ✓ Momentum screener returned {len(signals)} signals")
else:
    error_msg = response.text[:300]
    print(f"   ✗ Error: {error_msg}")
print()

# Test 6: Screening funnel
print("6. GET /api/v1/research/screening/run")
response = client.get("/api/v1/research/screening/run")
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    session = data.get("session", {})
    print(f"   ✓ Screening funnel evaluated {session.get('ticker_count', 0)} companies")
    funnel = data.get("funnel", {})
    if funnel:
        passed_final = funnel.get("screen_4", 0)
        print(f"   ✓ Final stage passed: {passed_final}")
else:
    error_msg = response.text[:300]
    print(f"   ✗ Error: {error_msg}")
print()

print("=" * 70)
print("✓ Route consolidation test complete!")
print("=" * 70)
