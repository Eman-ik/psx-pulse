/**
 * Module 6, Sprint R8: Trade Planning Dashboard UI
 *
 * Comprehensive trade planning interface integrating:
 * - R1: Position sizing calculations
 * - R2: Trade plan persistence
 * - R3: Technical context (support/resistance)
 * - R4: Market context (regime, sector)
 * - R5: Fundamental context (quality, momentum)
 * - R6: Valuation context (P/E, margin of safety)
 * - R7: Events context (catalyst timing)
 */

import React, { useState, useEffect } from 'react';
import './TradePlanDashboard.css';

// Context layer interfaces
interface CalculatorOutput {
  risk_per_share: number;
  max_loss: number;
  position_size: number;
  capital_required: number;
  allocation_pct: number;
  warnings: string[];
}

interface TechnicalContext {
  zones: any[];
  atr: number;
  volatility_pct: number;
  suggested_stop: number;
  suggested_targets: number[];
}

interface MarketContext {
  regime: string;
  regime_confidence: number;
  market_health: string;
  sector_trend: string;
  breadth_pct: number;
}

interface FundamentalContext {
  momentum: string;
  financial_health_score: number;
  quality_score: number;
  eps_trend: string;
}

interface ValuationContext {
  status: string;
  pe_relative: string;
  valuation_score: number;
  margin_of_safety: number;
  upside_potential: number;
}

interface EventCalendar {
  nearest_event?: {
    event_type: string;
    event_date: string;
    importance: number;
  };
  days_to_nearest: number;
  event_risk_score: number;
  entry_recommendation: string;
}

interface TradePlan {
  ticker: string;
  entry_price: number;
  stop_price: number;
  target_prices: number[];
  thesis: string;
  invalidation_thesis: string;
  calculator_output?: CalculatorOutput;
  technical_context?: TechnicalContext;
  market_context?: MarketContext;
  fundamental_context?: FundamentalContext;
  valuation_context?: ValuationContext;
  event_calendar?: EventCalendar;
}

interface TradeStatus {
  status: 'DRAFT' | 'WATCHING' | 'READY' | 'ENTERED' | 'CLOSED';
  confidence: number;
}

// ════════════════════════════════════════════════════════════════════════════════
// Main Dashboard Component
// ════════════════════════════════════════════════════════════════════════════════

