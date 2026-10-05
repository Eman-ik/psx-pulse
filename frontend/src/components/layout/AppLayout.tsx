import { ReactNode } from "react";
import Sidebar from "@/components/dashboard/Sidebar";
import MobileNav from "@/components/layout/MobileNav";

interface AppLayoutProps {
  children: ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="flex min-h-screen w-full bg-transparent">
      <Sidebar />
      <MobileNav />
      <div className="flex min-w-0 flex-1 flex-col">
        <main className="flex-1">
          {children}
        </main>
      </div>
    </div>
  );
}
