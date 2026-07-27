import type { CompanyOverview } from "@/lib/api";

const MONTH_NAMES = [
  "", "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

export default function CompanyProfile({ issuer }: { issuer: CompanyOverview["issuer"] }) {
  return (
    <div className="rounded-2xl border border-border bg-surface p-5">
      <h3 className="mb-3 font-semibold">Business Profile</h3>
      {issuer.business_description ? (
        <p className="mb-4 text-sm leading-relaxed text-muted">{issuer.business_description}</p>
      ) : (
        <p className="mb-4 text-xs text-muted">No business description on file yet.</p>
      )}
      <div className="grid grid-cols-2 gap-4 text-xs sm:grid-cols-5">
        <div>
          <p className="mb-1 text-muted">Address</p>
          <p>{issuer.address ?? "—"}</p>
        </div>
        <div>
          <p className="mb-1 text-muted">Auditor</p>
          <p>{issuer.auditor ?? "—"}</p>
        </div>
        <div>
          <p className="mb-1 text-muted">Registrar</p>
          <p>{issuer.registrar ?? "—"}</p>
        </div>
        <div>
          <p className="mb-1 text-muted">Fiscal Year End</p>
          <p>{issuer.fiscal_year_end_month ? MONTH_NAMES[issuer.fiscal_year_end_month] : "—"}</p>
        </div>
        <div>
          <p className="mb-1 text-muted">Established</p>
          <p>{issuer.establishment_year ?? "—"}</p>
        </div>
      </div>
    </div>
  );
}
