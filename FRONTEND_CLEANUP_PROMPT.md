# PSX Pulse Frontend Cleanup: Surgical Fix for 25 Architectural Issues

**Objective:** Fix architectural debt and design system inconsistencies introduced in the latest two redesign commits without breaking backend functionality or removing working routes.

**Scope:** Architecture first, aesthetics later. Do NOT add new features. Do NOT change backend logic. Do NOT introduce fake data.

---

## CRITICAL FIXES (P0 - Blocking)

These must be fixed before anything else looks correct.

### Issue 1: Atmospheric Background Covered by Opaque Layers
**Problem:** Root layout creates beautiful `atmospheric-bg` and `grain-overlay`, but AppLayout renders `bg-bg` with `--color-bg: #DAE1EE` (solid opaque color), covering the gradients.

**Impact:** Glass cards blur a flat color instead of the layered background. The entire premium aesthetic is defeated.

**Fix:**
1. Remove the `bg-bg` class from AppLayout main wrapper
2. Remove the solid background color from `--color-bg` on AppLayout
3. Trust the root layout's global atmospheric effects
4. Ensure AppLayout itself is transparent: `bg-transparent`
5. Move any color to child containers that need opaque backgrounds, not the shell

**Files to change:**
- `frontend/src/components/layout/AppLayout.tsx` — remove opaque background, add `bg-transparent`
- Verify `frontend/src/app/globals.css` atmospheric-bg is still applied globally

### Issue 2: Research Studio Overpainting Atmosphere Again
**Problem:** `ResearchStudioProduction.tsx` adds `min-h-screen bg-[var(--bg-page-deep)]` inside AppLayout, painting another opaque blue rectangle over the atmosphere.

**Impact:** Research pages look flat and dead despite glassmorphism claims.

**Fix:**
1. Remove `min-h-screen bg-[var(--bg-page-deep)]` from ResearchStudioProduction outer wrapper
2. Change wrapper to `bg-transparent`
3. Let root layout atmosphere show through
4. Move background color only to internal sections that need it (e.g., a research header card)

**Files to change:**
- `frontend/src/components/research/ResearchStudioProduction.tsx` — remove opaque full-screen background

### Issue 3: Duplicate Atmospheric Layers on Company Page
**Problem:** Company detail page adds its own `atmospheric-bg` and `grain-overlay` even though root already provides them globally. This creates either double-blurred surfaces or competing effects.

**Impact:** Visual inconsistency, unclear which atmosphere is "correct."

**Fix:**
1. Remove `atmospheric-bg` and `grain-overlay` classes from company detail page
2. Trust the root layout global atmosphere
3. If company page needs a distinct background zone, use a glass card, not duplicate atmospheric effects

**Files to change:**
- `frontend/src/app/company/[ticker]/page.tsx` — remove duplicate atmospheric classes

### Issue 4: Mobile Navigation Completely Missing
**Problem:** Sidebar is `hidden lg:flex`. AppLayout provides no mobile header, hamburger button, drawer, sheet, or bottom navigation. Below `lg` breakpoint, navigation disappears entirely.

**Impact:** App is unusable on mobile/tablet.

**Fix:**
1. Create `MobileNav.tsx` component — floating bottom navigation or slide-out drawer
2. Render in AppLayout with responsive logic: `lg:hidden` (mobile), `hidden lg:flex` (desktop sidebar)
3. Mobile nav should expose same items as desktop Sidebar: Dashboard, Market, Research, Screeners, Ask AI, Trade Planning, Company Search
4. Use glass styling to match desktop aesthetic
5. Touch targets must be ≥44px

**Files to create:**
- `frontend/src/components/layout/MobileNav.tsx`

**Files to update:**
- `frontend/src/components/layout/AppLayout.tsx` — add mobile nav logic

### Issue 5: Major Features Missing from Navigation
**Problem:** Current Sidebar only exposes: Dashboard, Market, Research, Screeners, Academy, Watchlists. Missing:
- Ask PSX Pulse (`/research-ask`)
- Trade Planning (`/trade-planning`)
- Company Search (`/search`)

These routes exist but are invisible.

**Impact:** Users cannot discover major product features.

