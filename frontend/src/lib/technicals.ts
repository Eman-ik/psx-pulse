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

// ─── ADX ─────────────────────────────────────────────────────────────────────

export interface AdxResult {
  available: boolean;
  requiredBars: number;
  availableBars: number;
  latest: { adx: number; plusDI: number; minusDI: number } | null;
  series: { date: string; adx: number; plusDI: number; minusDI: number }[];
}

function adx(bars: PriceBar[], period = 14): AdxResult {
  const required = period * 2 + 1;
  if (bars.length < required) return { available: false, requiredBars: required, availableBars: bars.length, latest: null, series: [] };

  const trArr: number[] = [], plusDMArr: number[] = [], minusDMArr: number[] = [];
  for (let i = 1; i < bars.length; i++) {
    const c = bars[i], p = bars[i - 1];
    trArr.push(Math.max(c.high - c.low, Math.abs(c.high - p.close), Math.abs(c.low - p.close)));
    const up = c.high - p.high, dn = p.low - c.low;
    plusDMArr.push(up > dn && up > 0 ? up : 0);
    minusDMArr.push(dn > up && dn > 0 ? dn : 0);
  }

  // Wilder smoothing: first value = sum of first `period` elements, then rolling
  function wilder(arr: number[]): number[] {
    let s = arr.slice(0, period).reduce((a, b) => a + b, 0);
    const out = [s];
    for (let i = period; i < arr.length; i++) { s = s - s / period + arr[i]; out.push(s); }
    return out;
  }

  const sTR = wilder(trArr), sPDM = wilder(plusDMArr), sMDM = wilder(minusDMArr);
  const dxArr: number[] = [], pDIArr: number[] = [], mDIArr: number[] = [];
  for (let i = 0; i < sTR.length; i++) {
    const pDI = sTR[i] > 0 ? 100 * sPDM[i] / sTR[i] : 0;
    const mDI = sTR[i] > 0 ? 100 * sMDM[i] / sTR[i] : 0;
    pDIArr.push(pDI); mDIArr.push(mDI);
    const dSum = pDI + mDI;
    dxArr.push(dSum > 0 ? 100 * Math.abs(pDI - mDI) / dSum : 0);
  }
  // ADX smoothing: initial value is AVERAGE of first `period` DX values (not sum).
  // TR/DM can use sum-based wilder because the DI ratio cancels the scale factor;
  // ADX (smoothed DX) has no such cancellation, so the sum must be divided here.
  function wilderAvg(arr: number[]): number[] {
    if (arr.length < period) return [];
    let val = arr.slice(0, period).reduce((a, b) => a + b, 0) / period;
    const out = [val];
    for (let i = period; i < arr.length; i++) { val = (val * (period - 1) + arr[i]) / period; out.push(val); }
    return out;
  }
  const adxArr = wilderAvg(dxArr);

  // Date alignment: adxArr[i] → bars[2*period - 1 + i]; pDIArr offset = period-1+i
  const series: AdxResult["series"] = [];
  for (let i = 0; i < adxArr.length; i++) {
    const barIdx = 2 * period - 1 + i;
    if (barIdx < bars.length) {
      series.push({ date: bars[barIdx].date, adx: adxArr[i], plusDI: pDIArr[period - 1 + i], minusDI: mDIArr[period - 1 + i] });
    }
  }
  const latest = series.length > 0 ? series[series.length - 1] : null;
  return { available: latest != null, requiredBars: required, availableBars: bars.length, latest, series };
}

// ─── OBV ─────────────────────────────────────────────────────────────────────

function obv(bars: PriceBar[]): IndicatorResult {
  const hasVol = bars.some((b) => b.volume != null && b.volume > 0);
  if (!hasVol) return insufficient(2, bars.length);
  if (bars.length < 2) return insufficient(2, bars.length);
  const series: IndicatorPoint[] = [];
  let val = 0;
  series.push({ date: bars[0].date, value: 0 });
  for (let i = 1; i < bars.length; i++) {
    const vol = bars[i].volume ?? 0;
    if (bars[i].close > bars[i - 1].close) val += vol;
    else if (bars[i].close < bars[i - 1].close) val -= vol;
    series.push({ date: bars[i].date, value: val });
  }
  return { available: true, requiredBars: 2, availableBars: bars.length, latest: series[series.length - 1].value, series };
}

// ─── Rolling VWAP (20-day) ────────────────────────────────────────────────────

