import type { PriceBar } from "./api";

/**
 * Technical indicator math for the company Technicals tab. Every indicator is computed
 * only when there are enough bars for its window; otherwise it reports `available: false`
 * with the bars it has vs needs, rather than silently truncating the window or fabricating
 * a value from too little history (see project working-style rule: suppress, don't fake).
 */

export interface IndicatorPoint {
  date: string;
  value: number;
}

export interface IndicatorResult {
  available: boolean;
  requiredBars: number;
  availableBars: number;
  latest: number | null;
  series: IndicatorPoint[];
}

function insufficient(requiredBars: number, availableBars: number): IndicatorResult {
  return { available: false, requiredBars, availableBars, latest: null, series: [] };
}

function smaSeries(closes: number[], dates: string[], period: number): IndicatorResult {
  if (closes.length < period) return insufficient(period, closes.length);
  const series: IndicatorPoint[] = [];
  let sum = 0;
  for (let i = 0; i < closes.length; i++) {
    sum += closes[i];
    if (i >= period) sum -= closes[i - period];
    if (i >= period - 1) series.push({ date: dates[i], value: sum / period });
  }
  return { available: true, requiredBars: period, availableBars: closes.length, latest: series[series.length - 1].value, series };
}

function emaSeriesFrom(closes: number[], dates: string[], period: number, seedIndex: number): IndicatorPoint[] {
  const k = 2 / (period + 1);
  const series: IndicatorPoint[] = [];
  let seed = 0;
  for (let i = 0; i <= seedIndex; i++) seed += closes[i];
  let prevEma = seed / (seedIndex + 1);
  series.push({ date: dates[seedIndex], value: prevEma });
  for (let i = seedIndex + 1; i < closes.length; i++) {
    prevEma = closes[i] * k + prevEma * (1 - k);
    series.push({ date: dates[i], value: prevEma });
  }
  return series;
}

function emaSeries(closes: number[], dates: string[], period: number): IndicatorResult {
  if (closes.length < period) return insufficient(period, closes.length);
  const series = emaSeriesFrom(closes, dates, period, period - 1);
  return { available: true, requiredBars: period, availableBars: closes.length, latest: series[series.length - 1].value, series };
}

function rsi14(closes: number[], dates: string[]): IndicatorResult {
  const period = 14;
  if (closes.length < period + 1) return insufficient(period + 1, closes.length);

  const series: IndicatorPoint[] = [];
  let avgGain = 0;
  let avgLoss = 0;
  for (let i = 1; i <= period; i++) {
    const change = closes[i] - closes[i - 1];
    if (change >= 0) avgGain += change;
    else avgLoss -= change;
  }
  avgGain /= period;
  avgLoss /= period;
  const pushRsi = (idx: number, gain: number, loss: number) => {
    const rs = loss === 0 ? 100 : gain / loss;
    const value = loss === 0 ? 100 : 100 - 100 / (1 + rs);
    series.push({ date: dates[idx], value });
  };
  pushRsi(period, avgGain, avgLoss);

  for (let i = period + 1; i < closes.length; i++) {
    const change = closes[i] - closes[i - 1];
    const gain = change > 0 ? change : 0;
    const loss = change < 0 ? -change : 0;
    avgGain = (avgGain * (period - 1) + gain) / period;
    avgLoss = (avgLoss * (period - 1) + loss) / period;
    pushRsi(i, avgGain, avgLoss);
  }
  return { available: true, requiredBars: period + 1, availableBars: closes.length, latest: series[series.length - 1].value, series };
}

export interface MacdResult {
  available: boolean;
  requiredBars: number;
  availableBars: number;
  latest: { macd: number; signal: number; histogram: number } | null;
  series: { date: string; macd: number; signal: number; histogram: number }[];
}

