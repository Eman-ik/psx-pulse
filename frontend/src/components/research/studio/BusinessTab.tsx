"use client";

import { useStudio } from "@/lib/studio-api";
import { Card, ErrorNote, Label, Loading, Missing, Row, when } from "./ui";

type Source = { url: string; retrieved_at: string } | null;
type Business = {
  description: { text: string | null; source: Source };
  facts: Record<string, { value: string | number | null; source: Source }>;
  parent: { name: string; psx_listed: boolean; basis: string } | null;
  key_people: { name: string; role: string }[];
  segments_and_products: { status: string; items: unknown[] };
  supply_chain: { status: string; disclosed: unknown[]; note: string };
  industry_dependencies: { label: string; items: string[] };
};

const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

function SourceNote({ source }: { source: Source }) {
  if (!source) return null;
  return (
    <p className="mt-3 flex flex-wrap items-center gap-2 text-xs text-muted">
      <Label kind="VERIFIED" /> From <a href={source.url} target="_blank" rel="noreferrer" className="underline">the PSX company page</a>, retrieved{" "}
      {when(source.retrieved_at)}
    </p>
  );
}

export function BusinessTab({ symbol }: { symbol: string }) {
  const { data, error, loading } = useStudio<Business>(symbol, "business");
  if (loading) return <Loading what="Loading business profile" />;
  if (error || !data) return <ErrorNote message={error ?? "No data."} />;
  const fy = data.facts.fiscal_year_end_month?.value;

  return (
    <div className="space-y-6">
      <Card title="Company description">
        {data.description.text ? <p className="text-sm leading-relaxed">{data.description.text}</p> : <Missing>No description on file.</Missing>}
        <SourceNote source={data.description.source} />
      </Card>

      <div className="grid gap-6 md:grid-cols-2">
        <Card title="Key facts">
          <Row label="Sector">{data.facts.sector?.value ?? "—"}</Row>
          <Row label="Fiscal year ends">{typeof fy === "number" ? MONTHS[fy - 1] : "Not on file"}</Row>
          <Row label="Website">{data.facts.website?.value ?? "—"}</Row>
          <Row label="Parent / controlling entity">
            {data.parent ? `${data.parent.name}${data.parent.psx_listed ? "" : " (not PSX-listed)"}` : "None stated"}
          </Row>
          {data.parent && <p className="mt-2 text-xs text-muted">{data.parent.basis}</p>}
        </Card>

        <Card title="Products, segments and geography">
          {data.segments_and_products.items.length === 0 ? (
            <Missing>
              No segment, product or geographic breakdown has been loaded from filings, and none is inferred.
            </Missing>
          ) : null}
        </Card>
      </div>

      <Card title="Suppliers, customers and partners">
        <Missing>{data.supply_chain.note}</Missing>
        <div className="mt-4 rounded-lg border border-border p-4">
          <p className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-muted">{data.industry_dependencies.label}</p>
          {data.industry_dependencies.items.length ? (
            <ul className="list-disc space-y-1 pl-5 text-sm">
              {data.industry_dependencies.items.map((i) => (
                <li key={i}>{i}</li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted">No sector template for this sector.</p>
          )}
        </div>
      </Card>
    </div>
  );
}

export function GovernanceTab({ symbol }: { symbol: string }) {
  const { data, error, loading } = useStudio<Business>(symbol, "business");
  if (loading) return <Loading what="Loading governance" />;
  if (error || !data) return <ErrorNote message={error ?? "No data."} />;
  const source = data.description.source;

  return (
    <div className="space-y-6">
      <Card title="Board and management">
        {data.key_people.length === 0 ? (
          <Missing>No key people on file.</Missing>
        ) : (
          <ul className="divide-y divide-border/50 text-sm">
            {data.key_people.map((p) => (
              <li key={`${p.name}-${p.role}`} className="flex flex-wrap justify-between gap-2 py-2">
                <span className="font-medium">{p.name}</span>
                <span className="text-muted">{p.role}</span>
              </li>
            ))}
          </ul>
        )}
        <SourceNote source={source} />
        <p className="mt-2 text-xs text-muted">PSX shows only the chair, chief executive and company secretary here, not the full board.</p>
      </Card>

      <Card title="Auditor and registrar">
        <Row label="Auditor">{String(data.facts.auditor?.value ?? "—")}</Row>
        <Row label="Share registrar">{String(data.facts.registrar?.value ?? "—")}</Row>
        <Row label="Registered address">{String(data.facts.address?.value ?? "—")}</Row>
        <SourceNote source={source} />
      </Card>

      <Card title="Ownership and disclosures">
        <Missing>
          Sponsor and substantial-shareholder holdings, free float, director dealings and auditor-change history are not loaded yet.
          They are not estimated.
        </Missing>
      </Card>
    </div>
  );
}
