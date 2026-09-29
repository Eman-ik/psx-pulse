import { NextRequest, NextResponse } from 'next/server';

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

    // Fetch reports for the ticker from equity-research API
    const reportsResponse = await fetch('http://localhost:8000/api/reports', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!reportsResponse.ok) {
      return NextResponse.json(
        { error: 'Could not fetch reports from research backend' },
        { status: reportsResponse.status }
      );
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
          message: `No published reports available for ${ticker}. Research data will be generated on demand.`,
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
  } catch (error) {
    console.error('Research analyze error:', error);
    return NextResponse.json(
      { error: 'Could not reach the research backend.' },
      { status: 500 }
    );
  }
}
