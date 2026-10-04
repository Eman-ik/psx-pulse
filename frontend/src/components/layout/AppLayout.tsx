"use client";

import { ReactNode } from "react";
import Sidebar from "@/components/dashboard/Sidebar";

interface AppLayoutProps {
  children: ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="flex min-h-screen w-full bg-bg">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <main className="flex-1">
          {children}
        </main>
      </div>
    </div>
  );
}
