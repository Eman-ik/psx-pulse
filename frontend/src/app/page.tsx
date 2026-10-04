import { AppLayout } from "@/components/layout/AppLayout";
import { SectionHeader, GlassCard, GlassPanel } from "@/components/glass";
import { ArrowRight, BarChart3, TrendingUp, Zap, Search, BookOpen } from "lucide-react";
import Link from "next/link";

export const metadata = { title: "PSX Pulse | Dashboard" };

export default function HomePage() {
  const features = [
    {
      icon: <BarChart3 className="w-6 h-6" />,
      title: "Market Overview",
      description: "Real-time PSX indices, breadth analysis, gainers & losers",
      href: "/market",
    },
    {
      icon: <BookOpen className="w-6 h-6" />,
      title: "Research Studio",
      description: "Deep company analysis with 11 research tabs & intelligence engines",
      href: "/research?t=FFC&tab=overview",
    },
    {
      icon: <TrendingUp className="w-6 h-6" />,
      title: "Screeners",
      description: "Fundamental, technical & momentum analysis across the market",
      href: "/screening",
    },
    {
      icon: <Zap className="w-6 h-6" />,
      title: "Trade Planning",
      description: "Position sizing, risk assessment & pre-trade checks",
      href: "/research?t=FFC&tab=trade",
    },
    {
      icon: <Search className="w-6 h-6" />,
      title: "Company Search",
      description: "Find companies and explore fundamental data",
      href: "/search",
    },
  ];

  return (
    <AppLayout>
      <div className="px-6 py-12 lg:px-8 max-w-7xl mx-auto">
        {/* Hero Section */}
        <SectionHeader
          title="PSX Pulse"
          subtitle="Research platform built on source-backed data"
        />

        <p className="text-base text-[var(--text-secondary)] mb-12 max-w-2xl">
          Comprehensive analysis, real-time market data, and intelligence-driven research for PSX investors
        </p>

        {/* Feature Grid - Asymmetric layout */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-16">
          {features.map((feature, idx) => (
            <Link
              key={idx}
              href={feature.href}
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
                  {feature.icon}
                </div>

                {/* Content */}
                <div className="flex-1">
                  <h3 className="text-base font-semibold mb-2 text-[var(--text-primary)] group-hover:text-[#10161A] transition-colors">
                    {feature.title}
                  </h3>
                  <p className="text-sm text-[var(--text-secondary)] group-hover:text-[var(--text-primary)]/70 transition-colors">
                    {feature.description}
                  </p>
                </div>

                {/* Arrow */}
                <div className="flex items-center gap-2 text-sm font-medium text-[var(--accent)] mt-6 opacity-0 group-hover:opacity-100 transition-opacity">
                  Explore
                  <ArrowRight className="w-4 h-4" />
                </div>
              </GlassCard>
            </Link>
          ))}
        </div>

        {/* Info Section - Premium Glass Panel */}
        <GlassPanel
          title="About PSX Pulse"
          className="max-w-3xl"
        >
          <div className="space-y-4">
            <p className="text-sm text-[var(--text-secondary)]">
              PSX Pulse is a research platform for Pakistan Stock Exchange investors, built exclusively on data with verified sources. Every price records the load that fetched it, and every financial figure links to the document it came from.
            </p>
            <p className="text-sm text-[var(--text-secondary)]">
              Missing data is shown as missing, never estimated. Our research-to-trade workflow combines fundamental analysis, technical screening, and institutional-grade intelligence to support better investment decisions.
            </p>
          </div>
        </GlassPanel>
      </div>
    </AppLayout>
  );
}
