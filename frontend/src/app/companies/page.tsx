import Link from "next/link";
import Sidebar from "@/components/dashboard/Sidebar";
import Topbar from "@/components/dashboard/Topbar";
import { fetchCompanies, fetchLiveQuotes } from "@/lib/api";

export default async function CompaniesPage() {
  const [companies, live] = await Promise.all([fetchCompanies(), fetchLiveQuotes()]);
  const quoteBySymbol = new Map((live?.quotes ?? []).map((q) => [q.symbol, q]));

  return (
    <div className="flex min-h-screen w-full bg-bg">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar isLive={!!live} />

        <main className="flex-1 px-6 py-6 lg:px-8">
          <h1 className="mb-1 text-xl font-semibold">Fertilizer Sector Companies</h1>
          <p className="mb-6 text-sm text-muted">
            {companies.length} companies covered — click through for full research pages.
          </p>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {companies.map((company) => {
              const quote = company.symbol ? quoteBySymbol.get(company.symbol) : undefined;
              return (
                <Link
                  key={company.id}
                  href={`/companies/${company.id}`}
                  className="rounded-2xl border border-border bg-surface p-5 transition-colors hover:border-accent/40"
                >
                  <div className="mb-1 flex items-center gap-2">
                    {company.symbol && (
                      <span className="rounded-md bg-accent/15 px-1.5 py-0.5 text-[10px] font-semibold text-accent">
                        {company.symbol}
                      </span>
                    )}
                    <p className="text-sm font-medium">{company.name}</p>
                  </div>
                  {quote && (
                    <p className={`text-xs ${((quote.change_pct ?? 0) >= 0) ? "text-positive" : "text-negative"}`}>
                      PKR {quote.price?.toFixed(2)} ({(quote.change_pct ?? 0) >= 0 ? "+" : ""}
                      {quote.change_pct?.toFixed(2)}%)
                    </p>
                  )}
                  {!quote && <p className="text-xs text-muted">View research page</p>}
                </Link>
              );
            })}
          </div>
        </main>
      </div>
    </div>
  );
}
