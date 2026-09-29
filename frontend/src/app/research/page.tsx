import { ResearchHub } from "@/components/research/ResearchHub";
import Sidebar from "@/components/dashboard/Sidebar";
import Topbar from "@/components/dashboard/Topbar";

export const metadata = { title: "Research Hub | PSX QuantResearch" };

export default function ResearchPage() {
  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar isLive={false} />
        <ResearchHub />
      </div>
    </div>
  );
}
