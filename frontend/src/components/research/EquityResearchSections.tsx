"use client";

import { CheckCircle2, CircleDashed } from "lucide-react";
import type { EquityResearchReportResponse } from "@/lib/api";

// Renders whatever the real Equity-research pipeline actually published for a
// ticker -- section by section, each honestly marked as real content or not-yet-
// available (has_real_content), rather than a single polished narrative. Replaces
// the old ResearchReport/ResearchJSON rich-chart view, which rendered a single-shot
// LLM's guess at all 18 stages regardless of what evidence actually backed it.
export function EquityResearchSections({ r }: { r: EquityResearchReportResponse }) {
  if (r.not_covered) {
    return (
      <div className="max-w-2xl mx-auto bg-surface border border-border rounded-xl p-5 text-center space-y-2">
        <p className="text-sm font-bold text-foreground">Not yet covered</p>
        <p className="text-xs text-muted font-sans">{r.coverage_note}</p>
      </div>
    );
  }

  const sections = r.sections ?? [];
  const total = r.sections_total ?? sections.length;
  const real = r.sections_with_real_content ?? sections.filter(s => s.has_real_content).length;

  return (
    <div className="max-w-3xl mx-auto space-y-5">
      <div className="flex items-center justify-between gap-3 flex-wrap bg-surface border border-border rounded-xl p-4">
        <div>
          <p className="text-sm font-bold text-foreground">
            {r.company_name ?? r.ticker} · {r.ticker}
          </p>
          <p className="text-[11px] text-muted font-mono mt-0.5">
            {r.status}{r.is_preliminary ? " (preliminary)" : ""}
            {r.published_at ? ` · published ${r.published_at.slice(0, 10)}` : ""}
          </p>
        </div>
        <div className="text-right">
          <p className="text-xs font-mono text-foreground">
            {real} / {total} sections have real content
          </p>
          <p className="text-[10px] text-muted font-sans">
            Real, citation-grounded Equity-research pipeline output — not an AI guess.
          </p>
        </div>
      </div>

      {sections.map((s, i) => (
        <div
          key={i}
          className={`border rounded-xl p-4 ${
            s.has_real_content ? "border-border bg-surface" : "border-border/50 bg-surface/40"
          }`}
        >
          <div className="flex items-center gap-2 mb-2">
            {s.has_real_content ? (
              <CheckCircle2 className="w-3.5 h-3.5 text-positive shrink-0" />
            ) : (
              <CircleDashed className="w-3.5 h-3.5 text-muted shrink-0" />
            )}
            <p className="text-xs font-bold text-foreground">{s.title}</p>
          </div>
          {s.has_real_content ? (
            <p className="text-[13px] text-foreground/90 font-sans whitespace-pre-wrap leading-relaxed">
              {s.content}
            </p>
          ) : (
            <p className="text-[11px] text-muted font-sans italic">
              Not yet available
              {s.missing_evidence.length > 0 ? ` — missing: ${s.missing_evidence.join(", ")}` : ""}.
            </p>
          )}
        </div>
      ))}
    </div>
  );
}
