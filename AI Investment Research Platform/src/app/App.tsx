import { useState, useMemo, useEffect } from "react";
import {
  AreaChart, Area, BarChart, Bar, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine, PieChart, Pie, Cell,
} from "recharts";
import {
  TrendingUp, TrendingDown, Minus, Activity, Search,
  Briefcase, Shield, AlertTriangle, Filter, Database,
  Clock, BarChart2, BookOpen, ChevronRight, Eye,
  ChevronDown, ChevronUp, Cpu, Info,
} from "lucide-react";

// ─── Types ────────────────────────────────────────────────────────────────────

type Regime = "bull" | "sideways" | "bear";
type Tab = "research" | "technicals" | "screener" | "portfolio";

interface Stock {
  rank: number;
  ticker: string;
  name: string;
  sector: string;
  price: number;
  mktCapB: number;
  change1d: number;
  fiveDayProb: number;
  expectedExcessReturn: number;
  downsideProb: number;
  dailyVol: number;
  regime: Regime;
  modelAgreement: number;
  dataScore: number;
  oodFlag: boolean;
  compositeScore: number;
  pe: number;
  pb: number;
  divYield: number;
  roe: number;
  debtEquity: number;
}

interface PriceBar {
  date: string;
  close: number;
  volume: number;
  rsi: number;
  macd: number;
  macdSignal: number;
  high: number;
  low: number;
}

// ─── Data ─────────────────────────────────────────────────────────────────────

const STOCKS: Stock[] = [
  { rank: 1, ticker: "LUCK", name: "Lucky Cement", sector: "Cement", price: 512.40, mktCapB: 184.2, change1d: 1.34, fiveDayProb: 0.562, expectedExcessReturn: 0.0143, downsideProb: 0.189, dailyVol: 0.0218, regime: "bull", modelAgreement: 0.712, dataScore: 0.934, oodFlag: false, compositeScore: 64, pe: 14.2, pb: 1.8, divYield: 2.1, roe: 13.4, debtEquity: 0.21 },
  { rank: 2, ticker: "ENGRO", name: "Engro Corporation", sector: "Conglomerate", price: 287.60, mktCapB: 312.8, change1d: 0.89, fiveDayProb: 0.548, expectedExcessReturn: 0.0121, downsideProb: 0.213, dailyVol: 0.0196, regime: "bull", modelAgreement: 0.698, dataScore: 0.912, oodFlag: false, compositeScore: 61, pe: 10.8, pb: 1.4, divYield: 5.6, roe: 16.2, debtEquity: 0.48 },
  { rank: 3, ticker: "ATRL", name: "Attock Refinery", sector: "Refinery", price: 228.75, mktCapB: 28.4, change1d: 2.14, fiveDayProb: 0.541, expectedExcessReturn: 0.0098, downsideProb: 0.224, dailyVol: 0.0267, regime: "sideways", modelAgreement: 0.654, dataScore: 0.889, oodFlag: false, compositeScore: 58, pe: 7.1, pb: 1.1, divYield: 6.8, roe: 18.9, debtEquity: 0.12 },
  { rank: 4, ticker: "TRG", name: "TRG Pakistan", sector: "Technology", price: 102.30, mktCapB: 44.7, change1d: 3.21, fiveDayProb: 0.537, expectedExcessReturn: 0.0087, downsideProb: 0.231, dailyVol: 0.0312, regime: "bull", modelAgreement: 0.632, dataScore: 0.856, oodFlag: false, compositeScore: 56, pe: 28.4, pb: 4.2, divYield: 0.0, roe: 22.1, debtEquity: 0.34 },
  { rank: 5, ticker: "MCB", name: "MCB Bank", sector: "Banking", price: 261.80, mktCapB: 276.4, change1d: 0.42, fiveDayProb: 0.534, expectedExcessReturn: 0.0079, downsideProb: 0.238, dailyVol: 0.0184, regime: "bull", modelAgreement: 0.621, dataScore: 0.967, oodFlag: false, compositeScore: 55, pe: 8.9, pb: 1.6, divYield: 7.2, roe: 21.4, debtEquity: 5.12 },
  { rank: 6, ticker: "SEARL", name: "Searle Company", sector: "Pharma", price: 142.50, mktCapB: 32.1, change1d: 1.67, fiveDayProb: 0.528, expectedExcessReturn: 0.0064, downsideProb: 0.244, dailyVol: 0.0243, regime: "sideways", modelAgreement: 0.589, dataScore: 0.878, oodFlag: false, compositeScore: 53, pe: 12.3, pb: 2.1, divYield: 3.4, roe: 19.8, debtEquity: 0.28 },
  { rank: 7, ticker: "OGDC", name: "Oil & Gas Dev. Corp.", sector: "Energy", price: 131.45, mktCapB: 567.8, change1d: -0.31, fiveDayProb: 0.524, expectedExcessReturn: 0.0058, downsideProb: 0.251, dailyVol: 0.0201, regime: "sideways", modelAgreement: 0.574, dataScore: 0.978, oodFlag: false, compositeScore: 52, pe: 6.4, pb: 0.9, divYield: 8.1, roe: 14.8, debtEquity: 0.08 },
  { rank: 8, ticker: "UBL", name: "United Bank Ltd", sector: "Banking", price: 183.20, mktCapB: 218.9, change1d: 0.71, fiveDayProb: 0.521, expectedExcessReturn: 0.0047, downsideProb: 0.258, dailyVol: 0.0192, regime: "sideways", modelAgreement: 0.556, dataScore: 0.945, oodFlag: false, compositeScore: 51, pe: 7.6, pb: 1.2, divYield: 8.9, roe: 18.2, debtEquity: 4.87 },
  { rank: 9, ticker: "FFC", name: "Fauji Fertilizer", sector: "Fertilizer", price: 118.90, mktCapB: 149.6, change1d: -0.54, fiveDayProb: 0.519, expectedExcessReturn: 0.0039, downsideProb: 0.264, dailyVol: 0.0223, regime: "sideways", modelAgreement: 0.541, dataScore: 0.923, oodFlag: false, compositeScore: 50, pe: 9.1, pb: 4.3, divYield: 11.4, roe: 54.2, debtEquity: 0.67 },
  { rank: 10, ticker: "HBL", name: "Habib Bank Ltd", sector: "Banking", price: 134.70, mktCapB: 195.3, change1d: 0.18, fiveDayProb: 0.516, expectedExcessReturn: 0.0031, downsideProb: 0.271, dailyVol: 0.0211, regime: "sideways", modelAgreement: 0.528, dataScore: 0.956, oodFlag: false, compositeScore: 49, pe: 7.2, pb: 0.9, divYield: 6.3, roe: 13.6, debtEquity: 5.34 },
  { rank: 11, ticker: "HUBC", name: "Hub Power Co.", sector: "Power", price: 96.40, mktCapB: 128.7, change1d: -0.83, fiveDayProb: 0.513, expectedExcessReturn: 0.0024, downsideProb: 0.278, dailyVol: 0.0198, regime: "sideways", modelAgreement: 0.514, dataScore: 0.901, oodFlag: false, compositeScore: 48, pe: 11.4, pb: 2.8, divYield: 9.7, roe: 27.1, debtEquity: 1.42 },
  { rank: 12, ticker: "PPL", name: "Pakistan Petroleum", sector: "Energy", price: 87.30, mktCapB: 213.5, change1d: -0.21, fiveDayProb: 0.511, expectedExcessReturn: 0.0018, downsideProb: 0.284, dailyVol: 0.0209, regime: "sideways", modelAgreement: 0.503, dataScore: 0.967, oodFlag: false, compositeScore: 47, pe: 5.8, pb: 0.7, divYield: 9.2, roe: 12.4, debtEquity: 0.11 },
  { rank: 13, ticker: "CHCC", name: "Cherat Cement", sector: "Cement", price: 108.20, mktCapB: 26.8, change1d: 0.94, fiveDayProb: 0.508, expectedExcessReturn: 0.0011, downsideProb: 0.291, dailyVol: 0.0287, regime: "sideways", modelAgreement: 0.489, dataScore: 0.867, oodFlag: false, compositeScore: 46, pe: 10.1, pb: 1.4, divYield: 4.1, roe: 15.2, debtEquity: 0.38 },
  { rank: 14, ticker: "AVN", name: "Avanceon Ltd", sector: "Technology", price: 57.85, mktCapB: 14.2, change1d: 2.88, fiveDayProb: 0.505, expectedExcessReturn: 0.0004, downsideProb: 0.298, dailyVol: 0.0334, regime: "sideways", modelAgreement: 0.474, dataScore: 0.823, oodFlag: false, compositeScore: 45, pe: 18.7, pb: 3.1, divYield: 1.8, roe: 17.8, debtEquity: 0.19 },
  { rank: 15, ticker: "PSO", name: "Pakistan State Oil", sector: "Energy", price: 305.40, mktCapB: 141.2, change1d: -1.24, fiveDayProb: 0.502, expectedExcessReturn: -0.0003, downsideProb: 0.304, dailyVol: 0.0234, regime: "sideways", modelAgreement: 0.461, dataScore: 0.934, oodFlag: false, compositeScore: 44, pe: 8.2, pb: 0.8, divYield: 5.9, roe: 10.2, debtEquity: 0.89 },
  { rank: 16, ticker: "EPCL", name: "Engro Polymer", sector: "Chemicals", price: 39.65, mktCapB: 31.4, change1d: -0.62, fiveDayProb: 0.498, expectedExcessReturn: -0.0009, downsideProb: 0.311, dailyVol: 0.0298, regime: "sideways", modelAgreement: 0.447, dataScore: 0.856, oodFlag: false, compositeScore: 43, pe: 9.8, pb: 1.3, divYield: 4.8, roe: 14.1, debtEquity: 0.52 },
  { rank: 17, ticker: "DGKC", name: "D.G. Khan Cement", sector: "Cement", price: 82.10, mktCapB: 42.8, change1d: -0.37, fiveDayProb: 0.494, expectedExcessReturn: -0.0016, downsideProb: 0.318, dailyVol: 0.0276, regime: "sideways", modelAgreement: 0.432, dataScore: 0.878, oodFlag: false, compositeScore: 42, pe: 11.2, pb: 0.9, divYield: 3.2, roe: 8.4, debtEquity: 0.44 },
  { rank: 18, ticker: "KAPCO", name: "Kot Addu Power", sector: "Power", price: 49.30, mktCapB: 56.1, change1d: -1.02, fiveDayProb: 0.491, expectedExcessReturn: -0.0023, downsideProb: 0.324, dailyVol: 0.0221, regime: "bear", modelAgreement: 0.418, dataScore: 0.889, oodFlag: false, compositeScore: 41, pe: 7.4, pb: 1.1, divYield: 13.2, roe: 16.7, debtEquity: 0.71 },
  { rank: 19, ticker: "MLCF", name: "Maple Leaf Cement", sector: "Cement", price: 46.75, mktCapB: 38.9, change1d: -1.58, fiveDayProb: 0.487, expectedExcessReturn: -0.0031, downsideProb: 0.332, dailyVol: 0.0312, regime: "bear", modelAgreement: 0.403, dataScore: 0.845, oodFlag: false, compositeScore: 40, pe: 14.8, pb: 1.2, divYield: 2.6, roe: 9.1, debtEquity: 0.61 },
  { rank: 20, ticker: "NBP", name: "National Bank", sector: "Banking", price: 46.20, mktCapB: 89.3, change1d: -0.89, fiveDayProb: 0.482, expectedExcessReturn: -0.0039, downsideProb: 0.341, dailyVol: 0.0243, regime: "bear", modelAgreement: 0.387, dataScore: 0.923, oodFlag: false, compositeScore: 38, pe: 4.1, pb: 0.4, divYield: 10.8, roe: 11.2, debtEquity: 6.21 },
  { rank: 21, ticker: "PAEL", name: "Pak Elektron", sector: "Engineering", price: 56.40, mktCapB: 21.7, change1d: -1.87, fiveDayProb: 0.478, expectedExcessReturn: -0.0048, downsideProb: 0.349, dailyVol: 0.0289, regime: "bear", modelAgreement: 0.371, dataScore: 0.812, oodFlag: false, compositeScore: 37, pe: 16.2, pb: 1.8, divYield: 1.4, roe: 12.8, debtEquity: 0.93 },
  { rank: 22, ticker: "PTCL", name: "Pakistan Telecom", sector: "Telecom", price: 12.85, mktCapB: 67.4, change1d: -0.54, fiveDayProb: 0.473, expectedExcessReturn: -0.0057, downsideProb: 0.358, dailyVol: 0.0267, regime: "bear", modelAgreement: 0.354, dataScore: 0.901, oodFlag: true, compositeScore: 35, pe: 22.1, pb: 0.6, divYield: 0.0, roe: 2.8, debtEquity: 1.87 },
  { rank: 23, ticker: "KEL", name: "K-Electric Ltd", sector: "Utility", price: 6.38, mktCapB: 76.8, change1d: -2.13, fiveDayProb: 0.467, expectedExcessReturn: -0.0068, downsideProb: 0.367, dailyVol: 0.0312, regime: "bear", modelAgreement: 0.336, dataScore: 0.867, oodFlag: true, compositeScore: 33, pe: 18.4, pb: 0.7, divYield: 0.0, roe: 4.1, debtEquity: 2.34 },
  { rank: 24, ticker: "FFBL", name: "Fauji Fertilizer Bin Qasim", sector: "Fertilizer", price: 18.95, mktCapB: 22.8, change1d: -2.47, fiveDayProb: 0.458, expectedExcessReturn: -0.0082, downsideProb: 0.381, dailyVol: 0.0356, regime: "bear", modelAgreement: 0.317, dataScore: 0.812, oodFlag: true, compositeScore: 30, pe: 0.0, pb: 0.8, divYield: 0.0, roe: -4.2, debtEquity: 3.12 },
];

