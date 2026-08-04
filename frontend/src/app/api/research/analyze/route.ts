import { NextRequest, NextResponse } from "next/server";
import { fetchCompanies, fetchCompanyOverview, fetchComparison } from "@/lib/api";

const EQUITY_RESEARCH_SYSTEM = `You are PSX QuantResearch, an institutional equity research analyst specialising in Pakistan Stock Exchange listed companies with deep expertise in the fertilizer sector (FFC, EFERT, FATIMA, AGL, AHCL).

You run initiations of coverage the way a disciplined sell-side analyst at a tier-1 house would: evidence-first, numbers reconciled, no vibe, no hype.

Core discipline:
- Separate "Is the business genuinely healthy?" from "Is the stock attractively priced?"
- Label every material claim: verified fact / management claim / model-derived / analyst judgment / assumption / missing evidence
- Work to profit attributable to parent owners, not headline consolidated
- Give a fair-value RANGE, never a single number
- Every thesis pillar needs a measurable falsifier

Fertilizer sector engine: Revenue = Production × Offtake × Retention price. Key drivers: gas feedstock (SSGC/Mari vs RLNG/SNGPL), urea offtake, retention price, GIDC liability, subsidy receivables, DAP import FX.

You will be given real data from our research DB. Use it as your primary source. Fill gaps with your knowledge, labeled as analyst judgment or assumption.

CRITICAL: You must return ONLY valid JSON matching the exact schema specified. No markdown, no explanation outside the JSON object.`;

function buildContext(overview: Awaited<ReturnType<typeof fetchCompanyOverview>>, compRow: { market_cap: number | null; pe_ratio: number | null; dividend_yield: number | null; roe: number | null; debt_to_equity: number | null } | undefined): string {
  if (!overview) return "";
  const { issuer, live_quote, financials, ratios, payouts, board, subsidiaries, announcements, thesis, free_float_pct, beta } = overview;

  const lines: string[] = [
    `COMPANY: ${issuer.name} (${overview.symbol ?? "N/A"})`,
    `SECTOR ID: ${issuer.sector_id ?? "N/A"} | AUDITOR: ${issuer.auditor ?? "N/A"}`,
    `FREE FLOAT: ${free_float_pct ?? "N/A"}% | BETA: ${beta?.value ?? "N/A"}`,
    `DESCRIPTION: ${issuer.business_description ?? "N/A"}`,
    "",
    "=== LIVE QUOTE ===",
    live_quote ? JSON.stringify(live_quote, null, 2) : "No live quote",
    "",
    "=== MARKET DATA (comparison endpoint) ===",
    compRow ? JSON.stringify(compRow, null, 2) : "Not available",
    "",
    "=== BOARD OF DIRECTORS ===",
    board.length ? board.map(b => `${b.role}: ${b.full_name}`).join("\n") : "Not available",
    "",
    "=== SUBSIDIARIES ===",
    subsidiaries.length ? subsidiaries.map(s => s.name).join(", ") : "None listed",
    "",
    "=== FINANCIAL FACTS (all periods) ===",
  ];

  for (const [metric, points] of Object.entries(financials)) {
    if (points.length > 0) {
      const vals = points
        .sort((a, b) => a.period_end.localeCompare(b.period_end))
        .map(p => `${p.period_end}(${p.period_type}): ${p.value.toLocaleString()} ${p.unit}`)
        .join(" | ");
      lines.push(`${metric}: ${vals}`);
    }
  }

  lines.push("", "=== FINANCIAL RATIOS ===");
  for (const [name, series] of Object.entries(ratios)) {
    if (series.values.length > 0) {
      const vals = series.values
        .sort((a, b) => a.period_end.localeCompare(b.period_end))
        .map(v => `${v.period_end}: ${v.value}`)
        .join(" | ");
      lines.push(`${name} (${series.unit}): ${vals}`);
    }
  }

  lines.push("", "=== DIVIDEND / PAYOUT HISTORY ===");
  lines.push(payouts.length
    ? payouts.slice(-10).map(p => `${p.effective_date} ${p.action_type}: ${p.ratio_or_amount ?? "N/A"}`).join("\n")
    : "None available");

  lines.push("", "=== RECENT PSX ANNOUNCEMENTS ===");
  lines.push(announcements.length
    ? announcements.slice(-15).map(a =>
        `[${a.published_at.slice(0, 10)}] [${a.category}] ${a.title} | sentiment: ${a.sentiment_score ?? "N/A"}`
      ).join("\n")
    : "None available");

  if (thesis) {
    lines.push("", "=== EXISTING THESIS (pre-populated) ===");
    lines.push(`Bull: ${thesis.bull_case}`);
    lines.push(`Base: ${thesis.base_case}`);
    lines.push(`Bear: ${thesis.bear_case}`);
    lines.push(`Catalysts: ${thesis.key_catalysts.join("; ")}`);
    lines.push(`Risks: ${thesis.key_risks.join("; ")}`);
  }

  return lines.join("\n");
}