export const TradePlanDashboard: React.FC = () => {
  const [tradePlan, setTradePlan] = useState<TradePlan>({
    ticker: '',
    entry_price: 0,
    stop_price: 0,
    target_prices: [],
    thesis: '',
    invalidation_thesis: '',
  });

  const [tradeStatus, setTradeStatus] = useState<TradeStatus>({
    status: 'DRAFT',
    confidence: 0,
  });

  const [activeTab, setActiveTab] = useState<
    'input' | 'calculator' | 'technical' | 'market' | 'fundamental' | 'valuation' | 'events' | 'summary'
  >('input');

  const calculateDecisionConfidence = (): number => {
    let confidence = 0;
    let factors = 0;

    // Technical
    if (tradePlan.technical_context) {
      confidence += 15;
      factors++;
    }

    // Market
    if (tradePlan.market_context?.regime === 'STRONG_BULLISH') {
      confidence += 20;
    } else if (tradePlan.market_context?.regime === 'BULLISH') {
      confidence += 10;
    }
    factors++;

    // Fundamentals
    if (tradePlan.fundamental_context) {
      const momentum = tradePlan.fundamental_context.momentum;
      if (momentum === 'ACCELERATING') {
        confidence += 15;
      } else if (momentum === 'IMPROVING') {
        confidence += 10;
      }
      factors++;
    }

    // Valuation
    if (tradePlan.valuation_context) {
      const mos = tradePlan.valuation_context.margin_of_safety;
      if (mos > 20) {
        confidence += 15;
      } else if (mos > 10) {
        confidence += 10;
      }
      factors++;
    }

    // Events
    if (tradePlan.event_calendar) {
      const eventRisk = tradePlan.event_calendar.event_risk_score;
      if (eventRisk < 30) {
        confidence += 10;
      } else if (eventRisk > 70) {
        confidence -= 10;
      }
      factors++;
    }

    return factors > 0 ? Math.min(100, (confidence / (factors * 20)) * 100) : 0;
  };

  useEffect(() => {
    setTradeStatus({
      ...tradeStatus,
      confidence: calculateDecisionConfidence(),
    });
  }, [tradePlan]);

  return (
    <div className="trade-plan-dashboard">
      <header className="dashboard-header">
        <h1>Trade Planning Dashboard</h1>
        <div className="header-info">
          <span className="ticker-display">{tradePlan.ticker || 'SELECT TICKER'}</span>
          <div className="status-badge" data-status={tradeStatus.status}>
            {tradeStatus.status}
          </div>
          <div className="confidence-meter">
            <span>Decision Quality</span>
            <div className="confidence-bar">
              <div
                className="confidence-fill"
                style={{ width: `${tradeStatus.confidence}%` }}
              ></div>
            </div>
            <span className="confidence-pct">{tradeStatus.confidence.toFixed(0)}%</span>
          </div>
        </div>
      </header>

      <nav className="tab-navigation">
        <button
          className={`tab ${activeTab === 'input' ? 'active' : ''}`}
          onClick={() => setActiveTab('input')}
        >
          Input
        </button>
        <button
          className={`tab ${activeTab === 'calculator' ? 'active' : ''}`}
          onClick={() => setActiveTab('calculator')}
        >
          Position Sizing
        </button>
        <button
          className={`tab ${activeTab === 'technical' ? 'active' : ''}`}
          onClick={() => setActiveTab('technical')}
        >
          Technical
        </button>
        <button
          className={`tab ${activeTab === 'market' ? 'active' : ''}`}
          onClick={() => setActiveTab('market')}
        >
          Market
        </button>
        <button
          className={`tab ${activeTab === 'fundamental' ? 'active' : ''}`}
          onClick={() => setActiveTab('fundamental')}
        >
          Fundamentals
        </button>
        <button
          className={`tab ${activeTab === 'valuation' ? 'active' : ''}`}
          onClick={() => setActiveTab('valuation')}
        >
          Valuation
        </button>
        <button
          className={`tab ${activeTab === 'events' ? 'active' : ''}`}
          onClick={() => setActiveTab('events')}
        >
          Events
        </button>
        <button
          className={`tab ${activeTab === 'summary' ? 'active' : ''}`}
          onClick={() => setActiveTab('summary')}
        >
          Summary
        </button>
      </nav>

      <main className="dashboard-content">
        {activeTab === 'input' && <InputSection tradePlan={tradePlan} setTradePlan={setTradePlan} />}
        {activeTab === 'calculator' && <CalculatorSection output={tradePlan.calculator_output} />}
        {activeTab === 'technical' && <TechnicalSection context={tradePlan.technical_context} />}
        {activeTab === 'market' && <MarketSection context={tradePlan.market_context} />}
        {activeTab === 'fundamental' && <FundamentalSection context={tradePlan.fundamental_context} />}
        {activeTab === 'valuation' && <ValuationSection context={tradePlan.valuation_context} />}
        {activeTab === 'events' && <EventsSection calendar={tradePlan.event_calendar} />}
        {activeTab === 'summary' && <SummarySection tradePlan={tradePlan} confidence={tradeStatus.confidence} />}
      </main>
    </div>
  );
};

// ════════════════════════════════════════════════════════════════════════════════
// Input Section
// ════════════════════════════════════════════════════════════════════════════════

