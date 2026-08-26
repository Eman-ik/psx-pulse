# Model Governance (DRAFT — no signal has been approved for public activation)

Status: **NOT COMPLETED**. This document defines the process; it does not itself
constitute approval of anything. As of this writing, no model or signal on this
platform meets the bar it sets — see [Current models: real status](#current-models-real-status)
below, which is not hypothetical, it's this session's actual measured results.

Companion to [`rights_matrix.template.md`](rights_matrix.template.md) (data licensing —
"are we allowed to use this data at all") and [`research_disclaimer.md`](research_disclaimer.md)
(what gets shown to a reader). This document covers a different question: "has this
specific model's output earned the right to be called a signal."

## The one distinction everything else here depends on

**Research output** and **investment recommendation** are not the same claim, and this
platform must never let the first one silently become the second.

- Research output: *"This model estimates a 57% probability of positive 5-day return for
  FFC, based on a walk-forward track record of 53% accuracy over 40 observations (not
  statistically significant, p=0.21)."* — a measured fact about a model, with its own
  uncertainty attached.
- Investment recommendation: *"BUY FFC."* — a directive a reader could act on with money,
  implying the platform has weighed the model's uncertainty on the reader's behalf and
  found it acceptable.

The second carries substantially greater regulatory exposure than the first (SECP
research-regulation review — see `rights_matrix.template.md` — has not happened). Every
surface this platform controls must be capable of stating the first without ever
collapsing into the second. Concretely: `ai_signal`/`ml_signal`/Kronos `signal` values are
labels on a probability distribution ("BUY" meaning "the gate's thresholds were cleared"),
never phrased as an instruction, and every surface carries `SCORE_DISCLAIMER`
(`app/api/comparison.py`) or the equivalent research-only framing already present in
`signal_qualification.py`'s `reason` field and `ml_signal_engine.py`'s module docstring.

## What the system is allowed to display

Three independent gates, checked in `app/core/config.py`, none of which override the
others:

1. **`public_launch_enabled`** — can this platform be shown to anyone outside the project
   owner at all. `False` by default; flipping it is a business decision, not a modeling one.
2. **`public_signals_enabled`** — can `ai_signal`/`ai_score` (the rules-based composite in
   `app/etl/signal_engine.py`) be shown to a non-internal reader. `False`.
3. **`ml_signals_enabled`** — can `ml_signal`/`outperformance_probability` (the pooled
   classifier in `app/etl/ml_signal_engine.py`) be shown to a non-internal reader. `False`.

All three are read at compute time, not hardcoded per-row (`MlSignalScore.is_public`,
`SignalScore` equivalent) — a flag flip doesn't require recomputing history, but it also
means a flag flip takes effect retroactively across everything already stored. That's a
real, sharp edge: flipping `ml_signals_enabled=True` makes every row ever computed public
at once, including runs made under looser thresholds than whatever's current. **Rule: a
flag flip is itself an approval action (see below) and must be preceded by a re-check that
every currently-stored row still passes the current validation bar, not just future ones.**

Even with all three `True`, the Kronos quant-forecast path (`quant_forecast.py`) and its
`signal_qualification.py` gate are a **separate, fourth surface** with its own
qualification logic — flipping the three flags above does not expose Kronos-derived
signals; that gate has no corresponding `_enabled` flag yet because nothing about it has
ever been reviewed for public exposure. Do not add one without extending this document.

## What constitutes a "signal" (vs. an unqualified model estimate)

A model producing a number is not the same as that number being a "signal." The
distinction lives in `signal_qualification.py` and `ml_signal_engine.py`'s `SignalModel.rank()`
today, and any future model must implement the same shape:

- A **raw estimate** (probability, expected return, direction) may exist internally for
  any ticker with enough history to compute one at all.
- A **qualified signal** is a raw estimate that has cleared *both* an accuracy floor and a
  statistical-significance test against its own real, walk-forward, never-seen-during-
  training track record — not against training-set performance, not against a single
  observation.
- Anything that hasn't cleared both bars is `NO_SIGNAL` / `"NO SIGNAL"`, displayed as such,
  never silently rounded up to the nearer of BUY or SELL. `ml_signal_engine.py`'s own
  design already forbids SELL entirely (see its module docstring) since the classifier
  only estimates one-sided probability — a second, independently-validated downside model
  would be required before a SELL signal could exist at all, qualified or not.

## Required validation metrics (current, per model — update if thresholds change)

| Model | Min. accuracy | Significance test | Beats naive baseline | Min. observations | Where enforced |
|---|---|---|---|---|---|
| Kronos quant forecast | 55% | exact two-sided binomial, p < 0.10 | required | 15 | `signal_qualification.py` (`MIN_ACCURACY`, `SIGNIFICANCE_P_VALUE`, `beats_naive_baseline`, `MIN_OBSERVATIONS`) |
| ML signal engine (pooled logistic) | 60% (on buy-precision, not raw accuracy) | — (no significance test; accuracy floor only) | not implemented | 30 | `ml_signal_engine.py` (`ModelConfig.minimum_validated_accuracy`, `minimum_observations`) |

"Beats naive baseline" (added after EFERT's real record cleared accuracy and significance
but still lost to trivially predicting its test window's own trend, see "Current models: real
status" below): the track record's accuracy must exceed always guessing the window's own
majority realized direction, computed per ticker by `build_validation_record.py`. A record
can be statistically significant against a 50/50 coin flip purely because the market moved
one direction during the test window, not because the model out-forecasts that movement --
this catches exactly that case instead of treating "significant" as sufficient on its own.

The ML signal engine's gate is weaker than Kronos's (no significance test, no naive-baseline
check) — noted here as a real gap, not something to quietly leave inconsistent. Before
`ml_signals_enabled` is ever considered, that gate should be brought up to the same two
checks the Kronos path already has, or an explicit written reason recorded here for why it
doesn't need them.

## Required backtesting period

No fixed calendar length — "enough real, non-overlapping, walk-forward observations to
clear the significance test above" is the actual bar, and it varies by how much genuine
history a ticker has. What's required, structurally:

- Anchors must be **genuinely out-of-sample**: not sitting in whatever data influenced
  checkpoint/model selection. This session found the Kronos fine-tune's original
  train/val split (`config_psx_scoped.yaml`: `train_ratio: 0.9, val_ratio: 0.1,
  test_ratio: 0.0`) had no such held-out slice at all — see
  `true_holdout_eval.py` and its results (`true_holdout_results.json`) for the corrected
  methodology: only anchors dated after the fine-tune's actual data export cutoff count.
- Anchors must be checked against a **naive baseline** (e.g. "always predict the trend"),
  not just against 50/50 chance — a model can beat chance and still lose to the trivial
  baseline in a one-directional market window, which is exactly what the true-holdout run
  found for FFC/LUCK/EFERT this session.
- Re-validation is required whenever the underlying price history changes materially
  (a corporate-action repair, a newly-discovered data-corruption fix) — this session's
  MARI/LUCK/KOHC price corrections are exactly this trigger, and the walk-forward record
  (`walk_forward_validation.json`) was rebuilt after them, not left stale.

## Current models: real status

Not aspirational — this is what was actually measured this session, and it is the reason
both `public_signals_enabled` and `ml_signals_enabled` should stay `False` until the
underlying accuracy problem is addressed, independent of any process fix in this document:

- **Kronos, 40-anchor walk-forward (393 total anchors, 8 tickers)**: no ticker clears both
  the accuracy and significance bars. Closest: EFERT (58.3%, p=0.31, not significant).
  FFC is significantly *worse* than chance (35.9%, p=0.053) — correctly rejected by the
  accuracy floor regardless of that inverted significance. See `walk_forward_validation.json`.
- **Kronos, true holdout (41 genuinely-unseen anchors, FFC/EFERT/LUCK)**: no ticker beats a
  naive trend-following baseline in the tested window. See `true_holdout_results.json`.
- **ML signal engine (pooled, 31 symbols, 109,906 walk-forward observations)**: ROC AUC
  0.523 (0.5 = no skill). Buy precision 48.3%, below its own 60% floor — correctly gated
  to `NO SIGNAL` for every symbol.

**What this does and doesn't establish.** The precise, defensible claim is: *this specific
implementation, on this specific data, has failed to demonstrate a statistically significant
predictive edge.* It is not evidence that PSX price/volume data carries no predictive
information at all.

Phase 1 (data integrity) is now substantially more complete than when the numbers above were
measured: every one of the 272 securities with any price history was audited
(`scripts/audit_price_discontinuities.py`), and every symbol with a severe (>=50%) single-day
move was cross-checked against a fresh re-scrape (`scripts/verify_and_repair_discontinuities.py`)
-- 59 symbols / 24,803 rows of genuinely corrupted data repaired, 22 symbols' real,
fresh-confirmed corporate actions recorded (`corporate_action` went from a handful of ingested
dividend/merger rows to 65, including 46 newly-detected splits -- still `verified=False`,
algorithmically detected against a fresh scrape rather than cross-checked against an actual
PSX announcement, but confirmed-real in the sense that matters for price continuity). Zero
symbols remained unresolved after the full pass. Not yet done: the 193 of 465 tracked
companies with no price history at all (nothing to audit without first backfilling them,
a decision deferred earlier this session -- see the fertilizer+cement-only backfill scoping),
and cross-referencing the 46 unverified splits against real PSX announcements.

**Update, same day: re-ran on the repaired data.** Only MARI's underlying prices actually
changed enough to matter (LUCK's Phase 1 check found zero disagreements against fresh data --
its record was already sound); MARI can no longer be evaluated at all -- its real 2024-09-16
split leaves too little post-split history (~200 trading days, below Kronos's 286-bar
minimum) given its price data is frozen outside the fertilizer+cement live-pricing scope.
The other 6 tickers' organically-grown anchor counts (53-92, driven by how many times this
script has been rerun across the session, not a fixed design) were otherwise unaffected.

Re-running surfaced a second, more serious gap than "not enough data" -- one in the gate
itself, not just the numbers. EFERT's real record reached 60.8% accuracy over 74 anchors,
p=0.081 (significant vs. random) -- clearing every check `signal_qualification.py` had.
It would have qualified as a real BUY signal. But 68.9% of EFERT's anchors in that window
realized negative: trivially always predicting "down" scores 68.9%, beating the model
outright. The significance was explained by the test window's own trend, not by the model
out-forecasting it -- exactly the trap `true_holdout_eval.py`'s results had already caught
for FFC/LUCK on a different (genuinely-unseen) window, now found inside the walk-forward
path too. Fixed by adding a `beats_naive_baseline` check (`build_validation_record.py`
computes it, `signal_qualification.py` now requires it) -- a track record must beat trivially
predicting its own window's dominant direction, not just beat a 50/50 coin flip. Covered by
a real test suite now too (`tests/test_signal_qualification.py`, all 10 gate branches).
With this fixed, current status: no ticker qualifies. EFERT and FFC are both significant vs.
random and both lose to their own naive baseline; the rest don't clear accuracy or
significance at all. See `walk_forward_validation.json` for exact per-ticker numbers.

This is a stronger, not weaker, confirmation of the original finding: it took a real second
data-integrity pass *and* a real second look at the gate's own logic to be confident there's
still no validated edge here -- not a coincidence found once and left unquestioned.

**Update, 2026-08-25: root-cause diagnostic on the "no edge" finding, plus a third,
independent check.** "No ticker qualifies" answers *whether* there's a validated edge, not
*why* -- open question was whether that's a training/capacity problem (Kronos-mini, 5 epochs,
predictor LR 1e-6 -- a light touch, see `config_psx_scoped.yaml`) or something more
fundamental. `diagnose_signal.py` re-used the existing 511 walk-forward anchor results (zero
new model inference) to check:

