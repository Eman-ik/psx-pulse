import { Suspense } from "react";
import { ResearchStudioProduction } from "@/components/research/ResearchStudioProduction";

export const metadata = { title: "Equity Research Studio | Khronos" };

export default function ResearchPage() {
  return (
    <Suspense fallback={null}>
      <ResearchStudioProduction />
    </Suspense>
  );
}
