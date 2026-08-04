"use client";

import React, { useState, useRef, useEffect } from "react";
import { Search, Loader2, AlertCircle, ChevronRight } from "lucide-react";
import type { ResearchJSON } from "./ResearchReport";
import { ResearchReport } from "./ResearchReport";

// ─── Terminal step log ─────────────────────────────────────────────────────────

const STEPS = [
  "Resolving ticker from PSX database…",
  "Fetching company overview and financials…",
  "Loading announcements and dividend history…",
  "Building research context from DB…",
  "Running 18-stage institutional equity workflow…",
  "Reconstructing financial statements…",
  "Running forensic accounting checks…",
  "Valuing via DCF / P/E / DDM methods…",
  "Building scenario analysis…",
  "Assembling research report…",
];

function TerminalLog({ activeStep }: { activeStep: number }) {
  return (
    <div className="bg-[#05070d] border border-border rounded-xl p-5 font-mono text-xs space-y-1.5 max-w-2xl mx-auto">
      <p className="text-muted text-[10px] uppercase tracking-wider mb-3">
        PSX QuantResearch · Institutional Equity Workflow
      </p>
      {STEPS.map((step, i) => {
        const done = i < activeStep;
        const current = i === activeStep;
        return (
          <div key={i} className={`flex items-center gap-2.5 transition-opacity duration-300 ${i > activeStep ? "opacity-20" : "opacity-100"}`}>
            <span className={`w-4 h-4 rounded-full flex items-center justify-center shrink-0 text-[9px] font-bold ${
              done ? "bg-positive/20 text-positive" :
              current ? "bg-accent/20 text-accent" :
              "bg-muted/10 text-muted"
            }`}>
              {done ? "✓" : i + 1}
            </span>
            <span className={`${done ? "text-muted line-through" : current ? "text-accent" : "text-muted/40"}`}>
              {step}
            </span>
            {current && <Loader2 className="w-3 h-3 text-accent animate-spin ml-auto" />}
          </div>
        );
      })}
    </div>
  );
}

// ─── Ticker pill ───────────────────────────────────────────────────────────────

const QUICK_TICKERS = ["FFC", "EFERT", "FATIMA", "AGL", "AHCL"];

// ─── Main component ────────────────────────────────────────────────────────────