function vwap(bars: PriceBar[], window = 20): IndicatorResult {
  const hasVol = bars.some((b) => b.volume != null && b.volume > 0);
  if (!hasVol || bars.length < window) return insufficient(window, bars.length);
  const series: IndicatorPoint[] = [];
  for (let i = window - 1; i < bars.length; i++) {
    let sumPV = 0, sumV = 0;
    for (let j = i - window + 1; j <= i; j++) {
      const tp = (bars[j].high + bars[j].low + bars[j].close) / 3;
      const v = bars[j].volume ?? 0;
      sumPV += tp * v; sumV += v;
    }
    series.push({ date: bars[i].date, value: sumV > 0 ? sumPV / sumV : bars[i].close });
  }
  return { available: true, requiredBars: window, availableBars: bars.length, latest: series[series.length - 1].value, series };
}

// ─── Stochastic RSI ───────────────────────────────────────────────────────────

export interface StochRsiResult {
  available: boolean;
  requiredBars: number;
  availableBars: number;
  latest: { k: number; d: number } | null;
  series: { date: string; k: number; d: number }[];
}

function stochRsi(closes: number[], dates: string[], rsiPeriod = 14, stochPeriod = 14, smoothK = 3, smoothD = 3): StochRsiResult {
  const required = rsiPeriod + stochPeriod + smoothK + smoothD;
  if (closes.length < required) return { available: false, requiredBars: required, availableBars: closes.length, latest: null, series: [] };

  // Build RSI series
  const rsiRes = rsi14(closes, dates);
  if (!rsiRes.available || rsiRes.series.length < stochPeriod + smoothK + smoothD - 2) {
    return { available: false, requiredBars: required, availableBars: closes.length, latest: null, series: [] };
  }
  const rsiVals = rsiRes.series.map((p) => p.value);
  const rsiDates = rsiRes.series.map((p) => p.date);

  // Stochastic of RSI
  const rawK: { date: string; value: number }[] = [];
  for (let i = stochPeriod - 1; i < rsiVals.length; i++) {
    const window = rsiVals.slice(i - stochPeriod + 1, i + 1);
    const lo = Math.min(...window), hi = Math.max(...window);
    rawK.push({ date: rsiDates[i], value: hi > lo ? ((rsiVals[i] - lo) / (hi - lo)) * 100 : 50 });
  }

  // SMA smoothing for %K
  function smaSmooth(arr: { date: string; value: number }[], p: number): { date: string; value: number }[] {
    const out: { date: string; value: number }[] = [];
    for (let i = p - 1; i < arr.length; i++) {
      const v = arr.slice(i - p + 1, i + 1).reduce((s, x) => s + x.value, 0) / p;
      out.push({ date: arr[i].date, value: v });
    }
    return out;
  }

  const kLine = smaSmooth(rawK, smoothK);
  const dLine = smaSmooth(kLine, smoothD);

  // Align K and D (D is shorter by smoothD-1)
  const offset = smoothD - 1;
  const series: StochRsiResult["series"] = dLine.map((d, i) => ({
    date: d.date, k: kLine[i + offset].value, d: d.value,
  }));
  const latest = series.length > 0 ? series[series.length - 1] : null;
  return { available: latest != null, requiredBars: required, availableBars: closes.length, latest, series };
}

// ─── Money Flow Index ─────────────────────────────────────────────────────────

function mfi(bars: PriceBar[], period = 14): IndicatorResult {
  const hasVol = bars.some((b) => b.volume != null && b.volume > 0);
  if (!hasVol || bars.length < period + 1) return insufficient(period + 1, bars.length);

  const series: IndicatorPoint[] = [];
  for (let i = period; i < bars.length; i++) {
    let posFlow = 0, negFlow = 0;
    let prevTP = (bars[i - period].high + bars[i - period].low + bars[i - period].close) / 3;
    for (let j = i - period + 1; j <= i; j++) {
      const tp = (bars[j].high + bars[j].low + bars[j].close) / 3;
      const rawMF = tp * (bars[j].volume ?? 0);
      if (tp > prevTP) posFlow += rawMF;
      else if (tp < prevTP) negFlow += rawMF;
      prevTP = tp;
    }
    const ratio = negFlow > 0 ? posFlow / negFlow : 100;
    series.push({ date: bars[i].date, value: negFlow === 0 ? 100 : 100 - 100 / (1 + ratio) });
  }
  return { available: true, requiredBars: period + 1, availableBars: bars.length, latest: series[series.length - 1].value, series };
}

// ─── Support / resistance (swing-point clustering) ────────────────────────────

export interface SupportResistanceLevel {
  price: number;
  type: "support" | "resistance";
  touches: number;
  lastTouchDate: string;
}

