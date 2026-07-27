import { ShieldCheck } from "lucide-react";
import type { CompanyOverview } from "@/lib/api";

const TIER_LABELS: Record<string, string> = {
  primary: "Primary source",
  licensed_secondary: "Licensed secondary source",
  prohibited: "Prohibited source",
};

export default function DataQualityPanel({ sources }: { sources: CompanyOverview["sources"] }) {
  const byType = sources.reduce<Record<string, number>>((acc, s) => {
    acc[s.document_type] = (acc[s.document_type] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <div className="rounded-2xl border border-border bg-surface p-5">
      <div className="mb-3 flex items-center gap-2">
        <ShieldCheck size={16} className="text-positive" />
        <h3 className="font-semibold">Data Quality &amp; Sources</h3>
      </div>
      {sources.length === 0 ? (
        <p className="text-xs text-muted">No source documents linked yet.</p>
      ) : (
        <>
          <div className="mb-3 flex flex-wrap gap-2">
            {Object.entries(byType).map(([type, count]) => (
              <span key={type} className="rounded-full bg-surface-alt px-2.5 py-1 text-xs">
                {type.replaceAll("_", " ")} × {count}
              </span>
            ))}
          </div>
          <div className="flex flex-col gap-1.5 text-xs text-muted">
            {sources.slice(0, 5).map((s, i) => (
              <div key={i} className="flex items-center justify-between">
                <span>{TIER_LABELS[s.source_tier] ?? s.source_tier}</span>
                <span>fetched {s.fetched_at.slice(0, 10)}</span>
              </div>
            ))}
          </div>
        </>
      )}
      <p className="mt-4 text-[10px] text-muted">
        Every fact on this page traces back to one of the source documents above — see
        docs/rights_matrix.template.md for the compliance status of each source.
      </p>
    </div>
  );
}
