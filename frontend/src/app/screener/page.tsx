import { AppLayout } from "@/components/layout/AppLayout";
import { SectionHeader, GlassCard } from "@/components/glass";
import { TrendingDown, LineChart, Zap } from "lucide-react";
import Link from "next/link";

export const metadata = {
  title: "Screeners | PSX Pulse",
  description: "Fundamental, technical, and momentum screening tools for PSX analysis"
};

export default function ScreenerHubPage() {
  const screenerTools = [
    {
      icon: <TrendingDown className="w-6 h-6" />,
      title: "Fundamental Screening",
      description: "Filter PSX companies by growth, profitability, valuation, and financial health metrics",
      href: "/screening",
    },
    {
      icon: <LineChart className="w-6 h-6" />,
      title: "Technical Analysis",
      description: "Analyze support/resistance, trends, momentum, and technical patterns",
      href: "/technical",
    },
    {
      icon: <Zap className="w-6 h-6" />,
      title: "Momentum Analysis",
      description: "Track momentum indicators, relative strength, and market breadth",
      href: "/momentum",
    },
  ];

  return (
    <AppLayout>
      <div className="px-6 py-12 lg:px-8 max-w-7xl mx-auto">
        {/* Header */}
        <SectionHeader
          title="Screeners"
          subtitle="Fundamental, technical, and momentum analysis tools"
        />

        {/* Screener Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
          {screenerTools.map((tool, idx) => (
            <Link
              key={idx}
              href={tool.href}
              className="group h-full"
            >
              <GlassCard
                variant="primary"
                interactive
                elevation={1}
                className="h-full flex flex-col justify-between hover:border-[rgba(255,255,255,0.88)]"
              >
                {/* Icon Badge */}
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#10161A] text-white shadow-md mb-4 group-hover:shadow-lg transition-shadow">
                  {tool.icon}
                </div>

                {/* Content */}
                <div className="flex-1">
                  <h3 className="text-base font-semibold mb-2 text-[var(--text-primary)]">
                    {tool.title}
                  </h3>
                  <p className="text-sm text-[var(--text-secondary)]">
                    {tool.description}
                  </p>
                </div>

                {/* Button */}
                <div className="mt-6 text-sm font-medium text-[var(--accent)]">
                  Open Screener →
                </div>
              </GlassCard>
            </Link>
          ))}
        </div>
      </div>
    </AppLayout>
  );
}
