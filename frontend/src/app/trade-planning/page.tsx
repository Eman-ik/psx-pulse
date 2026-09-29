/**
 * Trade Planning Dashboard Page
 *
 * Khronos Module 6 - Trade Planning & Risk Management
 * Integrated into PSX Frontend
 */

import { Metadata } from "next";
import { UnifiedResearchTradeFlow } from "@/components/UnifiedResearchTradeFlow";

export const metadata: Metadata = {
  title: "Unified Research & Trade Planning | Khronos",
  description: "Evidence gates, thesis synthesis, and risk-based position sizing",
};

export default function TradePlanningPage() {
  return (
    <UnifiedResearchTradeFlow />
  );
}