**Fix:**
1. Add to Sidebar navigation:
   - "Ask PSX Pulse" → `/research-ask` (with icon)
   - "Trade Planning" → `/trade-planning` (with icon)
   - "Company Search" → `/search` (with icon)
2. Remove or disable fake items:
   - Academy, Watchlists (mark as disabled/coming-soon if not implemented)
   - Documentation, Preferences, Sign Out (these are fake links to `#`)
3. Keep "Dashboard", "Market", "Research", "Screeners"

**Files to update:**
- `frontend/src/components/dashboard/Sidebar.tsx` — add navigation items, remove fakes

### Issue 6: Fake Navigation Links
**Problem:** Sidebar items "Documentation", "Preferences", "Sign Out" link to `#` instead of real routes. They appear functional but do nothing. Unlike Academy/Watchlists, they're not marked disabled.

**Impact:** Misleading UX, user expects functionality that doesn't exist.

**Fix:**
1. Remove "Documentation" and "Preferences" entirely (they have no routes)
2. Remove "Sign Out" unless auth exists (check backend)
3. If these should exist, create actual routes and link them
4. Mark genuinely missing features (Academy, Watchlists) with `disabled` state and visual indicator

**Files to update:**
- `frontend/src/components/dashboard/Sidebar.tsx` — remove fake links

---

## ARCHITECTURAL FIXES (P1 - Core Coherence)

### Issue 7: Route Consolidation Not Completed
**Problem:** Three competing Trade Planning experiences still exist:
- `/trade-planning` (standalone page)
- `/research-trade` (separate route)
- `/research?t=FFC&tab=trade` (Research Studio tab)

**Impact:** Users don't know which Trade Planning is canonical. Data might be inconsistent.

**Fix:**
1. Choose ONE canonical Trade Planning experience
   - **Option A:** Keep `/research?t=FFC&tab=trade` inside Research Studio
   - **Option B:** Keep `/trade-planning` as standalone, redirect others to it
2. If choosing Option A:
   - Delete `/trade-planning/page.tsx` and directory
   - Redirect `/trade-planning` → `/research?t=FFC&tab=trade`
   - Delete `/research-trade/page.tsx`, redirect → `/research?t=FFC&tab=trade`
3. If choosing Option B:
   - Keep `/trade-planning`
   - Redirect `/research-trade` → `/trade-planning`
   - Make Research Studio Trade tab link to `/trade-planning`
4. Update navigation to point to chosen canonical route

**Recommendation:** Option A (keep in Research Studio, delete standalone) — simpler, keeps company context.

**Files to change:**
- Remove unused route directories
- Update navigation links
- Add redirects in unused route files or delete entirely

### Issue 8: Company Research Not Consolidated
**Problem:** Two competing company research experiences:
- `/company/[ticker]` (standalone company detail page)
- `/research?t=FFC&tab=overview` (Research Studio)

**Impact:** Duplicate features, inconsistent UX, unclear which is canonical.

**Fix:**
1. Choose ONE canonical company research experience
   - **Option A:** Keep Research Studio as canonical (`/research?t=ticker`)
   - **Option B:** Keep company page as canonical (`/company/[ticker]`)
2. If choosing Option A:
   - Delete `/company/[ticker]/page.tsx`
   - Redirect `/company/[ticker]` → `/research?t=[ticker]&tab=overview`
3. If choosing Option B:
   - Delete Research Studio from app
   - Add tabs to company page
   - Consolidate content
4. Update navigation to use canonical path

**Recommendation:** Option A (Research Studio canonical) — it's more fully featured, already integrated into app shell.

**Files to change:**
- Delete or redirect unused route

### Issue 9: Screener Hub Not Actually Implemented
**Problem:** Previous commit claimed `/screener` was created as a Screener Hub, but current routes are `/screening`, `/technical`, `/momentum`. No hub exists. Sidebar was changed to point directly at `/screening`.

**Impact:** Architecture diverged from stated plan. Unclear if intentional.

**Fix:**
1. Decide: Do you actually need `/screener` hub?
   - If YES: Create `/screener/page.tsx` as hub with links to `/screening`, `/technical`, `/momentum`
   - If NO: Document that Sidebar now points directly to screeners (OK, but update commit message)
