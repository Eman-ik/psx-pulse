'use client';

/**
 * Module 7: Unified Research-to-Trade Flow
 *
 * Complete workflow: Research Report → Technical Setup → Position Sizing → Decision
 *
 * Tabs:
 * 1. Research: Display 18-section report + quality score
 * 2. Technical Setup: Input entry/stop/targets + portfolio
 * 3. Position Calculator: Display position sizing results
 * 4. Decision Scorecard: Display unified confidence + recommendation
 */

import React, { useState, useEffect } from 'react';
import { AlertCircle, CheckCircle2, TrendingUp, TrendingDown, Zap } from 'lucide-react';
import { EquityResearchSections } from './research/EquityResearchSections';
import './UnifiedResearchTradeFlow.css';


// ════════════════════════════════════════════════════════════════════════════════
// TYPE DEFINITIONS
// ════════════════════════════════════════════════════════════════════════════════

interface RiskMetrics {
  risk_per_share: number;
  max_loss: number;
  position_size: number;
  capital_required: number;
  allocation_pct: number;
}

interface RiskRewardRatio {
  target: number;
  reward: number;
  ratio: number;
}

interface CalculatorOutput {
  risk_metrics: RiskMetrics;
  risk_reward_ratios: RiskRewardRatio[];
  liquidity_category: string | null;
  warnings: string[];
}

interface ResearchQualityScore {
  overall_score: number;
  total_sections: number;
  real_content_sections: number;
  missing_evidence_count: number;
  confidence_adjustment: number;
}

interface ConfidenceBreakdown {
  research_quality_score: number;
  technical_score: number;
  market_score: number;
  fundamental_score: number;
  valuation_score: number;
  events_score: number;
  overall_confidence: number;
  key_reasons: string[];
}

interface UnifiedResponse {
  ticker: string;
  security_id: string | null;
  research_report: any;
  research_quality_score: ResearchQualityScore;
  calculator_output: CalculatorOutput;
  contexts: {
    technical: any;
    market: any;
    fundamental: any;
    valuation: any;
    events: any;
  };
  confidence_breakdown: ConfidenceBreakdown;
  unified_confidence_score: number;
  entry_recommendation: 'ENTER' | 'CAUTION' | 'WAIT' | 'AVOID';
}


// ════════════════════════════════════════════════════════════════════════════════
// MAIN COMPONENT
// ════════════════════════════════════════════════════════════════════════════════

