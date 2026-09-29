import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    // Forward to equity-research API
    const response = await fetch('http://localhost:8000/api/research/analyze', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const error = await response.text();
      return NextResponse.json(
        { error: `Research API error: ${error}` },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json({ result: data });
  } catch (error) {
    console.error('Research analyze error:', error);
    return NextResponse.json(
      { error: 'Could not reach the research backend.' },
      { status: 500 }
    );
  }
}
