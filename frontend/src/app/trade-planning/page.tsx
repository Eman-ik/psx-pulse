import { Metadata } from "next";
import { TradeCheck } from "@/components/research/TradeCheck";
import { AppLayout } from "@/components/layout/AppLayout";

export const metadata: Metadata = {
  title: "Trade Planning | PSX Pulse",
  description: "Position sizing, risk assessment & pre-trade checks for PSX investments",
};

export default function TradePlanningPage() {
  return (
    <AppLayout>
      <div className="flex-1">
        <TradeCheck />
      </div>
    </AppLayout>
  );
}
