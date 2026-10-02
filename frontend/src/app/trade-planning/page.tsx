import { Metadata } from "next";
import { TradeCheck } from "@/components/research/TradeCheck";

export const metadata: Metadata = {
  title: "Trade check | Khronos",
  description: "Individual pre-trade checks and risk-based position sizing from stored PSX data",
};

export default function TradePlanningPage() {
  return <TradeCheck />;
}
