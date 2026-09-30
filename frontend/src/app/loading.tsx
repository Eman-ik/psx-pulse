import { Sprout } from "lucide-react";

export default function Loading() {
  return (
    <div className="flex min-h-screen w-full items-center justify-center bg-[#DAE1EE]">
      <div className="flex flex-col items-center gap-3">
        <span className="flex h-12 w-12 animate-pulse items-center justify-center rounded-xl bg-[#B4C0D5]/40 text-[#8E9CB7]">
          <Sprout size={22} />
        </span>
        <p className="text-sm text-[#566680]">Loading real data from psxdata &amp; the research database…</p>
      </div>
    </div>
  );
}
