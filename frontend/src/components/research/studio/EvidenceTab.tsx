"use client";

import { useStudio } from "@/lib/studio-api";
import { Card, day, ErrorNote, Label, Loading, Missing, when } from "./ui";

type Evidence = {
  datasets: { dataset: string; status: string; as_of: string | null; source: string | null; label: string }[];
  documents: { id: number; type: string; url: string | null; local_path: string | null; tier: string; published_at: string | null; retrieved_at: string; figures_linked: number }[];
  latest_runs: { id: number; source: string; table: string | null; status: string; finished_at: string | null; rows_inserted: number; error_count: number }[];
  balance_sheet_flags: { period_end: string; total_assets: number; total_liabilities_plus_equity: number; diff_pct: number }[];
  label_legend: Record<string, string>;
};

export function EvidenceTab({ symbol }: { symbol: string }) {
  const { data, error, loading } = useStudio<Evidence>(symbol, "evidence");
  if (loading) return <Loading what="Loading evidence ledger" />;
  if (error || !data) return <ErrorNote message={error ?? "No data."} />;

  return (
    <div className="space-y-6">
      <Card title="Coverage and freshness">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[560px] text-sm">
            <thead>
              <tr className="text-left text-muted">
                <th className="py-2 font-medium">Dataset</th>
                <th className="py-2 font-medium">Status</th>
                <th className="py-2 font-medium">As of</th>
                <th className="py-2 font-medium">Source</th>
                <th className="py-2 font-medium">Label</th>
              </tr>
            </thead>
            <tbody>
              {data.datasets.map((d) => (
                <tr key={d.dataset} className="border-t border-border/50">
                  <td className="py-2 font-medium">{d.dataset}</td>
                  <td className="py-2">{d.status.replaceAll("_", " ").toLowerCase()}</td>
                  <td className="py-2">{day(d.as_of)}</td>
                  <td className="max-w-[260px] truncate py-2 text-muted" title={d.source ?? ""}>{d.source ?? "—"}</td>
                  <td className="py-2"><Label kind={d.label} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <dl className="mt-4 grid gap-1 text-xs text-muted sm:grid-cols-2">
          {Object.entries(data.label_legend).map(([k, v]) => (
            <div key={k} className="flex items-center gap-2"><Label kind={k} /> {v}</div>
          ))}
        </dl>
      </Card>

      {data.balance_sheet_flags.length > 0 && (
        <Card title="Data-quality flags">
          {data.balance_sheet_flags.map((f) => (
            <p key={f.period_end} className="text-sm">
              {day(f.period_end)}: total assets {(f.total_assets / 1e6).toFixed(2)} bn do not match liabilities plus equity{" "}
              {(f.total_liabilities_plus_equity / 1e6).toFixed(2)} bn ({f.diff_pct}% apart). The source itself doesn&apos;t balance.
            </p>
          ))}
        </Card>
      )}

      <Card title="Source documents">
        {data.documents.length === 0 ? (
          <Missing>No source documents on file.</Missing>
        ) : (
          <ul className="divide-y divide-border/50 text-sm">
            {data.documents.map((d) => (
              <li key={d.id} className="py-2">
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <span className="font-medium">{d.type.replaceAll("_", " ")}</span>
                  <span className="text-xs text-muted">published {day(d.published_at)} · retrieved {when(d.retrieved_at)}</span>
                </div>
                <p className="break-all text-xs text-muted">
                  {d.url ? <a href={d.url} target="_blank" rel="noreferrer" className="underline">{d.url}</a> : d.local_path}
                  {" · "}tier {d.tier}
                  {d.figures_linked > 0 && ` · ${d.figures_linked} figures linked`}
                </p>
              </li>
            ))}
          </ul>
        )}
      </Card>

      <Card title="Latest data loads">
        <ul className="divide-y divide-border/50 text-sm">
          {data.latest_runs.map((r) => (
            <li key={r.id} className="flex flex-wrap justify-between gap-2 py-2">
              <span>{r.source} → {r.table ?? "n/a"}</span>
              <span className={`text-xs ${r.status === "ok" ? "text-muted" : "text-negative"}`}>
                {r.status} · {r.rows_inserted} rows · {r.error_count} errors · {when(r.finished_at)}
              </span>
            </li>
          ))}
        </ul>
        <p className="mt-2 text-xs text-muted">These are market-wide loads, not specific to this company.</p>
      </Card>
    </div>
  );
}
