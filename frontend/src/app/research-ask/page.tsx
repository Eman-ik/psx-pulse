import { Suspense } from "react";
import AskPanel from "@/app/components/AskPanel";
import { AppLayout } from "@/components/layout/AppLayout";

export const metadata = {
  title: 'Research Ask | PSX Pulse',
  description: 'Query-based research interface for PSX companies',
};

export default function ResearchAskPage() {
  return (
    <AppLayout>
      <div className="flex-1">
        <Suspense fallback={null}>
          <AskPanel />
        </Suspense>
      </div>
    </AppLayout>
  );
}
