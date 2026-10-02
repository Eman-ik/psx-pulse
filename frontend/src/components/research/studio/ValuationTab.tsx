"use client";

import { useStudio } from "@/lib/studio-api";
import { Card, ErrorNote, Label, Loading, Missing, num, Row, when } from "./ui";

type Valuation = {
  psx_reported: {
    status: string;
    retrieved_at: string;
    source?: string;
    badge?: string;
    pe_ratio?: number | null;
    dividend_yield_pct?: number | null;
    change_1y_pct?: number | null;
    index_membership?: string[];
    error_code?: string;
  };
  computed: { status: string; reason: string };
};

export function ValuationTab({ symbol }: { symbol: string }) {
  const { data, error, loading } = useStudio<Valuation>(symbol, "valuation");
  if (loading) return <Loading what="Fetching PSX-reported multiples" />;
  if (error || !data) return <ErrorNote message={error ?? "No data."} />;
  const q = data.psx_reported;

  return (
    <div className="space-y-6">
      <Card title="Multiples reported by PSX" aside={q.status === "AVAILABLE" ? <Label kind="DELAYED" /> : <Label kind="MISSING" />}>
        {q.status === "AVAILABLE" ? (
          <>
            <Row label="Price / earnings">{q.pe_ratio == null ? "Not meaningful or not reported" : `${num(q.pe_ratio)}×`}</Row>
            <Row label="Dividend yield">{q.dividend_yield_pct == null ? "—" : `${num(q.dividend_yield_pct)}%`}</Row>
            <Row label="Price change over one year">{q.change_1y_pct == null ? "—" : `${num(q.change_1y_pct)}%`}</Row>
            <p className="mt-3 text-xs text-muted">
              Source: {q.source}, retrieved {when(q.retrieved_at)}. These are PSX&apos;s own figures. Their earnings basis and period
              aren&apos;t disclosed, so treat them as a reference and not as a value judgement.
            </p>
            {q.index_membership && q.index_membership.length > 0 && (
              <p className="mt-3 text-xs text-muted">Index membership reported by PSX: {q.index_membership.join(", ")}</p>
            )}
          </>
        ) : (
          <ErrorNote message="PSX multiples could not be fetched right now. Nothing has been substituted." />
        )}
      </Card>

      <Card title="Own-history, peer and scenario valuation">
        <Missing>{data.computed.reason}</Missing>
        <p className="mt-3 text-xs text-muted">
          A business can be healthy and expensive, or unhealthy and cheap, so valuation is never folded into the health domains.
        </p>
      </Card>
    </div>
  );
}
