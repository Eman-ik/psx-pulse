// Research Studio API Integration
// Connects frontend to R1-R7 backend modules

import axios, { AxiosInstance } from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000/api";

export interface ResearchData {
  company: {
    company_id: number;
    ticker: string;
    legal_name: string;
    sector: string;
    market_cap: number;
    stock_price: number;
    shares_outstanding: number;
  };
  financials: {
    revenue: number;
    gross_profit: number;
    operating_profit: number;
    pat: number;
    total_assets: number;
    total_debt: number;
    equity: number;
    period: string;
  };
  metrics: {
    eps: number;
    roe: number;
    roa: number;
    gross_margin: number;
    net_margin: number;
    debt_to_equity: number;
    current_ratio: number;
    interest_coverage: number;
    pe_ratio: number;
    dividend_yield: number;
  };
  valuations: {
    metric: string;
    value: number;
    sector_median: number;
    percentile: number;
  }[];
  announcements: {
    date: string;
    type: string;
    title: string;
    impact: number;
    metrics: Record<string, number>;
  }[];
  research_quality_score: number;
}

class ResearchAPIClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 10000,
      headers: {
        "Content-Type": "application/json",
      },
    });
  }

  // R1: Get Company Master Data
  async getCompanyMaster(ticker: string): Promise<any> {
    try {
      const response = await this.client.get(`/research/company/${ticker}`);
      return response.data;
    } catch (error) {
      console.error(`Failed to fetch company master for ${ticker}:`, error);
      return null;
    }
  }

  // R2-R3: Get Financial Statements
  async getFinancialStatements(ticker: string, period?: string): Promise<any> {
    try {
      const params = period ? { period } : {};
      const response = await this.client.get(`/research/${ticker}/financials`, {
        params,
      });
      return response.data;
    } catch (error) {
      console.error(`Failed to fetch financials for ${ticker}:`, error);
      return null;
    }
  }

  // R4: Get Calculated Metrics
  async getMetrics(ticker: string, period?: string): Promise<any> {
    try {
      const params = period ? { period } : {};
      const response = await this.client.get(`/research/${ticker}/metrics`, {
        params,
      });
      return response.data;
    } catch (error) {
      console.error(`Failed to fetch metrics for ${ticker}:`, error);
      return null;
    }
  }

  // R5: Get Valuation Data
  async getValuations(ticker: string): Promise<any> {
    try {
      const response = await this.client.get(`/research/${ticker}/valuations`);
      return response.data;
    } catch (error) {
      console.error(`Failed to fetch valuations for ${ticker}:`, error);
      return null;
    }
  }

  // R6: Get Announcements
  async getAnnouncements(ticker: string, limit: number = 10): Promise<any> {
    try {
      const response = await this.client.get(
        `/research/${ticker}/announcements`,
        { params: { limit } }
      );
      return response.data;
    } catch (error) {
      console.error(`Failed to fetch announcements for ${ticker}:`, error);
      return null;
    }
  }

  // R7: Get AI Research Summary
  async getResearchSummary(ticker: string): Promise<any> {
    try {
      const response = await this.client.get(`/research/${ticker}/summary`);
      return response.data;
    } catch (error) {
      console.error(`Failed to fetch research summary for ${ticker}:`, error);
      return null;
    }
  }

  // Unified Data Fetch (all modules at once)
  async getUnifiedResearchData(ticker: string): Promise<ResearchData | null> {
    try {
      const [company, financials, metrics, valuations, announcements, summary] =
        await Promise.all([
          this.getCompanyMaster(ticker),
          this.getFinancialStatements(ticker),
          this.getMetrics(ticker),
          this.getValuations(ticker),
          this.getAnnouncements(ticker, 5),
          this.getResearchSummary(ticker),
        ]);

      if (!company) return null;

      return {
        company,
        financials: financials?.latest || {},
        metrics: metrics?.calculated || {},
        valuations: valuations?.data || [],
        announcements: announcements?.data || [],
        research_quality_score: summary?.quality_score || 0,
      };
    } catch (error) {
      console.error(`Failed to fetch unified research data for ${ticker}:`, error);
      return null;
    }
  }

  // List covered companies
  async getCoveredCompanies(): Promise<any[]> {
    try {
      const response = await this.client.get("/research/companies");
      return response.data.data || [];
    } catch (error) {
      console.error("Failed to fetch covered companies:", error);
      return [];
    }
  }

  // Generate PDF report
  async generateReport(ticker: string, format: "pdf" | "json" = "pdf"): Promise<Blob | any> {
    try {
      const response = await this.client.get(`/research/${ticker}/report`, {
        params: { format },
        responseType: format === "pdf" ? "blob" : "json",
      });
      return response.data;
    } catch (error) {
      console.error(`Failed to generate report for ${ticker}:`, error);
      return null;
    }
  }
}

export const researchAPI = new ResearchAPIClient();
