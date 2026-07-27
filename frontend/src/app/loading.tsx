import { Sprout } from "lucide-react";

export default function Loading() {
  return (
    <div className="flex min-h-screen w-full items-center justify-center bg-bg">
      <div className="flex flex-col items-center gap-3">
        <span className="flex h-12 w-12 animate-pulse items-center justify-center rounded-xl bg-accent/15 text-accent">
          <Sprout size={22} />
        </span>
        <p className="text-sm text-muted">Loading real data from psxdata &amp; the research database…</p>
      </div>
    </div>
  );
}
