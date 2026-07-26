export interface CompanySummary {
  symbol: string;
  name: string;
  marketCapPkrBn: number;
  price: number;
  changePct: number;
}

export interface IndexPoint {
  date: string;
  sectorIndex: number;
  kse100Index: number;
}

export interface SectorRiskSnapshot {
  overallRisk: "LOW" | "MODERATE" | "ELEVATED" | "HIGH";
  geopolitical: string;
  economy: string;
  imfProgram: string;
  currencyPkr: string;
  keyPositives: string[];
  keyNegatives: string[];
  asOfDate: string;
}

export type AnnouncementStatus = "analyst_reviewed" | "pending_review" | "ingested";

export interface AnnouncementRow {
  date: string;
  company: string;
  symbol: string;
  category: "Results" | "Dividend" | "Board Meeting" | "Contract" | "Production";
  title: string;
  status: AnnouncementStatus;
}