const JSON_SCHEMA = `{
  "ticker": "string",
  "fullName": "string",
  "exchange": "PSX",
  "analysisDate": "string (today YYYY-MM-DD)",
  "finalPosture": "BUY | HOLD | AVOID | WATCHLIST | PRELIMINARY",
  "companyHealthScore": "number 0-100",
  "stockAttractivenessScore": "number 0-100",
  "evidenceConfidence": "High | Medium | Low",
  "executiveSummary": "string (3-5 sentences)",
  "variantPerception": "string (what market believes vs your differentiated view)",
  "kpis": {
    "priceLabel": "string e.g. PKR 565",
    "marketCapLabel": "string e.g. PKR 813bn",
    "peLabel": "string e.g. 9.2x",
    "forwardPeLabel": "string e.g. 7.0x",
    "dividendYieldLabel": "string e.g. 6.5%",
    "roicLabel": "string e.g. 39.9%",
    "netCashLabel": "string e.g. PKR 128bn",
    "epsLabel": "string e.g. PKR 58.44",
    "pbLabel": "string e.g. 2.9x",
    "evEbitdaLabel": "string e.g. 5.1x",
    "peValue": "number or null",
    "dividendYieldValue": "number or null",
    "roicValue": "number or null"
  },
  "historicalFinancials": [
    {
      "year": "string e.g. FY2021",
      "revenueMn": "number PKR millions",
      "netIncomeMn": "number PKR millions",
      "eps": "number PKR",
      "fcfMn": "number PKR millions or null",
      "grossMarginPct": "number percent",
      "netMarginPct": "number percent",
      "ocfNiRatioPct": "number percent or null"
    }
  ],
  "forecast": [
    {
      "year": "string e.g. FY2026E",
      "revenueMn": "number",
      "netIncomeMn": "number",
      "eps": "number",
      "dps": "number",
      "fcfMn": "number"
    }
  ],
  "fairValueRange": {
    "bear": "number PKR",
    "base": "number PKR",
    "bull": "number PKR",
    "currentPrice": "number PKR"
  },
  "scenarios": [
    {
      "case": "Bull | Base | Bear | Stress",
      "centralAssumption": "string",
      "targetPrice": "number PKR",
      "totalReturnLabel": "string e.g. +46%",
      "eps": "number PKR",
      "probability": "number percent 0-100"
    }
  ],
  "thesisPillars": [
    {
      "pillar": "string short name",
      "detail": "string 1-2 sentences",
      "falsifier": "string specific measurable trigger"
    }
  ],
  "topRisks": [
    {
      "risk": "string",
      "severity": "Low | Medium | High | Critical",
      "detail": "string"
    }
  ],
  "catalysts": [
    {
      "catalyst": "string",
      "timing": "string e.g. Q4 2026",
      "impact": "Positive | Negative | Binary"
    }
  ],
  "monitoringKPIs": [
    {
      "kpi": "string",
      "current": "string",
      "confirms": "string threshold",
      "breaks": "string threshold"
    }
  ],
  "ownership": {
    "sponsor": "number percent",
    "publicFloat": "number percent",
    "institutional": "number percent",
    "foreign": "number percent"
  },
  "sectorDrivers": [
    {
      "driver": "string",
      "status": "positive | neutral | negative | risk",
      "detail": "string"
    }
  ],
  "managementVerdict": "string 1-2 sentences",
  "capitalAllocationVerdict": "string 1-2 sentences",
  "forensicSummary": "string 1-2 sentences on earnings quality",
  "dataWarnings": ["string array of missing evidence flags"]
}`;

