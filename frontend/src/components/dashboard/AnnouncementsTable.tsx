import { Eye, Download } from "lucide-react";
import type { AnnouncementRow, AnnouncementStatus } from "@/lib/types";

const STATUS_LABEL: Record<AnnouncementStatus, string> = {
  analyst_reviewed: "Analyst Reviewed",
  pending_review: "Pending Review",
  ingested: "Ingested",
};

const STATUS_TONE: Record<AnnouncementStatus, string> = {
  analyst_reviewed: "bg-positive/10 text-positive",
  pending_review: "bg-accent-yellow/10 text-accent-yellow",
  ingested: "bg-muted/10 text-muted",
};

export default function AnnouncementsTable({ rows }: { rows: AnnouncementRow[] }) {
  return (
    <div className="rounded-2xl border border-border bg-surface p-5">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="font-semibold">Recent Announcements &amp; Results</h3>
        <button className="text-xs text-accent hover:underline">Newest first</button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[560px] text-left text-sm">
          <thead>
            <tr className="text-xs text-muted">
              <th className="pb-3 font-medium">Date</th>
              <th className="pb-3 font-medium">Company</th>
              <th className="pb-3 font-medium">Type</th>
              <th className="pb-3 font-medium">Status</th>
              <th className="pb-3 font-medium text-right">Evidence</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {rows.map((row) => (
              <tr key={`${row.symbol}-${row.title}`} className="text-sm">
                <td className="py-3 text-muted">{row.date}</td>
                <td className="py-3">
                  <p className="font-medium">{row.title}</p>
                  <p className="text-xs text-muted">
                    {row.company} · {row.symbol}
                  </p>
                </td>
                <td className="py-3 text-muted">{row.category}</td>
                <td className="py-3">
                  <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${STATUS_TONE[row.status]}`}>
                    {STATUS_LABEL[row.status]}
                  </span>
                </td>
                <td className="py-3">
                  <div className="flex items-center justify-end gap-3 text-muted">
                    <Eye size={15} className="cursor-pointer hover:text-foreground" />
                    <Download size={15} className="cursor-pointer hover:text-foreground" />
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
