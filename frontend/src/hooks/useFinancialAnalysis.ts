import { useEffect, useState } from 'react'

const ANALYSIS_API = 'http://localhost:5000/api'

export function useFinancialAnalysis(ticker?: string) {
  const [analysis, setAnalysis] = useState<Record<string, any>>({})
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!ticker) return

    setLoading(true)
    Promise.all([
      fetch(`${ANALYSIS_API}/research/${ticker}/financial-growth`).then(r => r.json()).catch(()=>({ growth_metrics: {}, margin_analysis: {}, dilution_analysis: {}, growth_scorecard: { overall_growth_score: 0, revenue_health: '', profit_health: '', margin_health: '', dilution_health: '', recommendations: [] } })),
      fetch(`${ANALYSIS_API}/research/${ticker}/returns-on-capital`).then(r => r.json()).catch(()=>({ roc_metrics: {}, efficiency_ratios: {}, roc_scorecard: { overall_roc_score: 0, roe_status: '', roa_status: '', roic_status: '', recommendations: [] } })),
      fetch(`${ANALYSIS_API}/research/${ticker}/balance-sheet`).then(r => r.json()).catch(()=>({ liquidity_ratios: {}, solvency_ratios: {}, balance_sheet_scorecard: { overall_strength_score: 0, liquidity_status: '', solvency_status: '', recommendations: [] } })),
      fetch(`${ANALYSIS_API}/research/${ticker}/cash-flow`).then(r => r.json()).catch(()=>({ cash_flow_metrics: {}, quality_metrics: {}, cash_flow_scorecard: { overall_health_score: 0, ocf_status: '', fcf_status: '', recommendations: [] } })),
      fetch(`${ANALYSIS_API}/research/${ticker}/earnings-quality`).then(r => r.json()).catch(()=>({ quality_metrics: {}, sustainability_metrics: {}, earnings_scorecard: { overall_quality_score: 0, sustainability_status: '', recommendations: [] } })),
      fetch(`${ANALYSIS_API}/research/${ticker}/working-capital`).then(r => r.json()).catch(()=>({ efficiency_metrics: {}, trends: {}, working_capital_scorecard: { overall_efficiency_score: 0, working_capital_status: '', recommendations: [] } })),
      fetch(`${ANALYSIS_API}/research/${ticker}/dividend`).then(r => r.json()).catch(()=>({ dividend_metrics: {}, payout_analysis: {}, dividend_scorecard: { overall_dividend_score: 0, payout_ratio_status: '', recommendations: [] } })),
      fetch(`${ANALYSIS_API}/research/${ticker}/valuation`).then(r => r.json()).catch(()=>({ valuation_metrics: {}, multiples_analysis: {}, valuation_scorecard: { overall_valuation_score: 0, pe_status: '', recommendations: [] } })),
      fetch(`${ANALYSIS_API}/research/${ticker}/capital-allocation`).then(r => r.json()).catch(()=>({ capex_metrics: {}, return_on_capex: {}, allocation_scorecard: { overall_allocation_score: 0, recommendations: [] } })),
      fetch(`${ANALYSIS_API}/research/${ticker}/risk-assessment`).then(r => r.json()).catch(()=>({ operational_risks: {}, financial_risks: {}, risk_scorecard: { overall_risk_score: 0, key_risks: [], recommendations: [] } })),
      fetch(`${ANALYSIS_API}/research/${ticker}/catalyst-analysis`).then(r => r.json()).catch(()=>({ positive_catalysts: {}, negative_catalysts: {}, catalyst_scorecard: { catalyst_count: 0 } })),
    ]).then(([growth, returns, balance, cashflow, earnings, wc, dividend, valuation, capital, risks, catalysts]) => {
      setAnalysis({
        growth, returns, balance, cashflow, earnings, 'working-capital': wc, dividend, valuation, capital, risks, catalysts
      })
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [ticker])

  return { analysis, loading }
}
