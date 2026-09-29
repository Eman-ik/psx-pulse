'use client';

/**
 * Module 7: Unified Research-to-Trade Flow (REFACTORED)
 *
 * Decision-Support Architecture:
 * Instead of "ENTER/CAUTION/WAIT/AVOID", emphasize case explanation
 *
 * Workflow:
 * 1. Company Intelligence: 18-section research + evidence score
 * 2. Trade Setup: Entry/stop/targets + thesis inputs (why/validation/invalidation/catalyst)
 * 3. Risk & Position: Decision gates validation + position sizing
 * 4. Decision Center: Thesis summary, pillar breakdown, ready to trade check
 */

import React, { useState } from 'react';
import { AlertCircle, CheckCircle2, XCircle, TrendingUp, Lock } from 'lucide-react';
import './UnifiedResearchTradeFlow.css';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

// ════════════════════════════════════════════════════════════════════════════════
// TYPE DEFINITIONS
// ════════════════════════════════════════════════════════════════════════════════

interface EvidenceCoverageScore {
  coverage_pct: number;
  total_sections: number;
  real_sections: number;
  missing_evidence: string[];
  data_freshness_score: number;
  source_reliability: number;
}

interface DecisionGateResult {
  gate_name: string;
  passed: boolean;
  issue: string | null;
}

interface PillarScores {
  Fundamental: number;
  Valuation: number;
  Technical: number;
  Market: number;
}

interface ThesisResult {
  thesis_valid: boolean;
  reason?: string;
  pillar_scores: PillarScores;
  confidence_score: number;
  evidence_coverage: number;
  gates_passed: boolean;
  bull_case: string;
  bear_case: string;
  invalidation: string;
}

interface RiskMetrics {
  risk_per_share: number;
  max_loss: number;
  position_size: number;
  capital_required: number;
  allocation_pct: number;
}

interface UnifiedFlowResponse {
  ticker: string;
  evidence_score: EvidenceCoverageScore;
  gates: DecisionGateResult[];
  gates_passed: boolean;
  fundamental: any;
  valuation: any;
  technical: any;
  market: any;
  events: any;
  thesis: ThesisResult;
  calculator: any;
  ready_to_trade: boolean;
  confidence: number;
  timestamp: string;
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

  // Thesis state
  const [thesisWhy, setThesisWhy] = useState('');
  const [thesisValidation, setThesisValidation] = useState('');
  const [thesisInvalidation, setThesisInvalidation] = useState('');
  const [thesisCatalyst, setThesisCatalyst] = useState('');

  // Results state
  const [unifiedData, setUnifiedData] = useState<UnifiedFlowResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('intelligence');

  // ════════════════════════════════════════════════════════════════════════════════
  // HANDLERS
  // ════════════════════════════════════════════════════════════════════════════════

