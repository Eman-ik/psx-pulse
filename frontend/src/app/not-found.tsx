import Link from "next/link";
import { Compass, Sprout } from "lucide-react";

export default function NotFound() {
  return (
    <div className="flex min-h-screen w-full items-center justify-center bg-bg px-6">
      <div className="flex max-w-md flex-col items-center gap-4 text-center">
        <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-accent/15 text-accent">
          <Sprout size={26} />
        </span>
        <h1 className="text-xl font-semibold">Page not found</h1>
        <p className="text-sm text-muted">
          This page doesn&apos;t exist, or the company/report it pointed to isn&apos;t part of
          this pilot&apos;s coverage.
        </p>
        <div className="flex gap-3">
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 rounded-full bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-accent/90"
          >
            <Compass size={14} /> Back to Dashboard
          </Link>
          <Link
            href="/companies"
            className="inline-flex items-center gap-1.5 rounded-full border border-border px-4 py-2 text-sm font-medium text-muted hover:text-foreground"
          >
            Browse Companies
          </Link>
        </div>
      </div>
    </div>
  );
}
