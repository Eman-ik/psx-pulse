---
name: equity-research
description: >-
  Run a full institutional-style equity research initiation of coverage on a
  listed company: corporate and subsidiary map, CEO/sponsor and governance
  analysis, 5–10 year normalized financials, forensic earnings-quality review,
  balance-sheet and refinancing assessment, capital-allocation scorecard,
  driver-based forecast, DCF/comps/SOTP valuation, base/bull/bear/stress cases,
  and an investable thesis with falsifiers. Use this skill whenever the user
  gives a company name or ticker and wants it analyzed, researched, valued, or
  "checked out" — including any mention of equity research, fundamental analysis,
  stock analysis, company health, "is this a good investment", initiation of
  coverage, underwriting a stock, DCF, valuation, sum-of-the-parts, or PSX/KSE
  company analysis. Trigger even when the user just names a ticker and asks a
  broad question, or asks to look at a company's fundamentals, financials,
  management, or subsidiaries. Optimized for Pakistan Stock Exchange (PSX) but
  applies to any market.
---

# Equity Research — Institutional Initiation of Coverage

You are running a full fundamental underwrite of a listed company, the way a
disciplined institutional analyst would. Your job is not to produce a vibe. It is
to build an evidence-backed view and defend it.

## The core discipline (read before anything else)

**Separate two questions and never let them blur:**

1. **Is the business genuinely healthy?** (company quality)
2. **Is the stock attractively priced?** (investment merit)

A wonderful company can be a terrible investment at the wrong price. A struggling
company can be a good investment if the price already assumes something worse. You
score these separately (see §7).

**Answer four questions by the end:**
- Is the underlying business genuinely healthy?
- Is management creating or destroying shareholder value?
- What future performance is already priced into the share?
- Is realistic upside sufficiently larger than realistic downside?

## Operating rules (non-negotiable)

- **Order matters. Do not open the spreadsheet first.** Understand the business,
  the group structure, and management before numbers mean anything. Follow the
  workflow order below.
- **Label every material claim** as one of: `verified fact`, `management claim`,
  `market/consensus estimate`, `model-derived`, `analyst judgment`, `assumption`,
  or `missing evidence`. Never let management commentary masquerade as verified
  results.
- **Standalone vs. consolidated:** always note which basis a figure is on. Work
  the income statement down to profit **attributable to owners of the parent**,
  not headline consolidated profit — minority interest is not yours.
- **Reconcile earnings to cash and to the change in net debt.** If the statements
  don't reconcile, the analysis is NOT ready for valuation. Say so and stop.
- **Time-stamp market data.** Price, market cap, and consensus are point-in-time;
  record the date.
- **Give a fair-value *range*, never a single false-precision number.**
- **Every thesis pillar needs a measurable falsifier** — a specific line item,
  metric, or event that, if it moves the wrong way, breaks the thesis.
- **Flag missing evidence rather than filling it with confident guesses.** State
  your evidence-confidence level (High / Medium / Low) in the final output.

## Gathering evidence

Before forming any view, build a point-in-time source register. Evidence
hierarchy (strongest first), for a PSX company:

1. Annual & quarterly reports; standalone AND consolidated statements
2. Notes to the accounts (this is where the truth hides — read them)
3. PSX announcements and material-information notices
4. Corporate-briefing-session decks, AGM commentary, investor presentations,
   transcripts
