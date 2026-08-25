"use client";

import React, { useState, useMemo } from 'react';
import {
  BacktestParams,
  BacktestResult,
  BacktestStrategyType
} from './types';
import {
  TickerList,
  runBacktestSimulation
} from './data/backtestDataAndEngine';
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
  Area,
  ReferenceLine
} from 'recharts';
import {
  Play,
  RotateCcw,
  TrendingUp,
  TrendingDown,
  Zap,
  Sliders,
  DollarSign,
  Percent,
  ShieldAlert,
  Bot,
  BarChart2,
  ArrowUpRight,
  ArrowDownRight,
  Sparkles,
  CheckCircle2,
  Clock
} from 'lucide-react';

interface StrategyBacktesterProps {
  onAskAgent?: (promptText: string) => void;
}

export const StrategyBacktester: React.FC<StrategyBacktesterProps> = ({ onAskAgent }) => {
  const [params, setParams] = useState<BacktestParams>({
    ticker: 'OGDC',
    strategy: 'sma_crossover',
    initialCapital: 1000000,
    fastPeriod: 20,
    slowPeriod: 50,
    rsiThresholdLow: 30,
    rsiThresholdHigh: 70,
    stopLossPct: 5,
    takeProfitPct: 15,
    timeFrameDays: 250
  });

  const [isSimulating, setIsSimulating] = useState(false);
  const [activeTab, setActiveTab] = useState<'equity' | 'trades' | 'parameters'>('equity');

  const backtestResult: BacktestResult = useMemo(() => {
    return runBacktestSimulation(params);
  }, [params]);

  const selectedTickerInfo = useMemo(() => {
    return TickerList.PSX_TICKERS.find(t => t.ticker === params.ticker) || TickerList.PSX_TICKERS[0];
  }, [params.ticker]);

  const handleRunBacktest = () => {
    setIsSimulating(true);
    setTimeout(() => {
      setIsSimulating(false);
    }, 400);
  };

  const isReturnPositive = backtestResult.totalReturnPct >= 0;
  const isAlphaPositive = backtestResult.totalReturnPct >= backtestResult.benchmarkReturnPct;

  return (
    <div className="bg-[#121214] border border-[#27272a] rounded-lg p-5 space-y-6 font-mono text-xs shadow-sm">

      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#27272a] pb-4">
        <div>
          <div className="flex items-center space-x-2 text-[#3b82f6] text-xs font-bold uppercase tracking-wider mb-1">
            <BarChart2 className="w-4 h-4 text-[#3b82f6]" />
            <span>PSX QUANT STRATEGY BACKTESTER</span>
            <span className="text-[10px] bg-[#3b82f6]/15 text-[#3b82f6] px-2 py-0.5 rounded border border-[#3b82f6]/30">
              Historical Engine v3.6
            </span>
          </div>
          <h2 className="text-xl font-bold text-[#fafafa] font-mono">
            Quantitative Algorithmic Backtesting & Strategy Simulation
          </h2>
          <p className="text-[#a1a1aa] text-xs font-sans mt-0.5">
            Simulate technical indicator trading strategies against historical PSX daily market data to evaluate return alpha, win rate, and max drawdown before live trade execution.
          </p>
        </div>

        <button
          onClick={handleRunBacktest}
          disabled={isSimulating}
          className="px-4 py-2 bg-[#10b981] hover:bg-[#059669] text-white font-mono font-bold text-xs rounded transition-all flex items-center justify-center space-x-2 cursor-pointer shadow-md shrink-0 disabled:opacity-50"
        >
          {isSimulating ? (
            <>
              <RotateCcw className="w-4 h-4 animate-spin" />
              <span>Simulating Strategy...</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4 fill-white" />
              <span>Run Backtest Simulation</span>
            </>
          )}
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 bg-[#18181b] p-4 rounded-lg border border-[#27272a]">

        <div className="space-y-1">
          <label className="text-[10px] font-bold text-[#a1a1aa] uppercase tracking-wider block">
            1. Select PSX Equity Ticker
          </label>
          <select
            value={params.ticker}
            onChange={(e) => setParams({ ...params, ticker: e.target.value })}
            className="w-full bg-[#121214] text-[#fafafa] border border-[#27272a] focus:border-[#3b82f6] rounded px-3 py-2 text-xs font-mono outline-none"
          >
            {TickerList.PSX_TICKERS.map((t) => (
              <option key={t.ticker} value={t.ticker}>
                ${t.ticker} - {t.name} ({t.sector})
              </option>
            ))}
          </select>
        </div>

        <div className="space-y-1">
          <label className="text-[10px] font-bold text-[#a1a1aa] uppercase tracking-wider block">
            2. Algorithmic Strategy
          </label>
          <select
            value={params.strategy}
            onChange={(e) => setParams({ ...params, strategy: e.target.value as BacktestStrategyType })}
            className="w-full bg-[#121214] text-[#fafafa] border border-[#27272a] focus:border-[#3b82f6] rounded px-3 py-2 text-xs font-mono outline-none"
          >
            <option value="sma_crossover">Golden Cross / Death Cross (SMA)</option>
            <option value="rsi_mean_reversion">RSI Mean Reversion (30 / 70)</option>
            <option value="macd_trend">MACD Trend Momentum</option>
            <option value="bollinger_breakout">Bollinger Band Volatility Breakout</option>
            <option value="ai_sentiment_momentum">AI Sentiment + Price Momentum</option>
          </select>
        </div>

        <div className="space-y-1">
          <label className="text-[10px] font-bold text-[#a1a1aa] uppercase tracking-wider block">
            3. Starting Capital (PKR)
          </label>
          <select
            value={params.initialCapital}
            onChange={(e) => setParams({ ...params, initialCapital: Number(e.target.value) })}
            className="w-full bg-[#121214] text-[#fafafa] border border-[#27272a] focus:border-[#3b82f6] rounded px-3 py-2 text-xs font-mono outline-none"
          >
            <option value={500000}>PKR 500,000</option>
            <option value={1000000}>PKR 1,000,000 (1M)</option>
            <option value={5000000}>PKR 5,000,000 (5M)</option>
            <option value={10000000}>PKR 10,000,000 (10M)</option>
          </select>
        </div>

        <div className="space-y-1">
          <label className="text-[10px] font-bold text-[#a1a1aa] uppercase tracking-wider block">
            4. Historical Time Horizon
          </label>
          <select
            value={params.timeFrameDays}
            onChange={(e) => setParams({ ...params, timeFrameDays: Number(e.target.value) })}
            className="w-full bg-[#121214] text-[#fafafa] border border-[#27272a] focus:border-[#3b82f6] rounded px-3 py-2 text-xs font-mono outline-none"
          >
            <option value={125}>6 Months (~125 Trading Days)</option>
            <option value={250}>1 Year (~250 Trading Days)</option>
            <option value={500}>2 Years (~500 Trading Days)</option>
          </select>
        </div>

      </div>

      <div className="bg-[#18181b] p-3.5 rounded-lg border border-[#27272a] space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-[10px] font-bold text-[#3b82f6] uppercase tracking-wider flex items-center gap-1.5">
            <Sliders className="w-3.5 h-3.5 text-[#3b82f6]" />
            FINE-TUNE STRATEGY PARAMETERS & RISK CONTROLS
          </span>
          <span className="text-[10px] text-[#a1a1aa]">Real-Time Re-calculation</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3">
          <div>
            <span className="text-[10px] text-[#a1a1aa] block mb-1">Fast SMA Period</span>
            <input
              type="number"
              min={5}
              max={50}
              value={params.fastPeriod}
              onChange={(e) => setParams({ ...params, fastPeriod: Math.max(5, Number(e.target.value)) })}
              className="w-full bg-[#121214] text-[#fafafa] border border-[#27272a] rounded px-2.5 py-1 text-xs font-mono"
            />
          </div>

          <div>
            <span className="text-[10px] text-[#a1a1aa] block mb-1">Slow SMA Period</span>
            <input
              type="number"
              min={20}
              max={200}
              value={params.slowPeriod}
              onChange={(e) => setParams({ ...params, slowPeriod: Math.max(20, Number(e.target.value)) })}
              className="w-full bg-[#121214] text-[#fafafa] border border-[#27272a] rounded px-2.5 py-1 text-xs font-mono"
            />
          </div>

          <div>
            <span className="text-[10px] text-[#a1a1aa] block mb-1">RSI Oversold Level</span>
            <input
              type="number"
              min={15}
              max={45}
              value={params.rsiThresholdLow}
              onChange={(e) => setParams({ ...params, rsiThresholdLow: Number(e.target.value) })}
              className="w-full bg-[#121214] text-[#fafafa] border border-[#27272a] rounded px-2.5 py-1 text-xs font-mono"
            />
          </div>

          <div>
            <span className="text-[10px] text-[#a1a1aa] block mb-1">RSI Overbought Level</span>
            <input
              type="number"
              min={55}
              max={85}
              value={params.rsiThresholdHigh}
              onChange={(e) => setParams({ ...params, rsiThresholdHigh: Number(e.target.value) })}
              className="w-full bg-[#121214] text-[#fafafa] border border-[#27272a] rounded px-2.5 py-1 text-xs font-mono"
            />
          </div>

          <div>
            <span className="text-[10px] text-[#a1a1aa] block mb-1">Stop Loss Limit %</span>
            <input
              type="number"
              min={0}
              max={25}
              value={params.stopLossPct}
              onChange={(e) => setParams({ ...params, stopLossPct: Number(e.target.value) })}
              className="w-full bg-[#121214] text-[#fafafa] border border-[#27272a] rounded px-2.5 py-1 text-xs font-mono text-[#ef4444]"
            />
          </div>

          <div>
            <span className="text-[10px] text-[#a1a1aa] block mb-1">Take Profit Target %</span>
            <input
              type="number"
              min={0}
              max={100}
              value={params.takeProfitPct}
              onChange={(e) => setParams({ ...params, takeProfitPct: Number(e.target.value) })}
              className="w-full bg-[#121214] text-[#fafafa] border border-[#27272a] rounded px-2.5 py-1 text-xs font-mono text-[#10b981]"
            />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">

        <div className={`p-3.5 rounded-lg border ${
          isReturnPositive ? 'bg-[#10b981]/10 border-[#10b981]/30' : 'bg-[#ef4444]/10 border-[#ef4444]/30'
        }`}>
          <span className="text-[10px] text-[#a1a1aa] block mb-0.5">STRATEGY RETURN</span>
          <div className="flex items-center space-x-1">
            {isReturnPositive ? (
              <ArrowUpRight className="w-4 h-4 text-[#10b981]" />
            ) : (
              <ArrowDownRight className="w-4 h-4 text-[#ef4444]" />
            )}
            <span className={`text-base font-extrabold ${isReturnPositive ? 'text-[#10b981]' : 'text-[#ef4444]'}`}>
              {isReturnPositive ? `+${backtestResult.totalReturnPct}%` : `${backtestResult.totalReturnPct}%`}
            </span>
          </div>
          <span className="text-[9px] text-[#a1a1aa] block mt-1">
            vs Buy & Hold: {backtestResult.benchmarkReturnPct > 0 ? `+${backtestResult.benchmarkReturnPct}%` : `${backtestResult.benchmarkReturnPct}%`}
          </span>
        </div>

        <div className="bg-[#18181b] p-3.5 rounded-lg border border-[#27272a]">
          <span className="text-[10px] text-[#a1a1aa] block mb-0.5">PORTFOLIO VALUE</span>
          <span className="text-base font-extrabold text-[#fafafa]">
            PKR {backtestResult.finalPortfolioValue.toLocaleString()}
          </span>
          <span className="text-[9px] text-[#3b82f6] block mt-1 font-bold">
            Alpha: {(backtestResult.totalReturnPct - backtestResult.benchmarkReturnPct).toFixed(2)}%
          </span>
        </div>

        <div className="bg-[#18181b] p-3.5 rounded-lg border border-[#27272a]">
          <span className="text-[10px] text-[#a1a1aa] block mb-0.5">WIN RATE %</span>
          <span className="text-base font-extrabold text-[#10b981]">
            {backtestResult.winRatePct}%
          </span>
          <span className="text-[9px] text-[#a1a1aa] block mt-1">
            {backtestResult.winningTrades} Win / {backtestResult.losingTrades} Loss
          </span>
        </div>

        <div className="bg-[#18181b] p-3.5 rounded-lg border border-[#27272a]">
          <span className="text-[10px] text-[#a1a1aa] block mb-0.5">SHARPE RATIO</span>
          <span className={`text-base font-extrabold ${backtestResult.sharpeRatio >= 1.0 ? 'text-[#10b981]' : 'text-[#fafafa]'}`}>
            {backtestResult.sharpeRatio}
          </span>
          <span className="text-[9px] text-[#a1a1aa] block mt-1">
            {backtestResult.sharpeRatio >= 1.0 ? 'Risk-Adjusted Outperformer' : 'Moderate Volatility'}
          </span>
        </div>

        <div className="bg-[#18181b] p-3.5 rounded-lg border border-[#27272a]">
          <span className="text-[10px] text-[#a1a1aa] block mb-0.5">MAX DRAWDOWN</span>
          <span className="text-base font-extrabold text-[#ef4444]">
            -{backtestResult.maxDrawdownPct}%
          </span>
          <span className="text-[9px] text-[#a1a1aa] block mt-1">
            Peak-to-Trough Decline
          </span>
        </div>

        <div className="bg-[#18181b] p-3.5 rounded-lg border border-[#27272a]">
          <span className="text-[10px] text-[#a1a1aa] block mb-0.5">TRADES EXECUTED</span>
          <span className="text-base font-extrabold text-[#3b82f6]">
            {backtestResult.totalTrades} Trades
          </span>
          <span className="text-[9px] text-[#a1a1aa] block mt-1">
            Avg PnL: PKR {backtestResult.avgPnlPerTrade.toLocaleString()}
          </span>
        </div>

      </div>

      <div className="space-y-4">

        <div className="flex items-center justify-between border-b border-[#27272a] pb-2">
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setActiveTab('equity')}
              className={`px-3 py-1.5 rounded-md text-xs font-bold transition-all ${
                activeTab === 'equity'
                  ? 'bg-[#3b82f6] text-white shadow-xs'
                  : 'bg-[#18181b] text-[#a1a1aa] hover:text-[#fafafa] border border-[#27272a]'
              }`}
            >
              Equity Curve & Price Chart
            </button>
            <button
              onClick={() => setActiveTab('trades')}
              className={`px-3 py-1.5 rounded-md text-xs font-bold transition-all flex items-center gap-1.5 ${
                activeTab === 'trades'
                  ? 'bg-[#3b82f6] text-white shadow-xs'
                  : 'bg-[#18181b] text-[#a1a1aa] hover:text-[#fafafa] border border-[#27272a]'
              }`}
            >
              <span>Trade Execution Log</span>
              <span className="bg-black/30 px-1.5 py-0.2 rounded text-[10px]">
                {backtestResult.tradeLogs.length}
              </span>
            </button>
          </div>

          <button
            onClick={() => {
              if (onAskAgent) {
                onAskAgent(`QuantAgent, analyze the backtest results for $${params.ticker} using ${backtestResult.strategyName}. Total return was ${backtestResult.totalReturnPct}% with a win rate of ${backtestResult.winRatePct}% and max drawdown of -${backtestResult.maxDrawdownPct}%. How can I optimize the parameters (SMA lengths, stop-loss, take-profit) to improve risk-adjusted Sharpe ratio?`);
              }
            }}
            className="px-3 py-1.5 bg-[#10b981]/15 hover:bg-[#10b981]/25 text-[#10b981] border border-[#10b981]/40 rounded font-bold text-xs flex items-center space-x-1.5 transition-all cursor-pointer"
          >
            <Bot className="w-4 h-4" />
            <span>Ask QuantAgent to Optimize Strategy</span>
          </button>
        </div>

        {activeTab === 'equity' && (
          <div className="bg-[#18181b] border border-[#27272a] rounded-lg p-4 space-y-3">
            <div className="flex items-center justify-between text-xs">
              <span className="font-bold text-[#fafafa] flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-[#10b981]" />
                PORTFOLIO EQUITY CURVE (${params.ticker}) VS BUY & HOLD BENCHMARK
              </span>
              <span className="text-[10px] text-[#a1a1aa]">
                Initial: PKR {params.initialCapital.toLocaleString()}
              </span>
            </div>

            <div className="h-[340px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={backtestResult.equityCurve}>
                  <defs>
                    <linearGradient id="strategyGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={isReturnPositive ? '#10b981' : '#ef4444'} stopOpacity={0.3} />
                      <stop offset="95%" stopColor={isReturnPositive ? '#10b981' : '#ef4444'} stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                  <XAxis dataKey="date" stroke="#a1a1aa" tick={{ fontSize: 10, fill: '#a1a1aa' }} />
                  <YAxis
                    stroke="#a1a1aa"
                    tick={{ fontSize: 10, fill: '#a1a1aa' }}
                    tickFormatter={(val) => `PKR ${(val / 1000).toFixed(0)}k`}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#121214',
                      borderColor: '#27272a',
                      borderRadius: '8px',
                      color: '#fafafa',
                      fontSize: '11px'
                    }}
                    formatter={(val, name) => [
                      `PKR ${Number(val).toLocaleString()}`,
                      name === 'strategyValue' ? 'Strategy Portfolio' : 'Buy & Hold Benchmark'
                    ]}
                  />
                  <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                  <Area
                    type="monotone"
                    dataKey="strategyValue"
                    name="Strategy Algorithmic Portfolio"
                    stroke={isReturnPositive ? '#10b981' : '#ef4444'}
                    fill="url(#strategyGrad)"
                    strokeWidth={2.5}
                  />
                  <Line
                    type="monotone"
                    dataKey="benchmarkValue"
                    name="Buy & Hold Benchmark"
                    stroke="#a1a1aa"
                    strokeWidth={1.8}
                    strokeDasharray="4 4"
                    dot={false}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {activeTab === 'trades' && (
          <div className="bg-[#18181b] border border-[#27272a] rounded-lg p-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="font-bold text-[#fafafa] text-xs flex items-center gap-2">
                <Clock className="w-4 h-4 text-[#3b82f6]" />
                SIMULATED HISTORICAL TRADE EXECUTION AUDIT LOG
              </span>
              <span className="text-[10px] text-[#a1a1aa]">
                {backtestResult.tradeLogs.length} Completed Trades
              </span>
            </div>

            {backtestResult.tradeLogs.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse font-mono text-[11px]">
                  <thead>
                    <tr className="border-b border-[#27272a] bg-[#121214] text-[#a1a1aa] uppercase text-[9px] tracking-wider">
                      <th className="p-2.5">Trade ID</th>
                      <th className="p-2.5">Entry Date</th>
                      <th className="p-2.5">Exit Date</th>
                      <th className="p-2.5">Entry Price</th>
                      <th className="p-2.5">Exit Price</th>
                      <th className="p-2.5">Shares</th>
                      <th className="p-2.5">PnL (PKR)</th>
                      <th className="p-2.5">Return %</th>
                      <th className="p-2.5">Exit Reason</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#27272a] text-[#fafafa]">
                    {backtestResult.tradeLogs.map((trade) => {
                      const isWin = trade.pnlPkr >= 0;
                      return (
                        <tr key={trade.id} className="hover:bg-[#27272a]/50 transition-all">
                          <td className="p-2.5 font-bold text-[#3b82f6]">{trade.id}</td>
                          <td className="p-2.5">{trade.entryDate}</td>
                          <td className="p-2.5">{trade.exitDate}</td>
                          <td className="p-2.5">PKR {trade.entryPrice.toFixed(2)}</td>
                          <td className="p-2.5">PKR {trade.exitPrice.toFixed(2)}</td>
                          <td className="p-2.5">{trade.shares.toLocaleString()}</td>
                          <td className={`p-2.5 font-bold ${isWin ? 'text-[#10b981]' : 'text-[#ef4444]'}`}>
                            {isWin ? `+PKR ${trade.pnlPkr.toLocaleString()}` : `-PKR ${Math.abs(trade.pnlPkr).toLocaleString()}`}
                          </td>
                          <td className="p-2.5 font-bold">
                            <span className={`px-2 py-0.5 rounded text-[10px] ${
                              isWin ? 'bg-[#10b981]/15 text-[#10b981]' : 'bg-[#ef4444]/15 text-[#ef4444]'
                            }`}>
                              {isWin ? `+${trade.returnPct}%` : `${trade.returnPct}%`}
                            </span>
                          </td>
                          <td className="p-2.5 text-[#a1a1aa] text-[10px]">{trade.exitReason}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="p-8 text-center text-[#a1a1aa]">
                No trade signals triggered under current parameter thresholds. Try adjusting Moving Average periods or RSI limits.
              </div>
            )}
          </div>
        )}

      </div>

    </div>
  );
};
