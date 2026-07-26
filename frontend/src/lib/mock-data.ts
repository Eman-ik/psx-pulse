import type {
  AnnouncementRow,
  CompanySummary,
  IndexPoint,
  SectorRiskSnapshot,
} from "./types";

/**
 * SAMPLE / PLACEHOLDER DATA ONLY.
 *
 * No PSX data license exists yet (see docs/rights_matrix.template.md), so this dashboard
 * is wired against illustrative sample data, not a live or real EOD feed. Every screen
 * that renders this data must keep the "Sample data" badge visible until Milestone 2
 * (real ingestion) and the compliance gate are both in place.
 */

export const pilotCompanies: CompanySummary[] = [
  { symbol: "FFC", name: "Fauji Fertilizer Company", marketCapPkrBn: 486, price: 121.4, changePct: 1.8 },
  { symbol: "EFERT", name: "Engro Fertilizers", marketCapPkrBn: 342, price: 258.9, changePct: -0.6 },
  { symbol: "FATIMA", name: "Fatima Fertilizer Company", marketCapPkrBn: 256, price: 47.3, changePct: 2.4 },
  { symbol: "DAWH", name: "Dawood Hercules Corporation", marketCapPkrBn: 189, price: 198.6, changePct: -1.1 },
];

export const sectorIndexHistory: IndexPoint[] = [
  { date: "1 Jul", sectorIndex: 100.0, kse100Index: 100.0 },
  { date: "4 Jul", sectorIndex: 101.2, kse100Index: 100.6 },
  { date: "7 Jul", sectorIndex: 99.4, kse100Index: 101.3 },
  { date: "10 Jul", sectorIndex: 102.6, kse100Index: 102.0 },
  { date: "13 Jul", sectorIndex: 104.8, kse100Index: 101.4 },
  { date: "16 Jul", sectorIndex: 103.1, kse100Index: 100.2 },
  { date: "19 Jul", sectorIndex: 105.9, kse100Index: 102.8 },
  { date: "22 Jul", sectorIndex: 108.3, kse100Index: 104.1 },
  { date: "25 Jul", sectorIndex: 106.7, kse100Index: 103.6 },
  { date: "26 Jul", sectorIndex: 109.5, kse100Index: 105.0 },
];

export const sectorRisk: SectorRiskSnapshot = {
  overallRisk: "HIGH",
  geopolitical: "HIGH TENSION",
  economy: "STRESSED",
  imfProgram: "UNKNOWN",
  currencyPkr: "MODERATE",
  asOfDate: "26 Jul 2026",
  keyPositives: [
    "Gas price relief proposals under discussion for the fertilizer sector",
    "Stable urea offtake into the Kharif season",
    "Rupee has held a narrow band over the last 4 weeks",
  ],
  keyNegatives: [
    "IMF program status unconfirmed — funding-gap risk",
    "Persistent circular debt exposure across the energy chain",
    "Elevated regional geopolitical tension affecting import costs",
  ],
};

export const announcements: AnnouncementRow[] = [
  { date: "24 Jul", company: "Fauji Fertilizer Company", symbol: "FFC", category: "Results", title: "Q2 CY26 financial results", status: "analyst_reviewed" },
  { date: "22 Jul", company: "Engro Fertilizers", symbol: "EFERT", category: "Dividend", title: "Interim cash dividend announcement", status: "analyst_reviewed" },
  { date: "20 Jul", company: "Fatima Fertilizer Company", symbol: "FATIMA", category: "Production", title: "Plant utilization update", status: "pending_review" },
  { date: "18 Jul", company: "Dawood Hercules Corporation", symbol: "DAWH", category: "Board Meeting", title: "Board meeting notice", status: "ingested" },
  { date: "15 Jul", company: "Fauji Fertilizer Company", symbol: "FFC", category: "Contract", title: "Gas supply agreement update", status: "pending_review" },
];

export const sectorMarketCapPkrBn = pilotCompanies.reduce((sum, c) => sum + c.marketCapPkrBn, 0);
export const sectorMarketCapChangePct = 1.4;
