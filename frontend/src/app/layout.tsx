import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PSX Research | Dashboard",
  description:
    "Pakistan Stock Exchange research platform — fundamentals, market data, sector intelligence, and compliance-gated AI signal scoring across 20 PSX sectors.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className="h-full antialiased dark"
    >
      <body className="min-h-full flex flex-col bg-bg text-foreground">{children}</body>
    </html>
  );
}
