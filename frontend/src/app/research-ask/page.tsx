import { Suspense } from "react";
import AskPanel from "@/app/components/AskPanel";

export const metadata = {
  title: 'Investment Research Ask Panel | Khronos',
  description: 'PSX Pulse LLM Integration - Research any ticker with AI-powered analysis',
};

export default function ResearchAskPage() {
  return (
    <Suspense fallback={null}>
      <AskPanel />
    </Suspense>
  );
}
