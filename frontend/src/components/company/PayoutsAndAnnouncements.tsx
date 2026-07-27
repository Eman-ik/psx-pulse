import type { CompanyOverview } from "@/lib/api";

const ACTION_LABELS: Record<string, string> = {
  dividend: "Dividend",
  bonus: "Bonus",
  rights: "Rights",
};

const CATEGORY_TONE: Record<string, string> = {
  results: "bg-accent/10 text-accent",
  board: "bg-accent-yellow/10 text-accent-yellow",
  dividend: "bg-positive/10 text-positive",
  other: "bg-muted/10 text-muted",
};

export default function PayoutsAndAnnouncements({ data }: { data: CompanyOverview }) {
  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <div className="rounded-2xl border border-border bg-surface p-5">
        <h3 className="mb-3 font-semibold">Payouts</h3>
        {data.payouts.length === 0 ? (
          <p className="text-xs text-muted">No payout history on file yet.</p>
        ) : (
          <div className="flex flex-col gap-2">
            {data.payouts.slice(0, 8).map((p, i) => (
              <div key={i} className="flex items-center justify-between text-sm">
                <span className="text-muted">{p.effective_date}</span>
                <span className="rounded-full bg-positive/10 px-2 py-0.5 text-xs font-medium text-positive">
                  {ACTION_LABELS[p.action_type] ?? p.action_type}
                  {p.ratio_or_amount != null && ` ${p.ratio_or_amount}%`}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="rounded-2xl border border-border bg-surface p-5">
        <h3 className="mb-3 font-semibold">Recent Announcements</h3>
        {data.announcements.length === 0 ? (
          <p className="text-xs text-muted">No announcements on file yet.</p>
        ) : (
          <div className="flex flex-col gap-2">
            {data.announcements.slice(0, 8).map((a) => (
              <div key={a.id} className="flex items-start justify-between gap-3 text-sm">
                <div className="min-w-0">
                  <p className="truncate">{a.title}</p>
                  <p className="text-xs text-muted">{a.published_at.slice(0, 10)}</p>
                </div>
                <span className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium ${CATEGORY_TONE[a.category] ?? CATEGORY_TONE.other}`}>
                  {a.category}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
