import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PSX Research | Intelligence Dashboard",
  description:
    "Pakistan Stock Exchange research platform — fundamentals, market data, sector intelligence, and compliance-gated AI signal scoring across 20 PSX sectors.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col bg-bg text-foreground selection:bg-[#B4C0D5] selection:text-[#10161A] relative">
        {/* Layer 1: Atmospheric background gradient */}
        <div className="atmospheric-bg" aria-hidden="true" />
        {/* Layer 2: Subtle fine grain texture */}
        <div className="grain-overlay" aria-hidden="true" />
        {/* Content container */}
        <div className="relative z-10 flex min-h-full flex-col">
          {children}
        </div>
      </body>
    </html>
  );
}
