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
    <div className="flex min-h-screen w-full items-center justify-center bg-[#DAE1EE] px-6">
      <div className="flex max-w-md flex-col items-center gap-4 text-center">
        <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-[#B4C0D5]/40 text-[#566680]">
          <TriangleAlert size={26} />
        </span>
        <h1 className="text-xl font-semibold text-[#10161A]">Something went wrong</h1>
        <p className="text-sm text-[#566680]">
          This page encountered an unexpected error. Some data or application services may be
          temporarily unavailable. Try again, or return to the previous page.
        </p>
        {error.digest && <p className="text-[10px] text-[#8E9CB7]">Error ref: {error.digest}</p>}
        <button
          onClick={() => unstable_retry()}
          className="inline-flex items-center gap-1.5 rounded-full bg-[#10161A] px-4 py-2 text-sm font-medium text-[#DAE1EE] hover:bg-[#10161A]/90"
        >
          <RotateCw size={14} /> Try again
        </button>
      </div>
    </div>
  );
}
