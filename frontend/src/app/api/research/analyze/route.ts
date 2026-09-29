import { NextRequest, NextResponse } from 'next/server';

const BACKEND_TIMEOUT = 5000; // 5 second timeout

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { ticker } = body;

    if (!ticker) {
      return NextResponse.json(
        { error: 'Ticker is required' },
        { status: 400 }
      );
    }

    // Fetch reports for the ticker from equity-research API with timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), BACKEND_TIMEOUT);

    try {
      const reportsResponse = await fetch('http://localhost:8000/api/reports', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!reportsResponse.ok) {
        return NextResponse.json({
          result: {
            ticker,
            reports: [],
            message: `No published reports available for ${ticker}. Use the Trade Planning tool to analyze this stock with our position sizing and decision gates.`,
          }
        });
      }

      const allReports = await reportsResponse.json();

      // Filter reports for this ticker
      const tickerReports = allReports.filter(
        (r: any) => r.ticker && r.ticker.toUpperCase() === ticker.toUpperCase()
      );

      if (tickerReports.length === 0) {
        return NextResponse.json({
          result: {
            ticker,
            reports: [],
            message: `No published reports available for ${ticker}. Use the Trade Planning tool to analyze this stock with our position sizing and decision gates.`,
          }
        });
      }

      // Return the latest report
      const latestReport = tickerReports.sort(
        (a: any, b: any) => new Date(b.published_at).getTime() - new Date(a.published_at).getTime()
      )[0];

      return NextResponse.json({
        result: {
          ticker,
          report: latestReport,
          reports: tickerReports,
        }
      });
    } catch (fetchError: any) {
      clearTimeout(timeoutId);

      // Backend timeout or unreachable
      return NextResponse.json({
        result: {
          ticker,
          reports: [],
          message: `Research backend is not available. Use the Trade Planning tool to analyze ${ticker} with our position sizing and decision gates.`,
        }
      });
    }
  } catch (error) {
    console.error('Research analyze error:', error);
    return NextResponse.json(
      { error: 'Could not process request.' },
      { status: 500 }
    );
  }
}
