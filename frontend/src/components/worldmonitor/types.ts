export type NewsCategory =
  | 'ALL'
  | 'PSX_EQUITIES'
  | 'GEOPOLITICS'
  | 'MACRO_SBP_IMF'
  | 'COMMODITIES_FX'
  | 'QUANT_SIGNALS';

export type SentimentType = 'BULLISH' | 'BEARISH' | 'NEUTRAL';

export type ImpactHorizon = 'INTRADAY' | '1-WEEK' | '1-MONTH' | '3-MONTHS';

export interface TrendProjection {
  bullCase: string;
  baseCase: string;
  bearCase: string;
  probabilityBull: number;
  probabilityBear: number;
  expectedIndexDelta: string;
  affectedSectors: string[];
}

export interface PSXNewsItem {
  id: string;
  title: string;
  summary: string;
  source: string;
  publishedAt: string;
  category: NewsCategory;
  tickers: string[];
  sentiment: SentimentType;
  sentimentScore: number;
  volatilityScore: number;
  impactHorizon: ImpactHorizon;
  aiAnalysis: string;
  trendProjection: TrendProjection;
  geopoliticalRegion?: string;
  isBreaking?: boolean;
  url?: string;
  transmissionPath?: string[];
}

export interface MacroIndicator {
  id: string;
  name: string;
  tickerSymbol?: string;
  value: string;
  change: string;
  changePercent: number;
  status: 'up' | 'down' | 'flat';
  unit: string;
  lastUpdated: string;
  sparkline: number[];
  description: string;
}

export interface SectorSentiment {
  sector: string;
  sentiment: SentimentType;
  score: number;
  keyDriver: string;
  topTickers: string[];
  correlationToMacro: number;
  weeklyChange: string;
}

export interface QuantAlertRule {
  id: string;
  name: string;
  category: NewsCategory;
  tickerFilter?: string;
  minSentimentScore?: number;
  minVolatility?: number;
  keyword?: string;
  active: boolean;
  notifyAudio?: boolean;
  createdTime: string;
}

export interface AlertNotification {
  id: string;
  ruleId: string;
  ruleName: string;
  newsItem: PSXNewsItem;
  timestamp: string;
  read: boolean;
}

export interface AgentChatMessage {
  id: string;
  sender: 'user' | 'agent';
  text: string;
  timestamp: string;
  groundingSources?: { title: string; url: string }[];
  impactData?: { ticker: string; direction: 'up' | 'down' | 'neutral'; percentage: string; horizon: string; note: string }[];
  suggestedActions?: string[];
}

export interface MapHotspot {
  id: string;
  name: string;
  lat: number;
  lng: number;
  xPct: number;
  yPct: number;
  region: string;
  type: 'GEOPOLITICAL' | 'MACRO_HUB' | 'ENERGY_MARITIME' | 'PSX_INFRASTRUCTURE';
  status: 'CRITICAL' | 'ELEVATED' | 'STABLE';
  summary: string;
  impactOnPSX: string;
  affectedTickers: string[];
  relatedNewsCount: number;
}

export interface SectorSentimentPoint {
  date: string;
  score: number;
  newsCount: number;
  bullishRatio: number;
  keyEvent?: string;
}

export interface SectorSentimentSeries {
  sector: string;
  color: string;
  history: SectorSentimentPoint[];
}

export interface HeatmapStockItem {
  ticker: string;
  name: string;
  sector: string;
  price: number;
  changePct: number;
  changePkr: number;
  marketCapBillion: number;
  volume: string;
  high52: number;
  low52: number;
  sentimentScore: number;
  sentiment: SentimentType;
  topDriver?: string;
  peRatio?: number;
  dividendYieldPct?: number;
  volatility30d?: number;
  sparkline24h?: number[];
}

export interface HeatmapSectorGroup {
  sector: string;
  totalMarketCapBillion: number;
  avgChangePct: number;
  stocks: HeatmapStockItem[];
  peRatio?: number;
  dividendYieldPct?: number;
  volatility30d?: number;
  sparkline24h?: number[];
}

export type BacktestStrategyType =
  | 'sma_crossover'
  | 'rsi_mean_reversion'
  | 'macd_trend'
  | 'bollinger_breakout'
  | 'ai_sentiment_momentum';

export interface BacktestParams {
  ticker: string;
  strategy: BacktestStrategyType;
  initialCapital: number;
  fastPeriod: number;
  slowPeriod: number;
  rsiThresholdLow: number;
  rsiThresholdHigh: number;
  stopLossPct: number;
  takeProfitPct: number;
  timeFrameDays: number;
}

export interface BacktestTradeLog {
  id: string;
  entryDate: string;
  exitDate: string;
  entryPrice: number;
  exitPrice: number;
  shares: number;
  pnlPkr: number;
  returnPct: number;
  type: 'LONG' | 'SHORT';
  exitReason: string;
}

export interface BacktestEquityPoint {
  date: string;
  price: number;
  strategyValue: number;
  benchmarkValue: number;
  signal?: 'BUY' | 'SELL' | 'HOLD';
  fastSma?: number;
  slowSma?: number;
  rsi?: number;
}

export interface BacktestResult {
  ticker: string;
  strategyName: string;
  initialCapital: number;
  finalPortfolioValue: number;
  totalReturnPct: number;
  benchmarkReturnPct: number;
  annualizedReturnPct: number;
  sharpeRatio: number;
  maxDrawdownPct: number;
  winRatePct: number;
  totalTrades: number;
  winningTrades: number;
  losingTrades: number;
  avgPnlPerTrade: number;
  equityCurve: BacktestEquityPoint[];
  tradeLogs: BacktestTradeLog[];
}

export type DisclosureCategory =
  | 'ALL'
  | 'FINANCIAL_RESULTS'
  | 'BOARD_MEETING'
  | 'DIVIDEND_DECLARATION'
  | 'MATERIAL_INFORMATION'
  | 'DIRECTORS_SHAREHOLDING';

export interface FinancialReportMetrics {
  period: string;
  revenuePkrBillion: number;
  grossProfitPkrBillion: number;
  netProfitPkrBillion: number;
  epsPkr: number;
  cashDividendPkrPerShare?: number;
  bonusSharesPct?: number;
  yoyRevenueGrowthPct: number;
  yoyNetProfitGrowthPct: number;
  grossMarginPct: number;
  netMarginPct: number;
}

export interface CompanyDisclosureItem {
  id: string;
  ticker: string;
  companyName: string;
  sector: string;
  title: string;
  category: DisclosureCategory;
  publishedAt: string;
  sourceUrl?: string;
  pdfReportUrl?: string;
  summary: string;
  fullBodyText?: string;
  financialMetrics?: FinancialReportMetrics;
  sentiment: SentimentType;
  sentimentScore: number;
  impactNote: string;
  isScrapedLive?: boolean;
}
