import Link from "next/link";
import { Eye } from "lucide-react";
import type { AnnouncementRow } from "@/lib/types";

const SENTIMENT_STYLES: Record<string, string> = {
  Positive: "bg-[#10161A] text-[#DAE1EE] font-semibold",
  Negative: "bg-[#B4C0D5]/50 text-[#10161A] border border-[#8E9CB7]/50 font-semibold",
  Neutral: "bg-white/80 text-[#566680] border border-white font-medium",
};

export default function AnnouncementsTable({ rows, isSample }: { rows: AnnouncementRow[]; isSample: boolean }) {
  return (
    <div className="glass-light rounded-2xl p-5 relative overflow-hidden">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="font-bold text-[#10161A] tracking-tight">Recent Corporate Disclosures &amp; Results</h3>
        {isSample ? (
          <span className="text-xs text-[#566680]">Sample data — backend stream pending</span>
        ) : (
          <Link href="/news" className="text-xs font-semibold text-[#10161A] hover:text-[#566680] underline transition-colors">
            View all disclosures
          </Link>
        )}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[560px] text-left text-sm">
          <thead>
            <tr className="text-xs font-semibold uppercase tracking-wider text-[#566680] border-b border-[#8E9CB7]/20">
              <th className="pb-3 font-semibold">Date</th>
              <th className="pb-3 font-semibold">Company</th>
              <th className="pb-3 font-semibold">Category</th>
              <th className="pb-3 font-semibold">Classification</th>
              <th className="pb-3 font-semibold text-right">Inspect</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#8E9CB7]/15">
            {rows.length === 0 && (
              <tr>
                <td colSpan={5} className="py-5 text-center text-xs text-[#566680]">
                  No disclosures recorded in current research cycle.
                </td>
              </tr>
            )}
            {rows.map((row, i) => (
              <tr key={`${row.symbol}-${row.title}-${i}`} className="text-sm hover:bg-white/40 transition-colors">
                <td className="py-3.5 text-xs font-mono text-[#566680]">{row.date}</td>
                <td className="py-3.5">
                  <p className="font-semibold text-[#10161A] leading-snug">{row.title}</p>
                  <p className="text-xs text-[#566680] mt-0.5">
                    {row.company} · <span className="font-mono font-medium text-[#10161A]">{row.symbol}</span>
                  </p>
                </td>
                <td className="py-3.5 text-xs text-[#566680] capitalize font-medium">{row.category}</td>
                <td className="py-3.5">
                  {row.sentimentLabel ? (
                    <span
                      className={`inline-block rounded-full px-2.5 py-0.5 text-[11px] ${SENTIMENT_STYLES[row.sentimentLabel] ?? SENTIMENT_STYLES.Neutral}`}
                    >
                      {row.sentimentLabel}
                    </span>
                  ) : (
                    <span className="text-xs text-[#8E9CB7]">Unclassified</span>
                  )}
                </td>
                <td className="py-3.5 text-right text-[#566680]">
                  <Eye size={15} className="ml-auto text-[#566680] hover:text-[#10161A] transition-colors cursor-pointer" />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