- Pooled correlation between the model's continuous prediction and realized return: r=0.061,
  Spearman rho=-0.051 -- indistinguishable from zero. Confirms the binary-accuracy null result
  isn't an artifact of thresholding a real continuous signal at 50%.
- The model's prediction is consistently *negatively* correlated with trailing 5-day momentum
  (pooled r=-0.366, negative on 7 of 8 tickers) -- the fine-tune has learned a genuine,
  structural mean-reversion bias, not pure noise. This is a real, identifiable pattern, and it
  qualitatively matches the market's own behavior in this window (trailing-momentum's own
  correlation with realized return is also mostly negative, pooled r=-0.177).
- That raised the obvious next question: is the market-wide short-term-reversal effect (a
  well-documented classical factor, zero Kronos involvement -- literally "bet against the
  trailing move") itself exploitable here, independent of whether this specific fine-tune
  expresses it well? Tested on the identical anchors/tickers with the identical significance
  test and naive-baseline gate this document already requires. Per-ticker, 2 of 8 (LUCK
  p=0.038, OGDC p=0.013) clear p<0.10 -- but testing 8 tickers separately at alpha=0.10
  produces ~0.8 false positives by chance alone (the same multiple-comparisons trap the
  naive-baseline gate exists to catch, one level up), so that alone isn't evidence. The single,
  pre-specified pooled test across all 511 anchors: 278/511 = 54.4% vs random, p=0.0515
  (borderline) -- but against the pooled naive baseline (290/511 = 56.8%), the reversal factor
  **does not win**. Same trap as EFERT, again: marginal significance vs. chance, still loses to
  the trivial baseline.

**Conclusion:** this is a third, methodologically independent line of evidence for "no
validated edge," not a restatement of the first two. It also answers the "is this fixable with
more training" question in the negative for the current approach specifically: the model's
mean-reversion bias is directionally sensible, but even its purest, best-case classical form
doesn't clear the real bar on this data/window, so more epochs on the same task framing
(5-day price direction from OHLCV alone) is unlikely to be the fix. Genuine next steps, not
attempted here because each is a real compute or product-scope commitment, not a quick
follow-up: testing other horizons (1-day, 20-day) comprehensively (report all tried, not the
best one -- anything less repeats this exact mistake at a different layer); expanding beyond
these 8 tickers to see if a cross-sectional, not time-series, signal exists; or reconsidering
whether Kronos's product role should be a standalone BUY/SELL signal generator at all, versus
context/input to a human-reviewed process. See `diagnose_signal.py` for the exact methodology.

## Who approves public activation

**Not filled in.** This is a real organizational decision (who at the project — presumably
the project owner, possibly plus outside counsel per `rights_matrix.template.md`'s
Capital Stake/PSX licensing question) that this document cannot make on its own. Record
here once decided: name/role, and whether one approver suffices or a second reviewer is
required for any of the three flags in "What the system is allowed to display."

## Required documentation, per activation decision

A flag flip (or a new model's first activation) must be recorded as a dated entry below,
not just as a git commit message — a commit explains code, not a business/compliance
decision. Minimum fields, matching the user's own requested shape:

| Field | Required |
|---|---|
| Model name + version | e.g. `psx_scoped_8_daily` fine-tune checkpoint identifier, or `ml_signal_engine.py`'s `MODEL_VERSION` |
| Approval date | |
| Reviewer(s) | matches "Who approves public activation" above |
| Validation metrics at approval time | accuracy, p-value, n, exact numbers — not "looked fine" |
| Backtesting period covered | date range, anchor count, whether true-holdout or contaminated walk-forward |
| Risk disclosures shown alongside | which disclaimer text, on which surfaces |
| Flags changed | which of the three, from/to |

No rows exist yet — nothing has been approved.

## Audit logs

Not yet implemented. What this needs, concretely: every change to
`public_signals_enabled` / `ml_signals_enabled` / `public_launch_enabled` (env var or
`.env` change) should be traceable to who changed it and when, separate from application
logs. `MlSignalScore` and `SignalScore` rows already carry `is_public` and
`model_version`/`policy_version` per-row (real, existing), which is necessary but not
sufficient — it shows what was public at compute time, not who decided the flag should be
`True` at all. A minimal fix: a `flag_change_log` table (settings key, old value, new
value, changed_by, changed_at, reason) written whenever these flags are toggled in a
running environment, not just in `.env` at deploy time.

## Model versioning

Partially real already:
- `ml_signal_engine.py`: `MODEL_VERSION = 1`, stored on every `MlSignalScore` row.
- `signal_engine.py`'s rules-based composite: `policy_version` on `SignalScore` (per
  earlier project work, not touched this session).
- Kronos: the fine-tune checkpoint is identified by `exp_name: "psx_scoped_8_daily"` in
  `config_psx_scoped.yaml`, but this string is **not** currently stored on
  `quant_forecast.py`'s output or on `walk_forward_validation.json` — if the checkpoint is
  ever retrained, there's no field recording which checkpoint produced which stored
  validation result. Gap: add a `model_checkpoint_id` (or similar) to both.

## Risk disclosures

Already real and in force, not aspirational:
- `research_disclaimer.md` — shown per `PUBLIC_SIGNALS_ENABLED`.
- `SCORE_DISCLAIMER` (`app/api/comparison.py`) — attached to every row with a
  score, internal-only framing.
- `signal_qualification.py`'s `reason` field — a specific, numeric explanation
  (not generic boilerplate) for every qualified-or-not determination, shown directly in
  the Quant Forecast UI.

Gap: none of these currently distinguish "this specific number is a raw model estimate"
from "this specific number is a qualified signal" *visually* as strongly as the
underlying data does — the frontend badge (`NO_SIGNAL`/`BUY`/etc.) carries the real
distinction, but a reader skimming past the badge to the raw probability number could
still read it as more validated than it is. Worth a design pass before any public
activation, not before.
