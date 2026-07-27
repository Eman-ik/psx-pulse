import Link from "next/link";
import { ArrowLeft, Globe } from "lucide-react";
import type { CompanyOverview } from "@/lib/api";

export default function CompanyHeader({ data }: { data: CompanyOverview }) {
  const { issuer, symbol, live_quote, free_float_pct } = data;
  const price = live_quote?.price;
  const changePct = live_quote?.change_pct;
  const positive = (changePct ?? 0) >= 0;
  const marketCapFact = data.financials["market_cap"]?.[data.financials["market_cap"].length - 1];

  return (
    <div className="mb-6">
      <Link href="/companies" className="mb-4 inline-flex items-center gap-1.5 text-xs text-muted hover:text-foreground">
        <ArrowLeft size={14} /> All companies
      </Link>

      <div className="flex flex-wrap items-start justify-between gap-4 rounded-2xl border border-border bg-surface p-6">
        <div>
          <div className="mb-1 flex items-center gap-2">
            <span className="rounded-md bg-accent/15 px-2 py-0.5 text-xs font-semibold text-accent">
              {symbol ?? "—"}
            </span>
            <span className="text-xs text-muted">Fertilizer sector</span>
            {issuer.is_conglomerate && (
              <span className="rounded-full bg-accent-yellow/10 px-2 py-0.5 text-[10px] font-medium text-accent-yellow">
                Conglomerate
              </span>
            )}
          </div>
          <h1 className="text-2xl font-semibold">{issuer.name}</h1>
          {issuer.website && (
            <a
              href={issuer.website.startsWith("http") ? issuer.website : `https://${issuer.website}`}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-1 inline-flex items-center gap-1 text-xs text-muted hover:text-accent"
            >
              <Globe size={12} /> {issuer.website}
            </a>
          )}
        </div>

        <div className="flex flex-wrap gap-6">
          <div>
            <p className="text-xs text-muted">Price</p>
            <p className="text-xl font-semibold">
              {price != null ? `PKR ${price.toFixed(2)}` : "—"}
              {changePct != null && (
                <span className={`ml-2 text-sm font-medium ${positive ? "text-positive" : "text-negative"}`}>
                  {positive ? "+" : ""}
                  {changePct.toFixed(2)}%
                </span>
              )}
            </p>
          </div>
          <div>
            <p className="text-xs text-muted">Market Cap</p>
            <p className="text-xl font-semibold">
              {marketCapFact ? `PKR ${(marketCapFact.value / 1_000_000).toFixed(1)} bn` : "—"}
            </p>
          </div>
          <div>
            <p className="text-xs text-muted">Free Float</p>
            <p className="text-xl font-semibold">{free_float_pct != null ? `${free_float_pct.toFixed(1)}%` : "—"}</p>
          </div>
          <div>
            <p className="text-xs text-muted">As of</p>
            <p className="text-xl font-semibold">{live_quote?.as_of_date ?? "—"}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