export interface SupportResistanceResult {
  available: boolean;
  requiredBars: number;
  availableBars: number;
  levels: SupportResistanceLevel[];
}

const SR_LOOKBACK = 5; // bars on each side that must be lower/higher for a swing point
const SR_CLUSTER_TOLERANCE = 0.015; // 1.5% — swing points this close are the same level
const SR_PROXIMITY_BAND = 0.4; // ignore levels more than 40% away from the current price
const SR_MAX_LEVELS_PER_SIDE = 3;

function findSwingPoints(bars: PriceBar[]): {
  highs: { price: number; date: string }[];
  lows: { price: number; date: string }[];
} {
  const highs: { price: number; date: string }[] = [];
  const lows: { price: number; date: string }[] = [];
  for (let i = SR_LOOKBACK; i < bars.length - SR_LOOKBACK; i++) {
    const window = bars.slice(i - SR_LOOKBACK, i + SR_LOOKBACK + 1);
    if (bars[i].high === Math.max(...window.map((b) => b.high))) {
      highs.push({ price: bars[i].high, date: bars[i].date });
    }
    if (bars[i].low === Math.min(...window.map((b) => b.low))) {
      lows.push({ price: bars[i].low, date: bars[i].date });
    }
  }
  return { highs, lows };
}

// Merges swing points into level clusters: points within SR_CLUSTER_TOLERANCE of a
// cluster's running average join it, so a level touched several times over the
// history collapses into one line with a real touch count instead of many near-
// duplicate points.
function clusterLevels(points: { price: number; date: string }[]): { price: number; touches: number; lastDate: string }[] {
  const sorted = [...points].sort((a, b) => a.price - b.price);
  const clusters: { prices: number[]; dates: string[] }[] = [];
  for (const p of sorted) {
    const last = clusters[clusters.length - 1];
    const avg = last ? last.prices.reduce((a, b) => a + b, 0) / last.prices.length : null;
    if (last && avg !== null && Math.abs(p.price - avg) / avg <= SR_CLUSTER_TOLERANCE) {
      last.prices.push(p.price);
      last.dates.push(p.date);
    } else {
      clusters.push({ prices: [p.price], dates: [p.date] });
    }
  }
  return clusters.map((c) => ({
    price: c.prices.reduce((a, b) => a + b, 0) / c.prices.length,
    touches: c.prices.length,
    lastDate: c.dates[c.dates.length - 1],
  }));
}

function supportResistance(bars: PriceBar[]): SupportResistanceResult {
  const required = SR_LOOKBACK * 2 + 20;
  if (bars.length < required) return { available: false, requiredBars: required, availableBars: bars.length, levels: [] };

  const currentPrice = bars[bars.length - 1].close;
  const inBand = (price: number) => Math.abs(price - currentPrice) / currentPrice <= SR_PROXIMITY_BAND;
  const { highs, lows } = findSwingPoints(bars);

  const rank = (clusters: { price: number; touches: number; lastDate: string }[]) =>
    [...clusters]
      .sort((a, b) => b.touches - a.touches || b.lastDate.localeCompare(a.lastDate))
      .slice(0, SR_MAX_LEVELS_PER_SIDE);

  const resistance = rank(clusterLevels(highs).filter((c) => c.price > currentPrice && inBand(c.price)));
  const support = rank(clusterLevels(lows).filter((c) => c.price < currentPrice && inBand(c.price)));

  const levels: SupportResistanceLevel[] = [
    ...support.map((c) => ({ price: c.price, type: "support" as const, touches: c.touches, lastTouchDate: c.lastDate })),
    ...resistance.map((c) => ({ price: c.price, type: "resistance" as const, touches: c.touches, lastTouchDate: c.lastDate })),
  ].sort((a, b) => b.price - a.price);

  return { available: true, requiredBars: required, availableBars: bars.length, levels };
}

// ─── Trend classification ──────────────────────────────────────────────────────

export interface TrendClassificationResult {
  available: boolean;
  requiredBars: number;
  availableBars: number;
  trend: "uptrend" | "downtrend" | "sideways" | null;
  strength: "strong" | "moderate" | "weak" | null;
  reasoning: string[];
}

const TREND_SLOPE_WINDOW = 15; // ~3 trading weeks, same horizon signal-analysis.ts's narrative uses

