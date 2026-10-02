"use client";

import { useState } from "react";
import { type StudioEvent, useStudio } from "@/lib/studio-api";
import { Card, day, ErrorNote, Loading, Missing, when } from "./ui";

type Events = {
  total: number;
  limit: number;
  offset: number;
  events: StudioEvent[];
  category_counts_90d: Record<string, number>;
  corporate_actions: { status: string; covered_from: string | null; items: unknown[]; note: string };
  sentiment: { status: string; note: string };
};

const CATEGORIES = [["", "All"], ["results", "Financial results"], ["board", "Board meetings"], ["other", "Other"]] as const;
const PAGE = 15;

export function EventsTab({ symbol }: { symbol: string }) {
  const [category, setCategory] = useState("");
  const [offset, setOffset] = useState(0);
  const { data, error, loading } = useStudio<Events>(symbol, `events?limit=${PAGE}&offset=${offset}${category ? `&category=${category}` : ""}`);

  return (
    <div className="space-y-6">
      <Card title="Announcements">
        <div className="mb-4 flex flex-wrap gap-2" role="group" aria-label="Filter by category">
          {CATEGORIES.map(([value, label]) => (
            <button
              key={value}
              type="button"
              aria-pressed={category === value}
              onClick={() => {
                setCategory(value);
                setOffset(0);
              }}
              className={`rounded-full border px-3 py-1 text-xs font-medium ${category === value ? "border-accent bg-accent/10 text-accent" : "border-border text-muted hover:text-foreground"}`}
            >
              {label}
            </button>
          ))}
        </div>

        {loading && <Loading what="Loading announcements" />}
        {error && <ErrorNote message={error} />}
        {data && data.events.length === 0 && <Missing>No announcements match.</Missing>}
        {data && data.events.length > 0 && (
          <>
            <ul className="divide-y divide-border/50">
              {data.events.map((e) => (
                <li key={e.id} className="py-3 text-sm">
                  <div className="flex flex-wrap items-baseline justify-between gap-2">
                    <span className="font-medium">
                      {e.source_url ? <a href={e.source_url} target="_blank" rel="noreferrer" className="underline">{e.title}</a> : e.title}
                    </span>
                    <span className="text-xs text-muted">{day(e.published_at)}</span>
                  </div>
                  <p className="mt-0.5 text-xs text-muted">
                    {e.category} · source tier {e.source_tier ?? "unknown"} · retrieved {when(e.retrieved_at)}
                  </p>
                </li>
              ))}
            </ul>
            <div className="mt-4 flex items-center justify-between text-xs text-muted">
              <span>
                {data.offset + 1}-{data.offset + data.events.length} of {data.total}
              </span>
              <span className="flex gap-2">
                <button type="button" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE))} className="rounded border border-border px-3 py-1 disabled:opacity-40">Newer</button>
                <button type="button" disabled={offset + PAGE >= data.total} onClick={() => setOffset(offset + PAGE)} className="rounded border border-border px-3 py-1 disabled:opacity-40">Older</button>
              </span>
            </div>
            <p className="mt-3 text-xs text-muted">PSX lists only a company&apos;s most recent announcements, so older history isn&apos;t available here.</p>
          </>
        )}
      </Card>

      <div className="grid gap-6 md:grid-cols-2">
        <Card title="Corporate actions">
          <Missing>
            {data?.corporate_actions.status === "NOT_YET_SEARCHED"
              ? "Dividends, bonus issues, rights and splits have not been loaded for this company yet, so none are shown, and none are assumed not to exist."
              : "No corporate actions in the searched range."}
          </Missing>
          <p className="mt-2 text-xs text-muted">{data?.corporate_actions.note}</p>
        </Card>
        <Card title="Sentiment">
          <Missing>{data?.sentiment.note ?? "No validated sentiment or impact model yet."}</Missing>
          {data && Object.keys(data.category_counts_90d).length > 0 && (
            <p className="mt-2 text-xs text-muted">
              Last 90 days: {Object.entries(data.category_counts_90d).map(([c, n]) => `${n} ${c}`).join(", ")}.
            </p>
          )}
        </Card>
      </div>
    </div>
  );
}
