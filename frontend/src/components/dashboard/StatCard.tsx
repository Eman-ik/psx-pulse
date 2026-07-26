interface StatCardProps {
  label: string;
  value: string;
  unit?: string;
  changePct: number;
}

export default function StatCard({ label, value, unit, changePct }: StatCardProps) {
  const positive = changePct >= 0;
  return (
    <div className="rounded-2xl border border-border bg-surface p-5">
      <p className="mb-3 text-xs text-muted">{label}</p>
      <div className="flex items-end justify-between">
        <p className="text-2xl font-semibold">
          {value}
          {unit && <span className="ml-1 text-sm font-normal text-muted">{unit}</span>}
        </p>
        <span
          className={`rounded-full px-2 py-1 text-xs font-medium ${
            positive ? "bg-positive/10 text-positive" : "bg-negative/10 text-negative"
          }`}
        >
          {positive ? "+" : ""}
          {changePct.toFixed(1)}%
        </span>
      </div>
    </div>
  );
}