const InputSection: React.FC<{
  tradePlan: TradePlan;
  setTradePlan: (plan: TradePlan) => void;
}> = ({ tradePlan, setTradePlan }) => {
  return (
    <section className="input-section">
      <h2>Trade Setup</h2>

      <div className="input-grid">
        <div className="form-group">
          <label>Ticker</label>
          <input
            type="text"
            value={tradePlan.ticker}
            onChange={(e) =>
              setTradePlan({ ...tradePlan, ticker: e.target.value.toUpperCase() })
            }
            placeholder="e.g., AAPL"
          />
        </div>

        <div className="form-group">
          <label>Entry Price ($)</label>
          <input
            type="number"
            value={tradePlan.entry_price}
            onChange={(e) =>
              setTradePlan({ ...tradePlan, entry_price: parseFloat(e.target.value) || 0 })
            }
            step="0.01"
            min="0"
          />
        </div>

        <div className="form-group">
          <label>Stop Price ($)</label>
          <input
            type="number"
            value={tradePlan.stop_price}
            onChange={(e) =>
              setTradePlan({ ...tradePlan, stop_price: parseFloat(e.target.value) || 0 })
            }
            step="0.01"
            min="0"
          />
        </div>

        <div className="form-group">
          <label>Target 1 ($)</label>
          <input
            type="number"
            value={tradePlan.target_prices[0] || ''}
            onChange={(e) => {
              const targets = [...tradePlan.target_prices];
              targets[0] = parseFloat(e.target.value) || 0;
              setTradePlan({ ...tradePlan, target_prices: targets });
            }}
            step="0.01"
            min="0"
          />
        </div>

        <div className="form-group">
          <label>Target 2 ($)</label>
          <input
            type="number"
            value={tradePlan.target_prices[1] || ''}
            onChange={(e) => {
              const targets = [...tradePlan.target_prices];
              targets[1] = parseFloat(e.target.value) || 0;
              setTradePlan({ ...tradePlan, target_prices: targets });
            }}
            step="0.01"
            min="0"
          />
        </div>

        <div className="form-group">
          <label>Target 3 ($)</label>
          <input
            type="number"
            value={tradePlan.target_prices[2] || ''}
            onChange={(e) => {
              const targets = [...tradePlan.target_prices];
              targets[2] = parseFloat(e.target.value) || 0;
              setTradePlan({ ...tradePlan, target_prices: targets });
            }}
            step="0.01"
            min="0"
          />
        </div>
      </div>

      <div className="thesis-section">
        <div className="form-group full-width">
          <label>Entry Thesis</label>
          <textarea
            value={tradePlan.thesis}
            onChange={(e) => setTradePlan({ ...tradePlan, thesis: e.target.value })}
            placeholder="Why are you entering this trade?"
            rows={4}
          />
        </div>

        <div className="form-group full-width">
          <label>Invalidation Thesis</label>
          <textarea
            value={tradePlan.invalidation_thesis}
            onChange={(e) =>
              setTradePlan({ ...tradePlan, invalidation_thesis: e.target.value })
            }
            placeholder="What would prove this thesis wrong?"
            rows={4}
          />
        </div>
      </div>

      <div className="quick-metrics">
        <div className="metric">
          <span className="label">Risk Per Share</span>
          <span className="value">${(tradePlan.entry_price - tradePlan.stop_price).toFixed(2)}</span>
        </div>
        <div className="metric">
          <span className="label">Risk/Reward (T1)</span>
          <span className="value">
            1:{tradePlan.target_prices[0]
              ? (
                  (tradePlan.target_prices[0] - tradePlan.entry_price) /
                  (tradePlan.entry_price - tradePlan.stop_price)
                ).toFixed(2)
              : '—'}
          </span>
        </div>
        <div className="metric">
          <span className="label">Risk/Reward (T2)</span>
          <span className="value">
            1:{tradePlan.target_prices[1]
              ? (
                  (tradePlan.target_prices[1] - tradePlan.entry_price) /
                  (tradePlan.entry_price - tradePlan.stop_price)
                ).toFixed(2)
              : '—'}
          </span>
        </div>
        <div className="metric">
          <span className="label">Risk/Reward (T3)</span>
          <span className="value">
            1:{tradePlan.target_prices[2]
              ? (
                  (tradePlan.target_prices[2] - tradePlan.entry_price) /
                  (tradePlan.entry_price - tradePlan.stop_price)
                ).toFixed(2)
              : '—'}
          </span>
        </div>
      </div>
    </section>
  );
};

// ════════════════════════════════════════════════════════════════════════════════
// Calculator Section (Position Sizing)
// ════════════════════════════════════════════════════════════════════════════════