export function ResearchStudio() {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [activeStep, setActiveStep] = useState(0);
  const [report, setReport] = useState<ResearchJSON | null>(null);
  const [error, setError] = useState<string | null>(null);
  const stepTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const reportRef = useRef<HTMLDivElement | null>(null);

  // Advance the terminal step log pseudo-randomly while loading
  const startStepTimer = () => {
    setActiveStep(0);
    let step = 0;
    // Steps 0-7 advance every ~8s, steps 8-9 advance slower
    stepTimerRef.current = setInterval(() => {
      step++;
      if (step < STEPS.length - 1) {
        setActiveStep(step);
      }
    }, 8000);
  };

  const stopStepTimer = () => {
    if (stepTimerRef.current) {
      clearInterval(stepTimerRef.current);
      stepTimerRef.current = null;
    }
  };

  const runResearch = async (ticker: string) => {
    const t = ticker.trim().toUpperCase();
    if (!t) return;

    setLoading(true);
    setReport(null);
    setError(null);
    startStepTimer();

    try {
      const res = await fetch("/api/research/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticker: t }),
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data.error ?? `Server error ${res.status}`);
        return;
      }
      if (!data.report) {
        setError("No report returned from server.");
        return;
      }

      setActiveStep(STEPS.length); // mark all done
      setReport(data.report as ResearchJSON);
      // Scroll to report after short delay so render completes
      setTimeout(() => {
        reportRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 200);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Network error");
    } finally {
      stopStepTimer();
      setLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    runResearch(input);
  };

  // Cleanup timer on unmount
  useEffect(() => () => stopStepTimer(), []);

  return (
    <div className="space-y-8 pb-16">
      {/* ── Hero + Search ─────────────────────────────────────────────── */}
      <div className="text-center space-y-2 pt-2">
        <span className="inline-block text-[10px] font-mono font-bold uppercase tracking-widest text-accent border border-accent/30 rounded px-3 py-1 bg-accent/5">
          PSX QuantResearch · Institutional Equity AI
        </span>
        <h1 className="text-3xl font-bold text-foreground">Research Studio</h1>
        <p className="text-muted text-sm max-w-xl mx-auto font-sans">
          Type a PSX ticker or company name. The AI runs a full 18-stage
          institutional equity research workflow and delivers it as a structured report.
        </p>
      </div>

      {/* Search bar */}
      <form onSubmit={handleSubmit} className="max-w-xl mx-auto">
        <div className="relative flex items-center gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted" />
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="e.g. FFC, EFERT, Fatima Fertilizer…"
              disabled={loading}
              className="w-full bg-surface border border-border rounded-lg pl-10 pr-4 py-3 text-sm text-foreground placeholder:text-muted/50 focus:outline-none focus:border-accent/60 focus:ring-1 focus:ring-accent/30 disabled:opacity-50 transition-colors font-mono"
            />
          </div>
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="flex items-center gap-1.5 px-5 py-3 bg-accent hover:bg-accent/80 disabled:opacity-40 disabled:cursor-not-allowed rounded-lg text-white text-sm font-semibold transition-colors shrink-0"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <ChevronRight className="w-4 h-4" />}
            Analyze
          </button>
        </div>

        {/* Quick-pick tickers */}
        <div className="flex items-center gap-2 mt-3 flex-wrap justify-center">
          <span className="text-[10px] text-muted uppercase tracking-wider font-mono">Quick:</span>
          {QUICK_TICKERS.map(t => (
            <button
              key={t}
              type="button"
              disabled={loading}
              onClick={() => { setInput(t); runResearch(t); }}
              className="px-2.5 py-1 border border-border rounded text-[11px] font-mono text-muted hover:text-foreground hover:border-accent/40 transition-colors disabled:opacity-40"
            >
              {t}
            </button>
          ))}
        </div>
      </form>

      {/* ── Loading state ───────────────────────────────────────────────── */}
      {loading && (
        <div className="space-y-4">
          <p className="text-center text-xs font-mono text-muted">
            Analysis typically takes 60–90 seconds via <span className="text-accent">claude-opus-5</span>
          </p>
          <TerminalLog activeStep={activeStep} />
        </div>
      )}

      {/* ── Error state ─────────────────────────────────────────────────── */}
      {error && !loading && (
        <div className="max-w-2xl mx-auto bg-negative/5 border border-negative/20 rounded-xl p-5 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-negative shrink-0 mt-0.5" />
          <div className="space-y-1">
            <p className="text-sm font-bold text-negative">Analysis Failed</p>
            <p className="text-xs text-muted font-sans">{error}</p>
            {error.includes("ANTHROPIC_API_KEY") && (
              <p className="text-xs text-muted font-mono mt-2">
                Add <code className="bg-surface border border-border rounded px-1">ANTHROPIC_API_KEY=sk-ant-...</code> to{" "}
                <code className="bg-surface border border-border rounded px-1">frontend/.env.local</code>
              </p>
            )}
          </div>
        </div>
      )}

      {/* ── Report ──────────────────────────────────────────────────────── */}
      {report && !loading && (
        <div ref={reportRef}>
          <ResearchReport r={report} />
        </div>
      )}

      {/* ── Empty hero (no report yet) ──────────────────────────────────── */}
      {!loading && !report && !error && (
        <div className="max-w-2xl mx-auto grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4">
          {[
            { icon: "⚙️", title: "18-Stage Workflow", desc: "From mandate to monitoring KPI dashboard, every institutional research stage covered." },
            { icon: "📊", title: "Charts & KPIs", desc: "Revenue, NI, EPS, margins, fair value range, scenario table — all rendered live." },
            { icon: "🎯", title: "Thesis + Falsifiers", desc: "Each thesis pillar comes with a measurable falsifier. No hype. Evidence-first." },
          ].map(card => (
            <div key={card.title} className="bg-surface border border-border rounded-xl p-4 space-y-2 text-center">
              <span className="text-2xl">{card.icon}</span>
              <p className="text-xs font-bold text-foreground font-mono">{card.title}</p>
              <p className="text-[11px] text-muted font-sans leading-snug">{card.desc}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
