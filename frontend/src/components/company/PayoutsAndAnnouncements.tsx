import { ExternalLink } from "lucide-react";
import type { CompanyOverview } from "@/lib/api";
import { SENTIMENT_TONE, sentimentLabel } from "@/lib/sentiment";
import NewsIntelligenceTerminal from "./NewsIntelligenceTerminal";

const ACTION_LABELS: Record<string, string> = {
  dividend: "Dividend",
  bonus: "Bonus",
  rights: "Rights",
};

const CATEGORY_TONE: Record<string, string> = {
  results: "bg-accent/10 text-accent",
  financials: "bg-accent/10 text-accent",
  board: "bg-accent-yellow/10 text-accent-yellow",
  leadership: "bg-accent-yellow/10 text-accent-yellow",
  dividend: "bg-positive/10 text-positive",
  payout: "bg-positive/10 text-positive",
  other: "bg-muted/10 text-muted",
  general: "bg-muted/10 text-muted",
};

export default function PayoutsAndAnnouncements({ data }: { data: CompanyOverview }) {
  return (
    <div className="space-y-0">
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
          <div className="flex flex-col gap-3">
            {data.announcements.slice(0, 8).map((a) => {
              const sentiment = sentimentLabel(a.sentiment_score);
              return (
                <div key={a.id} className="border-b border-border pb-3 last:border-0 last:pb-0">
                  <div className="flex items-start justify-between gap-3 text-sm">
                    <div className="min-w-0">
                      <p className="truncate">{a.title}</p>
                      <p className="text-xs text-muted">{a.published_at.slice(0, 10)}</p>
                    </div>
                    <div className="flex shrink-0 items-center gap-1.5">
                      {sentiment && (
                        <span
                          className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${SENTIMENT_TONE[sentiment] ?? SENTIMENT_TONE.Neutral}`}
                        >
                          {sentiment}
                        </span>
                      )}
                      <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${CATEGORY_TONE[a.category] ?? CATEGORY_TONE.other}`}>
                        {a.category}
                      </span>
                    </div>
                  </div>
                  {a.summary && <p className="mt-1.5 text-xs text-muted">{a.summary}</p>}
                  {a.source_url && (
                    <a
                      href={a.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="mt-1.5 inline-flex items-center gap-1 text-[11px] text-accent hover:underline"
                    >
                      <ExternalLink size={10} /> Original source
                    </a>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
      <NewsIntelligenceTerminal />
    </div>
  );
}
