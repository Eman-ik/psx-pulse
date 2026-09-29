import { ComprehensiveResearchStudio } from "@/components/research/ComprehensiveResearchStudio";
import Sidebar from "@/components/dashboard/Sidebar";
import Topbar from "@/components/dashboard/Topbar";

export const metadata = { title: "Research Studio | PSX QuantResearch" };

export default function ResearchPage() {
  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar isLive={false} />
        <div className="flex-1 overflow-y-auto">
          <ComprehensiveResearchStudio />
        </div>
      </div>
    </div>
  );
}
