import type { AnnouncementRow, CompanySummary, IndexPoint } from "./types";
import type { RiskSnapshot } from "./api";

/**
 * SAMPLE / PLACEHOLDER DATA — market cap figures only.
 *
 * Price/change now come from the live `/market/live` endpoint (psxdata) when it's reachable;
 * see src/lib/api.ts and app/page.tsx. Market cap has no reliable free live source yet, so it
 * stays illustrative until Milestone 2/3 build real ingestion — keep it clearly labeled.
 *
 * This company list is PSX's actual "FERTILIZER" sector classification (confirmed via
 * psxdata.symbols() on 2026-07-26), not a guess: FFC, EFERT, FATIMA, AGL, AHCL.
 * Dawood Hercules (DAWH) was in an earlier draft of this list but is not actually classified
 * under Fertilizer by PSX, so it has been dropped. FFBL and ENGRO were in this list too but
 * were removed 2026-07-27 after both stopped trading in a Scheme of Arrangement restructuring
 * (FFBL merged into FFC ~2024-12-20; ENGRO's own restructuring with parent Dawood Hercules
 * took effect ~2025-01-03) — see the full evidence trail in
 * backend/app/ingestion/psx_live.py and mark_delisted_securities.py.
 */

export const pilotCompanies: CompanySummary[] = [
  { symbol: "FFC", name: "Fauji Fertilizer Company", marketCapPkrBn: 486, price: 121.4, changePct: 1.8 },
  { symbol: "EFERT", name: "Engro Fertilizers", marketCapPkrBn: 342, price: 258.9, changePct: -0.6 },
  { symbol: "FATIMA", name: "Fatima Fertilizer Company", marketCapPkrBn: 256, price: 47.3, changePct: 2.4 },
  { symbol: "AGL", name: "Agritech", marketCapPkrBn: 12, price: 46.1, changePct: -0.8 },
  { symbol: "AHCL", name: "Arif Habib Corporation", marketCapPkrBn: 38, price: 14.7, changePct: 1.2 },
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

/** Fallback only — rendered when GET /macro/risk-snapshot is unreachable, always labeled as sample. */
export const sectorRisk: RiskSnapshot = {
  overall_risk: "HIGH",
  geopolitical: "HIGH TENSION",
  economy: "STRESSED",
  imf_program: "UNKNOWN",
  currency_pkr: "MODERATE",
  as_of_date: "26 Jul 2026",
  key_positives: [
    "Gas price relief proposals under discussion for the fertilizer sector",
    "Stable urea offtake into the Kharif season",
    "Rupee has held a narrow band over the last 4 weeks",
  ],
  key_negatives: [
    "IMF program status unconfirmed — funding-gap risk",
    "Persistent circular debt exposure across the energy chain",
    "Elevated regional geopolitical tension affecting import costs",
  ],
};

/** Fallback only — rendered when GET /news/announcements is unreachable, always labeled as sample. */
export const announcements: AnnouncementRow[] = [
  { date: "24 Jul", company: "Fauji Fertilizer Company", symbol: "FFC", category: "results", title: "Q2 CY26 financial results", sentimentLabel: null },
  { date: "22 Jul", company: "Engro Fertilizers", symbol: "EFERT", category: "payout", title: "Interim cash dividend announcement", sentimentLabel: null },
  { date: "20 Jul", company: "Fatima Fertilizer Company", symbol: "FATIMA", category: "operations", title: "Plant utilization update", sentimentLabel: null },
  { date: "18 Jul", company: "Fauji Fertilizer Bin Qasim", symbol: "FFBL", category: "leadership", title: "Board meeting notice", sentimentLabel: null },
  { date: "15 Jul", company: "Fauji Fertilizer Company", symbol: "FFC", category: "general", title: "Gas supply agreement update", sentimentLabel: null },
];

export const sectorMarketCapPkrBn = pilotCompanies.reduce((sum, c) => sum + c.marketCapPkrBn, 0);
