"use client";

import { AlertTriangle, CheckCircle2, Factory, HelpCircle } from "lucide-react";

export interface IndustryIntelligence {
  sector: string;
  as_of: string;
  structure: {
    listed_competitor_count: number;
    competitors: { symbol: string; name: string; coverage_tier: string }[];
    dimensions: {
      key: string;
      label: string;
      evidence_status: "available" | "partial" | "missing";
      available_series: string[];
      required_source: string;
    }[];
  };
  economics: {
    verified_company_count: number;
    listed_company_count: number;
    verified_coverage_pct: number;
    sector_medians: {
      key: string;
      label: string;
      value: number | null;
      unit: string;
      companies_covered: number;
      evidence_status: string;
    }[];
    operating_data_coverage: Record<string, { companies_covered: number; observations: number; latest_period: string; units: string[] }>;
    derived_metrics: Record<string, { value?:number; unit:string; period_end:string; formula:string; values?:{issuer_id:number;value:number}[] }>;
    profit_driver_framework: string[];
    profit_driver_status: string;
  };
  cycle: { state: string; reason: string };
  economy_context: {
    status: string;
    conclusion: string;
    transmission_channels: { key: string; label: string; industry_effect: string; required_source: string; current_observation: number | null; unit:string|null; period:string|null; source:string|null; evidence_status: string }[];
  };
  attractiveness: { status: string; conclusion: string; required_for_conclusion: string[] };
}

const number = (value: number | null, unit: string) => value == null ? "Not available" : `${value.toFixed(2)}${unit}`;

export function IndustryIntelligencePanel({ industry }: { industry: IndustryIntelligence }) {
  return <div className="space-y-5">
    <section className="rounded-xl border border-border bg-surface p-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div><p className="text-xs font-bold uppercase tracking-wider text-accent">Stage 2 · Industry</p><h3 className="mt-1 text-xl font-bold">{industry.sector} industry structure</h3><p className="mt-1 text-sm text-muted">Company → Industry → Economy. Missing evidence is shown rather than inferred.</p></div>
        <div className="rounded-lg border border-border bg-background px-4 py-3 text-center"><p className="text-2xl font-black">{industry.structure.listed_competitor_count}</p><p className="text-[10px] uppercase text-muted">listed competitors</p></div>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">{industry.structure.competitors.map(company=><span key={company.symbol} title={company.name} className={`rounded-full border px-2.5 py-1 text-xs ${company.coverage_tier === "full" ? "border-positive/40 text-positive" : "border-border text-muted"}`}>{company.symbol} · {company.coverage_tier.replace("_", " ")}</span>)}</div>
    </section>

    <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
      {industry.structure.dimensions.map(item=><article key={item.key} className="rounded-xl border border-border bg-surface p-4">
        <div className="flex items-center justify-between gap-2"><h4 className="font-semibold">{item.label}</h4>{item.evidence_status === "missing" ? <HelpCircle className="h-4 w-4 text-amber-300"/> : <CheckCircle2 className="h-4 w-4 text-positive"/>}</div>
        <p className={`mt-2 text-xs font-bold uppercase ${item.evidence_status === "missing" ? "text-amber-300" : "text-positive"}`}>{item.evidence_status}</p>
        {item.available_series.length ? <p className="mt-2 text-xs text-muted">Available: {item.available_series.join(", ")}</p> : <p className="mt-2 text-xs text-muted">Needed: {item.required_source}</p>}
      </article>)}
    </section>

    <section className="grid gap-5 lg:grid-cols-2">
      <div className="rounded-xl border border-border bg-surface p-5"><h3 className="font-bold">Industry economics</h3><p className="mt-1 text-xs text-muted">Verified fundamentals: {industry.economics.verified_company_count}/{industry.economics.listed_company_count} companies ({industry.economics.verified_coverage_pct.toFixed(1)}%)</p><div className="mt-4 space-y-3">{industry.economics.sector_medians.map(metric=><div key={metric.key} className="flex items-center justify-between gap-4 border-b border-border pb-2"><div><p className="text-sm font-medium">{metric.label}</p><p className="text-[10px] text-muted">{metric.companies_covered} verified companies</p></div><p className="font-mono font-bold">{number(metric.value, metric.unit)}</p></div>)}</div></div>
      <div className="rounded-xl border border-border bg-surface p-5"><div className="flex items-center gap-2"><Factory className="h-5 w-5 text-accent"/><h3 className="font-bold">Where profits may come from</h3></div><p className="mt-2 text-xs text-amber-300">Research framework — each driver still requires sourced confirmation.</p><ul className="mt-4 space-y-2 text-sm text-muted">{industry.economics.profit_driver_framework.map(item=><li key={item}>• {item}</li>)}</ul></div>
    </section>

    {Object.keys(industry.economics.derived_metrics).length>0&&<section className="rounded-xl border border-border bg-surface p-5"><h3 className="font-bold">Derived industry indicators</h3><p className="mt-1 text-xs text-muted">Calculated deterministically from verified industry observations.</p><div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">{Object.entries(industry.economics.derived_metrics).filter(([,metric])=>metric.value!=null).map(([key,metric])=><article key={key} className="rounded-lg border border-border bg-background p-4"><p className="text-[10px] font-bold uppercase text-muted">{key.replaceAll("_"," ")}</p><p className="mt-2 font-mono text-xl font-bold">{metric.value?.toFixed(2)} {metric.unit}</p><p className="mt-2 text-[10px] text-muted">{metric.formula} · {metric.period_end}</p></article>)}</div></section>}

    <section className="grid gap-5 lg:grid-cols-2">
      <div className="rounded-xl border border-amber-400/30 bg-amber-400/10 p-5"><div className="flex items-center gap-2 text-amber-200"><AlertTriangle className="h-5 w-5"/><h3 className="font-bold">Industry cycle: {industry.cycle.state.replaceAll("_", " ")}</h3></div><p className="mt-2 text-sm text-amber-100/80">{industry.cycle.reason}</p></div>
      <div className="rounded-xl border border-border bg-surface p-5"><h3 className="font-bold">Is this structurally a good industry?</h3><p className="mt-2 text-sm text-muted">{industry.attractiveness.conclusion}</p><p className="mt-4 text-xs font-bold uppercase text-muted">Required before conclusion</p><ul className="mt-2 space-y-1 text-xs text-muted">{industry.attractiveness.required_for_conclusion.map(item=><li key={item}>• {item}</li>)}</ul></div>
    </section>

    <section className="rounded-xl border border-border bg-surface p-5"><p className="text-xs font-bold uppercase tracking-wider text-accent">Industry → Economy</p><h3 className="mt-1 font-bold">Economic transmission map</h3><p className="mt-2 text-sm text-muted">{industry.economy_context.conclusion}</p><div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">{industry.economy_context.transmission_channels.map(channel=><article key={channel.key} className="rounded-lg border border-border bg-background p-4"><div className="flex items-center justify-between"><h4 className="text-sm font-semibold">{channel.label}</h4><span className={`text-[10px] font-bold uppercase ${channel.evidence_status === "available" ? "text-positive" : "text-amber-300"}`}>{channel.evidence_status}</span></div>{channel.current_observation != null&&<p className="mt-2 font-mono text-lg font-bold">{channel.current_observation.toFixed(2)} {channel.unit}<span className="ml-2 text-[10px] font-normal text-muted">{channel.period}</span></p>}<p className="mt-2 text-xs text-muted">{channel.industry_effect}</p><p className="mt-3 text-[10px] text-muted">{channel.source ? `Source: ${channel.source}` : `Source required: ${channel.required_source}`}</p></article>)}</div></section>
  </div>;
}
