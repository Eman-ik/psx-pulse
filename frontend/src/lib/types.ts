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

export interface AnnouncementRow {
  date: string;
  company: string;
  symbol: string;
  category: string;
  title: string;
  sentimentLabel: string | null;
}