2. If creating hub:
   - `/screener` should show: "Fundamental Screening", "Technical Analysis", "Momentum Analysis" with descriptions
   - Use glass cards
   - Link each to respective route
3. Update Sidebar to link to `/screener` (the hub)

**Recommendation:** Create the hub. It improves discoverability and matches the architecture promise.

**Files to create/update:**
- `frontend/src/app/screener/page.tsx` (if needed)
- Update Sidebar navigation

### Issue 10: Inconsistent Root Metadata
**Problem:** Root `layout.tsx` metadata still says `"PSX Research | Intelligence Dashboard"` while page-level metadata and Sidebar now say `"PSX Pulse"`.

**Impact:** Mixed branding signals.

**Fix:**
1. Update root metadata title to `"PSX Pulse"`
2. Update root metadata description to reference PSX Pulse
3. Ensure all page titles follow pattern: `"PageName | PSX Pulse"`

**Files to update:**
- `frontend/src/app/layout.tsx` — update root metadata

---

## DESIGN SYSTEM CONSOLIDATION (P2)

### Issue 11: Overlapping CSS Class System
**Problem:** `globals.css` has:
- `.glass-card`, `.glass-strong`, `.glass-soft`, `.glass-light`, `.glass-blue`
- Legacy aliases
- Dark panels
- Elevation classes
- Multiple hover/interaction states

PLUS separate React components: `GlassCard`, `GlassPanel`, `MetricCard`, etc.

**Impact:** Multiple ways to style the same thing. Rapid inconsistency as pages use mix of both.

**Fix:**
1. **Consolidate CSS classes**: Keep only core primitives
   - `.glass-card` — primary glass container
   - `.glass-card--strong` — stronger glass variant
   - `.glass-card--soft` — soft tinted glass
   - `.elevation-1`, `.elevation-2`, `.elevation-3` — shadow hierarchy
   - Remove redundant aliases and dark panels

2. **Establish rule:** 
   - Use React components (`GlassCard`, `GlassPanel`) for most interactive/reusable surfaces
   - Use CSS classes only for one-off styling or when component would be overkill
   - NEVER use both on same element

3. **Migrate pages** to use components instead of raw classes where practical

**Files to update:**
- `frontend/src/app/globals.css` — remove duplicates, keep only core
- All page files — prefer components over raw classes
- Remove unused CSS utility classes

### Issue 12: Hover Animation Over-Applied
**Problem:** `.glass-card:hover` applies `translateY(-2px)` globally. Every glass card lifts on hover, even static informational containers that aren't clickable.

**Impact:** "Everything floats when I move my mouse" — feels gimmicky, poor affordance.

**Fix:**
1. Remove global hover transform from `.glass-card`
2. Create `.glass-card--interactive:hover` for actually clickable cards
3. Apply only to cards that are links or buttons
4. Static informational cards should NOT lift

**Files to update:**
- `frontend/src/app/globals.css` — remove `.glass-card:hover` transform

### Issue 13: Radius System Under-Used
**Problem:** Design system defines `--radius-lg` (22px), `--radius-xl` (28px), `--radius-2xl` (34px), but glass classes use only `var(--radius-md)` (16px). Reference designs had more sculpted 24–34px surfaces.

**Impact:** UI looks too conservative, doesn't match premium aesthetic.

**Fix:**
1. Audit where larger radii should be used:
   - Major panels (Dashboard cards, Research header) → `--radius-xl` or `--radius-2xl`
   - Standard cards → `--radius-lg` (22px)
   - Small components (badges, buttons) → `--radius-sm` (12px)
2. Update glass classes to use appropriate tokens
3. Ensure consistency across pages

**Files to update:**
- `frontend/src/app/globals.css` — update glass class radii

---

## CONTENT & INFORMATION ARCHITECTURE (P3)

### Issue 14: Homepage Not a Real Dashboard
**Problem:** Homepage is five generic feature marketing cards + about panel. It does not surface:
- KSE index state
- Market breadth
- Top movers
- Data freshness
- Important research
- Screening signals
- Real market data

**Impact:** Doesn't function as a financial dashboard. It's a navigation menu.

