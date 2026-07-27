import Link from "next/link";
import { Eye } from "lucide-react";
import { SENTIMENT_TONE } from "@/lib/sentiment";
import type { AnnouncementRow } from "@/lib/types";

export default function AnnouncementsTable({ rows, isSample }: { rows: AnnouncementRow[]; isSample: boolean }) {
  return (
    <div className="rounded-2xl border border-border bg-surface p-5">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="font-semibold">Recent Announcements &amp; Results</h3>
        {isSample ? (
          <span className="text-xs text-muted">Sample data — backend unreachable</span>
        ) : (
          <Link href="/news" className="text-xs text-accent hover:underline">
            View all
          </Link>
        )}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[560px] text-left text-sm">
          <thead>
            <tr className="text-xs text-muted">
              <th className="pb-3 font-medium">Date</th>
              <th className="pb-3 font-medium">Company</th>
              <th className="pb-3 font-medium">Type</th>
              <th className="pb-3 font-medium">Sentiment</th>
              <th className="pb-3 font-medium text-right">Source</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {rows.length === 0 && (
              <tr>
                <td colSpan={5} className="py-4 text-center text-xs text-muted">
                  No announcements on file yet.
                </td>
              </tr>
            )}
            {rows.map((row, i) => (
              <tr key={`${row.symbol}-${row.title}-${i}`} className="text-sm">
                <td className="py-3 text-muted">{row.date}</td>
                <td className="py-3">
                  <p className="font-medium">{row.title}</p>
                  <p className="text-xs text-muted">
                    {row.company} · {row.symbol}
                  </p>
                </td>
                <td className="py-3 text-muted capitalize">{row.category}</td>
                <td className="py-3">
                  {row.sentimentLabel ? (
                    <span
                      className={`rounded-full px-2.5 py-1 text-xs font-medium ${SENTIMENT_TONE[row.sentimentLabel] ?? SENTIMENT_TONE.Neutral}`}
                    >
                      {row.sentimentLabel}
                    </span>
                  ) : (
                    <span className="text-xs text-muted">Not classified</span>
                  )}
                </td>
                <td className="py-3 text-right text-muted">
                  <Eye size={15} className="ml-auto" />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
