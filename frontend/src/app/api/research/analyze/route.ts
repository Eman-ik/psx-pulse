import { NextRequest, NextResponse } from "next/server";
import { fetchEquityResearchReport } from "@/lib/api";

// Relays the real Equity-research pipeline's published report (backend/app/api/
// equity_research.py -> Equity-research's own Postgres DB). This used to call the
// Anthropic API directly with a single-shot prompt asking the model to narrate all
// "18 stages" in one message -- fast and good-looking, but ungrounded: no citations,
// no verification pass, none of the deterministic engines the real 8-agent pipeline
// runs. That duplicated (and disagreed with) the real pipeline instead of using it.
//
// This route now does no LLM work itself. It's honest about coverage: not_covered
// for tickers outside the pipeline's real evidence base, and per-section
// has_real_content flags for a covered ticker whose report isn't fully populated yet.
export async function POST(req: NextRequest) {
  const body = await req.json().catch(() => ({}));
  const { ticker } = body as { ticker?: string };
  if (!ticker?.trim()) {
    return NextResponse.json({ error: "ticker is required" }, { status: 400 });
  }

  const tickerUpper = ticker.trim().toUpperCase();
  const result = await fetchEquityResearchReport(tickerUpper);

  if (!result) {
    return NextResponse.json(
      { error: "Could not reach the research backend." },
      { status: 502 }
    );
  }

  if (result.unavailable) {
    return NextResponse.json(
      { error: result.error ?? "Equity-research database is unavailable." },
      { status: 503 }
    );
  }

  return NextResponse.json({ result });
}
