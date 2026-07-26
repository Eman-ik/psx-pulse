import { Search, Bell, Sprout } from "lucide-react";

export default function Topbar() {
  return (
    <header className="flex items-center justify-between gap-4 border-b border-border px-6 py-4 lg:px-8">
      <div>
        <p className="text-xs text-muted">
          Homepage / <span className="text-foreground">Dashboard</span>
        </p>
        <h1 className="text-xl font-semibold">Fertilizer Sector</h1>
      </div>

      <div className="flex flex-1 items-center justify-end gap-3">
        <div className="hidden max-w-xs flex-1 items-center gap-2 rounded-full border border-border bg-surface px-4 py-2 sm:flex">
          <Search size={15} className="text-muted" />
          <input
            type="text"
            placeholder="Search companies, tickers..."
            className="w-full bg-transparent text-sm text-foreground placeholder:text-muted focus:outline-none"
          />
        </div>

        <span className="hidden rounded-full border border-accent-yellow/30 bg-accent-yellow/10 px-3 py-1.5 text-xs font-medium text-accent-yellow sm:inline-block">
          Sample data — not live
        </span>

        <button className="relative flex h-9 w-9 items-center justify-center rounded-full border border-border bg-surface text-muted hover:text-foreground">
          <Bell size={16} />
          <span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-negative" />
        </button>

        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-accent/15 text-accent">
          <Sprout size={16} />
        </div>
      </div>
    </header>
  );
}
