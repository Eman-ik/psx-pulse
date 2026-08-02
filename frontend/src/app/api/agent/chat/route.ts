import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    return NextResponse.json(
      { error: 'ANTHROPIC_API_KEY is not set. Add it to frontend/.env.local to enable the AI agent.' },
      { status: 503 }
    );
  }

  let body: { messages?: unknown[]; systemPrompt?: string };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body' }, { status: 400 });
  }

  const { messages = [], systemPrompt } = body;

  const system = systemPrompt ?? `You are PSX QuantAgent, an AI research assistant specializing in the Pakistan Stock Exchange (PSX) fertilizer sector. Your pilot universe is: FFC (Fauji Fertilizer Company), EFERT (Engro Fertilizer — listed entity), FATIMA (Fatima Fertilizer), AGL (Agritech Limited), AHCL (Al-Hamd Chemical). You provide analysis grounded in Pakistani agricultural economics, SBP monetary policy, gas feedstock pricing, and PSX regulatory filings. Be concise, data-oriented, and always note when you are reasoning rather than citing a live source. Never fabricate specific prices, EPS figures, or dividend announcements.`;

  const response = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': apiKey,
      'anthropic-version': '2023-06-01',
    },
    body: JSON.stringify({
      model: 'claude-haiku-4-5-20251001',
      max_tokens: 1024,
      system,
      messages,
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
  const text: string = data?.content?.[0]?.text ?? '';

  return NextResponse.json({ text });
}
