"use client";

import { useState } from "react";
import { CheckCircle2, ChevronDown, XCircle } from "lucide-react";
import type { Domain, Overview } from "@/lib/studio-api";
import { Card, day, ErrorNote, Label, Loading, Missing, num, pct, stateText, stateTone, tone, when } from "./ui";
import { useStudio } from "@/lib/studio-api";

const NOT_ASSESSED = new Set(["INSUFFICIENT_DATA", "UNAVAILABLE"]);

function DomainCard({ d }: { d: Domain }) {
  const [open, setOpen] = useState(false);
  const assessed = !NOT_ASSESSED.has(d.state);
  return (
    <div className="rounded-lg border border-border p-4">
      <p className="text-xs text-muted">{d.label}</p>
      <p className={`mt-1 text-lg font-bold ${assessed ? stateTone(d.state) : "text-muted"}`}>{stateText(d.state)}</p>
      <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-muted">
        {d.stale && <Label kind="STALE" />}
        {assessed && d.confidence != null && <span>Confidence {Math.round(d.confidence * 100)}%</span>}
        {d.as_of && <span>as of {day(d.as_of)}</span>}
      </div>
      {!assessed && d.reason && <p className="mt-2 text-xs text-muted">{d.reason}</p>}
      {(d.supports.length > 0 || d.could_change.length > 0) && (
        <>
          <button
            type="button"
            onClick={() => setOpen(!open)}
            aria-expanded={open}
            className="mt-3 flex items-center gap-1 text-xs font-medium text-accent hover:underline"
          >
            <ChevronDown className={`h-3 w-3 transition ${open ? "rotate-180" : ""}`} /> Why, and what would change it
          </button>
          {open && (
            <div className="mt-2 space-y-2 text-xs">
              <ul className="list-disc space-y-1 pl-4">
                {d.supports.map((s) => (
                  <li key={s}>{s}</li>
                ))}
              </ul>
              {d.could_change.map((c) => (
                <p key={c} className="text-muted">{c}</p>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

export function OverviewTab({ symbol, onOpenTab }: { symbol: string; onOpenTab: (tab: string) => void }) {
  const { data, error, loading } = useStudio<Overview>(symbol, "overview");
  if (loading) return <Loading what="Loading overview" />;
  if (error || !data) return <ErrorNote message={error ?? "No data."} />;
  const { price, research_view: view } = data;
  const conf = view.data_confidence;

  return (
    <div className="space-y-6">
      <Card>
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold">{data.name}</h2>
            <p className="text-sm text-muted">
              {data.symbol} · {data.sector ?? "Sector not on file"} · {data.listing_status}
            </p>
          </div>
          <div className="text-right">
            <p className="text-2xl font-bold tabular-nums">{price.close == null ? "—" : `PKR ${num(price.close)}`}</p>
            <p className={`text-sm font-semibold ${tone(price.change_pct)}`}>{pct(price.change_pct)} on the day</p>
          </div>
        </div>
        <p className="mt-3 flex flex-wrap items-center gap-2 text-xs text-muted">
          <Label kind={price.freshness.stale ? "STALE" : price.badge} />
          Close {day(price.freshness.as_of)} · {price.freshness.sources.join(", ") || "no source"} · retrieved {when(price.freshness.retrieved_at)}
        </p>
      </Card>

      <Card title="What it does">
        {data.what_it_does ? (
          <>
            <p className="text-sm leading-relaxed">{data.what_it_does}</p>
            {data.profile_source && (
              <p className="mt-3 flex flex-wrap items-center gap-2 text-xs text-muted">
                <Label kind="VERIFIED" /> Company profile from{" "}
                <a href={data.profile_source.url} target="_blank" rel="noreferrer" className="underline">PSX</a>, retrieved {when(data.profile_source.retrieved_at)}
              </p>
            )}
          </>
        ) : (
          <Missing>No company profile on file.</Missing>
        )}
      </Card>

      <Card
        title="Research view"
        aside={<span className="text-xs text-muted">Methodology {view.methodology_version}</span>}
      >
        <div className="mb-5 rounded-lg bg-background/60 p-4 text-sm">
          <p className="font-semibold">
            Overall: <span className={stateTone(view.overall.state)}>{stateText(view.overall.state)}</span>
          </p>
          <p className="mt-1 text-muted">{view.overall.reason}</p>
          {view.overall.disagreements.map((x) => (
            <p key={x} className="mt-1">{x}</p>
          ))}
          <p className="mt-2 text-xs text-muted">
            There is no single score: each domain stands alone, and a missing or stale input leaves a domain unassessed instead of
            filling it in.
          </p>
        </div>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {view.domains.map((d) => (
            <DomainCard key={d.key} d={d} />
          ))}
          <div className="rounded-lg border border-border p-4">
            <p className="text-xs text-muted">Data confidence</p>
            <p className={`mt-1 text-lg font-bold ${stateTone(conf.level)}`}>{stateText(conf.level)}</p>
            <ul className="mt-2 space-y-1 text-xs">
              {conf.checks.map((c) => (
                <li key={c.key} className="flex gap-1.5">
                  {c.passed ? <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-positive" /> : <XCircle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-negative" />}
                  <span><span className="font-medium">{c.key.replaceAll("_", " ")}:</span> <span className="text-muted">{c.detail}</span></span>
                </li>
              ))}
            </ul>
            <p className="mt-2 text-[11px] text-muted">{conf.rule}</p>
          </div>
        </div>
        <p className="mt-4 text-xs text-muted">Describes the evidence on file as of {when(data.generated_at)}. It is not a recommendation.</p>
      </Card>

      <Card
        title="Latest announcements"
        aside={<button type="button" onClick={() => onOpenTab("events")} className="text-xs font-medium text-accent hover:underline">All events</button>}
      >
        {data.latest_events.length === 0 ? (
          <Missing>No announcements on file.</Missing>
        ) : (
          <ul className="divide-y divide-border/50 text-sm">
            {data.latest_events.map((e) => (
              <li key={e.id} className="flex flex-wrap items-baseline justify-between gap-2 py-2">
                <span>
                  {e.source_url ? <a href={e.source_url} target="_blank" rel="noreferrer" className="underline">{e.title}</a> : e.title}
                  <span className="ml-2 text-xs text-muted">{e.category}</span>
                </span>
                <span className="text-xs text-muted">{day(e.published_at)}</span>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