export function UnifiedResearchTradeFlow() {
  // Input state
  const [ticker, setTicker] = useState('');
  const [entry, setEntry] = useState('');
  const [stop, setStop] = useState('');
  const [target1, setTarget1] = useState('');
  const [target2, setTarget2] = useState('');
  const [target3, setTarget3] = useState('');
  const [portfolio, setPortfolio] = useState('');
  const [riskPercent, setRiskPercent] = useState('2');

  // Results state
  const [unifiedData, setUnifiedData] = useState<UnifiedResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // UI state
  const [activeTab, setActiveTab] = useState<'research' | 'setup' | 'calculator' | 'scorecard'>('research');
  const [showConfirmation, setShowConfirmation] = useState(false);


  // ─── TAB 1: RESEARCH ─────────────────────────────────────────────────────────

  const TabResearch = () => (
    <div className="research-tab">
      <div className="tab-header">
        <h3>Company Research</h3>
        <div className="research-quality-badge">
          <span className="quality-label">Research Quality</span>
          <span className="quality-score">
            {unifiedData?.research_quality_score.overall_score.toFixed(0)}%
          </span>
          <span className="quality-details">
            {unifiedData?.research_quality_score.real_content_sections}/
            {unifiedData?.research_quality_score.total_sections} sections
          </span>
        </div>
      </div>

      {unifiedData?.research_report ? (
        <EquityResearchSections r={unifiedData.research_report} />
      ) : (
        <div className="placeholder">
          <p className="text-muted">Enter a ticker and click "Fetch Research" to load report</p>
        </div>
      )}
    </div>
  );


  // ─── TAB 2: TECHNICAL SETUP ──────────────────────────────────────────────────

  const TabTechnicalSetup = () => (
    <div className="setup-tab">
      <div className="tab-header">
        <h3>Technical Setup</h3>
      </div>

      <div className="input-section">
        {/* Ticker input */}
        <div className="input-group">
          <label htmlFor="ticker" className="input-label">Ticker</label>
          <input
            id="ticker"
            type="text"
            className="input-field"
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
            placeholder="e.g., FFC"
          />
        </div>

        {/* Entry/Stop/Targets grid */}
        <div className="price-inputs">
          <div className="input-group">
            <label htmlFor="stop" className="input-label">Stop Loss</label>
            <input
              id="stop"
              type="number"
              className="input-field"
              value={stop}
              onChange={(e) => setStop(e.target.value)}
              placeholder="e.g., 240"
              step="0.01"
            />
          </div>

          <div className="input-group">
            <label htmlFor="entry" className="input-label">Entry Price</label>
            <input
              id="entry"
              type="number"
              className="input-field"
              value={entry}
              onChange={(e) => setEntry(e.target.value)}
              placeholder="e.g., 250"
              step="0.01"
            />
          </div>

          <div className="input-group">
            <label htmlFor="target1" className="input-label">Target 1</label>
            <input
              id="target1"
              type="number"
              className="input-field"
              value={target1}
              onChange={(e) => setTarget1(e.target.value)}
              placeholder="e.g., 260"
              step="0.01"
            />
          </div>

          <div className="input-group">
            <label htmlFor="target2" className="input-label">Target 2</label>
            <input
              id="target2"
              type="number"
              className="input-field"
              value={target2}
              onChange={(e) => setTarget2(e.target.value)}
              placeholder="e.g., 270"
              step="0.01"
            />
          </div>

          <div className="input-group">
            <label htmlFor="target3" className="input-label">Target 3</label>
            <input
              id="target3"
              type="number"
              className="input-field"
              value={target3}
              onChange={(e) => setTarget3(e.target.value)}
              placeholder="e.g., 280"
              step="0.01"
            />
          </div>
        </div>

        {/* Portfolio and risk */}
        <div className="portfolio-inputs">
          <div className="input-group">
            <label htmlFor="portfolio" className="input-label">Portfolio Value</label>
            <input
              id="portfolio"
              type="number"
              className="input-field"
              value={portfolio}
              onChange={(e) => setPortfolio(e.target.value)}
              placeholder="e.g., 100000"
              step="1000"
            />
          </div>

          <div className="input-group">
            <label htmlFor="risk" className="input-label">Risk % per Trade</label>
            <input
              id="risk"
              type="number"
              className="input-field"
              value={riskPercent}
              onChange={(e) => setRiskPercent(e.target.value)}
              placeholder="e.g., 2"
              min="0.1"
              max="10"
              step="0.1"
            />
          </div>
        </div>

        {/* Action buttons */}
        <div className="action-buttons">
          <button
            className="button button-primary"
            onClick={handleCalculate}
            disabled={loading || !ticker || !entry || !stop || !target1 || !portfolio}
          >
            {loading ? 'Calculating...' : 'Calculate All'}
          </button>
        </div>

        {error && (
          <div className="alert alert-danger">
            <AlertCircle size={16} />
            {error}
          </div>
        )}
      </div>
    </div>
  );


  // ─── TAB 3: POSITION CALCULATOR ──────────────────────────────────────────────

  const TabPositionCalculator = () => (
    <div className="calculator-tab">
      <div className="tab-header">
        <h3>Position Sizing Results</h3>
      </div>

      {unifiedData?.calculator_output ? (
        <div className="results-container">
          {/* Risk metrics grid */}
          <div className="metrics-grid">
            <div className="metric-card">
              <div className="metric-label">Risk per Share</div>
              <div className="metric-value">
                PKR {unifiedData.calculator_output.risk_metrics.risk_per_share.toFixed(2)}
              </div>
            </div>

            <div className="metric-card">
              <div className="metric-label">Max Loss</div>
              <div className="metric-value warning">
                PKR {unifiedData.calculator_output.risk_metrics.max_loss.toFixed(0)}
              </div>
            </div>

            <div className="metric-card">
              <div className="metric-label">Position Size</div>
              <div className="metric-value">
                {unifiedData.calculator_output.risk_metrics.position_size} shares
              </div>
            </div>

            <div className="metric-card">
              <div className="metric-label">Capital Required</div>
              <div className="metric-value">
                PKR {unifiedData.calculator_output.risk_metrics.capital_required.toFixed(0)}
              </div>
            </div>

            <div className="metric-card">
              <div className="metric-label">Allocation %</div>
              <div className="metric-value">
                {unifiedData.calculator_output.risk_metrics.allocation_pct.toFixed(1)}%
              </div>
            </div>

            <div className="metric-card">
              <div className="metric-label">Liquidity</div>
              <div className="metric-value">
                {unifiedData.calculator_output.liquidity_category || 'N/A'}
              </div>
            </div>
          </div>

          {/* Risk/Reward ratios */}
          {unifiedData.calculator_output.risk_reward_ratios.length > 0 && (
            <div className="content-card">
              <h4>Risk/Reward Ratios</h4>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Target Price</th>
                    <th>Reward per Share</th>
                    <th>Ratio</th>
                  </tr>
                </thead>
                <tbody>
                  {unifiedData.calculator_output.risk_reward_ratios.map((rr, i) => (
                    <tr key={i}>
                      <td>PKR {rr.target.toFixed(2)}</td>
                      <td>PKR {rr.reward.toFixed(2)}</td>
                      <td>{rr.ratio.toFixed(2)}:1</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Warnings */}
          {unifiedData.calculator_output.warnings.length > 0 && (
            <div className="content-card">
              <h4>Warnings</h4>
              {unifiedData.calculator_output.warnings.map((warning, i) => (
                <div key={i} className="alert alert-warning">
                  <AlertCircle size={16} />
                  {warning}
                </div>
              ))}
            </div>
          )}
        </div>
      ) : (
        <div className="placeholder">
          <p className="text-muted">Fill in the technical setup and click "Calculate All" to see results</p>
        </div>
      )}
    </div>
  );


  // ─── TAB 4: DECISION SCORECARD ───────────────────────────────────────────────

  const TabDecisionScorecard = () => (
    <div className="scorecard-tab">
      <div className="tab-header">
        <h3>Decision Scorecard</h3>
      </div>

      {unifiedData ? (
        <div className="scorecard-container">
          {/* Confidence score - large display */}
          <div className="confidence-section">
            <div className="confidence-meter">
              <div
                className="confidence-fill"
                style={{
                  width: `${unifiedData.unified_confidence_score}%`,
                  backgroundColor:
                    unifiedData.unified_confidence_score >= 75
                      ? '#10b981'
                      : unifiedData.unified_confidence_score >= 60
                      ? '#f59e0b'
                      : '#ef4444',
                }}
              />
            </div>
            <div className="confidence-value">
              {unifiedData.unified_confidence_score.toFixed(0)}% Confidence
            </div>
          </div>

          {/* Entry recommendation - large badge */}
          <div className="recommendation-section">
            <div
              className={`recommendation-badge recommendation-${unifiedData.entry_recommendation.toLowerCase()}`}
            >
              {unifiedData.entry_recommendation}
            </div>
            <div className="recommendation-label">
              {unifiedData.entry_recommendation === 'ENTER' && '✅ Ready to enter'}
              {unifiedData.entry_recommendation === 'CAUTION' && '⚠️ Proceed with caution'}
              {unifiedData.entry_recommendation === 'WAIT' && '⏳ Wait for confirmation'}
              {unifiedData.entry_recommendation === 'AVOID' && '❌ Do not enter'}
            </div>
          </div>

          {/* Key reasons breakdown */}
          <div className="content-card">
            <h4>Key Reasons for {unifiedData.unified_confidence_score.toFixed(0)}% Confidence</h4>
            <div className="reasons-list">
              {unifiedData.confidence_breakdown.key_reasons.map((reason, i) => (
                <div key={i} className="reason-item">
                  <div className="reason-dot" />
                  <span>{reason}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Detailed breakdown */}
          <div className="content-card">
            <h4>Detailed Score Breakdown</h4>
            <div className="breakdown-grid">
              <ScoreBar
                label="Research Quality"
                score={unifiedData.confidence_breakdown.research_quality_score}
                weight={15}
              />
              <ScoreBar
                label="Technical"
                score={unifiedData.confidence_breakdown.technical_score}
                weight={20}
              />
              <ScoreBar
                label="Market"
                score={unifiedData.confidence_breakdown.market_score}
                weight={20}
              />
              <ScoreBar
                label="Fundamental"
                score={unifiedData.confidence_breakdown.fundamental_score}
                weight={15}
              />
              <ScoreBar
                label="Valuation"
                score={unifiedData.confidence_breakdown.valuation_score}
                weight={15}
              />
              <ScoreBar
                label="Events"
                score={unifiedData.confidence_breakdown.events_score}
                weight={15}
              />
            </div>
          </div>

          {/* Position recap */}
          <div className="content-card">
            <h4>Position Summary</h4>
            <div className="summary-grid">
              <div className="summary-item">
                <span className="summary-label">Shares</span>
                <span className="summary-value">
                  {unifiedData.calculator_output.risk_metrics.position_size}
                </span>
              </div>
              <div className="summary-item">
                <span className="summary-label">Capital</span>
                <span className="summary-value">
                  PKR {unifiedData.calculator_output.risk_metrics.capital_required.toFixed(0)}
                </span>
              </div>
              <div className="summary-item">
                <span className="summary-label">Max Loss</span>
                <span className="summary-value warning">
                  PKR {unifiedData.calculator_output.risk_metrics.max_loss.toFixed(0)}
                </span>
              </div>
              <div className="summary-item">
                <span className="summary-label">% Portfolio</span>
                <span className="summary-value">
                  {unifiedData.calculator_output.risk_metrics.allocation_pct.toFixed(1)}%
                </span>
              </div>
            </div>
          </div>

          {/* Action buttons */}
          <div className="action-buttons">
            <button className="button button-secondary" onClick={handleExportPDF}>
              📄 Export to PDF
            </button>
            <button className="button button-secondary" onClick={handleSaveTradePlan}>
              💾 Save Trade Plan
            </button>
            <button className="button button-primary" onClick={() => setShowConfirmation(true)}>
              ✅ Mark Ready
            </button>
          </div>
        </div>
      ) : (
        <div className="placeholder">
          <p className="text-muted">Calculate to see decision scorecard</p>
        </div>
      )}
    </div>
  );


  // ─── EVENT HANDLERS ──────────────────────────────────────────────────────────

  async function handleCalculate() {
    if (!ticker || !entry || !stop || !target1 || !portfolio) {
      setError('Please fill in all required fields');
      return;
    }

    const targets = [parseFloat(target1)];
    if (target2) targets.push(parseFloat(target2));
    if (target3) targets.push(parseFloat(target3));

    setLoading(true);
    setError('');

    try {
      const response = await fetch('/api/research-trade/unified-flow', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ticker,
          entry: parseFloat(entry),
          stop: parseFloat(stop),
          targets,
          portfolio_value: parseFloat(portfolio),
          risk_percent: parseFloat(riskPercent),
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        setError(data.error || `Server error ${response.status}`);
        return;
      }

      setUnifiedData(data.unified_response);
      setActiveTab('calculator');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Network error');
    } finally {
      setLoading(false);
    }
  }

  function handleExportPDF() {
    alert('PDF export coming soon!');
  }

  function handleSaveTradePlan() {
    alert('Save to database coming soon!');
  }


  // ─── RENDER ──────────────────────────────────────────────────────────────────

  return (
    <div className="unified-research-trade-flow">
      <div className="flow-header">
        <h1>Research-to-Trade Decision Tool</h1>
        <p className="flow-subtitle">Unified analysis: Research + Technical + Position Sizing + Confidence Scoring</p>
      </div>

      {/* Tab navigation */}
      <div className="tabs-container">
        <button
          className={`tab-button ${activeTab === 'research' ? 'active' : ''}`}
          onClick={() => setActiveTab('research')}
        >
          📊 Research
        </button>
        <button
          className={`tab-button ${activeTab === 'setup' ? 'active' : ''}`}
          onClick={() => setActiveTab('setup')}
        >
          ⚙️ Setup
        </button>
        <button
          className={`tab-button ${activeTab === 'calculator' ? 'active' : ''}`}
          onClick={() => setActiveTab('calculator')}
        >
          🧮 Calculator
        </button>
        <button
          className={`tab-button ${activeTab === 'scorecard' ? 'active' : ''}`}
          onClick={() => setActiveTab('scorecard')}
        >
          🎯 Scorecard
        </button>
      </div>

      {/* Tab content */}
      <div className="tabs-content">
        {activeTab === 'research' && <TabResearch />}
        {activeTab === 'setup' && <TabTechnicalSetup />}
        {activeTab === 'calculator' && <TabPositionCalculator />}
        {activeTab === 'scorecard' && <TabDecisionScorecard />}
      </div>

      {/* Confirmation modal */}
      {showConfirmation && (
        <div className="modal-overlay" onClick={() => setShowConfirmation(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3 className="modal-title">Mark Trade Plan as Ready?</h3>
            <p className="modal-text">
              You're about to mark this trade plan as ready for execution. Make sure all analysis is complete.
            </p>
            <div className="modal-buttons">
              <button className="button button-secondary" onClick={() => setShowConfirmation(false)}>
                Cancel
              </button>
              <button className="button button-primary" onClick={() => {
                alert('Status updated to READY');
                setShowConfirmation(false);
              }}>
                Mark Ready
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}


// ════════════════════════════════════════════════════════════════════════════════
// HELPER COMPONENTS
// ════════════════════════════════════════════════════════════════════════════════

interface ScoreBarProps {
  label: string;
  score: number;
  weight: number;
}

function ScoreBar({ label, score, weight }: ScoreBarProps) {
  const points = Math.round((score * weight) / 100);
  return (
    <div className="score-bar-container">
      <div className="score-bar-label">{label}</div>
      <div className="score-bar-wrapper">
        <div
          className="score-bar-fill"
          style={{
            width: `${score}%`,
            backgroundColor: score >= 75 ? '#10b981' : score >= 60 ? '#f59e0b' : '#ef4444',
          }}
        />
      </div>
      <div className="score-bar-value">
        {score.toFixed(0)}/100 ({weight}% weight, {points} pts)
      </div>
    </div>
  );
}