function generatePriceHistory(basePrice: number, seed: number): PriceBar[] {
  const rng = (s: number) => { const x = Math.sin(s * 9301 + 49297) * 233280; return x - Math.floor(x); };
  const data: PriceBar[] = [];
  let price = basePrice * (0.82 + rng(seed) * 0.1);
  for (let i = 89; i >= 0; i--) {
    const r = rng(seed + i);
    price = Math.max(price * (1 + (r - 0.485) * 0.028), price * 0.7);
    const volFactor = 0.01 + rng(seed + i + 200) * 0.012;
    const high = price * (1 + rng(seed + i + 300) * volFactor);
    const low = price * (1 - rng(seed + i + 400) * volFactor);
    const date = new Date(2026, 4, 13);
    date.setDate(date.getDate() + (89 - i));
    data.push({
      date: date.toLocaleDateString("en-US", { month: "short", day: "numeric" }),
      close: parseFloat(price.toFixed(2)),
      high: parseFloat(high.toFixed(2)),
      low: parseFloat(low.toFixed(2)),
      volume: Math.floor((0.4 + rng(seed + i + 500) * 1.8) * 1800000),
      rsi: 20 + rng(seed + i + 600) * 65,
      macd: (rng(seed + i + 700) - 0.48) * 4,
      macdSignal: (rng(seed + i + 800) - 0.49) * 3.2,
    });
  }
  return data;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

const fmt = {
  pct: (v: number, decimals = 1) => `${v >= 0 ? "+" : ""}${(v * 100).toFixed(decimals)}%`,
  pctAbs: (v: number, decimals = 1) => `${(v * 100).toFixed(decimals)}%`,
  price: (v: number) => v >= 100 ? v.toFixed(2) : v < 10 ? v.toFixed(2) : v.toFixed(2),
  score: (v: number) => v.toFixed(1),
  vol: (v: number) => v >= 1e9 ? `₨${(v / 1e9).toFixed(1)}B` : `₨${(v / 1e6).toFixed(0)}M`,
};

function regimeColor(r: Regime) {
  return r === "bull" ? "text-emerald-400" : r === "bear" ? "text-red-400" : "text-amber-400";
}

function regimeBg(r: Regime) {
  return r === "bull" ? "bg-emerald-400/10 text-emerald-400 border-emerald-400/20"
    : r === "bear" ? "bg-red-400/10 text-red-400 border-red-400/20"
    : "bg-amber-400/10 text-amber-400 border-amber-400/20";
}

function changeColor(v: number) { return v >= 0 ? "text-emerald-400" : "text-red-400"; }

function probBar(prob: number) {
  const pct = Math.round(prob * 100);
  const color = prob > 0.53 ? "bg-emerald-400" : prob < 0.47 ? "bg-red-400" : "bg-amber-400";
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1 bg-white/5 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full`} style={{ width: `${pct}%` }} />
      </div>
      <span className={`font-mono text-xs ${prob > 0.53 ? "text-emerald-400" : prob < 0.47 ? "text-red-400" : "text-amber-400"}`}>{pct}%</span>
    </div>
  );
}

// ─── Ticker Strip ─────────────────────────────────────────────────────────────

function TickerStrip() {
  const items = [
    { label: "KSE-100", val: "95,420.51", ch: "+403.21", pct: "+0.43%" },
    { label: "KSE-30", val: "34,812.60", ch: "+156.40", pct: "+0.45%" },
    { label: "USD/PKR", val: "278.42", ch: "+0.82", pct: "+0.30%" },
    { label: "KIBOR 3M", val: "12.48%", ch: "-0.12%", pct: "" },
    { label: "GOLD OZ", val: "2,418.30", ch: "+14.20", pct: "+0.59%" },
    { label: "BRENT", val: "78.64", ch: "-0.34", pct: "-0.43%" },
    { label: "T-BILL 3M", val: "11.92%", ch: "-0.08%", pct: "" },
    { label: "OGDC", val: "131.45", ch: "-0.41", pct: "-0.31%" },
    { label: "ENGRO", val: "287.60", ch: "+2.55", pct: "+0.89%" },
    { label: "LUCK", val: "512.40", ch: "+6.80", pct: "+1.34%" },
    { label: "MCB", val: "261.80", ch: "+1.10", pct: "+0.42%" },
    { label: "HBL", val: "134.70", ch: "+0.24", pct: "+0.18%" },
  ];
  return (
    <div className="border-b border-border overflow-hidden bg-secondary/30">
      <div className="flex animate-[ticker_60s_linear_infinite] whitespace-nowrap">
        {[...items, ...items].map((it, i) => (
          <span key={i} className="inline-flex items-center gap-2 px-5 py-1 text-xs font-mono border-r border-border/40">
            <span className="text-muted-foreground">{it.label}</span>
            <span className="text-foreground">{it.val}</span>
            <span className={it.ch.startsWith("-") ? "text-red-400" : "text-emerald-400"}>{it.ch}</span>
          </span>
        ))}
      </div>
    </div>
  );
}

// ─── Top Bar ──────────────────────────────────────────────────────────────────

function TopBar({ tab, setTab }: { tab: Tab; setTab: (t: Tab) => void }) {
  const [time, setTime] = useState(new Date());
  useEffect(() => { const id = setInterval(() => setTime(new Date()), 1000); return () => clearInterval(id); }, []);
  const tabs: { id: Tab; label: string; icon: React.ReactNode }[] = [
    { id: "research", label: "QUANT RESEARCH", icon: <Cpu size={12} /> },
    { id: "technicals", label: "TECHNICALS", icon: <BarChart2 size={12} /> },
    { id: "screener", label: "SCREENER", icon: <Filter size={12} /> },
    { id: "portfolio", label: "PORTFOLIO", icon: <Briefcase size={12} /> },
  ];
  return (
    <header className="border-b border-border bg-card flex-shrink-0">
      <div className="flex items-center justify-between px-4 py-2.5">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-primary rounded-sm flex items-center justify-center">
              <span className="text-primary-foreground font-bold text-xs font-mono">P</span>
            </div>
            <div>
              <div className="text-xs font-semibold tracking-widest text-foreground leading-none">PSX QUANT</div>
              <div className="text-[9px] text-muted-foreground tracking-widest leading-none mt-0.5">RESEARCH TERMINAL</div>
            </div>
          </div>
          <div className="w-px h-6 bg-border mx-1" />
          <div className="flex items-center gap-1.5 text-[10px] text-muted-foreground font-mono">
            <div className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
            <span>HISTORICAL DATA</span>
            <span className="text-border">·</span>
            <span>24 PSX EQUITIES</span>
            <span className="text-border">·</span>
            <span>MODEL v2.4.1</span>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <div className="text-xs font-mono text-foreground">{time.toLocaleTimeString("en-US", { hour12: false, timeZone: "Asia/Karachi" })}</div>
            <div className="text-[9px] text-muted-foreground font-mono">PKT · {time.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}</div>
          </div>
          <div className="flex items-center gap-1 px-2 py-1 border border-amber-400/30 bg-amber-400/5 rounded-sm">
            <Database size={10} className="text-amber-400" />
            <span className="text-[10px] text-amber-400 font-mono">YAHOO HIST.</span>
          </div>
        </div>
      </div>
      <div className="flex border-t border-border">
        {tabs.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex items-center gap-1.5 px-4 py-2 text-[10px] font-mono tracking-widest border-r border-border transition-colors ${
              tab === t.id
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:text-foreground hover:bg-accent/50"
            }`}
          >
            {t.icon}
            {t.label}
          </button>
        ))}
      </div>
    </header>
  );
}

