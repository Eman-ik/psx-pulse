import { Suspense } from "react";
import { ResearchStudioProduction } from "@/components/research/ResearchStudioProduction";
import { AppLayout } from "@/components/layout/AppLayout";

export const metadata = { title: "Research Studio | PSX Pulse" };

export default function ResearchPage() {
  return (
    <AppLayout>
      <Suspense fallback={null}>
        <ResearchStudioProduction />
      </Suspense>
    </AppLayout>
  );
}
