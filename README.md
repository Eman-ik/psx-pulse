# PSX Fertilizer Research Platform (pilot)

A single-sector (PSX Fertilizer) pilot of a PSX investment research platform: fundamentals,
market data, macro/geopolitical risk context and a compliance-gated AI signal layer. See
`docs/` in `backend/` for the compliance gate templates this project is built around.

**Compliance gate**: no PSX data license exists yet. `PUBLIC_LAUNCH_ENABLED`,
`PUBLIC_SIGNALS_ENABLED` and `COMMERCIAL_DATA_ENABLED` default to `false` and must stay that
way until `backend/docs/rights_matrix.template.md` is actually filled in and reviewed.

## Stack

- Frontend: Next.js 16 (App Router) + TypeScript + Tailwind v4 + Recharts
- Backend: FastAPI + SQLAlchemy 2.0 + Alembic, Postgres
- Local dev: Docker Compose (Postgres + backend + frontend), or run each service natively

## Running locally

### Option A — Docker Compose (requires Docker Desktop running)

```bash
cp backend/.env.example backend/.env
docker compose up --build
```

Frontend: http://localhost:3000 · Backend: http://localhost:8000/health

### Option B — native (what this repo was verified against)

Backend:
```bash
cd backend
python -m venv .venv
.venv/Scripts/activate   # or .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
cp .env.example .env     # point DATABASE_URL at your own Postgres
alembic upgrade head
uvicorn app.main:app --reload
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

## Repo layout

```
frontend/    Next.js app — dashboard UI (sample data for now, see src/lib/mock-data.ts)
backend/     FastAPI app, SQLAlchemy models, Alembic migrations, ingestion/etl/scoring modules
backend/docs/  Compliance gate templates (rights matrix, source registry, editorial SOP, disclaimer)
```

## Status

Milestone 1 (foundation) complete: schema, API skeleton, feature-flag gate, dashboard UI on
sample data. See the plan this was built from for Milestones 2-8 (real data ingestion,
ratio engine, full company research pages, market data, screener, AI signal layer).


Build a PSX-native fork/derivative of TradingAgents, using TradingAgents as the orchestration skeleton but replacing the market-specific intelligence layer with your own Pakistan Stock Exchange infrastructure.

The target should not be:

“TradingAgents that happens to accept PSX tickers.”

It should be:

“TradingAgents rebuilt around the institutional realities of Pakistan’s capital market.”

The current TradingAgents architecture is well suited to this because it already separates analysts, bull/bear research, trader, risk debate, and portfolio management through LangGraph. It also now has structured outputs, checkpointing, persistent decision logs, multiple LLM providers, Docker support and data-provider fallbacks.

PSX TradingAgents

I would build it conceptually like this:

                     PSX TRADINGAGENTS

                            │
                            ▼
                    User selects FFC
                            │
                            ▼
                  PSX DATA ORCHESTRATOR
                            │
       ┌────────────────────┼────────────────────┐
       │                    │                    │
       ▼                    ▼                    ▼
   COMPANY DATA          MARKET DATA         EVENT DATA
       │                    │                    │
 Financials              OHLCV               PSX notices
 Annual reports          Volume              Results
 Quarterly reports       Indicators          Dividends
 Ownership               Liquidity            Rights
 Management              Factors              Board meetings
 Subsidiaries            ML predictions       Material info
       │                    │                    │
       └────────────────────┼────────────────────┘
                            │
                            ▼
                    ANALYST AGENTS
                            │
 ┌──────────┬────────┬─────────┬─────────┬────────────┐
 ▼          ▼        ▼         ▼         ▼            ▼
Fund.     Quant    Tech.      News     Macro      Governance
Analyst   Analyst  Analyst    Analyst   Analyst     Analyst
 └──────────┴────────┴─────────┴─────────┴────────────┘
                            │
                            ▼
                    Bull ↔ Bear Debate
                            │
                            ▼
                     Research Manager
                            │
                            ▼
                       Trader Agent
                            │
                            ▼
          Aggressive ↔ Neutral ↔ Conservative
                            │
                            ▼
                     Portfolio Manager
                            │
                            ▼
                 FINAL PSX INVESTMENT VIEW
What we keep from TradingAgents

A surprisingly large amount of its engineering can remain.

TradingAgents component	PSX version
LangGraph orchestration	Keep
Analyst → Research → Trader → Risk workflow	Keep
Bull/Bear debate	Keep
Aggressive/Neutral/Conservative risk debate	Keep
Portfolio Manager	Keep
Agent memory	Keep and expand
Checkpointing	Keep
Structured outputs	Keep
OpenAI / Claude / Gemini etc. abstraction	Keep
CLI	Keep for development
Docker	Keep
Report generation	Keep and redesign
Backtesting framework	Keep concept, heavily modify
yfinance / Alpha Vantage data layer	Replace
Reddit / StockTwits emphasis	Replace
US macro assumptions	Replace
US company fundamentals pipeline	Replace

TradingAgents currently depends on LangGraph and LangChain, and also includes Backtrader, pandas, stockstats, yfinance, Redis and checkpointing infrastructure.

So we aren't starting from zero.

The biggest change: dataflows

This is where your actual PSX product begins.

Original TradingAgents effectively thinks:

Agent
 ↓
TradingAgents tool
 ↓
Alpha Vantage / Yahoo / FRED / Reddit / StockTwits

Your clone should think:

Agent
 ↓
PSX Tool Registry
 ↓
PSX Intelligence Database
 ↓
Verified source

For example:

get_company_financials("FFC", as_of="2026-06-30")

get_psx_announcements("FFC", as_of="2026-08-17")

get_price_history("FFC", start, end)

get_shareholding_pattern("FFC")

get_subsidiaries("FFC")

get_company_documents("FFC")

get_sector_metrics("FERTILIZER")

get_macro_snapshot("2026-08-17")

get_technical_indicators("FFC")

get_quant_forecast("FFC", horizon=5)

The agents should never need to know where this information came from.

Your data gateway handles that.

That separation is extremely important.

I would actually create a new package

Don't call everything tradingagents.

Something like:

psx-tradingagents/
│
├── psxagents/
│
│   ├── agents/
│   │   ├── analysts/
│   │   ├── researchers/
│   │   ├── trader/
│   │   ├── risk/
│   │   └── managers/
│   │
│   ├── graph/
│   │   ├── setup.py
│   │   ├── routing.py
│   │   ├── propagation.py
│   │   └── state.py
│   │
│   ├── tools/
│   │   ├── financials.py
│   │   ├── market.py
│   │   ├── announcements.py
│   │   ├── documents.py
│   │   ├── macro.py
│   │   ├── technical.py
│   │   ├── quant.py
│   │   └── valuation.py
│   │
│   ├── dataflows/
│   │   └── psx/
│   │
│   ├── schemas/
│   ├── memory/
│   ├── backtesting/
│   └── api/
│
├── tests/
├── docker/
├── pyproject.toml
└── README.md

It would remain recognizably descended from TradingAgents, but your application architecture would be clean rather than becoming a pile of patches.

And I would expand the analyst team

The original framework has four main analyst functions: fundamentals, sentiment, news and technical analysis.

For PSX, that's not enough.

Your first production version should probably have:

Fundamental Analyst

Financial health, revenue, earnings, margins, cash flow, working capital, leverage, ROE/ROIC, capital expenditure.

Business Analyst

What the company actually does, value chain, customers, suppliers, pricing power, production capacity and utilization.

Valuation Analyst

P/E, EV/EBITDA, P/B, dividend yield, DCF, reverse DCF, historical bands and peers.

Governance Analyst

Sponsors, directors, ownership, related-party transactions, auditor issues, capital allocation and governance concerns.

Technical Analyst

RSI, MACD, moving averages, ATR, Bollinger Bands, ADX, support/resistance, volume and trend regime.

Quant Analyst

This is where your real data-science work belongs:

Fama-French
CAPM
APT
factor sensitivities
5-day prediction
volatility model
momentum
market regime
probability distributions

News Analyst

Company, sector and Pakistan news.

PSX Announcement Analyst

Separate from news.

It understands:

material information
board meeting notices
financial results
dividends
bonus shares
rights
director transactions
AGMs / EGMs
credit ratings
plant shutdowns
production changes
acquisitions

Pakistan Macro Analyst

Understands things that actually move Pakistani equities:

SBP policy rate
PKR/USD
inflation
KIBOR
T-bill yields
PIB yields
IMF
fiscal policy
taxation
energy tariffs
oil
LNG
gas
current account
foreign reserves
government borrowing

Liquidity Analyst

Important for PSX.

A stock can theoretically look attractive while being almost impossible to enter/exit at scale.

Then the Bull/Bear system becomes much more valuable

Suppose your system analyzes LUCK.

The analyst layer might produce:

Fundamental:       82/100
Business quality:  85/100
Governance:        77/100
Valuation:         64/100
Technical:         71/100
Quant:             68/100
Sentiment:         73/100
Macro:             58/100

But you DON'T calculate:

average = BUY

Instead:

Bull Researcher

Builds the strongest possible investment thesis.

Bear Researcher

Finds everything that could make the investment thesis wrong.

Then they debate.

That debate mechanism is one of the core features of TradingAgents' design.

Then your Research Manager performs synthesis

Its question isn't:

Is this a good company?

It is:

Is this a good investment at today's price?

That distinction matters enormously.

A fantastic company at 40× earnings can be a terrible investment.

A mediocre cyclical business trading below liquidation value might be attractive.

Then the Trader Agent becomes PSX-specific

Instead of merely producing:

BUY

I want your version to generate:

FFC

Rating
BUY

Confidence
78%

Investment horizon
6–12 months

Fair value
Rs XXX

Current valuation
Rs XXX

Expected upside
+22%

Bear-case downside
-12%

Risk/reward
1.83×

And then:

Investment thesis
Catalysts
Risks
Thesis breakers
Upcoming events
Technical setup
Quant signal
Macro sensitivity
Valuation
Evidence quality
Keep TradingAgents' five-tier recommendation scale

Interestingly, the project itself already moved to:

BUY
OVERWEIGHT
HOLD
UNDERWEIGHT
SELL

for its Portfolio Manager.

I would retain this.

It's substantially better than forcing everything into BUY/HOLD/SELL.

But add TWO different outputs

This is extremely important for your platform.

Don't confuse:

Investment recommendation

with:

Trading signal

For example:

ENGROH

INVESTMENT VIEW
BUY
12-month horizon
Confidence: 82%

SHORT-TERM TRADING VIEW
HOLD
5-day horizon
Confidence: 61%

Why?

Because fundamentals might say:

Undervalued.

while your technical/quant model says:

Stock likely declines over the next five sessions.

Both can simultaneously be correct.

Your platform should expose that distinction.

Your 5-day model becomes a tool

Not an LLM.

Something like:

Quant Forecast

P(+ return next 5 sessions)       68%
Expected 5D return               +2.4%
Expected downside VaR            -3.1%
Expected volatility               2.8%
Trend regime                     bullish
Model confidence                 medium-high

Then the Quant Analyst interprets that.

That's how your data science work and agentic AI work together.

PSX sector intelligence should also be built in

This is where a generic TradingAgents clone would still fail.

Different PSX sectors require different information.

For fertilizer:

gas price
urea price
DAP price
inventory
offtake
gas allocation
imports
subsidies

Banks:

policy rate
NIM
ADR
IDR
infection ratio
CAR
CASA
deposit growth
government securities exposure

E&P:

oil
gas
production
well flows
reserves
circular debt
receivables
PKR/USD

Cement:

dispatches
coal
power
capacity
utilization
north/south pricing
exports

Automobiles:

sales
localization
PKR
interest rates
CKD imports
inventory
PAMA data

So your analyst agents should dynamically load a sector-specific analytical toolkit.

That could become one of your strongest differentiators.

And your database has to be point-in-time

This is non-negotiable.

TradingAgents itself has recently had to fix historical look-ahead-data problems in its backtesting/data fetchers.

Every piece of your PSX data needs at minimum:

period_end
publication_date
available_from
source
retrieved_at
revision_number

Suppose FFC released Q2 results on August 15.

A backtest running:

2026-08-01

must not see them.

Otherwise your AI magically knows the future.

That destroys your backtest.

The final architecture I want for you
                         PSX INTELLIGENCE
                               │
                               │
                     ┌─────────▼─────────┐
                     │ PSX DATA PLATFORM │
                     └─────────┬─────────┘
                               │
        ┌──────────────────────┼───────────────────────┐
        │                      │                       │
 FINANCIAL DATA          MARKET DATA              DOCUMENTS
        │                      │                       │
        └──────────────────────┼───────────────────────┘
                               │
                         PSX TOOL LAYER
                               │
                               ▼
                     PSX TRADINGAGENTS
                               │
               ┌───────────────┼───────────────┐
               │               │               │
             LLM             QUANT           RULES
            AGENTS           MODELS          ENGINE
               │               │               │
               └───────────────┼───────────────┘
                               │
                     INVESTMENT COMMITTEE
                               │
                               ▼
                        FINAL DECISION
                               │
          ┌────────────────────┼────────────────────┐
          ▼                    ▼                    ▼
     Long-term view       Trading signal       Risk view
                               │
                               ▼
                           BACKTEST
                               │
                               ▼
                         PERFORMANCE DB
                               │
                               ▼
                        AGENT REFLECTION

That's the product.

I would build it in six stages
Phase	Build
0	Fork TradingAgents and get original version running
1	Remove reliance on US-market data and create PSX data interfaces
2	Make Fundamental + Technical + News agents work for 10 PSX stocks
3	Add Governance, Valuation, Macro, Announcement and Quant agents
4	Build Bull/Bear + Risk + Portfolio Manager PSX prompts
5	Add point-in-time backtesting, decision tracking and agent scoring
6	Connect it to your PSX Intelligence website

And I would not start with all ~500 PSX securities.

Start with perhaps:

FFC
EFERT
LUCK
MARI
OGDC
PPL
HBL
UBL
MCB
SYS

Get those ten working extremely well.

Then expand.

Most importantly: don't rewrite TradingAgents first

The first practical move should be:

fork the current TradingAgents repository and map every component into three categories: KEEP, MODIFY, REPLACE.

TradingAgents is Apache-2.0 licensed, so the upstream project is explicitly open-source and structured for modification, subject to its license requirements.

Then we can turn the existing repository into:

PSXTradingAgents v0.1

without destroying the architecture that already works.

And because this is already a fairly substantial software engineering project, I suggest our next step be very concrete: I can go through the actual TradingAgents repository folder by folder and file by file and give you a migration map such as:

tradingagents/agents/analysts/fundamentals_analyst.py
→ MODIFY
→ exactly what changes

tradingagents/dataflows/y_finance.py
→ REPLACE
→ psx_market_data.py

tradingagents/dataflows/alpha_vantage.py
→ REMOVE/optional

tradingagents/graph/trading_graph.py
→ KEEP
→ add PSX agents here

That would effectively become the technical blueprint for building your PSX clone from the actual codebase, rather than just discussing the concept.