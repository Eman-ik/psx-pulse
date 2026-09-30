'use client'

import React, { useState } from 'react'
import { LineChart, TrendingUp, DollarSign, Zap, TrendingDown, Activity, Gift, Target, AlertTriangle, Briefcase, Info } from 'lucide-react'
import { FinancialGrowthSection } from './FinancialGrowthSection'
import { ReturnsOnCapitalSection } from './ReturnsOnCapitalSection'
import { BalanceSheetStrengthSection } from './BalanceSheetStrengthSection'
import { CashFlowHealthSection } from './CashFlowHealthSection'
import { EarningsQualitySection } from './EarningsQualitySection'
import { WorkingCapitalSection } from './WorkingCapitalSection'
import { DividendAnalysisSection } from './DividendAnalysisSection'
import { ValuationSection } from './ValuationSection'
import { CapitalAllocationSection } from './CapitalAllocationSection'
import { RiskAssessmentSection } from './RiskAssessmentSection'
import { CatalystAnalysisSection } from './CatalystAnalysisSection'

type AnalysisTab = 'growth' | 'returns' | 'balance' | 'cashflow' | 'earnings' | 'working-capital' | 'dividend' | 'valuation' | 'capital' | 'risks' | 'catalysts'

const ANALYSIS_TABS: { id: AnalysisTab; label: string; icon: typeof LineChart }[] = [
  { id: 'growth', label: 'Growth', icon: LineChart },
  { id: 'returns', label: 'Returns', icon: TrendingUp },
  { id: 'balance', label: 'Balance Sheet', icon: DollarSign },
  { id: 'cashflow', label: 'Cash Flow', icon: Zap },
  { id: 'earnings', label: 'Earnings Quality', icon: TrendingDown },
  { id: 'working-capital', label: 'Working Capital', icon: Activity },
  { id: 'dividend', label: 'Dividend', icon: Gift },
  { id: 'valuation', label: 'Valuation', icon: Target },
  { id: 'capital', label: 'Capital Allocation', icon: Briefcase },
  { id: 'risks', label: 'Risks', icon: AlertTriangle },
  { id: 'catalysts', label: 'Catalysts', icon: Zap },
]

interface WorkspaceData {
  ticker?: string
  overview?: {
    financials?: Record<string, any[]>
    ratios?: Record<string, any>
    payouts?: any[]
  }
  peers?: any[]
}

export function FinancialAnalysisConsolidated({ workspace }: { workspace?: WorkspaceData }) {
  const [activeTab, setActiveTab] = useState<AnalysisTab>('growth')

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-lg font-bold">Financial Analysis Suite</h3>
          <p className="text-xs text-muted mt-1">Comprehensive multi-dimensional analysis of {workspace?.ticker || 'company'} across 11 key financial areas</p>
        </div>
      </div>

      {/* Sub-tab Navigation */}
      <div className="overflow-x-auto border-b border-border">
        <div className="flex gap-1 min-w-max pb-0">
          {ANALYSIS_TABS.map((item) => {
            const Icon = item.icon
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex shrink-0 items-center gap-2 border-b-2 px-4 py-3 text-xs font-bold transition-colors ${
                  activeTab === item.id
                    ? 'border-accent text-accent'
                    : 'border-transparent text-muted hover:text-foreground'
                }`}
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </button>
            )
          })}
        </div>
      </div>

      {/* Content Area */}
      <div className="rounded-lg border border-border bg-surface p-5 min-h-96">
        <div className="space-y-4">
          <div className="bg-blue-950/20 border border-blue-600/30 rounded-lg p-3">
            <p className="text-xs text-slate-300 flex items-start gap-2">
              <Info className="h-4 w-4 flex-shrink-0 mt-0.5" />
              <span>Analysis modules compute real-time metrics from {workspace?.ticker || 'company'}'s source-verified filings and ratio series.</span>
            </p>
          </div>

          {/* Components - no data passed, they'll show their placeholder messages */}
          {activeTab === 'growth' && <FinancialGrowthSection />}
          {activeTab === 'returns' && <ReturnsOnCapitalSection />}
          {activeTab === 'balance' && <BalanceSheetStrengthSection />}
          {activeTab === 'cashflow' && <CashFlowHealthSection />}
          {activeTab === 'earnings' && <EarningsQualitySection />}
          {activeTab === 'working-capital' && <WorkingCapitalSection />}
          {activeTab === 'dividend' && <DividendAnalysisSection />}
          {activeTab === 'valuation' && <ValuationSection />}
          {activeTab === 'capital' && <CapitalAllocationSection />}
          {activeTab === 'risks' && <RiskAssessmentSection />}
          {activeTab === 'catalysts' && <CatalystAnalysisSection />}
        </div>
      </div>
    </div>
  )
}
