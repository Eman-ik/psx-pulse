/**
 * Trade Planning Dashboard Page
 *
 * Khronos Module 6 - Trade Planning & Risk Management
 * Integrated into PSX Frontend
 */

import { Metadata } from "next";
import TradePlanDashboard from "@/components/TradePlanDashboard";
import "./dashboard.css";

export const metadata: Metadata = {
  title: "Trade Planning Dashboard | PSX Fertilizer",
  description: "Comprehensive trade planning dashboard with multi-layer decision support",
};

export default function TradePlanningPage() {
  return (
    <div className="trade-planning-page">
      <TradePlanDashboard />
    </div>
  );
}