**Fix:**
1. Keep the structure but populate with REAL backend data
2. Replace generic "Market Overview" card with actual:
   - KSE-100 index value + change
   - Breadth (advancers/decliners)
   - Last data timestamp
3. Replace generic "Research Studio" with:
   - Featured company (e.g., FFC)
   - Current price + research score
4. Keep other cards but ensure they're navigation entry points, not the whole story
5. Add small data panels below showing:
   - Market freshness
   - Recent research updates (if available)

**Files to update:**
- `frontend/src/app/page.tsx` — integrate backend market data

### Issue 15: "Real-time" Claim is Inaccurate
**Problem:** Homepage says "Real-time PSX indices" but your Market page/backend serves delayed/end-of-day data. This is a trust issue.

**Impact:** Users expect real-time data, gets delayed data, loses trust.

**Fix:**
1. Change homepage copy from "Real-time" to "End-of-day" or "Market Overview"
2. Update homepage to clearly show data freshness timestamp
3. Be accurate about data sources throughout

**Files to update:**
- `frontend/src/app/page.tsx` — update copy

---

## INTERNAL UI CONSOLIDATION (P4)

### Issue 16: Research Studio Uses Legacy Design System Internally
**Problem:** Outer Research Studio shell was given glass styling, but content (Financials, etc.) still uses legacy `<Card>`, old `Label` components, old studio UI primitives.

**Impact:** Premium header sits above old-looking content. Visually incoherent.

**Fix:**
1. Migrate Research Studio internals to glass primitives:
   - Replace legacy `<Card>` with `<GlassCard>`
   - Replace legacy labels with `<Label>` from glass system
   - Update Intelligence dashboard to use `<MetricCard>`
   - Update Financials table to use glass table styling
2. Ensure all tabs use consistent design language
3. This is a multi-file refactor; prioritize by tab usage:
   - Overview (most-used)
   - Intelligence
   - Financials
   - Technicals
   - Others

**Scope:** Large; may need dedicated focus. Documented under "Next Steps" in previous commit.

**Files affected:** Most files in `frontend/src/components/research/`

### Issue 17: Trade Planning Has Multiple Overlapping Components
**Problem:** Trade Planning area has:
- 21 KB `trade-planning/dashboard.css`
- `TradePlanDashboard.css`
- `TradePlanDashboard.tsx`
- `TradeCheck.tsx`
- `TradePlanningView.tsx`

Multiple overlapping components and stylesheets for one product area.

**Impact:** Inconsistent styling, unclear data flow, difficult to maintain.

**Fix:**
1. Consolidate: Keep ONE Trade Planning component
   - Migrate to glass design system
   - Remove legacy CSS files
   - Unify data flow
2. Choose canonical component (likely `TradePlanDashboard.tsx`)
3. Delete redundant files
4. Ensure it uses `GlassCard`, `GlassInput`, `GlassButton` etc.

**Files to consolidate:**
- Keep `TradePlanDashboard.tsx` (main component)
- Delete or merge `TradeCheck.tsx`, `TradePlanningView.tsx` if redundant
- Delete `TradePlanDashboard.css` and `dashboard.css` if styles migrated to globals

### Issue 18: Unused Imports (Code Cleanliness)
**Problem:** `GlassInput` imported in Research Studio but actual search field uses `.glass-input` class. Small sign of hasty refactor.

**Impact:** Code debt, confusion about intended usage.

**Fix:**
1. Audit Research Studio for unused imports
2. Either use the component or remove the import
3. Establish rule: if component exists, use it; otherwise remove import

**Files to update:**
- `frontend/src/components/research/ResearchStudioProduction.tsx` — remove unused imports

---

## INTERACTION & UX FIXES (P2-P3)

### Issue 19: AppLayout is "use client" but Doesn't Need Client State
**Problem:** AppLayout wrapper is marked `"use client"` but contains no client state. Only Sidebar needs client behavior. This unnecessarily pushes major architectural boundary to client side.

**Impact:** Reduces Server-Side Rendering (SSR) opportunities, bloats client bundle.

**Fix:**
1. Remove `"use client"` from AppLayout if it only renders children
2. Move `"use client"` to `Sidebar.tsx` only (it needs interaction state)
3. Keep AppLayout server-renderable

