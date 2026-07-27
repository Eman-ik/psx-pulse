"use client";

import { useMemo, useState } from "react";
import { ExternalLink, Search } from "lucide-react";
import type { NewsAnnouncement } from "@/lib/api";
import { SENTIMENT_TONE, sentimentLabel } from "@/lib/sentiment";

interface CompanyInfo {
  name: string;
  symbol: string | null;
}

export default function NewsFeed({
  rows,
  companyById,
}: {
  rows: NewsAnnouncement[];
  companyById: Record<number, CompanyInfo>;
}) {
  const [query, setQuery] = useState("");
  const [issuerFilter, setIssuerFilter] = useState<string>("all");
  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const [sentimentFilter, setSentimentFilter] = useState<string>("all");

  const categories = useMemo(() => Array.from(new Set(rows.map((r) => r.category))).sort(), [rows]);
  const issuerOptions = useMemo(() => {
    const seen = new Map<number, string>();
    for (const r of rows) {
      if (r.issuer_id != null && !seen.has(r.issuer_id)) {
        seen.set(r.issuer_id, companyById[r.issuer_id]?.name ?? `Issuer ${r.issuer_id}`);
      }
    }
    return Array.from(seen.entries()).sort((a, b) => a[1].localeCompare(b[1]));
  }, [rows, companyById]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return rows.filter((r) => {
      if (q && !r.title.toLowerCase().includes(q)) return false;
      if (issuerFilter !== "all" && String(r.issuer_id) !== issuerFilter) return false;
      if (categoryFilter !== "all" && r.category !== categoryFilter) return false;
      if (sentimentFilter !== "all" && (sentimentLabel(r.sentiment_score) ?? "Unclassified") !== sentimentFilter)
        return false;
      return true;
    });
  }, [rows, query, issuerFilter, categoryFilter, sentimentFilter]);

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <div className="flex min-w-[220px] flex-1 items-center gap-2 rounded-full border border-border bg-surface px-4 py-2">
          <Search size={15} className="text-muted" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search headlines..."
            className="w-full bg-transparent text-sm text-foreground placeholder:text-muted focus:outline-none"
          />
        </div>
        <select
          value={issuerFilter}
          onChange={(e) => setIssuerFilter(e.target.value)}
          className="rounded-full border border-border bg-surface px-3 py-2 text-xs text-foreground"
        >
          <option value="all">All companies</option>
          {issuerOptions.map(([id, name]) => (
            <option key={id} value={id}>
              {name}
            </option>
          ))}
        </select>
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="rounded-full border border-border bg-surface px-3 py-2 text-xs capitalize text-foreground"
        >
          <option value="all">All types</option>
          {categories.map((c) => (
            <option key={c} value={c} className="capitalize">
              {c}
            </option>
          ))}
        </select>
        <select
          value={sentimentFilter}
          onChange={(e) => setSentimentFilter(e.target.value)}
          className="rounded-full border border-border bg-surface px-3 py-2 text-xs text-foreground"
        >
          <option value="all">All sentiment</option>
          <option value="Positive">Positive</option>
          <option value="Neutral">Neutral</option>
          <option value="Negative">Negative</option>
        </select>
      </div>

      <p className="mb-3 text-xs text-muted">
        {filtered.length} of {rows.length} announcements
      </p>

      <div className="flex flex-col gap-3">
        {filtered.length === 0 && (
          <div className="rounded-2xl border border-border bg-surface p-6 text-center text-sm text-muted">
            No announcements match these filters.
          </div>
        )}
        {filtered.map((a) => {
          const sentiment = sentimentLabel(a.sentiment_score);
          const company = a.issuer_id != null ? companyById[a.issuer_id] : undefined;
          return (
            <div key={a.id} className="rounded-2xl border border-border bg-surface p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-sm font-medium">{a.title}</p>
                  <p className="mt-1 text-xs text-muted">
                    {a.published_at.slice(0, 10)}
                    {company && ` · ${company.name}${company.symbol ? ` (${company.symbol})` : ""}`}
                  </p>
                </div>
                <div className="flex shrink-0 items-center gap-1.5">
                  {sentiment && (
                    <span
                      className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${SENTIMENT_TONE[sentiment] ?? SENTIMENT_TONE.Neutral}`}
                    >
                      {sentiment}
                    </span>
                  )}
                  <span className="rounded-full bg-surface-alt px-2 py-0.5 text-[10px] font-medium capitalize text-muted">
                    {a.category}
                  </span>
                </div>
              </div>
              {a.summary && <p className="mt-2 text-xs text-muted">{a.summary}</p>}
              {a.source_url && (
                <a
                  href={a.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-2 inline-flex items-center gap-1 text-[11px] text-accent hover:underline"
                >
                  <ExternalLink size={10} /> Original source
                </a>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
