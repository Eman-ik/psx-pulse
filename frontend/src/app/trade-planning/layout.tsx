/**
 * Trade Planning Layout
 * Khronos Module 6 Integration
 */

import type { ReactNode } from "react";

export default function TradePlanningLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <div className="trade-planning-layout">
      {children}
    </div>
  );
}