// ─── No Signal Banner ─────────────────────────────────────────────────────────

function NoSignalBanner() {
  const [open, setOpen] = useState(false);
  return (
    <div className="border-b border-red-500/20 bg-red-500/5 px-4 py-2.5 flex-shrink-0">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="flex items-center gap-2 mt-0.5">
            <div className="w-2 h-2 rounded-full bg-red-400" />
            <span className="text-[10px] font-mono tracking-widest text-red-400">MODEL STATUS: NO SIGNAL</span>
          </div>
          <div className="text-[11px] text-muted-foreground leading-relaxed max-w-3xl">
            Validated predictive performance does not satisfy the minimum required standard (≥60% historical accuracy on out-of-sample decile separation).
            All probability estimates are displayed for research transparency only. This platform does not issue BUY/SELL recommendations.
          </div>
        </div>
        <button onClick={() => setOpen(o => !o)} className="flex items-center gap-1 text-[10px] text-muted-foreground hover:text-foreground font-mono whitespace-nowrap mt-0.5 transition-colors">
          <Info size={10} />
          {open ? "HIDE" : "DISCLOSURE"}
          {open ? <ChevronUp size={10} /> : <ChevronDown size={10} />}
        </button>
      </div>
      {open && (
        <div className="mt-3 pt-3 border-t border-red-500/10 grid grid-cols-3 gap-4">
          {[
            { label: "Platform Type", val: "PSX Quantitative Research Tool" },
            { label: "Data Source", val: "Yahoo Finance Historical (non-licensed)" },
            { label: "Universe", val: "24 PSX equities · Equal-weight KSE proxy benchmark" },
            { label: "Forecast Horizon", val: "5-day relative return vs benchmark" },
            { label: "Signal Threshold", val: "≥60% out-of-sample accuracy (not yet met)" },
            { label: "Intended Use", val: "Research · Historical analysis · Not investment advice" },
          ].map(item => (
            <div key={item.label}>
              <div className="text-[9px] text-muted-foreground font-mono tracking-widest">{item.label}</div>
              <div className="text-[11px] text-foreground mt-0.5">{item.val}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Metric Card ──────────────────────────────────────────────────────────────

function MetricCard({ label, value, sub, accent, icon }: { label: string; value: string; sub?: string; accent?: boolean; icon: React.ReactNode }) {
  return (
    <div className={`border border-border bg-card p-3.5 rounded-sm ${accent ? "border-amber-400/30" : ""}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-[9px] font-mono tracking-widest text-muted-foreground">{label}</span>
        <span className={`${accent ? "text-amber-400" : "text-muted-foreground"}`}>{icon}</span>
      </div>
      <div className={`text-xl font-mono font-semibold ${accent ? "text-amber-400" : "text-foreground"}`}>{value}</div>
      {sub && <div className="text-[10px] text-muted-foreground mt-1 font-mono">{sub}</div>}
    </div>
  );
}

// ─── Stock Detail Panel ───────────────────────────────────────────────────────

function StockDetail({ stock }: { stock: Stock }) {
  const data = useMemo(() => generatePriceHistory(stock.price, stock.rank * 17), [stock.ticker]);
  const pct = Math.round(stock.fiveDayProb * 100);
  const gaugeColor = pct > 53 ? "#34d399" : pct < 47 ? "#f87171" : "#f59e0b";
  const history = data.slice(-30);

  return (
    <div className="flex flex-col gap-3 h-full overflow-y-auto pr-1 text-xs">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-lg font-semibold text-foreground">{stock.ticker}</span>
            <span className={`text-[9px] font-mono px-1.5 py-0.5 border rounded-sm ${regimeBg(stock.regime)}`}>{stock.regime.toUpperCase()}</span>
            {stock.oodFlag && <span className="text-[9px] font-mono px-1.5 py-0.5 border border-orange-400/30 bg-orange-400/10 text-orange-400 rounded-sm">OOD</span>}
          </div>
          <div className="text-[11px] text-muted-foreground mt-0.5">{stock.name} · {stock.sector}</div>
        </div>
        <div className="text-right">
          <div className="font-mono text-base font-semibold text-foreground">₨{fmt.price(stock.price)}</div>
          <div className={`text-[11px] font-mono ${changeColor(stock.change1d)}`}>{stock.change1d >= 0 ? "+" : ""}{stock.change1d.toFixed(2)}%</div>
        </div>
      </div>

      {/* Mini sparkline */}
      <div className="h-16 border border-border rounded-sm bg-secondary/20 overflow-hidden">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={history} margin={{ top: 4, right: 0, bottom: 0, left: 0 }}>
            <defs>
              <linearGradient id="spark" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={gaugeColor} stopOpacity={0.2} />
                <stop offset="95%" stopColor={gaugeColor} stopOpacity={0} />
              </linearGradient>
            </defs>
            <Area type="monotone" dataKey="close" stroke={gaugeColor} strokeWidth={1.5} fill="url(#spark)" dot={false} />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* 5-Day Outperformance Probability */}
      <div className="border border-border bg-secondary/20 rounded-sm p-3">
        <div className="text-[9px] font-mono tracking-widest text-muted-foreground mb-2">5-DAY MARKET OUTPERFORMANCE PROBABILITY</div>
        <div className="flex items-center gap-3 mb-2">
          <div className="text-2xl font-mono font-semibold" style={{ color: gaugeColor }}>{pct}%</div>
          <div className="flex-1">
            <div className="h-2 bg-white/5 rounded-full overflow-hidden">
              <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, backgroundColor: gaugeColor }} />
            </div>
            <div className="flex justify-between text-[9px] text-muted-foreground font-mono mt-1">
              <span>0%</span>
              <span className="text-border">·</span>
              <span>50%</span>
              <span className="text-border">·</span>
              <span>100%</span>
            </div>
          </div>
        </div>
        <div className="text-[10px] text-muted-foreground">
          Calibrated probability that {stock.ticker} will outperform the equal-weight KSE proxy over the next 5 trading days.
        </div>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-2 gap-2">
        {[
          { label: "EXPECTED EXCESS RETURN (5D)", val: fmt.pct(stock.expectedExcessReturn, 2), color: stock.expectedExcessReturn >= 0 ? "text-emerald-400" : "text-red-400" },
          { label: "DOWNSIDE PROBABILITY (>5%)", val: fmt.pctAbs(stock.downsideProb), color: stock.downsideProb > 0.3 ? "text-red-400" : stock.downsideProb > 0.22 ? "text-amber-400" : "text-emerald-400" },
          { label: "DAILY VOLATILITY (HIST.)", val: fmt.pctAbs(stock.dailyVol, 2), color: "text-foreground" },
          { label: "ANNUALISED VOLATILITY", val: fmt.pctAbs(stock.dailyVol * Math.sqrt(252), 1), color: "text-foreground" },
        ].map(m => (
          <div key={m.label} className="border border-border bg-secondary/20 rounded-sm p-2.5">
            <div className="text-[9px] font-mono tracking-widest text-muted-foreground mb-1">{m.label}</div>
            <div className={`text-sm font-mono font-semibold ${m.color}`}>{m.val}</div>
          </div>
        ))}
      </div>

      {/* Model Diagnostics */}
      <div className="border border-border rounded-sm p-3">
        <div className="text-[9px] font-mono tracking-widest text-muted-foreground mb-3">MODEL DIAGNOSTICS</div>
        <div className="space-y-2.5">
          {[
            { label: "MODEL AGREEMENT", val: stock.modelAgreement, note: "Cross-model consensus" },
            { label: "DATA COMPLETENESS", val: stock.dataScore, note: "Feature coverage score" },
          ].map(d => (
            <div key={d.label}>
              <div className="flex justify-between mb-1">
                <span className="text-[9px] font-mono text-muted-foreground">{d.label}</span>
                <span className="text-[9px] font-mono text-foreground">{(d.val * 100).toFixed(1)}%</span>
              </div>
              <div className="h-1 bg-white/5 rounded-full overflow-hidden">
                <div className="h-full bg-amber-400/70 rounded-full" style={{ width: `${d.val * 100}%` }} />
              </div>
              <div className="text-[9px] text-muted-foreground mt-0.5">{d.note}</div>
            </div>
          ))}
          <div className="flex items-center justify-between pt-1 border-t border-border">
            <span className="text-[9px] font-mono text-muted-foreground">OUT-OF-DISTRIBUTION FLAG</span>
            <span className={`text-[9px] font-mono ${stock.oodFlag ? "text-orange-400" : "text-emerald-400"}`}>
              {stock.oodFlag ? "⚠ FLAGGED" : "✓ CLEAR"}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-[9px] font-mono text-muted-foreground">COMPOSITE SCORE</span>
            <span className="text-[9px] font-mono text-amber-400">{stock.compositeScore} / 100</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-[9px] font-mono text-muted-foreground">CROSS-SECTIONAL RANK</span>
            <span className="text-[9px] font-mono text-foreground">#{stock.rank} of 24</span>
          </div>
        </div>
      </div>

      {/* Fundamentals */}
      <div className="border border-border rounded-sm p-3">
        <div className="text-[9px] font-mono tracking-widest text-muted-foreground mb-3">FUNDAMENTAL SNAPSHOT <span className="text-orange-400/70">(DEMO DATA)</span></div>
        <div className="grid grid-cols-3 gap-2">
          {[
            { k: "P/E", v: stock.pe > 0 ? stock.pe.toFixed(1) + "x" : "N/A" },
            { k: "P/B", v: stock.pb.toFixed(1) + "x" },
            { k: "DIV YLD", v: stock.divYield > 0 ? stock.divYield.toFixed(1) + "%" : "—" },
            { k: "ROE", v: (stock.roe >= 0 ? "" : "") + stock.roe.toFixed(1) + "%" },
            { k: "D/E", v: stock.debtEquity.toFixed(2) + "x" },
            { k: "MKT CAP", v: `₨${stock.mktCapB.toFixed(0)}B` },
          ].map(f => (
            <div key={f.k} className="text-center">
              <div className="text-[9px] font-mono text-muted-foreground">{f.k}</div>
              <div className="text-[11px] font-mono text-foreground mt-0.5">{f.v}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── Quant Research Tab ───────────────────────────────────────────────────────

function QuantResearch() {
  const [selected, setSelected] = useState(STOCKS[0]);
  const [sortBy, setSortBy] = useState<keyof Stock>("rank");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");
  const [filter, setFilter] = useState("");

  const sorted = useMemo(() => {
    let list = STOCKS.filter(s =>
      s.ticker.includes(filter.toUpperCase()) ||
      s.name.toLowerCase().includes(filter.toLowerCase()) ||
      s.sector.toLowerCase().includes(filter.toLowerCase())
    );
    list = [...list].sort((a, b) => {
      const va = a[sortBy] as number | string;
      const vb = b[sortBy] as number | string;
      const dir = sortDir === "asc" ? 1 : -1;
      return typeof va === "number" ? (va - (vb as number)) * dir : String(va).localeCompare(String(vb)) * dir;
    });
    return list;
  }, [sortBy, sortDir, filter]);

  function toggleSort(col: keyof Stock) {
    if (sortBy === col) setSortDir(d => d === "asc" ? "desc" : "asc");
    else { setSortBy(col); setSortDir("asc"); }
  }

  const SortIcon = ({ col }: { col: keyof Stock }) => (
    <span className="ml-0.5 opacity-40">
      {sortBy === col ? (sortDir === "asc" ? "↑" : "↓") : "↕"}
    </span>
  );

  // Summary cards
  const avgProb = STOCKS.reduce((s, x) => s + x.fiveDayProb, 0) / STOCKS.length;
  const bullCount = STOCKS.filter(s => s.regime === "bull").length;
  const bearCount = STOCKS.filter(s => s.regime === "bear").length;
  const avgAgreement = STOCKS.reduce((s, x) => s + x.modelAgreement, 0) / STOCKS.length;

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <NoSignalBanner />

      {/* Summary Row */}
      <div className="grid grid-cols-4 gap-3 p-4 pb-3 border-b border-border bg-secondary/10 flex-shrink-0">
        <MetricCard label="KSE-100 (LIVE)" value="95,420" sub="+403 pts · +0.43% today" icon={<TrendingUp size={12} />} />
        <MetricCard label="COVERAGE UNIVERSE" value="24" sub="PSX equities · Yahoo historical" icon={<Database size={12} />} />
        <MetricCard label="MARKET REGIME MIX" value={`${bullCount}B · ${24 - bullCount - bearCount}S · ${bearCount}Br`} sub="Bull · Sideways · Bear" icon={<Activity size={12} />} />
        <MetricCard label="AVG MODEL AGREEMENT" value={`${(avgAgreement * 100).toFixed(1)}%`} sub={`Avg 5D prob: ${(avgProb * 100).toFixed(1)}%`} accent icon={<Cpu size={12} />} />
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden flex gap-0">
        {/* Table */}
        <div className="flex flex-col w-[62%] border-r border-border overflow-hidden">
          <div className="px-4 py-2.5 border-b border-border flex items-center gap-3 flex-shrink-0">
            <span className="text-[10px] font-mono tracking-widest text-muted-foreground">CROSS-SECTIONAL RANKINGS</span>
            <div className="flex-1" />
            <div className="flex items-center gap-1.5 bg-secondary rounded-sm px-2 py-1 border border-border">
              <Search size={10} className="text-muted-foreground" />
              <input
                value={filter}
                onChange={e => setFilter(e.target.value)}
                placeholder="Filter ticker, name, sector…"
                className="bg-transparent text-[11px] font-mono text-foreground placeholder:text-muted-foreground outline-none w-40"
              />
            </div>
          </div>
          <div className="overflow-auto flex-1">
            <table className="w-full text-[10px] font-mono">
              <thead className="sticky top-0 bg-card z-10 border-b border-border">
                <tr className="text-muted-foreground">
                  {[
                    { key: "rank", label: "#" },
                    { key: "ticker", label: "TICKER" },
                    { key: "sector", label: "SECTOR" },
                    { key: "price", label: "PRICE" },
                    { key: "fiveDayProb", label: "5D PROB" },
                    { key: "expectedExcessReturn", label: "EXC. RET." },
                    { key: "downsideProb", label: "DWNSIDE" },
                    { key: "regime", label: "REGIME" },
                    { key: "modelAgreement", label: "AGRMNT" },
                    { key: "dataScore", label: "DATA" },
                  ].map(col => (
                    <th
                      key={col.key}
                      onClick={() => toggleSort(col.key as keyof Stock)}
                      className="text-left px-3 py-2 cursor-pointer hover:text-foreground tracking-widest whitespace-nowrap select-none"
                    >
                      {col.label}<SortIcon col={col.key as keyof Stock} />
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {sorted.map(s => (
                  <tr
                    key={s.ticker}
                    onClick={() => setSelected(s)}
                    className={`border-b border-border/40 cursor-pointer transition-colors ${
                      selected.ticker === s.ticker ? "bg-amber-400/8 border-amber-400/20" : "hover:bg-accent/40"
                    }`}
                  >
                    <td className="px-3 py-2 text-muted-foreground">{s.rank}</td>
                    <td className="px-3 py-2">
                      <span className={`font-semibold ${selected.ticker === s.ticker ? "text-amber-400" : "text-foreground"}`}>{s.ticker}</span>
                    </td>
                    <td className="px-3 py-2 text-muted-foreground">{s.sector}</td>
                    <td className="px-3 py-2 text-foreground">₨{fmt.price(s.price)}</td>
                    <td className="px-3 py-2">{probBar(s.fiveDayProb)}</td>
                    <td className={`px-3 py-2 ${changeColor(s.expectedExcessReturn)}`}>{fmt.pct(s.expectedExcessReturn, 2)}</td>
                    <td className={`px-3 py-2 ${s.downsideProb > 0.3 ? "text-red-400" : s.downsideProb > 0.22 ? "text-amber-400" : "text-emerald-400"}`}>{fmt.pctAbs(s.downsideProb)}</td>
                    <td className="px-3 py-2">
                      <span className={`text-[9px] px-1.5 py-0.5 border rounded-sm ${regimeBg(s.regime)}`}>{s.regime.toUpperCase()}</span>
                    </td>
                    <td className="px-3 py-2 text-foreground">{(s.modelAgreement * 100).toFixed(0)}%</td>
                    <td className="px-3 py-2">
                      <span className={`${s.dataScore >= 0.9 ? "text-emerald-400" : s.dataScore >= 0.8 ? "text-amber-400" : "text-red-400"}`}>
                        {(s.dataScore * 100).toFixed(0)}%
                      </span>
                      {s.oodFlag && <span className="ml-1 text-orange-400">⚠</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Detail Panel */}
        <div className="w-[38%] p-4 overflow-hidden flex flex-col">
          <StockDetail stock={selected} />
        </div>
      </div>
    </div>
  );
}

// ─── Technicals Tab ───────────────────────────────────────────────────────────

function Technicals() {
  const [ticker, setTicker] = useState("OGDC");
  const [period, setPeriod] = useState<30 | 60 | 90>(90);
  const stock = STOCKS.find(s => s.ticker === ticker) || STOCKS[6];
  const allData = useMemo(() => generatePriceHistory(stock.price, stock.rank * 17), [stock.ticker]);
  const data = allData.slice(-period);
  const minClose = Math.min(...data.map(d => d.low));
  const maxClose = Math.max(...data.map(d => d.high));
  const domain: [number, number] = [minClose * 0.99, maxClose * 1.01];

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Controls */}
      <div className="border-b border-border px-4 py-2.5 flex items-center gap-4 flex-shrink-0 bg-secondary/10">
        <div className="flex items-center gap-2">
          <span className="text-[9px] font-mono tracking-widest text-muted-foreground">SYMBOL</span>
          <select
            value={ticker}
            onChange={e => setTicker(e.target.value)}
            className="bg-secondary border border-border rounded-sm text-[11px] font-mono text-foreground px-2 py-1 outline-none"
          >
            {STOCKS.map(s => <option key={s.ticker} value={s.ticker}>{s.ticker} — {s.name}</option>)}
          </select>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[9px] font-mono tracking-widest text-muted-foreground">PERIOD</span>
          <div className="flex border border-border rounded-sm overflow-hidden">
            {([30, 60, 90] as const).map(p => (
              <button key={p} onClick={() => setPeriod(p)}
                className={`px-3 py-1 text-[10px] font-mono transition-colors ${period === p ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground"}`}>
                {p}D
              </button>
            ))}
          </div>
        </div>
        <div className="flex-1" />
        <div className="flex items-center gap-3 text-[10px] font-mono">
          <span className="text-muted-foreground">LAST</span>
          <span className="text-foreground">₨{fmt.price(data[data.length - 1]?.close || 0)}</span>
          <span className={changeColor(stock.change1d)}>{stock.change1d >= 0 ? "+" : ""}{stock.change1d.toFixed(2)}%</span>
          <span className="text-border">·</span>
          <span className="text-orange-400/80 text-[9px]">DEMO DATA</span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {/* Price Chart */}
        <div className="border border-border rounded-sm bg-card p-3">
          <div className="text-[9px] font-mono tracking-widest text-muted-foreground mb-3">PRICE · {ticker} · {period}D HISTORY</div>
          <ResponsiveContainer width="100%" height={180}>
            <AreaChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
              <defs>
                <linearGradient id="priceGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="2 4" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="date" tick={{ fontSize: 9, fill: "#636880", fontFamily: "JetBrains Mono" }} tickLine={false} axisLine={false} interval={Math.floor(period / 6)} />
              <YAxis domain={domain} tick={{ fontSize: 9, fill: "#636880", fontFamily: "JetBrains Mono" }} tickLine={false} axisLine={false} tickFormatter={v => `₨${v.toFixed(0)}`} width={52} />
              <Tooltip
                contentStyle={{ background: "#0d0f1b", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 2, fontSize: 10, fontFamily: "JetBrains Mono" }}
                labelStyle={{ color: "#636880" }}
                itemStyle={{ color: "#f59e0b" }}
                formatter={(v: number) => [`₨${v.toFixed(2)}`, "Close"]}
              />
              <Area type="monotone" dataKey="close" stroke="#f59e0b" strokeWidth={1.5} fill="url(#priceGrad)" dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Volume */}
        <div className="border border-border rounded-sm bg-card p-3">
          <div className="text-[9px] font-mono tracking-widest text-muted-foreground mb-3">VOLUME</div>
          <ResponsiveContainer width="100%" height={70}>
            <BarChart data={data} margin={{ top: 0, right: 8, bottom: 0, left: 0 }}>
              <CartesianGrid strokeDasharray="2 4" stroke="rgba(255,255,255,0.04)" vertical={false} />
              <XAxis dataKey="date" tick={false} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 9, fill: "#636880", fontFamily: "JetBrains Mono" }} tickLine={false} axisLine={false} tickFormatter={v => `${(v / 1e6).toFixed(0)}M`} width={40} />
              <Tooltip
                contentStyle={{ background: "#0d0f1b", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 2, fontSize: 10, fontFamily: "JetBrains Mono" }}
                formatter={(v: number) => [fmt.vol(v), "Volume"]}
                labelStyle={{ color: "#636880" }}
                itemStyle={{ color: "#3b82f6" }}
              />
              <Bar dataKey="volume" fill="#3b82f6" opacity={0.6} radius={[1, 1, 0, 0]} maxBarSize={8} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* RSI */}
        <div className="border border-border rounded-sm bg-card p-3">
          <div className="text-[9px] font-mono tracking-widest text-muted-foreground mb-3">RSI (14)</div>
          <ResponsiveContainer width="100%" height={80}>
            <LineChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
              <CartesianGrid strokeDasharray="2 4" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="date" tick={false} axisLine={false} tickLine={false} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 9, fill: "#636880", fontFamily: "JetBrains Mono" }} tickLine={false} axisLine={false} width={28} />
              <ReferenceLine y={70} stroke="#ef4444" strokeDasharray="3 3" strokeWidth={1} strokeOpacity={0.5} />
              <ReferenceLine y={30} stroke="#22c55e" strokeDasharray="3 3" strokeWidth={1} strokeOpacity={0.5} />
              <ReferenceLine y={50} stroke="rgba(255,255,255,0.1)" strokeWidth={1} />
              <Tooltip
                contentStyle={{ background: "#0d0f1b", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 2, fontSize: 10, fontFamily: "JetBrains Mono" }}
                formatter={(v: number) => [v.toFixed(1), "RSI"]}
                labelStyle={{ color: "#636880" }}
                itemStyle={{ color: "#a78bfa" }}
              />
              <Line type="monotone" dataKey="rsi" stroke="#a78bfa" strokeWidth={1.5} dot={false} />
            </LineChart>
          </ResponsiveContainer>
          <div className="flex gap-4 mt-1 text-[9px] font-mono text-muted-foreground">
            <span className="text-red-400">— 70 Overbought</span>
            <span className="text-emerald-400">— 30 Oversold</span>
            <span className="ml-auto">Current: {data[data.length - 1]?.rsi.toFixed(1)}</span>
          </div>
        </div>

        {/* MACD */}
        <div className="border border-border rounded-sm bg-card p-3">
          <div className="text-[9px] font-mono tracking-widest text-muted-foreground mb-3">MACD (12, 26, 9)</div>
          <ResponsiveContainer width="100%" height={80}>
            <LineChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
              <CartesianGrid strokeDasharray="2 4" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="date" tick={false} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 9, fill: "#636880", fontFamily: "JetBrains Mono" }} tickLine={false} axisLine={false} width={28} />
              <ReferenceLine y={0} stroke="rgba(255,255,255,0.15)" strokeWidth={1} />
              <Tooltip
                contentStyle={{ background: "#0d0f1b", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 2, fontSize: 10, fontFamily: "JetBrains Mono" }}
                labelStyle={{ color: "#636880" }}
              />
              <Line type="monotone" dataKey="macd" stroke="#f59e0b" strokeWidth={1.5} dot={false} name="MACD" />
              <Line type="monotone" dataKey="macdSignal" stroke="#3b82f6" strokeWidth={1} dot={false} strokeDasharray="3 3" name="Signal" />
            </LineChart>
          </ResponsiveContainer>
          <div className="flex gap-4 mt-1 text-[9px] font-mono text-muted-foreground">
            <span className="text-amber-400">— MACD</span>
            <span className="text-blue-400">--- Signal</span>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Screener Tab ─────────────────────────────────────────────────────────────

