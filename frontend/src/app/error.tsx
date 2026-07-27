"use client";

import { useEffect } from "react";
import { RotateCw, TriangleAlert } from "lucide-react";

export default function Error({
  error,
  unstable_retry,
}: {
  error: Error & { digest?: string };
  unstable_retry: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="flex min-h-screen w-full items-center justify-center bg-bg px-6">
      <div className="flex max-w-md flex-col items-center gap-4 text-center">
        <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-negative/10 text-negative">
          <TriangleAlert size={26} />
        </span>
        <h1 className="text-xl font-semibold">Something went wrong</h1>
        <p className="text-sm text-muted">
          This page hit an unexpected error — most often the backend API or database being
          unreachable, not lost data. Retrying usually fixes it once the backend is back up.
        </p>
        {error.digest && <p className="text-[10px] text-muted">Error ref: {error.digest}</p>}
        <button
          onClick={() => unstable_retry()}
          className="inline-flex items-center gap-1.5 rounded-full bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-accent/90"
        >
          <RotateCw size={14} /> Try again
        </button>
      </div>
    </div>
  );
}
