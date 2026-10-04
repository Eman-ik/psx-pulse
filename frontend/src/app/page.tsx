import { AppLayout } from "@/components/layout/AppLayout";
import { ArrowRight, BarChart3, TrendingUp, Zap, Search, BookOpen } from "lucide-react";
import Link from "next/link";

export const metadata = { title: "PSX Pulse | Dashboard" };

export default function HomePage() {
  const features = [
    {
      icon: <BarChart3 className="w-8 h-8" />,
      title: "Market Overview",
      description: "Real-time PSX indices, breadth analysis, gainers & losers",
      href: "/market",
      color: "from-blue-500 to-cyan-500",
    },
    {
      icon: <BookOpen className="w-8 h-8" />,
      title: "Research Studio",
      description: "Deep company analysis with 11 research tabs & intelligence engines",
      href: "/research?t=FFC&tab=overview",
      color: "from-purple-500 to-pink-500",
    },
    {
      icon: <TrendingUp className="w-8 h-8" />,
      title: "Screeners",
      description: "Fundamental, technical & momentum analysis across the market",
      href: "/screening",
      color: "from-green-500 to-emerald-500",
    },
    {
      icon: <Zap className="w-8 h-8" />,
      title: "Trade Planning",
      description: "Position sizing, risk assessment & pre-trade checks",
      href: "/research?t=FFC&tab=trade",
      color: "from-orange-500 to-red-500",
    },
    {
      icon: <Search className="w-8 h-8" />,
      title: "Company Search",
      description: "Find companies and explore fundamental data",
      href: "/search",
      color: "from-indigo-500 to-blue-500",
    },
  ];

  return (
    <AppLayout>
      <div className="px-6 py-8 lg:px-8">
        {/* Hero Section */}
        <div className="mb-12">
          <h1 className="text-4xl md:text-5xl font-bold mb-4 text-foreground">
            PSX Pulse
          </h1>
          <p className="text-lg text-muted mb-2">
            Research platform built on source-backed data
          </p>
          <p className="text-sm text-muted">
            Comprehensive analysis, real-time market data, and intelligence-driven research for PSX investors
          </p>
        </div>

        {/* Feature Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
          {features.map((feature, idx) => (
            <Link
              key={idx}
              href={feature.href}
              className="group relative overflow-hidden rounded-2xl border border-border bg-surface p-6 transition-all hover:shadow-lg hover:border-accent/50"
            >
              {/* Background gradient accent */}
              <div className={`absolute inset-0 opacity-0 group-hover:opacity-10 bg-gradient-to-br ${feature.color} transition-opacity`} />

              {/* Icon */}
              <div className={`mb-4 inline-flex p-3 rounded-lg bg-gradient-to-br ${feature.color} text-white`}>
                {feature.icon}
              </div>

              {/* Content */}
              <h3 className="text-lg font-semibold mb-2 text-foreground group-hover:text-accent transition-colors">
                {feature.title}
              </h3>
              <p className="text-sm text-muted mb-4 group-hover:text-foreground/70 transition-colors">
                {feature.description}
              </p>

              {/* Arrow */}
              <div className="flex items-center text-sm font-medium text-accent opacity-0 group-hover:opacity-100 transition-opacity">
                Explore <ArrowRight className="w-4 h-4 ml-2" />
              </div>
            </Link>
          ))}
        </div>

        {/* Info Section */}
        <div className="rounded-xl border border-border bg-surface/50 p-6 max-w-2xl">
          <h2 className="text-lg font-semibold mb-3 text-foreground">About PSX Pulse</h2>
          <p className="text-sm text-muted mb-3">
            PSX Pulse is a research platform for Pakistan Stock Exchange investors, built exclusively on data with verified sources. Every price records the load that fetched it, and every financial figure links to the document it came from.
          </p>
          <p className="text-sm text-muted">
            Missing data is shown as missing, never estimated. Our research-to-trade workflow combines fundamental analysis, technical screening, and institutional-grade intelligence to support better investment decisions.
          </p>
        </div>
      </div>
    </AppLayout>
  );
}