**Files to update:**
- `frontend/src/components/layout/AppLayout.tsx` — remove "use client"
- Ensure `Sidebar.tsx` has "use client"

### Issue 20: Company Hero Not Designed
**Problem:** Research Studio says generic "Equity Research Studio" header, then "Viewing FFC." Missing strong company identity.

**Impact:** Doesn't match Bloomberg/Fiscal.ai-style premium company research product.

**Fix:**
1. Create hero header showing:
   - Company ticker (large, bold)
   - Company name
   - Current price + % change
   - Sector
   - Data freshness
   - Research quality score (if available)
2. Use glass cards with premium styling
3. Make it visually dominant — this is THE company view

**Files to update:**
- Create `frontend/src/components/research/CompanyHeader.tsx` (or similar)
- Update `ResearchStudioProduction.tsx` to render it

### Issue 21: Research Tab Information Architecture Too Flat
**Problem:** 11 research tabs at same hierarchy level (Overview / Intelligence / Business / ... / Evidence) is overwhelming. No grouping.

**Impact:** Confusing, crowded, users don't know where to look.

**Fix:**
1. Group tabs into logical sections:
   - **Snapshot:** Overview
   - **Analysis:** Intelligence, Business, Financials, Valuation, Technicals
   - **Context:** News & events, Peers, Governance
   - **Evidence:** Evidence
2. Use collapsible groups or visual separators
3. Or: make Overview primary, hide others behind "Full Research" button initially
4. Ensure UX test on mobile (11 tabs won't fit on small screens)

**Files to update:**
- `frontend/src/components/research/ResearchTabs.tsx` or similar

---

## FINAL VERIFICATION (After All Fixes)

### Issue 22: Build & Tests Pass
After fixing, verify:
1. `npm run build` succeeds
2. `npm run lint` shows no new errors
3. `npm run type-check` passes
4. No console errors on main pages
5. Existing tests still pass (if any)

### Issue 23: No Broken Routes
Verify:
1. All routes in Sidebar are real: `/`, `/market`, `/research`, `/screening`, etc.
2. All deep links work: `/research?t=FFC&tab=overview`, etc.
3. Redirects work: `/company/[ticker]` → `/research?t=ticker` (if implemented)
4. No 404s on navigation

### Issue 24: Responsive Checks
Test on:
- Desktop (1440px, 1920px)
- Tablet (768px)
- Mobile (375px, 430px)
Verify:
- No clipped content
- Mobile nav accessible and usable
- Touch targets ≥44px
- Glass effects visible and readable

### Issue 25: Data Accuracy
Verify:
- No fake financial data
- Data freshness timestamps accurate
- "Real-time" claims corrected to "end-of-day"
- All API calls functional (or gracefully fail)

---

## Implementation Order

**Phase 1 (Make it work):** Issues 1-6, 10, 18, 19, 22-25
- Blocks: Everything else until unblocked

**Phase 2 (Make it coherent):** Issues 7-9, 11-13
- Architecture consolidation
- Design system unification

**Phase 3 (Make it real):** Issues 14-15
- Real dashboard data
- Accurate copy

**Phase 4 (Make it polish):** Issues 16-17, 20-21
- Internal UI migration
- Information architecture
- Hero header design

---

## Constraints

✅ **DO:**
- Fix architectural problems
- Consolidate overlapping systems
- Remove fake/dead code
- Use existing components
- Preserve all routes
- Preserve all backend logic
- Add real data where possible

❌ **DON'T:**
- Add new features
- Change backend calculations
- Introduce fake data
- Break existing functionality
- Redesign further (aesthetics only after coherence)
- Add new dependencies

---

## Success Criteria

After all fixes:
- ✅ Atmospheric backgrounds visible (not covered)
- ✅ Mobile navigation exists and works
- ✅ All product features in navigation
- ✅ No fake links
- ✅ No duplicate routes
- ✅ One canonical Company Research path
- ✅ One canonical Trade Planning path
- ✅ One design system (not overlapping)
- ✅ Homepage shows real market data
- ✅ Data claims accurate
- ✅ No unused code
- ✅ All tests pass
- ✅ No 404s
- ✅ Responsive on all screen sizes
- ✅ Glass effects working (cards blur real background)
