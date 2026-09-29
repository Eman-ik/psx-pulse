/**
 * What v1 actually ships, and what is parked.
 *
 * The company page grew to twelve tabs while the pilot explored what was possible. Most of
 * them are real code that works; they are parked because they are not the summary/research
 * flow v1 is being cut down to, or because the data underneath them is not ready to be shown
 * to anyone. Parked means hidden from the surface, not deleted -- every component stays
 * importable and every endpoint stays alive, so unparking is a one-line change here.
 *
 * Each parked tab carries the reason it is parked. If the reason stops being true, move the
 * tab back into V1_COMPANY_TABS rather than quietly rendering it again from somewhere else.
 */

export const V1_COMPANY_TABS = [
  "Summary",
  "Profile",
  "Financials",
  "Ratios",
  "Technicals",
  "Announcements",
  "Competitors",
  "Analyst",
] as const;

export type V1CompanyTab = (typeof V1_COMPANY_TABS)[number];

export const PARKED_COMPANY_TABS: Record<string, string> = {
  Operations:
    "app/ingestion/operational_kpi_seed.py only ever covered FFC and EFERT -- there are no " +
    "cement production or despatch volumes on file at all, and none for FATIMA. Two of 23 " +
    "companies is not a tab. Unpark once cement despatch data is actually ingested.",

  "AI Signal":
    "Gated by PUBLIC_SIGNALS_ENABLED, which is false and stays false until " +
    "backend/docs/rights_matrix.template.md is actually completed and reviewed. Not a scope " +
    "call -- a compliance one.",

  "ML Model":
    "The ML signal engine's own A/B record (see the psx-fertilizer commit log: 'also didn't help', " +
    "and the khronos walk-forward and true-holdout evaluations) did not establish a genuine edge. " +
    "Shipping a confident-looking model tab on top of that would be the least honest surface here.",

  "Quant Forecast":
    "Same evidence problem as ML Model -- this is the Kronos fine-tune, whose own diagnosis commit " +
    "concluded 'mean-reversion bias, but no exploitable signal'.",
};

/**
 * Tabs that need verified fundamentals to render anything truthful.
 *
 * Competitors is here because a peer table built from quarantined figures is worse than no
 * peer table: it invites the reader to compare a verified company against unchecked ones and
 * draw a conclusion from the gap. Within a single sector the comparison is genuinely useful
 * -- FFC against EFERT against FATIMA is the question a fertilizer reader actually has --
 * which is why it ships for full-coverage companies rather than staying parked.
 */
const REQUIRES_FUNDAMENTALS: ReadonlySet<string> = new Set([
  "Financials",
  "Ratios",
  "Competitors",
  "Analyst",
]);

/** Mirrors app/universe.py's tiers. Keep the string values in sync with that module. */
export type CoverageTier = "full" | "unverified" | "price_only";

/**
 * The tabs to show for a company, given how well covered it is.
 *
 * A price-only company keeps the tabs that run purely off EOD prices and announcements. It
 * does not get an empty ratio grid -- an empty grid reads as "this company has no debt",
 * not as "we have not entered this company's balance sheet yet".
 */
export function visibleCompanyTabs(tier: CoverageTier): readonly V1CompanyTab[] {
  if (tier === "full") return V1_COMPANY_TABS;
  return V1_COMPANY_TABS.filter((tab) => !REQUIRES_FUNDAMENTALS.has(tab));
}

/**
 * The note explaining why a company is missing the fundamentals-backed tabs.
 *
 * Deliberately different wording for the two reasons: "nobody has entered this yet" and "the
 * numbers on file were never checked" are different promises to a user, and collapsing them
 * into one vague "unavailable" is how the second one quietly becomes invisible.
 */
export function coverageNote(tier: CoverageTier): string | null {
  switch (tier) {
    case "full":
      return null;
    case "unverified":
      return (
        "Financial statements for this company are on file but have not been verified against " +
        "the published annual reports, so ratios and written analysis are withheld. Price " +
        "history and announcements below are unaffected."
      );
    case "price_only":
      return (
        "Price history and announcements are covered for this company. Financial statements " +
        "have not been entered yet, so ratios and written analysis are not available."
      );
  }
}