function macd(closes: number[], dates: string[]): MacdResult {
  const required = 26 + 9; // slow EMA warmup + signal-line smoothing
  if (closes.length < required) {
    return { available: false, requiredBars: required, availableBars: closes.length, latest: null, series: [] };
  }
  const ema12 = emaSeriesFrom(closes, dates, 12, 11);
  const ema26 = emaSeriesFrom(closes, dates, 26, 25);
  // ema12[k] represents original index 11+k; ema26[j] represents original index 25+j.
  // To line up the same original index: 11+k = 25+j => k = j + 14.
  const alignOffset = 25 - 11;
  const macdLineCloses: number[] = [];
  const macdDates: string[] = [];
  for (let j = 0; j < ema26.length; j++) {
    macdLineCloses.push(ema12[j + alignOffset].value - ema26[j].value);
    macdDates.push(ema26[j].date);
  }
  if (macdLineCloses.length < 9) {
    return { available: false, requiredBars: required, availableBars: closes.length, latest: null, series: [] };
  }
  const signalSeries = emaSeriesFrom(macdLineCloses, macdDates, 9, 8);
  const signalOffset = macdLineCloses.length - signalSeries.length;
  const series = signalSeries.map((s, i) => {
    const macdValue = macdLineCloses[i + signalOffset];
    return { date: s.date, macd: macdValue, signal: s.value, histogram: macdValue - s.value };
  });
  return {
    available: true,
    requiredBars: required,
    availableBars: closes.length,
    latest: series[series.length - 1],
    series,
  };
}

export interface BollingerResult {
  available: boolean;
  requiredBars: number;
  availableBars: number;
  latest: { middle: number; upper: number; lower: number } | null;
  series: { date: string; middle: number; upper: number; lower: number }[];
}

function bollinger(closes: number[], dates: string[], period = 20, stdDevMult = 2): BollingerResult {
  if (closes.length < period) return { available: false, requiredBars: period, availableBars: closes.length, latest: null, series: [] };
  const series: { date: string; middle: number; upper: number; lower: number }[] = [];
  for (let i = period - 1; i < closes.length; i++) {
    const window = closes.slice(i - period + 1, i + 1);
    const mean = window.reduce((a, b) => a + b, 0) / period;
    const variance = window.reduce((a, b) => a + (b - mean) ** 2, 0) / period;
    const stdDev = Math.sqrt(variance);
    series.push({ date: dates[i], middle: mean, upper: mean + stdDevMult * stdDev, lower: mean - stdDevMult * stdDev });
  }
  return { available: true, requiredBars: period, availableBars: closes.length, latest: series[series.length - 1], series };
}

function atr14(bars: PriceBar[]): IndicatorResult {
  const period = 14;
  if (bars.length < period + 1) return insufficient(period + 1, bars.length);
  const trueRanges: number[] = [];
  for (let i = 1; i < bars.length; i++) {
    const highLow = bars[i].high - bars[i].low;
    const highClose = Math.abs(bars[i].high - bars[i - 1].close);
    const lowClose = Math.abs(bars[i].low - bars[i - 1].close);
    trueRanges.push(Math.max(highLow, highClose, lowClose));
  }
  const series: IndicatorPoint[] = [];
  let atr = trueRanges.slice(0, period).reduce((a, b) => a + b, 0) / period;
  series.push({ date: bars[period].date, value: atr });
  for (let i = period; i < trueRanges.length; i++) {
    atr = (atr * (period - 1) + trueRanges[i]) / period;
    series.push({ date: bars[i + 1].date, value: atr });
  }
  return { available: true, requiredBars: period + 1, availableBars: bars.length, latest: series[series.length - 1].value, series };
}

export interface TechnicalsResult {
  sma20: IndicatorResult;
  sma50: IndicatorResult;
  sma200: IndicatorResult;
  ema20: IndicatorResult;
  ema50: IndicatorResult;
  rsi14: IndicatorResult;
  macd: MacdResult;
  bollinger: BollingerResult;
  atr14: IndicatorResult;
}

export function computeTechnicals(bars: PriceBar[]): TechnicalsResult {
  const sorted = [...bars].sort((a, b) => a.date.localeCompare(b.date));
  const closes = sorted.map((b) => b.close);
  const dates = sorted.map((b) => b.date);
  return {
    sma20: smaSeries(closes, dates, 20),
    sma50: smaSeries(closes, dates, 50),
    sma200: smaSeries(closes, dates, 200),
    ema20: emaSeries(closes, dates, 20),
    ema50: emaSeries(closes, dates, 50),
    rsi14: rsi14(closes, dates),
    macd: macd(closes, dates),
    bollinger: bollinger(closes, dates),
    atr14: atr14(sorted),
  };
}
