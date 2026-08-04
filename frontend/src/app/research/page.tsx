import { ResearchStudio } from "@/components/research/ResearchStudio";
import Sidebar from "@/components/dashboard/Sidebar";
import Topbar from "@/components/dashboard/Topbar";

export const metadata = { title: "Research Studio · PSX QuantResearch" };

export default function ResearchPage() {
  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <Topbar isLive={false} />
        <main className="flex-1 overflow-y-auto px-4 sm:px-6 lg:px-8 py-6 max-w-5xl w-full mx-auto">
          <ResearchStudio />
        </main>
      </div>
    </div>
  );
}
