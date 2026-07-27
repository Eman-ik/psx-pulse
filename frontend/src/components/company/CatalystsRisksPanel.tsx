import type { CompanyOverview } from "@/lib/api";

export default function CatalystsRisksPanel({ thesis }: { thesis: CompanyOverview["thesis"] }) {
  if (!thesis) {
    return (
      <div className="rounded-2xl border border-border bg-surface p-5">
        <h3 className="mb-2 font-semibold">Key Catalysts &amp; Risks</h3>
        <p className="text-xs text-muted">No analyst thesis on file for this company yet.</p>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-border bg-surface p-5">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="font-semibold">Key Catalysts &amp; Risks</h3>
        <span className="text-[10px] text-muted">As of {thesis.as_of_date}</span>
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <p className="mb-1.5 text-xs font-medium text-positive">Key Catalysts</p>
          <ul className="space-y-1 text-xs text-muted">
            {thesis.key_catalysts.map((c) => (
              <li key={c} className="flex gap-2">
                <span className="mt-1 h-1 w-1 shrink-0 rounded-full bg-positive" />
                {c}
              </li>
            ))}
          </ul>
        </div>
        <div>
          <p className="mb-1.5 text-xs font-medium text-negative">Key Risks</p>
          <ul className="space-y-1 text-xs text-muted">
            {thesis.key_risks.map((r) => (
              <li key={r} className="flex gap-2">
                <span className="mt-1 h-1 w-1 shrink-0 rounded-full bg-negative" />
                {r}
              </li>
            ))}
          </ul>
        </div>
      </div>
      <p className="mt-4 text-[10px] text-muted">
        {thesis.author} — analyst interpretation, not a regulated recommendation.
      </p>
    </div>
  );
}
