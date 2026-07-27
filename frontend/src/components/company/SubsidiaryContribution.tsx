import type { CompanyOverview } from "@/lib/api";

const LINE_ITEM_LABELS: Record<string, string> = {
  revenue: "Revenue",
  profit_after_tax: "Profit After Tax",
  total_assets: "Total Assets",
};

export default function SubsidiaryContribution({ data }: { data: CompanyOverview["subsidiary_contributions"] }) {
  if (data.length === 0) return null;

  const byPeriod = new Map<string, typeof data>();
  for (const row of data) {
    const key = `${row.subsidiary_name}|${row.period_end}`;
    byPeriod.set(key, [...(byPeriod.get(key) ?? []), row]);
  }

  return (
    <div className="rounded-2xl border border-border bg-surface p-5">
      <h3 className="mb-1 font-semibold">Subsidiary Contribution</h3>
      <p className="mb-4 text-xs text-muted">
        Share of this issuer&apos;s own reported figures contributed by each subsidiary — scope
        (consolidated vs standalone) assumed consistent but not independently confirmed.
      </p>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[480px] text-left text-sm">
          <thead>
            <tr className="text-xs text-muted">
              <th className="pb-2 font-medium">Subsidiary</th>
              <th className="pb-2 font-medium">Year</th>
              <th className="pb-2 font-medium">Metric</th>
              <th className="pb-2 font-medium text-right">Contribution</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {data.map((row, i) => {
              const extreme = row.contribution_pct > 100 || row.contribution_pct < 0;
              return (
                <tr key={i}>
                  <td className="py-2">{row.subsidiary_name}</td>
                  <td className="py-2 text-muted">{row.period_end.slice(0, 4)}</td>
                  <td className="py-2 text-muted">{LINE_ITEM_LABELS[row.line_item] ?? row.line_item}</td>
                  <td className="py-2 text-right">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                        extreme ? "bg-accent-yellow/10 text-accent-yellow" : "bg-accent/10 text-accent"
                      }`}
                    >
                      {row.contribution_pct}%
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p className="mt-3 text-[10px] text-muted">
        A contribution above 100% means the parent&apos;s other segments/subsidiaries reported a net
        drag that year — a real signal, not a data error, when it appears.
      </p>
    </div>
  );
}
