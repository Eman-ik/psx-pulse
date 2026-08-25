import type { ComparisonRow } from "@/lib/api";

const META: Record<ComparisonRow["coverage_status"], { emoji: string; label: string; title: string }> = {
  live: {
    emoji: "🟢",
    label: "Live",
    title: "Live price + financials on file.",
  },
  historical: {
    emoji: "🟡",
    label: "Historical",
    title: "Price history on file, but no live quote (outside the fertilizer+cement pilot's live-pricing scope).",
  },
  partial: {
    emoji: "🟠",
    label: "Partial",
    title: "Some financial data on file, but no price history yet.",
  },
  unverified: {
    emoji: "🔴",
    label: "Unverified",
    title: "An identity record exists (PSX-listed), but no price or financial data has been ingested yet.",
  },
};

export default function CoverageBadge({ status }: { status: ComparisonRow["coverage_status"] }) {
  const m = META[status];
  return (
    <span title={m.title} className="inline-flex cursor-help items-center gap-1 text-xs text-muted">
      <span aria-hidden>{m.emoji}</span> {m.label}
    </span>
  );
}
