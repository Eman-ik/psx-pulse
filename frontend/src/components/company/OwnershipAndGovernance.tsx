import { ChevronRight } from "lucide-react";
import type { CompanyOverview } from "@/lib/api";

export default function OwnershipAndGovernance({ data }: { data: CompanyOverview }) {
  const { parent_chain, subsidiaries, board } = data;

  return (
    <div className="rounded-2xl border border-border bg-surface p-5">
      <h3 className="mb-3 font-semibold">Group, Ownership &amp; Leadership</h3>

      {(parent_chain.length > 0 || subsidiaries.length > 0) && (
        <div className="mb-4 flex flex-wrap items-center gap-2 text-sm">
          {[...parent_chain].reverse().map((p) => (
            <span key={p.id} className="flex items-center gap-2">
              <span className="rounded-full bg-surface-alt px-3 py-1 text-xs">
                {p.name}
                {!p.is_psx_listed && <span className="ml-1 text-muted">(not PSX-listed)</span>}
              </span>
              <ChevronRight size={13} className="text-muted" />
            </span>
          ))}
          <span className="rounded-full bg-accent/15 px-3 py-1 text-xs font-medium text-accent">{data.issuer.name}</span>
          {subsidiaries.map((s) => (
            <span key={s.id} className="flex items-center gap-2">
              <ChevronRight size={13} className="text-muted" />
              <span className="rounded-full bg-surface-alt px-3 py-1 text-xs">{s.name}</span>
            </span>
          ))}
        </div>
      )}

      {board.length > 0 ? (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          {board.map((member) => (
            <div key={`${member.full_name}-${member.role}`} className="rounded-xl bg-surface-alt p-3">
              <p className="text-sm font-medium">{member.full_name}</p>
              <p className="text-xs text-muted">{member.role}</p>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-xs text-muted">No governance data on file yet.</p>
      )}
    </div>
  );
}
