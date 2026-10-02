"use client";

import { AlertCircle, Loader2 } from "lucide-react";

const LABEL_STYLE: Record<string, string> = {
  VERIFIED: "border-positive/40 text-positive",
  DERIVED: "border-accent/40 text-accent",
  DELAYED: "border-border text-muted",
  STALE: "border-negative/40 text-negative",
  MISSING: "border-border text-muted",
};

/** Per-datapoint provenance label from the SRS classification (verified, derived, delayed, stale, missing). */
export function Label({ kind }: { kind: keyof typeof LABEL_STYLE | string }) {
  return (
    <span className={`rounded border px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${LABEL_STYLE[kind] ?? LABEL_STYLE.MISSING}`}>
      {kind}
    </span>
  );
}

export function Card({ title, children, aside }: { title?: string; children: React.ReactNode; aside?: React.ReactNode }) {
  return (
    <section className="rounded-lg border border-border bg-surface p-5 sm:p-6">
      {(title || aside) && (
        <div className="mb-4 flex items-center justify-between gap-3">
          {title && <h2 className="text-lg font-semibold">{title}</h2>}
          {aside}
        </div>
      )}
      {children}
    </section>
  );
}

export function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-border/50 py-2 text-sm last:border-0">
      <span className="text-muted">{label}</span>
      <span className="text-right font-medium">{children}</span>
    </div>
  );
}

export function Loading({ what = "Loading" }: { what?: string }) {
  return (
    <p className="flex items-center gap-2 text-sm text-muted">
      <Loader2 className="h-4 w-4 animate-spin" /> {what}…
    </p>
  );
}

export function ErrorNote({ message }: { message: string }) {
  return (
    <p className="flex items-center gap-2 rounded-lg border border-negative/40 bg-negative/10 p-4 text-sm text-negative">
      <AlertCircle className="h-4 w-4 shrink-0" /> {message}
    </p>
  );
}

export function Missing({ children }: { children: React.ReactNode }) {
  return <p className="rounded-lg border border-dashed border-border p-4 text-sm text-muted">{children}</p>;
}

export const pct = (v: number | null | undefined, digits = 2) =>
  v == null ? "—" : `${v > 0 ? "+" : ""}${v.toFixed(digits)}%`;
export const tone = (v: number | null | undefined) => (v == null ? "text-muted" : v >= 0 ? "text-positive" : "text-negative");
export const num = (v: number | null | undefined, digits = 2) =>
  v == null ? "—" : v.toLocaleString(undefined, { maximumFractionDigits: digits, minimumFractionDigits: digits });
export const when = (iso: string | null | undefined) =>
  iso ? new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: iso.length > 10 ? "short" : undefined }) : "—";
export const day = (iso: string | null | undefined) => (iso ? new Date(iso).toLocaleDateString(undefined, { dateStyle: "medium" }) : "—");

const STATE_TONE: Record<string, string> = {
  IMPROVING: "text-positive", POSITIVE: "text-positive", HIGH: "text-positive", FAVORABLE: "text-positive",
  DETERIORATING: "text-negative", NEGATIVE: "text-negative", LOW: "text-negative", UNFAVORABLE: "text-negative",
};
export const stateTone = (s: string) => STATE_TONE[s] ?? "text-foreground";
export const stateText = (s: string) => s.replaceAll("_", " ").toLowerCase().replace(/^\w/, (c) => c.toUpperCase());