const CalculatorSection: React.FC<{ output?: CalculatorOutput }> = ({ output }) => {
  if (!output) {
    return (
      <section className="context-section">
        <h2>Position Sizing Results</h2>
        <div className="placeholder">No calculation data available</div>
      </section>
    );
  }

  return (
    <section className="context-section calculator-section">
      <h2>Position Sizing Results</h2>

      <div className="metrics-grid">
        <div className="metric-card">
          <span className="metric-label">Risk Per Share</span>
          <span className="metric-value">${output.risk_per_share.toFixed(2)}</span>
        </div>

        <div className="metric-card">
          <span className="metric-label">Max Loss</span>
          <span className="metric-value">${output.max_loss.toFixed(0)}</span>
        </div>

        <div className="metric-card">
          <span className="metric-label">Position Size</span>
          <span className="metric-value">{output.position_size.toFixed(0)} shares</span>
        </div>

        <div className="metric-card">
          <span className="metric-label">Capital Required</span>
          <span className="metric-value">${output.capital_required.toFixed(0)}</span>
        </div>

        <div className="metric-card">
          <span className="metric-label">Portfolio Allocation</span>
          <span className="metric-value">{output.allocation_pct.toFixed(2)}%</span>
        </div>
      </div>

      {output.warnings && output.warnings.length > 0 && (
        <div className="warnings-section">
          <h3>⚠️ Warnings</h3>
          <ul>
            {output.warnings.map((warning, idx) => (
              <li key={idx}>{warning}</li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
};

// ════════════════════════════════════════════════════════════════════════════════
// Technical Section
// ════════════════════════════════════════════════════════════════════════════════

const TechnicalSection: React.FC<{ context?: TechnicalContext }> = ({ context }) => {
  if (!context) {
    return (
      <section className="context-section">
        <h2>Technical Context</h2>
        <div className="placeholder">No technical data available</div>
      </section>
    );
  }

  return (
    <section className="context-section">
      <h2>Technical Context</h2>

      <div className="metrics-grid">
        <div className="metric-card">
          <span className="metric-label">ATR (14)</span>
          <span className="metric-value">${context.atr.toFixed(2)}</span>
        </div>

        <div className="metric-card">
          <span className="metric-label">Volatility</span>
          <span className="metric-value">{context.volatility_pct.toFixed(1)}%</span>
        </div>

        <div className="metric-card">
          <span className="metric-label">Suggested Stop</span>
          <span className="metric-value">${context.suggested_stop.toFixed(2)}</span>
        </div>
      </div>

      <div className="targets-section">
        <h3>Suggested Targets (ATR-based)</h3>
        <div className="targets-list">
          {context.suggested_targets.map((target, idx) => (
            <div key={idx} className="target-item">
              <span className="target-label">Target {idx + 1}</span>
              <span className="target-value">${target.toFixed(2)}</span>
            </div>
          ))}
        </div>
      </div>

      {context.zones && context.zones.length > 0 && (
        <div className="zones-section">
          <h3>Support/Resistance Zones</h3>
          <div className="zones-list">
            {context.zones.map((zone, idx) => (
              <div key={idx} className="zone-item">
                <span className="zone-level">${zone.level.toFixed(2)}</span>
                <span className={`zone-strength ${zone.strength.toLowerCase()}`}>
                  {zone.strength}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
};

// ════════════════════════════════════════════════════════════════════════════════
// Market Section
// ════════════════════════════════════════════════════════════════════════════════

const MarketSection: React.FC<{ context?: MarketContext }> = ({ context }) => {
  if (!context) {
    return (
      <section className="context-section">
        <h2>Market Context</h2>
        <div className="placeholder">No market data available</div>
      </section>
    );
  }

  return (
    <section className="context-section">
      <h2>Market Context</h2>

      <div className="metrics-grid">
        <div className="metric-card">
          <span className="metric-label">Market Regime</span>
          <span className={`metric-value regime-${context.regime.toLowerCase()}`}>
            {context.regime}
          </span>
        </div>

        <div className="metric-card">
          <span className="metric-label">Regime Confidence</span>
          <span className="metric-value">{(context.regime_confidence * 100).toFixed(0)}%</span>
        </div>

        <div className="metric-card">
          <span className="metric-label">Market Health</span>
          <span className={`metric-value health-${context.market_health.toLowerCase()}`}>
            {context.market_health}
          </span>
        </div>

        <div className="metric-card">
          <span className="metric-label">Sector Trend</span>
          <span className={`metric-value trend-${context.sector_trend.toLowerCase()}`}>
            {context.sector_trend}
          </span>
        </div>

        <div className="metric-card">
          <span className="metric-label">Market Breadth</span>
          <span className="metric-value">{context.breadth_pct.toFixed(1)}%</span>
        </div>
      </div>
    </section>
  );
};

// ════════════════════════════════════════════════════════════════════════════════
// Fundamental Section
// ════════════════════════════════════════════════════════════════════════════════

const FundamentalSection: React.FC<{ context?: FundamentalContext }> = ({ context }) => {
  if (!context) {
    return (
      <section className="context-section">
        <h2>Fundamental Context</h2>
        <div className="placeholder">No fundamental data available</div>
      </section>
    );
  }

  return (
    <section className="context-section">
      <h2>Fundamental Context</h2>

      <div className="metrics-grid">
        <div className="metric-card">
          <span className="metric-label">Financial Momentum</span>
          <span className={`metric-value momentum-${context.momentum.toLowerCase()}`}>
            {context.momentum}
          </span>
        </div>

        <div className="metric-card">
          <span className="metric-label">Financial Health</span>
          <span className="metric-value">{context.financial_health_score.toFixed(0)}/100</span>
        </div>

        <div className="metric-card">
          <span className="metric-label">Quality Score</span>
          <span className="metric-value">{context.quality_score.toFixed(0)}/100</span>
        </div>

        <div className="metric-card">
          <span className="metric-label">EPS Trend</span>
          <span className={`metric-value trend-${context.eps_trend.toLowerCase()}`}>
            {context.eps_trend}
          </span>
        </div>
      </div>

      <div className="score-bars">
        <div className="score-bar">
          <span className="label">Financial Health</span>
          <div className="bar-container">
            <div className="bar-fill" style={{ width: `${context.financial_health_score}%` }}></div>
          </div>
        </div>
        <div className="score-bar">
          <span className="label">Quality Score</span>
          <div className="bar-container">
            <div className="bar-fill" style={{ width: `${context.quality_score}%` }}></div>
          </div>
        </div>
      </div>
    </section>
  );
};

// ════════════════════════════════════════════════════════════════════════════════
// Valuation Section
// ════════════════════════════════════════════════════════════════════════════════

const ValuationSection: React.FC<{ context?: ValuationContext }> = ({ context }) => {
  if (!context) {
    return (
      <section className="context-section">
        <h2>Valuation Context</h2>
        <div className="placeholder">No valuation data available</div>
      </section>
    );
  }

  return (
    <section className="context-section">
      <h2>Valuation Context</h2>

      <div className="metrics-grid">
        <div className="metric-card">
          <span className="metric-label">Valuation Status</span>
          <span className={`metric-value status-${context.status.toLowerCase()}`}>
            {context.status}
          </span>
        </div>

        <div className="metric-card">
          <span className="metric-label">P/E Relative</span>
          <span className="metric-value">{context.pe_relative}</span>
        </div>

        <div className="metric-card">
          <span className="metric-label">Valuation Score</span>
          <span className="metric-value">{context.valuation_score.toFixed(0)}/100</span>
        </div>

        <div className="metric-card">
          <span className="metric-label">Margin of Safety</span>
          <span className={context.margin_of_safety > 0 ? 'metric-value positive' : 'metric-value negative'}>
            {context.margin_of_safety > 0 ? '+' : ''}{context.margin_of_safety.toFixed(1)}%
          </span>
        </div>

        <div className="metric-card">
          <span className="metric-label">Upside Potential</span>
          <span className="metric-value positive">{context.upside_potential.toFixed(1)}%</span>
        </div>
      </div>

      <div className="mos-section">
        <h3>Margin of Safety Analysis</h3>
        <div className="mos-bar">
          <div
            className="mos-fill"
            style={{
              width: `${Math.max(0, Math.min(100, context.margin_of_safety))}%`,
              backgroundColor: context.margin_of_safety > 15 ? '#22c55e' : context.margin_of_safety > 0 ? '#eab308' : '#ef4444',
            }}
          ></div>
        </div>
        <div className="mos-label">
          {context.margin_of_safety > 20 ? '✓ Excellent safety margin' : context.margin_of_safety > 10 ? '≈ Good safety margin' : '⚠ Limited safety margin'}
        </div>
      </div>
    </section>
  );
};

// ════════════════════════════════════════════════════════════════════════════════
// Events Section
// ════════════════════════════════════════════════════════════════════════════════

const EventsSection: React.FC<{ calendar?: EventCalendar }> = ({ calendar }) => {
  if (!calendar) {
    return (
      <section className="context-section">
        <h2>Events Calendar</h2>
        <div className="placeholder">No event data available</div>
      </section>
    );
  }

  return (
    <section className="context-section">
      <h2>Events Calendar</h2>

      <div className="metrics-grid">
        <div className="metric-card">
          <span className="metric-label">Days to Nearest Event</span>
          <span className="metric-value">{calendar.days_to_nearest}</span>
        </div>

        <div className="metric-card">
          <span className="metric-label">Event Risk Score</span>
          <span
            className="metric-value"
            style={{
              color:
                calendar.event_risk_score > 70 ? '#ef4444' : calendar.event_risk_score > 40 ? '#eab308' : '#22c55e',
            }}
          >
            {calendar.event_risk_score.toFixed(0)}/100
          </span>
        </div>

        <div className="metric-card">
          <span className="metric-label">Entry Recommendation</span>
          <span className={`metric-value rec-${calendar.entry_recommendation.toLowerCase()}`}>
            {calendar.entry_recommendation}
          </span>
        </div>
      </div>

      {calendar.nearest_event && (
        <div className="event-card">
          <h3>Nearest Event</h3>
          <div className="event-details">
            <div className="event-type">{calendar.nearest_event.event_type}</div>
            <div className="event-date">📅 {calendar.nearest_event.event_date}</div>
            <div className="event-importance">
              Importance: {calendar.nearest_event.importance}/10
            </div>
          </div>
        </div>
      )}
    </section>
  );
};

// ════════════════════════════════════════════════════════════════════════════════
// Summary Section
// ════════════════════════════════════════════════════════════════════════════════

const SummarySection: React.FC<{
  tradePlan: TradePlan;
  confidence: number;
}> = ({ tradePlan, confidence }) => {
  return (
    <section className="summary-section">
      <h2>Trade Decision Summary</h2>

      <div className="summary-card">
        <h3>🎯 Entry Decision Quality</h3>
        <div className="confidence-display">
          <div className="confidence-circle" style={{ fontSize: `${Math.min(confidence, 50)}px` }}>
            {confidence.toFixed(0)}%
          </div>
          <div className="confidence-description">
            {confidence > 75
              ? '✓ Strong conviction — multi-layer support'
              : confidence > 60
              ? '≈ Moderate conviction — several confirmations'
              : confidence > 40
              ? '⚠ Caution — limited confirmations'
              : '✗ Weak conviction — insufficient data'}
          </div>
        </div>
      </div>

      <div className="checklist-grid">
        <div className="checklist-card">
          <h3>✓ Confirmations</h3>
          <ul>
            {tradePlan.technical_context && <li>✓ Technical structure (support/resistance)</li>}
            {tradePlan.market_context?.regime && <li>✓ Bullish market regime</li>}
            {tradePlan.fundamental_context?.momentum && <li>✓ Financial momentum</li>}
            {tradePlan.valuation_context?.margin_of_safety && tradePlan.valuation_context?.margin_of_safety > 0 && (
              <li>✓ Valuation support (undervalued)</li>
            )}
            {tradePlan.event_calendar?.entry_recommendation === 'FAVORABLE' && (
              <li>✓ Event timing favorable</li>
            )}
          </ul>
        </div>

        <div className="checklist-card">
          <h3>⚠️ Risk Factors</h3>
          <ul>
            {tradePlan.market_context?.regime?.includes('BEARISH') && (
              <li>⚠ Bearish market regime</li>
            )}
            {tradePlan.valuation_context?.margin_of_safety && tradePlan.valuation_context?.margin_of_safety < 0 && (
              <li>⚠ Overvalued entry</li>
            )}
            {tradePlan.event_calendar?.event_risk_score && tradePlan.event_calendar?.event_risk_score > 70 && (
              <li>⚠ High event risk</li>
            )}
            {tradePlan.calculator_output?.allocation_pct && tradePlan.calculator_output?.allocation_pct > 10 && (
              <li>⚠ Large position size</li>
            )}
          </ul>
        </div>
      </div>

      <div className="exit-plan">
        <h3>Exit Plan</h3>
        <div className="exit-levels">
          <div className="exit-item stop">
            <span className="label">Stop Loss</span>
            <span className="price">${tradePlan.stop_price.toFixed(2)}</span>
            <span className="risk">
              {tradePlan.entry_price > 0 && (
                <>
                  Risk: {((tradePlan.entry_price - tradePlan.stop_price) / tradePlan.entry_price * 100).toFixed(1)}%
                </>
              )}
            </span>
          </div>

          {tradePlan.target_prices.map((target, idx) => (
            <div key={idx} className="exit-item target">
              <span className="label">Target {idx + 1}</span>
              <span className="price">${target.toFixed(2)}</span>
              <span className="profit">
                {tradePlan.entry_price > 0 && (
                  <>
                    Profit: {((target - tradePlan.entry_price) / tradePlan.entry_price * 100).toFixed(1)}%
                  </>
                )}
              </span>
            </div>
          ))}
        </div>
      </div>

      <div className="action-buttons">
        <button className="btn btn-primary">Save Trade Plan</button>
        <button className="btn btn-secondary">Export PDF</button>
        <button className="btn btn-secondary">Mark as Ready</button>
      </div>
    </section>
  );
};

export default TradePlanDashboard;