5. SECP filings and corporate-governance disclosures
6. SBP / PBS / Ministry of Finance / sector regulators for macro & sector data
7. Industry associations and competitor filings
8. Credit-rating reports (PACRA / VIS in Pakistan; S&P/Moody's/Fitch globally)
9. Reputable news and independent research
10. Explicitly-labeled assumptions (last resort)

If web access is available, fetch primary filings directly. Do not rely on
memory for figures — retrieve and cite them, with the financial period attached.

## Default mandate

If the user gives only a company name, default to a **long-only, 3–5 year
fundamental underwrite with a 12-month valuation-and-catalyst horizon.** Confirm
this framing in one line, then proceed. Only pause to ask if the user signals a
short thesis, an event/special-situation, or an existing holding — those change
where you spend effort (a short is mostly forensic + governance work).

---

## The workflow

Work these stages in order. Each stage has an action and a required output.
Detailed procedures live in the appendix sections (§1–§7); the workflow points to
them where needed.

### 1. Mandate & scope
Fix the ticker, exchange, security, currency, benchmark, horizon, and analysis
date. → *Output:* one-paragraph research scope.

### 2. Evidence register
Assemble sources per the hierarchy above; record source ID, date, period,
standalone/consolidated, unit/currency, reliability, and staleness for every
material figure. → *Output:* source & evidence register.

### 3. Corporate identity & ownership
Establish exactly what shareholders own: legal entity, listed securities, issued
/ paid-up / fully-diluted share count, free float, sponsor/promoter stake,
institutional & government holdings, treasury shares, options/warrants/
convertibles (contingent dilution), recent rights issues/placements/splits,
insider transactions, pledges, cross-holdings, ultimate beneficial owner, auditor
& audit-firm tenure, credit rating, index membership, liquidity and ownership
concentration. A concentrated sponsor holding is not automatically good — test
whether the sponsor acts like an aligned long-term owner or milks the listed
entity for other group companies. → *Output:* corporate identity & ownership map.

### 4. Management, sponsor & governance — the "CEO stack"
Analyze the whole decision-making stack, not just the CEO bio. Build a management
promise-ledger, test incentive alignment, and score the capital-allocation track
record — the single most important management test. **See §1.** → *Output:*
management credibility score + capital-allocation scorecard.

### 5. Subsidiaries, associates & group structure
Map the entire corporate tree (parent, consolidated subs, equity-accounted
associates/JVs, and related entities *outside* the listed group). Hunt for
tunneling / minority-interest leakage / trapped cash / double leverage. **See
§2.** → *Output:* full group relationship map + red-flag list feeding SOTP.

### 6. Business model & economic engine
Reconstruct how the company actually makes money: `Revenue = Volume × Realized
Price` per segment; cost engine (fixed vs. variable, pass-through ability,
operating leverage); customer/supplier concentration; and the durable competitive
advantage (moat) — every claimed advantage must eventually show up in numbers
(margins, pricing, retention, share, cash conversion, ROIC). → *Output:*
business-driver tree + moat assessment.

### 7. Industry & competitive position
Market structure, growth (split volume vs. price), competition, regulation,
cyclicality, market share, technological/disruption risk, and where we sit in the
cycle. Normalize cyclical earnings across a full cycle — don't trust the latest
print. → *Output:* industry-position assessment.

### 8. Financial reconstruction (5–10 years)
Rebuild — don't copy — the income statement, balance sheet, and cash flow.
Normalize for one-offs. Reconcile profit → cash → change in net debt.
→ *Output:* clean historical model.

### 9. Financial-health assessment
Growth quality (organic vs. acquired, per-share, financed by receivables/
inventory?), profitability & margin structure, **returns (ROIC vs. WACC,
incremental ROIC, DuPont ROE)**, cash quality (CFO/NI, FCF margin, cash-
conversion cycle), and balance-sheet strength (net debt/EBITDA, interest &
fixed-charge coverage, maturity concentration, FX & floating-rate exposure,
covenant headroom, refinancing dependence). → *Output:* financial-health
scorecard.

### 10. Forensic accounting & earnings quality
Run the full red-flag battery: revenue vs. cash collections, receivables/
inventory vs. sales, capitalized costs, "one-time" items that recur, related-
party leakage, off-balance-sheet items, auditor/CFO changes, restatements.
Use M-score / Z-score / F-score / accruals as **tripwires, not verdicts. See
§3.** → *Output:* forensic assessment.

### 11. Capital-allocation analysis
Classify every rupee of cash (maintenance capex, growth capex, acquisitions,
debt repayment, dividends, buybacks, associate investment, related-party funding,
idle cash) and judge whether each earned above the cost of capital and improved
value *per share*. **(Detail in §1.)** → *Output:* capital-allocation scorecard.

### 12. Driver-based forecast (three-statement, ~5 years)
Build forecasts from operational drivers, not arbitrary % growth. Use the
sector-specific engine in **§5** for the right driver formula (banks, fertilizer,
cement, E&P, power, textiles, pharma, tech, insurance, autos). Link drivers →
revenue → margins → profit → working capital → cash flow → capex/debt → balance
sheet → EPS & FCF, and confirm the three statements reconcile. → *Output:*
three-statement forecast.

### 13. Macro & factor exposure (CAPM / APT)
Use CAPM for the cost of equity; use APT to understand which macro factors
actually drive the company (rates, inflation, PKR/USD, GDP, relevant commodities,
sovereign risk, sector index, domestic liquidity, export demand). Distinguish
correlation from real economic exposure. **(Factor list in §5.)** → *Output:*
discount rate + risk-driver map.

### 14. Market expectations — "what's priced in?"
Study the stock, not just the company: price (timestamped), market cap, EV, free
float, ADV, spread, volatility, beta, drawdown, ownership, positioning,
valuation history, peer multiples, consensus and estimate-revision direction.
Then run a **reverse valuation**: solve for the growth/margin/ROIC the *current
price* implies, and judge whether that's conservative, normal, or heroic.
→ *Output:* expectations gap analysis.

### 15. Valuation
Use **at least two independent methods**, matched to company type. Build the EV
bridge and the equity bridge correctly (leases, minorities, pensions, prefs,
associates, non-operating assets, contingent dilution, fully-diluted shares).
**See §4.** → *Output:* fair-value range + expected total return.

### 16. Scenarios (base / bull / bear / stress)
Each internally consistent. The bear case must explain *exactly how shareholders
lose money*, not just be a weaker base case. Stress-test refinancing, FX,
rates, commodity shocks, volume/margin collapse, dividend suspension, dilution.
**(Detail in §4.)** → *Output:* risk/reward distribution.

### 17. Thesis, variant perception & falsifiers
State what the market believes, what you believe differently and why, which
financial line changes if you're right, the catalyst that reveals it, the
falsifier that proves you wrong, and the downside mechanism and magnitude.
→ *Output:* investable thesis (or a reasoned rejection).

### 18. Scoring, deliverable & monitoring
Produce the three separate scores (Company Health, Stock Attractiveness, Evidence
Confidence), assemble the final report, and build a monitoring KPI dashboard with
thesis-breaking triggers. **See §6 for scoring weights and the exact report
template, and §7 for the monitoring dashboard.** → *Output:* full initiation
report + live thesis tracker + final posture (Buy / Hold / Avoid / Watchlist /
Insufficient evidence).

## What to ask the user for

Minimum: **Company, Ticker, Exchange.**
Helpful: investment horizon; long / short / neutral; current holding; preferred
benchmark; any specific concern. With only a company name, apply the default
mandate and begin with the corporate and subsidiary map before forming any
conclusion.

---

# APPENDIX — Detailed procedures

## §1 — Management ("CEO stack") & capital allocation

This is where edge is earned and careless analysts lose money. Over a multi-year
hold, management decisions matter more than almost anything, because **capital
allocation compounds.**

**The CEO stack.** Investigate the whole decision-making stack, not just the CEO
bio: sponsors / controlling family; chairperson, CEO, CFO, COO; segment &
subsidiary heads; board & independent directors; audit and remuneration
committees; company secretary; external auditor; key related-party entities.

**Credibility tests** (esp. CEO, CFO, sponsors): track record & performance in
prior roles; history of turnarounds/expansions/failures; experience through a
real downturn; regulatory/legal/governance controversies; senior-management
turnover frequency; key-man dependence & succession; and promises vs. results.

**Management promise-ledger.** Pull reports/transcripts from 3–5 years back and
score what was said against what happened. This single exercise saves more capital
than any ratio. Chronic promise-missers rarely reform; consistent under-promise /
over-deliver is a genuine positive.

| Statement | Date promised | Target period | Actual outcome | Variance | Explanation |
|---|---|---|---|---|---|
| Revenue / volume target | | | | | |
| Margin target | | | | | |
| Capacity expansion / project | | | | | |
| Debt reduction | | | | | |
| Return on a specific investment | | | | | |

**Incentive alignment.** Management shareholding (and *how* they own — direct
shares vs. short-dated options); comp vs. profits & shareholder returns; what the
bonus rewards (revenue/EBITDA/EPS = gameable; FCF/ROIC/long-term = aligned);
related-party comp; loans/benefits to executives; option-driven dilution; whether
management gets paid even when shareholders lose. Insider open-market **buying** is
one of the few genuinely informative signals; a cluster of executives all selling
is worth noting.

**Capital-allocation scorecard.** Every rupee goes to one bucket: maintenance
capex, growth capex, acquisitions, debt repayment, dividends, buybacks, associate
investment, related-party funding, or idle cash. For every major decision compute:
amount invested & funding source; promised vs. actual cash generation; ROIC
achieved; effect on debt, EPS, and **value per share.** Central questions:
- Does it earn more than its cost of capital? Can it reinvest at similar returns
  (incremental ROIC)?
- Is growth funded internally or by repeated debt/equity issuance?
- Acquisitions at sensible prices? (Check goodwill and later write-downs —
  impairments are the tombstones of bad deals.)
- Dividends sustainable from FCF? Buybacks **below** intrinsic value (good) or
  above (value destruction)?
- Did growth improve value **per share**, or just make the company bigger?

For capital-intensive names, don't approve a positive thesis until the model
includes maintenance capex, debt, leases, refinancing, dilution, and
**after-financing** returns.

## §2 — Subsidiaries, associates & group structure

Subsidiaries are where hidden value — or hidden risk — sits. Map the whole tree
before trusting any consolidated headline.

| Entity | Ownership % | Treatment | Revenue | Profit | Assets | Debt | FCF | Parent guarantees | Standalone value |
|---|---|---|---|---|---|---|---|---|---|
| Subsidiary A | | Consolidated | | | | | | | |
| Associate B | | Equity method | | | | | | | |
| JV C | | Equity method | | | | | | | |

For every entity: nature & strategic purpose, ownership %, voting control, other
shareholders, revenue/profit/cash contribution, debt & leases, parent guarantees,
capex commitments, intercompany loans, intercompany sales/purchases & transfer
pricing, dividends actually upstreamed to the parent, restrictions on upstreaming
cash, minority-interest leakage, contingent liabilities, auditor, standalone
value.

**Consolidated vs. unconsolidated reality.** Consolidated accounts blend 100% of a
subsidiary's revenue/assets even if the parent owns 60%. **Non-controlling
(minority) interest** shows how much consolidated profit is **not yours** — always
work down to profit attributable to owners of the parent.

**Cash mobility & debt location.** Can cash actually move up to the parent?
(Capital controls, JV-partner approval, covenants can trap it.) Is debt at the
parent or pushed into subsidiaries? Parent-level shareholders are **structurally
subordinated** to subsidiary lenders. Watch for **double leverage** (holdco
borrows to inject "equity" into an already-levered sub).

**Group-level red flags:** profits in subsidiaries but no cash reaching the
parent; parent guaranteeing subsidiary debt; loss-making subs repeatedly re-funded
by the listed company; related-entity sales inflating revenue; assets transferred
between group companies at questionable prices; unexplained intercompany
receivables; circular ownership; the genuinely profitable business sitting
**outside** the listed entity; minorities absorbing disproportionate risk.

**Tunneling (critical in family-controlled / EM groups).** Value gets siphoned
from the *listed* entity (outside shareholders are a minority) into *privately
held* group entities (family owns 100%) via transfer pricing, related-party loans
& "advances," off-market asset sales, management fees, and shared-cost
arrangements. This is the number-one way minorities are expropriated on markets
like PSX. **Read every related-party note line by line** and quantify the flows.
This feeds the SOTP in §4.

## §3 — Forensic accounting & earnings quality

Run this on **every** company, even ones you like. Earnings are an opinion; cash
is a fact. Any single flag warrants investigation; **two or more together, raise
your bar dramatically.**

**Revenue & receivables:** revenue growing faster than cash collections (core
accruals warning); receivables faster than sales → rising DSO (channel-stuffing,
pulled-forward revenue, weak payers); rising contract assets / unbilled revenue.

**Inventory:** growing faster than sales despite weak demand → future write-down
loading up, or obsolete stock carried too high.

**Cost & margin manipulation:** operating costs being **capitalized** (R&D,
software, interest) to inflate profit and defer the hit (compare policies to
peers); changed depreciation lives; asset revaluations propping up profit/equity;
margins wildly above peers with no nameable moat.

**Quality of the profit line:** large unexplained "other income"; recurring
"one-time" items (if they recur, they're operating items in disguise); declining
**cash** taxes despite rising reported profit; EPS growth driven by tax/FX/lower
finance cost rather than operations; EPS growth from accounting adjustments.

**Balance-sheet & financing games:** supplier financing hidden in working capital;
factoring masking collection speed; off-balance-sheet commitments & guarantees
(esp. for group companies); large goodwill/intangibles (fragile equity — one
write-down and it evaporates); acquisition accounting masking organic decline.

**Governance tripwires:** auditor qualification / emphasis-of-matter; auditor
change (esp. top-tier → obscure); restatements; frequent auditor/CFO changes;
abrupt CFO exit before results (one of the loudest signals in the market); weak or
shrinking segment disclosure.

**Metrics to compute:** accruals ratio (NI vs. OCF gap over time — high accruals
reliably predict underperformance); CFO/NI and CFO/EBITDA (should track ≥1);
FCF conversion (FCF/NI, ~80–100%+ healthy); DSO/DIO/DPO and cash-conversion cycle
across years; maintenance-vs-growth capex split.

**Screening models — tripwires, not verdicts:** Beneish M-Score (manipulation
likelihood), Altman Z-Score (distress), Piotroski F-Score (fundamental strength).
A failing score is a prompt to investigate the underlying line items, never a
standalone decision.

**Reconciliation gate:** before valuation, reconcile reported profit → operating
cash flow → change in net debt. If you can't make these tie out, don't proceed to
a fair value — document the gap and lower evidence confidence.

## §4 — Valuation, bridges & scenarios

Value only **after** the business/group/management/forensic work. Use **at least
two independent methods** and see whether they agree. Output a **range**, plus an
expected total return.

**Method by company type:** mature operating → DCF, P/E, EV/EBITDA; conglomerate/
holdco → SOTP; bank → P/B, residual income, dividend-discount; insurance → P/B,
embedded value, dividend model; cyclical/commodity → mid-cycle earnings, NAV,
normalized EV/EBITDA; asset-heavy → NAV, replacement cost, DCF; high-growth →
DCF, scenario, reverse DCF; binary/event-driven → probability-weighted. Use
**EV-based** multiples when capital structures differ.

**Enterprise-value bridge:**
`EV = Equity value + Debt + Leases + Preference shares + Minority interest − Cash`

**Equity-value bridge:** from operating/enterprise value, adjust for net debt,
leases, minority interests, pension deficits, preference shares, associates &
investments (add at fair value), non-operating assets (add), contingent dilution;
divide by **fully-diluted** shares.

**DCF:** project FCF on defensible, driver-linked assumptions (not hockey sticks),
discount at WACC, add terminal value; **always run sensitivity tables** (growth ×
discount rate; margin × multiple). For capital-intensive names, FCF must be after
maintenance capex, financing, and dilution.

**Reverse DCF (often more useful):** solve for the growth/margin/ROIC the *current
price* implies, then judge whether that's conservative, normal, a turnaround,
permanent high growth, or heroic. Reframes valuation as "what does the market
believe?" — where mispricing actually lives.

**Comps:** compare to the company's **own history** and to **genuine** peers. A
cheap multiple is usually cheap for a reason — ask why.

**SOTP (holdcos/conglomerates):** value each stake with the right method, sum,
subtract net parent debt and capitalized head-office cost, apply a **justified**
holdco discount (understand *why* it exists — governance, illiquidity, tax on
unwind, poor allocation — and whether it's opportunity or warning).

**Asset-based:** NAV, liquidation, replacement cost — a floor when earnings power
is uncertain.

**Scenarios (four, internally consistent):**

| Case | Central assumption | Output |
|---|---|---|
| Bull | Strong demand, pricing, operating leverage | Upside value |
| Base | Most probable normalized performance | Central fair value |
| Bear | Operational disappointment + multiple compression | Fundamental downside |
| Stress | Liquidity / refinancing / severe-cycle shock | Survival value |

The **base** case drives the decision; the **bear** case must explain *exactly how
shareholders lose money*, not merely be a softer base case. Stress inputs: PKR
depreciation, rate hikes, commodity shocks, volume decline, margin compression,
delayed projects, key-customer loss, regulatory/tariff change, working-capital
blockage, refinancing at higher rates, dilution, dividend suspension.

**Expected total return** = `(Target price − Current price + Expected dividends) /
Current price`. Only take a positive stance with a **margin of safety** (price
meaningfully below base-case value). Weight scenarios by probability for a
risk/reward distribution, not a point estimate.

## §5 — Sector engines (PSX) & factor risk

Build revenue and margins from **operational drivers**, not generic % growth. Pick
the matching engine; model drivers → revenue → margins → profit → working capital
→ cash flow → capex/debt → balance sheet → EPS & FCF; confirm the statements
reconcile.

- **Banks:** `deposits × asset deployment × spreads − credit costs`. Watch NIM,
  deposit mix/CASA, asset quality, infection (NPL) ratio, coverage, cost of risk,
  CAR. Value via P/B, residual income, DDM.
- **Fertilizer:** `production × offtake × retention price`. Watch gas
  availability/pricing, inventory, subsidy receivables, GIDC/regulatory pricing.
- **Cement:** `dispatches × retention price − coal/energy/freight`. Watch capacity
  utilization, local vs. export mix, coal price, FX on coal, expansion/supply-glut
  risk.
- **E&P:** `production × realized price − lifting cost`. Watch reserves &
  replacement ratio, realized vs. benchmark price, circular-debt receivables,
  PKR/USD (dollar-linked revenue).
- **Power / IPPs:** `availability × tariff × capacity/energy payments`. Watch heat
  rate, capacity payments, tariff adjustments, **circular-debt exposure.**
- **Textiles:** `export orders × mix × price − cotton/energy/FX`. Watch cotton &
  energy cost, FX, working-capital intensity, customer concentration, value-added
  vs. basic mix.
- **Pharma:** `portfolio volume × DRAP-regulated price`. Watch DRAP pricing &
  approvals, imported-input cost & FX, pipeline, molecule concentration.
- **Technology / IT:** `customers × revenue per customer × retention`. Watch dollar
  revenue, customer concentration, employee-cost inflation, capitalized dev
  expense, net revenue retention.
- **Insurance:** `premium growth − claims − expenses (+ investment income)`. Watch
  combined ratio, claims/reserving, solvency, investment-book risk.
- **Autos / parts:** `volumes × price − localized/imported input cost`. Watch
  localization %, FX content, pricing power, inventory, financing rates, model
  cycle.
- **Generic manufacturing (fallback):** `capacity × utilization × yield × price −
  variable cost`.

**Factor risk.** CAPM for cost of equity: `Ke = Rf + β·(Rm − Rf)` (use a
long-tenor local sovereign yield for PKR cash flows and a market-appropriate ERP).
APT to see which macro risks actually drive the company:
`E(R) = Rf + β1·λ1 + β2·λ2 + … + βn·λn`. Candidate PSX factors: market return,
rates, inflation, PKR/USD, GDP/industrial production, relevant commodities (oil,
gas, coal, cotton, agri), sovereign risk, sector index, domestic liquidity, export
demand. Estimate rolling sensitivities, test across regimes, and **distinguish
correlation from genuine economic exposure.** CAPM supports the discount rate; APT
explains risk drivers. Neither replaces fundamental cash-flow analysis.

## §6 — Scoring & final deliverable

Don't bury everything in one number. Score three things separately.

**A. Company Health (out of 100):** business quality & competitive position 15;
management & governance 15; financial & earnings quality 20; balance-sheet strength
15; capital allocation & ROIC 15; growth runway 10; subsidiary transparency &
group risk 10.

**B. Stock Attractiveness (out of 100):** valuation & margin of safety 25;
expectations & variant gap 20; estimate-revision direction 15; catalysts & timing
15; downside & scenario skew 15; liquidity, positioning & technical setup 10.

**C. Evidence Confidence:** High (primary, recent, reconciled) / Medium (credible
but incomplete or indirect) / Low (material missing info or assumption-heavy).

A high-quality company can score low on attractiveness (too expensive); a cheap
stock can be uninvestable if governance/solvency/evidence is too weak. Keep the
three honest and independent.

**Final posture (exactly one):** Research-qualified Buy / Hold / Avoid / Watchlist
— wait for proof / Preliminary underwrite — insufficient evidence / Re-underwrite
required.

**Final report template (assemble in this order):**
1. Executive investment view
2. Company-health classification (Score A + one-line rationale)
3. Stock-attractiveness assessment (Score B + one-line rationale)
4. Central market debate (what bull and bear are really arguing about)
5. 3–5 thesis pillars, each with its measurable falsifier
6. What is currently priced in (from reverse valuation)
7. Company & value-chain explanation
8. Sponsor, CEO & management analysis (incl. promise-ledger verdict)
9. Complete subsidiary & associate map
10. 5–10 year normalized financial analysis
11. Earnings-quality & forensic review
12. Balance-sheet & refinancing assessment
13. Capital-allocation history & scorecard
14. Industry & peer analysis
15. ~5-year driver-based forecast
16. CAPM & APT risk analysis
17. DCF, comparable & SOTP valuation → fair-value range + expected total return
18. Base / bull / bear / stress cases
19. Catalysts & timeline
20. Ranked risks
21. Measurable thesis falsifiers
22. Monitoring KPI dashboard
23. Management questions for the next corporate briefing
24. Evidence register, missing sources & confidence level (A/B/C summary)

Keep it evidence-labeled throughout (verified fact / management claim / estimate /
model-derived / judgment / assumption / missing).

## §7 — Monitoring dashboard (live thesis tracker)

The report is not the end — the position must be monitored. Build a tracker with:
the operational KPIs the thesis depends on (from the sector engine), each with the
level that confirms vs. breaks it; earnings checkpoints (next results, guidance,
briefing dates); a catalyst calendar with expected timing; and **thesis-breaking
triggers** — the specific events or metric thresholds that invalidate the call and
prompt a re-underwrite or exit.

Standard for a good falsifier — specific and measurable, not vague: *"Margin
expansion depends on utilization rising above X% and unit energy cost normalizing
below Y. The thesis weakens if utilization stays below X% for two consecutive
quarters or unit energy cost stays above Y."* That is far stronger than
"management is strong and the sector has potential."