export async function POST(req: NextRequest) {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    return NextResponse.json(
      { error: "ANTHROPIC_API_KEY not set. Add it to frontend/.env.local to enable research." },
      { status: 503 }
    );
  }

  const body = await req.json().catch(() => ({}));
  const { ticker } = body as { ticker?: string };
  if (!ticker?.trim()) {
    return NextResponse.json({ error: "ticker is required" }, { status: 400 });
  }

  const tickerUpper = ticker.trim().toUpperCase();

  // Resolve issuer_id from ticker
  const companies = await fetchCompanies();
  const company = companies.find(
    c => c.symbol?.toUpperCase() === tickerUpper || c.name.toUpperCase().includes(tickerUpper)
  );

  let overview = null;
  let compRow = undefined;

  if (company) {
    const [ov, comparison] = await Promise.all([
      fetchCompanyOverview(company.id),
      fetchComparison(),
    ]);
    overview = ov;
    compRow = comparison.find(r => r.symbol?.toUpperCase() === tickerUpper);
  }

  const context = overview ? buildContext(overview, compRow) : `No DB data found for ${tickerUpper}. Use your knowledge, labeled as analyst judgment.`;

  const userMessage = `Run a full institutional equity research initiation of coverage on ${tickerUpper}.

REAL-TIME DATA FROM RESEARCH DB (use as primary source; label gaps as analyst judgment):
${context}

Analysis date: ${new Date().toISOString().slice(0, 10)}
Mandate: Long-only, 3–5 year fundamental underwrite, 12-month valuation-and-catalyst horizon.

Work all 18 stages of the equity research workflow (mandate → evidence → corporate identity → management → subsidiaries → business model → industry → financial reconstruction → health → forensics → capital allocation → forecast → macro factors → market expectations → valuation → scenarios → thesis → scoring).

Return ONLY a single valid JSON object matching this exact schema. No markdown, no preamble, no trailing text:

${JSON_SCHEMA}

Rules:
- historicalFinancials: 4-6 years of actuals (most recent first is fine, or chronological)
- forecast: 3-4 years forward
- scenarios: exactly 4 (Bull, Base, Bear, Stress)
- thesisPillars: 3-5 pillars each with a measurable falsifier
- monitoringKPIs: 5-8 KPIs
- topRisks: 4-6 risks
- catalysts: 3-5 catalysts
- sectorDrivers: 4-6 drivers
- All PKR values in millions unless labelled
- companyHealthScore and stockAttractivenessScore must be 0-100 integers
- finalPosture must be exactly one of: BUY, HOLD, AVOID, WATCHLIST, PRELIMINARY`;

  const response = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": apiKey,
      "anthropic-version": "2023-06-01",
    },
    body: JSON.stringify({
      model: process.env.RESEARCH_MODEL ?? "claude-opus-5",
      max_tokens: 8192,
      system: EQUITY_RESEARCH_SYSTEM,
      messages: [{ role: "user", content: userMessage }],
    }),
  });

  if (!response.ok) {
    const err = await response.text();
    return NextResponse.json(
      { error: `Anthropic API error ${response.status}: ${err}` },
      { status: response.status }
    );
  }

  const data = await response.json();
  const raw: string = data?.content?.[0]?.text ?? "";

  // Extract JSON from the response (strip any accidental markdown fences)
  const jsonMatch = raw.match(/\{[\s\S]*\}/);
  if (!jsonMatch) {
    return NextResponse.json({ error: "Model did not return valid JSON", raw }, { status: 502 });
  }

  try {
    const report = JSON.parse(jsonMatch[0]);
    return NextResponse.json({ report });
  } catch (e) {
    return NextResponse.json({ error: "JSON parse failed", raw }, { status: 502 });
  }
}
