interface StatCardProps {
  label: string;
  value: string;
  unit?: string;
  changePct: number;
}

export default function StatCard({ label, value, unit, changePct }: StatCardProps) {
  const positive = changePct >= 0;
  return (
    <div className="glass-light rounded-2xl p-5 relative overflow-hidden group">
      {/* Subtle top inner reflection border */}
      <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-white to-transparent opacity-80" />

      <p className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-[#566680]">
        {label}
      </p>
      
      <div className="flex items-baseline justify-between gap-3">
        <p className="text-2xl font-bold tracking-tight text-[#10161A]">
          {value}
          {unit && <span className="ml-1 text-xs font-medium text-[#566680]">{unit}</span>}
        </p>
        <span
          className={`rounded-full px-2.5 py-0.5 text-xs font-semibold tracking-tight ${
            positive
              ? "bg-[#10161A] text-[#DAE1EE]"
              : "bg-[#B4C0D5]/50 text-[#10161A] border border-[#8E9CB7]/40"
          }`}
        >
          {positive ? "+" : ""}
          {changePct.toFixed(1)}%
        </span>
      </div>
    </div>
  );
}