const SECTORS = ["All", "Banking", "Cement", "Chemicals", "Conglomerate", "Energy", "Engineering", "Fertilizer", "Pharma", "Power", "Refinery", "Technology", "Telecom", "Utility"];
const REGIMES: ("all" | Regime)[] = ["all", "bull", "sideways", "bear"];

function Screener() {
  const [sector, setSector] = useState("All");
  const [regime, setRegime] = useState<"all" | Regime>("all");
  const [minScore, setMinScore] = useState(0);
  const [minProb, setMinProb] = useState(0);
  const [maxDE, setMaxDE] = useState(99);
  const [sortCol, setSortCol] = useState<keyof Stock>("compositeScore");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  const filtered = useMemo(() => {
    let list = STOCKS.filter(s =>
      (sector === "All" || s.sector === sector) &&
      (regime === "all" || s.regime === regime) &&
      s.compositeScore >= minScore &&
      s.fiveDayProb >= minProb / 100 &&
      s.debtEquity <= maxDE
    );
    return [...list].sort((a, b) => {
      const va = a[sortCol] as number;
      const vb = b[sortCol] as number;
      return (va - vb) * (sortDir === "asc" ? 1 : -1);
    });
  }, [sector, regime, minScore, minProb, maxDE, sortCol, sortDir]);

  function toggleSort(col: keyof Stock) {
    if (sortCol === col) setSortDir(d => d === "asc" ? "desc" : "asc");
    else { setSortCol(col); setSortDir("desc"); }
  }

  return (
    <div className="flex h-full overflow-hidden">
      {/* Filters */}
      <div className="w-52 border-r border-border p-4 flex flex-col gap-4 overflow-y-auto flex-shrink-0 bg-secondary/10">
        <div>
          <div className="text-[9px] font-mono tracking-widest text-muted-foreground mb-2">SECTOR</div>
          <div className="space-y-0.5">
            {SECTORS.map(s => (
              <button key={s} onClick={() => setSector(s)}
                className={`w-full text-left px-2 py-1 text-[10px] font-mono rounded-sm transition-colors ${sector === s ? "bg-amber-400/10 text-amber-400" : "text-muted-foreground hover:text-foreground hover:bg-accent/40"}`}>
                {s}
              </button>
            ))}
          </div>
        </div>
        <div className="border-t border-border pt-4">
          <div className="text-[9px] font-mono tracking-widest text-muted-foreground mb-2">REGIME</div>
          <div className="flex flex-col gap-0.5">
            {REGIMES.map(r => (
              <button key={r} onClick={() => setRegime(r)}
                className={`text-left px-2 py-1 text-[10px] font-mono rounded-sm transition-colors capitalize ${regime === r ? "bg-amber-400/10 text-amber-400" : "text-muted-foreground hover:text-foreground hover:bg-accent/40"}`}>
                {r === "all" ? "All Regimes" : r}
              </button>
            ))}
          </div>
        </div>
        <div className="border-t border-border pt-4 space-y-4">
          <div>
            <div className="flex justify-between mb-1">
              <span className="text-[9px] font-mono tracking-widest text-muted-foreground">MIN SCORE</span>
              <span className="text-[10px] font-mono text-amber-400">{minScore}</span>
            </div>
            <input type="range" min={0} max={70} value={minScore} onChange={e => setMinScore(+e.target.value)}
              className="w-full accent-amber-400 cursor-pointer" />
          </div>
          <div>
            <div className="flex justify-between mb-1">
              <span className="text-[9px] font-mono tracking-widest text-muted-foreground">MIN 5D PROB</span>
              <span className="text-[10px] font-mono text-amber-400">{minProb}%</span>
            </div>
            <input type="range" min={0} max={60} value={minProb} onChange={e => setMinProb(+e.target.value)}
              className="w-full accent-amber-400 cursor-pointer" />
          </div>
          <div>
            <div className="flex justify-between mb-1">
              <span className="text-[9px] font-mono tracking-widest text-muted-foreground">MAX D/E</span>
              <span className="text-[10px] font-mono text-amber-400">{maxDE === 99 ? "Any" : maxDE + "x"}</span>
            </div>
            <input type="range" min={0} max={99} value={maxDE} onChange={e => setMaxDE(+e.target.value)}
              className="w-full accent-amber-400 cursor-pointer" />
          </div>
        </div>
        <div className="border-t border-border pt-4">
          <button onClick={() => { setSector("All"); setRegime("all"); setMinScore(0); setMinProb(0); setMaxDE(99); }}
            className="w-full text-[10px] font-mono text-muted-foreground hover:text-foreground border border-border rounded-sm py-1.5 transition-colors">
            RESET FILTERS
          </button>
        </div>
        <div className="text-[9px] text-orange-400/70 font-mono border-t border-border pt-3 leading-relaxed">
          Fundamental data shown is demonstration data only — not verified PSX financials.
        </div>
      </div>

      {/* Results */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="px-4 py-2.5 border-b border-border flex items-center gap-3 flex-shrink-0 bg-secondary/10">
          <span className="text-[10px] font-mono tracking-widest text-muted-foreground">SCREENER RESULTS</span>
          <span className="text-[10px] font-mono text-amber-400">{filtered.length} matches</span>
        </div>
        <div className="overflow-auto flex-1">
          <table className="w-full text-[10px] font-mono">
            <thead className="sticky top-0 bg-card border-b border-border z-10">
              <tr className="text-muted-foreground tracking-widest">
                {[
                  { key: "ticker", label: "TICKER" },
                  { key: "sector", label: "SECTOR" },
                  { key: "price", label: "PRICE" },
                  { key: "change1d", label: "1D CHG" },
                  { key: "compositeScore", label: "SCORE" },
                  { key: "fiveDayProb", label: "5D PROB" },
                  { key: "pe", label: "P/E" },
                  { key: "divYield", label: "DIV YLD" },
                  { key: "roe", label: "ROE" },
                  { key: "debtEquity", label: "D/E" },
                  { key: "regime", label: "REGIME" },
                  { key: "mktCapB", label: "MKT CAP" },
                ].map(col => (
                  <th key={col.key} onClick={() => toggleSort(col.key as keyof Stock)}
                    className="text-left px-3 py-2 cursor-pointer hover:text-foreground whitespace-nowrap select-none">
                    {col.label}
                    <span className="ml-0.5 opacity-40">{sortCol === col.key ? (sortDir === "asc" ? "↑" : "↓") : "↕"}</span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map(s => (
                <tr key={s.ticker} className="border-b border-border/40 hover:bg-accent/30 transition-colors">
                  <td className="px-3 py-2 font-semibold text-foreground">{s.ticker}</td>
                  <td className="px-3 py-2 text-muted-foreground">{s.sector}</td>
                  <td className="px-3 py-2 text-foreground">₨{fmt.price(s.price)}</td>
                  <td className={`px-3 py-2 ${changeColor(s.change1d)}`}>{s.change1d >= 0 ? "+" : ""}{s.change1d.toFixed(2)}%</td>
                  <td className="px-3 py-2">
                    <div className="flex items-center gap-2">
                      <div className="w-12 h-1 bg-white/5 rounded-full overflow-hidden">
                        <div className="h-full bg-amber-400/70 rounded-full" style={{ width: `${s.compositeScore}%` }} />
                      </div>
                      <span className="text-amber-400">{s.compositeScore}</span>
                    </div>
                  </td>
                  <td className="px-3 py-2">{probBar(s.fiveDayProb)}</td>
                  <td className="px-3 py-2 text-foreground">{s.pe > 0 ? s.pe.toFixed(1) + "x" : "N/A"}</td>
                  <td className="px-3 py-2 text-foreground">{s.divYield > 0 ? s.divYield.toFixed(1) + "%" : "—"}</td>
                  <td className={`px-3 py-2 ${s.roe >= 0 ? "text-emerald-400" : "text-red-400"}`}>{s.roe.toFixed(1)}%</td>
                  <td className={`px-3 py-2 ${s.debtEquity > 3 ? "text-red-400" : s.debtEquity > 1 ? "text-amber-400" : "text-foreground"}`}>{s.debtEquity.toFixed(2)}x</td>
                  <td className="px-3 py-2">
                    <span className={`text-[9px] px-1.5 py-0.5 border rounded-sm ${regimeBg(s.regime)}`}>{s.regime.toUpperCase()}</span>
                  </td>
                  <td className="px-3 py-2 text-muted-foreground">₨{s.mktCapB.toFixed(0)}B</td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={12} className="px-4 py-8 text-center text-muted-foreground text-[11px]">No results match current filters.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ─── Portfolio Tab ────────────────────────────────────────────────────────────

const HOLDINGS = [
  { ticker: "OGDC", qty: 4000, avgCost: 118.20 },
  { ticker: "LUCK", qty: 800, avgCost: 488.50 },
  { ticker: "MCB", qty: 2500, avgCost: 248.30 },
  { ticker: "ENGRO", qty: 1200, avgCost: 271.80 },
  { ticker: "FFC", qty: 3000, avgCost: 112.40 },
  { ticker: "TRG", qty: 1500, avgCost: 89.60 },
  { ticker: "SEARL", qty: 1000, avgCost: 131.20 },
  { ticker: "HBL", qty: 2000, avgCost: 128.90 },
];

const ALLOC_COLORS = ["#f59e0b", "#22c55e", "#3b82f6", "#a78bfa", "#f97316", "#06b6d4", "#ec4899", "#84cc16"];

function Portfolio() {
  const holdings = useMemo(() => {
    return HOLDINGS.map(h => {
      const s = STOCKS.find(x => x.ticker === h.ticker)!;
      const mktVal = s.price * h.qty;
      const costBasis = h.avgCost * h.qty;
      const pnl = mktVal - costBasis;
      const pnlPct = (pnl / costBasis) * 100;
      return { ...h, stock: s, mktVal, costBasis, pnl, pnlPct };
    });
  }, []);

  const totalMktVal = holdings.reduce((s, h) => s + h.mktVal, 0);
  const totalCost = holdings.reduce((s, h) => s + h.costBasis, 0);
  const totalPnl = totalMktVal - totalCost;
  const totalPnlPct = (totalPnl / totalCost) * 100;

  const sectorAlloc = useMemo(() => {
    const map: Record<string, number> = {};
    holdings.forEach(h => {
      map[h.stock.sector] = (map[h.stock.sector] || 0) + h.mktVal;
    });
    return Object.entries(map).map(([name, value]) => ({ name, value: parseFloat(((value / totalMktVal) * 100).toFixed(1)) }));
  }, [holdings, totalMktVal]);

  const regimeDist = useMemo(() => {
    const map: Record<string, number> = { bull: 0, sideways: 0, bear: 0 };
    holdings.forEach(h => { map[h.stock.regime] += h.mktVal; });
    return Object.entries(map).map(([name, v]) => ({ name: name.toUpperCase(), value: parseFloat(((v / totalMktVal) * 100).toFixed(1)) }));
  }, [holdings, totalMktVal]);

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {/* Portfolio Summary */}
      <div className="grid grid-cols-4 gap-3">
        <MetricCard label="TOTAL MKT VALUE" value={`₨${(totalMktVal / 1e6).toFixed(2)}M`} sub="8 holdings · PSX equities" icon={<Briefcase size={12} />} accent />
        <MetricCard label="TOTAL P&L" value={`${totalPnl >= 0 ? "+" : ""}₨${(totalPnl / 1e3).toFixed(0)}K`} sub={`${totalPnlPct >= 0 ? "+" : ""}${totalPnlPct.toFixed(2)}% vs cost basis`} icon={totalPnl >= 0 ? <TrendingUp size={12} /> : <TrendingDown size={12} />} />
        <MetricCard label="COST BASIS" value={`₨${(totalCost / 1e6).toFixed(2)}M`} sub="Weighted avg cost" icon={<Database size={12} />} />
        <MetricCard label="PORTFOLIO HEALTH" value="Moderate" sub="Regime: Mixed · 3 sectors" icon={<Shield size={12} />} />
      </div>

      <div className="grid grid-cols-3 gap-4">
        {/* Holdings Table */}
        <div className="col-span-2 border border-border rounded-sm bg-card overflow-hidden">
          <div className="px-4 py-2.5 border-b border-border">
            <span className="text-[9px] font-mono tracking-widest text-muted-foreground">HOLDINGS · DEMONSTRATION PORTFOLIO</span>
          </div>
          <table className="w-full text-[10px] font-mono">
            <thead className="border-b border-border">
              <tr className="text-muted-foreground tracking-widest">
                {["TICKER", "QTY", "AVG COST", "CUR. PRICE", "MKT VAL", "P&L", "P&L %", "5D PROB", "SCORE", "REGIME"].map(h => (
                  <th key={h} className="text-left px-3 py-2">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {holdings.map(h => (
                <tr key={h.ticker} className="border-b border-border/40 hover:bg-accent/30 transition-colors">
                  <td className="px-3 py-2 font-semibold text-foreground">{h.ticker}</td>
                  <td className="px-3 py-2 text-muted-foreground">{h.qty.toLocaleString()}</td>
                  <td className="px-3 py-2 text-muted-foreground">₨{h.avgCost.toFixed(2)}</td>
                  <td className="px-3 py-2 text-foreground">₨{fmt.price(h.stock.price)}</td>
                  <td className="px-3 py-2 text-foreground">₨{(h.mktVal / 1e3).toFixed(0)}K</td>
                  <td className={`px-3 py-2 ${h.pnl >= 0 ? "text-emerald-400" : "text-red-400"}`}>{h.pnl >= 0 ? "+" : ""}₨{(h.pnl / 1e3).toFixed(0)}K</td>
                  <td className={`px-3 py-2 ${h.pnlPct >= 0 ? "text-emerald-400" : "text-red-400"}`}>{h.pnlPct >= 0 ? "+" : ""}{h.pnlPct.toFixed(2)}%</td>
                  <td className="px-3 py-2">{probBar(h.stock.fiveDayProb)}</td>
                  <td className="px-3 py-2 text-amber-400">{h.stock.compositeScore}</td>
                  <td className="px-3 py-2">
                    <span className={`text-[9px] px-1.5 py-0.5 border rounded-sm ${regimeBg(h.stock.regime)}`}>{h.stock.regime.toUpperCase()}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Side Charts */}
        <div className="space-y-4">
          <div className="border border-border rounded-sm bg-card p-3">
            <div className="text-[9px] font-mono tracking-widest text-muted-foreground mb-3">SECTOR ALLOCATION</div>
            <ResponsiveContainer width="100%" height={160}>
              <PieChart>
                <Pie data={sectorAlloc} cx="50%" cy="50%" innerRadius={42} outerRadius={68} dataKey="value" strokeWidth={0}>
                  {sectorAlloc.map((_, i) => <Cell key={i} fill={ALLOC_COLORS[i % ALLOC_COLORS.length]} opacity={0.85} />)}
                </Pie>
                <Tooltip
                  contentStyle={{ background: "#0d0f1b", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 2, fontSize: 10, fontFamily: "JetBrains Mono" }}
                  formatter={(v: number) => [`${v}%`, "Weight"]}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="mt-2 space-y-1">
              {sectorAlloc.map((s, i) => (
                <div key={s.name} className="flex items-center justify-between text-[9px] font-mono">
                  <div className="flex items-center gap-1.5">
                    <div className="w-2 h-2 rounded-full" style={{ backgroundColor: ALLOC_COLORS[i % ALLOC_COLORS.length] }} />
                    <span className="text-muted-foreground">{s.name}</span>
                  </div>
                  <span className="text-foreground">{s.value}%</span>
                </div>
              ))}
            </div>
          </div>

          <div className="border border-border rounded-sm bg-card p-3">
            <div className="text-[9px] font-mono tracking-widest text-muted-foreground mb-3">REGIME EXPOSURE</div>
            <div className="space-y-2">
              {regimeDist.map(r => (
                <div key={r.name}>
                  <div className="flex justify-between text-[9px] font-mono mb-1">
                    <span className={r.name === "BULL" ? "text-emerald-400" : r.name === "BEAR" ? "text-red-400" : "text-amber-400"}>{r.name}</span>
                    <span className="text-foreground">{r.value}%</span>
                  </div>
                  <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                    <div className={`h-full rounded-full ${r.name === "BULL" ? "bg-emerald-400" : r.name === "BEAR" ? "bg-red-400" : "bg-amber-400"}`} style={{ width: `${r.value}%` }} />
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-3 pt-3 border-t border-border text-[9px] font-mono text-muted-foreground">
              <div className="flex justify-between">
                <span>Avg AI Score</span>
                <span className="text-amber-400">{(holdings.reduce((s, h) => s + h.stock.compositeScore, 0) / holdings.length).toFixed(0)}/100</span>
              </div>
              <div className="flex justify-between mt-1">
                <span>OOD Holdings</span>
                <span className="text-foreground">{holdings.filter(h => h.stock.oodFlag).length} of {holdings.length}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Risk Disclaimer */}
      <div className="border border-amber-400/20 bg-amber-400/5 rounded-sm p-3 text-[10px] font-mono text-amber-400/80 flex items-start gap-2">
        <AlertTriangle size={12} className="mt-0.5 flex-shrink-0" />
        <span>This is a demonstration portfolio using simulated holdings. Portfolio data, P&L figures, and allocation are for illustrative purposes only. This platform does not provide investment advice. PSX investments carry market, liquidity, currency, and regulatory risks.</span>
      </div>
    </div>
  );
}

// ─── App ──────────────────────────────────────────────────────────────────────

export default function App() {
  const [tab, setTab] = useState<Tab>("research");

  return (
    <div className="size-full flex flex-col bg-background text-foreground overflow-hidden" style={{ fontFamily: "'Inter', sans-serif" }}>
      <style>{`
        @keyframes ticker {
          from { transform: translateX(0); }
          to { transform: translateX(-50%); }
        }
        ::-webkit-scrollbar { width: 4px; height: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 2px; }
        ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }
        .font-mono { font-family: 'JetBrains Mono', monospace !important; }
        select option { background: #0d0f1b; color: #dde1ed; }
      `}</style>
      <TopBar tab={tab} setTab={setTab} />
      <TickerStrip />
      <main className="flex-1 overflow-hidden flex flex-col">
        {tab === "research" && <QuantResearch />}
        {tab === "technicals" && <Technicals />}
        {tab === "screener" && <Screener />}
        {tab === "portfolio" && <Portfolio />}
      </main>
    </div>
  );
}