// Deterministic, explainable rule over already-computed indicators (price vs. SMA50,
// SMA50 vs. SMA200 when available, SMA20 slope) — never re-derives new price math,
// and every point counted toward the verdict is returned in `reasoning` so the badge
// is never a black box.
function classifyTrend(
  closes: number[],
  sma20: IndicatorResult,
  sma50: IndicatorResult,
  sma200: IndicatorResult,
  adx: AdxResult
): TrendClassificationResult {
  const required = 50;
  if (!sma20.available || !sma50.available || sma20.series.length <= TREND_SLOPE_WINDOW) {
    return { available: false, requiredBars: required, availableBars: closes.length, trend: null, strength: null, reasoning: [] };
  }

  const price = closes[closes.length - 1];
  const s50 = sma50.latest!;
  const s200 = sma200.available ? sma200.latest! : null;
  const adxVal = adx.available ? adx.latest!.adx : null;

  const sma20Now = sma20.series[sma20.series.length - 1].value;
  const sma20Then = sma20.series[sma20.series.length - 1 - TREND_SLOPE_WINDOW].value;
  const slopePct = ((sma20Now - sma20Then) / sma20Then) * 100;

  const reasoning: string[] = [];
  let bullPoints = 0;
  let bearPoints = 0;

  if (price > s50) {
    bullPoints++;
    reasoning.push("Price above SMA50");
  } else {
    bearPoints++;
    reasoning.push("Price below SMA50");
  }

  if (s200 !== null) {
    if (s50 > s200) {
      bullPoints++;
      reasoning.push("SMA50 above SMA200");
    } else {
      bearPoints++;
      reasoning.push("SMA50 below SMA200");
    }
  }

  if (slopePct > 0.5) {
    bullPoints++;
    reasoning.push(`SMA20 rising ${slopePct.toFixed(1)}% over ${TREND_SLOPE_WINDOW} sessions`);
  } else if (slopePct < -0.5) {
    bearPoints++;
    reasoning.push(`SMA20 falling ${slopePct.toFixed(1)}% over ${TREND_SLOPE_WINDOW} sessions`);
  } else {
    reasoning.push(`SMA20 roughly flat over ${TREND_SLOPE_WINDOW} sessions`);
  }

  let trend: "uptrend" | "downtrend" | "sideways";
  if (bullPoints - bearPoints >= 2) trend = "uptrend";
  else if (bearPoints - bullPoints >= 2) trend = "downtrend";
  else trend = "sideways";

  let strength: "strong" | "moderate" | "weak";
  if (adxVal !== null) {
    strength = adxVal >= 25 ? "strong" : adxVal >= 15 ? "moderate" : "weak";
    reasoning.push(`ADX ${adxVal.toFixed(1)}`);
  } else {
    strength = "moderate";
  }

  return { available: true, requiredBars: required, availableBars: closes.length, trend, strength, reasoning };
}

// ─── Result & compute ─────────────────────────────────────────────────────────

export interface TechnicalsResult {
  sma20: IndicatorResult;
  sma50: IndicatorResult;
  sma200: IndicatorResult;
  ema20: IndicatorResult;
  ema50: IndicatorResult;
  ema200: IndicatorResult;
  rsi14: IndicatorResult;
  macd: MacdResult;
  bollinger: BollingerResult;
  atr14: IndicatorResult;
  adx: AdxResult;
  obv: IndicatorResult;
  vwap: IndicatorResult;
  stochRsi: StochRsiResult;
  mfi: IndicatorResult;
  supportResistance: SupportResistanceResult;
  trendClassification: TrendClassificationResult;
}

export function computeTechnicals(bars: PriceBar[]): TechnicalsResult {
  const sorted = [...bars].sort((a, b) => a.date.localeCompare(b.date));
  const closes = sorted.map((b) => b.close);
  const dates = sorted.map((b) => b.date);
  const sma20 = smaSeries(closes, dates, 20);
  const sma50 = smaSeries(closes, dates, 50);
  const sma200 = smaSeries(closes, dates, 200);
  const adxResult = adx(sorted);
  return {
    sma20,
    sma50,
    sma200,
    ema20: emaSeries(closes, dates, 20),
    ema50: emaSeries(closes, dates, 50),
    ema200: emaSeries(closes, dates, 200),
    rsi14: rsi14(closes, dates),
    macd: macd(closes, dates),
    bollinger: bollinger(closes, dates),
    atr14: atr14(sorted),
    adx: adxResult,
    obv: obv(sorted),
    vwap: vwap(sorted),
    stochRsi: stochRsi(closes, dates),
    mfi: mfi(sorted),
    supportResistance: supportResistance(sorted),
    trendClassification: classifyTrend(closes, sma20, sma50, sma200, adxResult),
  };
}