  const handleCalculate = async () => {
    if (!ticker || !entry || !stop || !portfolio) {
      setError('Please fill in all required fields');
      return;
    }

    const targets = [target1, target2, target3].filter(t => t).map(Number);
    if (targets.length === 0) {
      setError('Please enter at least one target');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE_URL}/research-trade/unified-flow`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ticker,
          entry: parseFloat(entry),
          stop: parseFloat(stop),
          targets: targets.map(Number),
          portfolio_value: parseFloat(portfolio),
          risk_percent: parseFloat(riskPercent),
        }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
      }

      const data = await response.json();
      setUnifiedData(data);
      setActiveTab('decision');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to calculate');
    } finally {
      setLoading(false);
    }
  };

  const handleExportPDF = () => {
    if (!unifiedData) return;
    // TODO: Implement PDF export
    console.log('Exporting to PDF...');
  };

  const handleSaveTradePlan = () => {
    if (!unifiedData) return;
    // TODO: Implement save to database
    console.log('Saving trade plan...');
  };

  // ════════════════════════════════════════════════════════════════════════════════
  // RENDER TABS
  // ════════════════════════════════════════════════════════════════════════════════

  const renderIntelligenceTab = () => (
    <div className="intelligence-tab">
      <div className="tab-header">
        <h3>Company Intelligence</h3>
        {unifiedData && (
          <div className="evidence-badge">
            <span className="badge-label">Evidence Coverage</span>
            <span className="badge-value">{Math.round(unifiedData.evidence_score.coverage_pct)}%</span>
          </div>
        )}
      </div>

      {!unifiedData ? (
        <div className="placeholder">
          <p className="text-muted">Enter ticker and run analysis to view 18-section research report</p>
        </div>
      ) : (
        <div className="evidence-display">
          <div className="coverage-stat">
            <div className="stat-label">Data Completeness</div>
            <div className="stat-value">{unifiedData.evidence_score.real_sections}/{unifiedData.evidence_score.total_sections} sections</div>
            <div className="stat-detail">Freshness: {Math.round(unifiedData.evidence_score.data_freshness_score)}% | Reliability: {Math.round(unifiedData.evidence_score.source_reliability)}%</div>
          </div>
          {unifiedData.evidence_score.missing_evidence.length > 0 && (
            <div className="missing-evidence">
              <div className="label">Missing Evidence</div>
              <ul>
                {unifiedData.evidence_score.missing_evidence.map((item, i) => (
                  <li key={i}>{item}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );

  const renderSetupTab = () => (
    <div className="setup-tab">
      <div className="tab-header">
        <h3>Trade Setup</h3>
      </div>

      <div className="section">
        <h4>Technical Entry Points</h4>
        <div className="input-section">
          <div className="input-group">
            <label className="input-label">Ticker</label>
            <input
              type="text"
              className="input-field"
              value={ticker}
              onChange={(e) => setTicker(e.target.value.toUpperCase())}
              placeholder="e.g., FFC"
            />
          </div>
          <div className="input-group">
            <label className="input-label">Stop Loss</label>
            <input
              type="number"
              className="input-field"
              value={stop}
              onChange={(e) => setStop(e.target.value)}
              step="0.01"
              placeholder="240.00"
            />
          </div>
          <div className="input-group">
            <label className="input-label">Entry Price</label>
            <input
              type="number"
              className="input-field"
              value={entry}
              onChange={(e) => setEntry(e.target.value)}
              step="0.01"
              placeholder="250.00"
            />
          </div>
        </div>

        <div className="price-inputs">
          <div className="input-group">
            <label className="input-label">Target 1</label>
            <input type="number" className="input-field" value={target1} onChange={(e) => setTarget1(e.target.value)} step="0.01" />
          </div>
          <div className="input-group">
            <label className="input-label">Target 2</label>
            <input type="number" className="input-field" value={target2} onChange={(e) => setTarget2(e.target.value)} step="0.01" />
          </div>
          <div className="input-group">
            <label className="input-label">Target 3</label>
            <input type="number" className="input-field" value={target3} onChange={(e) => setTarget3(e.target.value)} step="0.01" />
          </div>
        </div>
      </div>

      <div className="section">
        <h4>Position Sizing</h4>
        <div className="input-section">
          <div className="input-group">
            <label className="input-label">Portfolio Value</label>
            <input type="number" className="input-field" value={portfolio} onChange={(e) => setPortfolio(e.target.value)} placeholder="100000" />
          </div>
          <div className="input-group">
            <label className="input-label">Risk per Trade (%)</label>
            <input type="number" className="input-field" value={riskPercent} onChange={(e) => setRiskPercent(e.target.value)} min="0.1" max="10" step="0.1" />
          </div>
        </div>
      </div>

      <div className="section">
        <h4>Trade Thesis</h4>
        <div className="textarea-group">
          <label className="input-label">Why am I buying this?</label>
          <textarea
            className="input-field textarea"
            value={thesisWhy}
            onChange={(e) => setThesisWhy(e.target.value)}
            placeholder="Describe the fundamental or technical reason for this trade..."
            rows={3}
          />
        </div>
        <div className="textarea-group">
          <label className="input-label">What proves me right?</label>
          <textarea
            className="input-field textarea"
            value={thesisValidation}
            onChange={(e) => setThesisValidation(e.target.value)}
            placeholder="What price action or news would validate this thesis..."
            rows={3}
          />
        </div>
        <div className="textarea-group">
          <label className="input-label">What proves me wrong?</label>
          <textarea
            className="input-field textarea"
            value={thesisInvalidation}
            onChange={(e) => setThesisInvalidation(e.target.value)}
            placeholder="What would invalidate this thesis (breaking support, negative earnings, etc)..."
            rows={3}
          />
        </div>
        <div className="textarea-group">
          <label className="input-label">Expected catalyst</label>
          <textarea
            className="input-field textarea"
            value={thesisCatalyst}
            onChange={(e) => setThesisCatalyst(e.target.value)}
            placeholder="What event or timeframe am I waiting for..."
            rows={2}
          />
        </div>
      </div>

      <div className="action-buttons">
        <button className="button button-primary" onClick={handleCalculate} disabled={loading}>
          {loading ? 'Analyzing...' : 'Run Analysis'}
        </button>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}
    </div>
  );

  const renderRiskTab = () => (
    <div className="risk-tab">
      <div className="tab-header">
        <h3>Risk & Position</h3>
      </div>

      {!unifiedData ? (
        <div className="placeholder">
          <p className="text-muted">Complete Trade Setup tab and run analysis to see risk validation</p>
        </div>
      ) : (
        <>
          <div className="gates-section">
            <h4>Decision Gates</h4>
            <div className="gates-list">
              {unifiedData.gates.map((gate, i) => (
                <div key={i} className={`gate-item ${gate.passed ? 'passed' : 'failed'}`}>
                  <div className="gate-icon">
                    {gate.passed ? <CheckCircle2 size={20} /> : <XCircle size={20} />}
                  </div>
                  <div className="gate-content">
                    <div className="gate-name">{gate.gate_name}</div>
                    {gate.issue && <div className="gate-issue">{gate.issue}</div>}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {unifiedData.calculator && (
            <div className="position-section">
              <h4>Position Sizing</h4>
              <div className="metrics-grid">
                <div className="metric-card">
                  <div className="metric-label">Shares</div>
                  <div className="metric-value">{Math.round(unifiedData.calculator.position_size_shares)}</div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Capital Required</div>
                  <div className="metric-value">${Math.round(unifiedData.calculator.capital_required).toLocaleString()}</div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Risk per Share</div>
                  <div className="metric-value">${(unifiedData.calculator.risk_per_share).toFixed(2)}</div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Max Loss</div>
                  <div className="metric-value warning">${Math.round(unifiedData.calculator.max_loss).toLocaleString()}</div>
                </div>
              </div>
            </div>
          )}

          {unifiedData.calculator?.warnings && unifiedData.calculator.warnings.length > 0 && (
            <div className="warnings-section">
              <h4>Warnings</h4>
              {unifiedData.calculator.warnings.map((warning, i) => (
                <div key={i} className="alert alert-warning">
                  <AlertCircle size={16} />
                  {warning}
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );

  const renderDecisionTab = () => (
    <div className="decision-tab">
      <div className="tab-header">
        <h3>Decision Center</h3>
      </div>

      {!unifiedData ? (
        <div className="placeholder">
          <p className="text-muted">Complete analysis to review final decision</p>
        </div>
      ) : (
        <>
          <div className="gates-status">
            {!unifiedData.gates_passed && (
              <div className="alert alert-danger">
                <XCircle size={20} />
                <div>
                  <div className="alert-title">Decision Gates Failed</div>
                  <div className="alert-detail">This trade does not pass required validation gates. Review the Risk & Position tab.</div>
                </div>
              </div>
            )}
          </div>

          {unifiedData.thesis && (
            <>
              <div className="thesis-section">
                <h4>Thesis Summary</h4>
                <div className="thesis-content">
                  <div className="thesis-item">
                    <div className="thesis-label">Bull Case</div>
                    <div className="thesis-text">{unifiedData.thesis.bull_case}</div>
                  </div>
                  <div className="thesis-item">
                    <div className="thesis-label">Bear Case</div>
                    <div className="thesis-text">{unifiedData.thesis.bear_case}</div>
                  </div>
                  <div className="thesis-item">
                    <div className="thesis-label">Invalidation</div>
                    <div className="thesis-text">{unifiedData.thesis.invalidation}</div>
                  </div>
                </div>
              </div>

              <div className="pillars-section">
                <h4>Pillar Analysis</h4>
                <div className="pillars-grid">
                  {unifiedData.thesis.pillar_scores && Object.entries(unifiedData.thesis.pillar_scores).map(([pillar, score]) => (
                    <div key={pillar} className="pillar-bar">
                      <div className="pillar-label">{pillar}</div>
                      <div className="pillar-score">{Math.round(score)}/100</div>
                      <div className="pillar-fill" style={{ width: `${score}%` }} />
                    </div>
                  ))}
                </div>
              </div>

              <div className="confidence-section">
                <h4>Investment Confidence</h4>
                <div className="confidence-display">
                  <div className="confidence-meter-container">
                    <div className="confidence-value">{Math.round(unifiedData.confidence)}%</div>
                    <div
                      className="confidence-meter"
                      style={{
                        background: unifiedData.confidence >= 70 ? '#10b981' : unifiedData.confidence >= 50 ? '#f59e0b' : '#ef4444',
                      }}
                    />
                  </div>
                  <div className="confidence-detail">
                    Evidence Coverage: {Math.round(unifiedData.thesis.evidence_coverage)}% | Gates Passed: {unifiedData.gates_passed ? 'Yes' : 'No'}
                  </div>
                </div>
              </div>
            </>
          )}

          <div className="action-buttons">
            <button
              className="button button-primary"
              onClick={handleSaveTradePlan}
              disabled={!unifiedData.ready_to_trade}
            >
              <CheckCircle2 size={16} />
              Mark Ready to Trade
            </button>
            <button className="button button-secondary" onClick={handleExportPDF}>
              Export to PDF
            </button>
          </div>
        </>
      )}
    </div>
  );

  // ════════════════════════════════════════════════════════════════════════════════
  // RENDER
  // ════════════════════════════════════════════════════════════════════════════════

  return (
    <div className="unified-research-trade-flow">
      <div className="flow-header">
        <h1>Trade Analysis</h1>
        <p className="flow-subtitle">Research-driven decision support for position entry</p>
      </div>

      <div className="tabs-container">
        <button
          className={`tab-button ${activeTab === 'intelligence' ? 'active' : ''}`}
          onClick={() => setActiveTab('intelligence')}
        >
          Company Intelligence
        </button>
        <button
          className={`tab-button ${activeTab === 'setup' ? 'active' : ''}`}
          onClick={() => setActiveTab('setup')}
        >
          Trade Setup
        </button>
        <button
          className={`tab-button ${activeTab === 'risk' ? 'active' : ''}`}
          onClick={() => setActiveTab('risk')}
        >
          Risk & Position
        </button>
        <button
          className={`tab-button ${activeTab === 'decision' ? 'active' : ''}`}
          onClick={() => setActiveTab('decision')}
        >
          Decision Center
        </button>
      </div>

      <div className="tabs-content">
        {activeTab === 'intelligence' && renderIntelligenceTab()}
        {activeTab === 'setup' && renderSetupTab()}
        {activeTab === 'risk' && renderRiskTab()}
        {activeTab === 'decision' && renderDecisionTab()}
      </div>
    </div>
  );
}
