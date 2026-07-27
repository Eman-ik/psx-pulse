"""Keyword-based sentiment classification for corporate announcement headlines.

Deliberately NOT machine-learning/LLM-based: this is a small, fully auditable list of
finance-announcement-relevant positive/negative trigger words matched against the
announcement title only (the underlying PDF document isn't parsed/summarized yet, so this
can't see anything beyond the headline). Most PSX announcement titles are purely procedural
("Notice of Board Meeting", "Transmission of Annual Report") and carry no sentiment at all --
those correctly score 0.0 (neutral), which is a real classification outcome, not a placeholder
for "not yet analyzed". A NULL sentiment_score means the classifier hasn't run on that row yet;
0.0 means it ran and found nothing sentiment-bearing in the title. The two must not be conflated.

Evidence class: "calculated_metric" (see app/db/models/evidence.py) -- a deterministic word
count, not a model. This is not part of the AI signal engine gated by PUBLIC_SIGNALS_ENABLED
(that's buy/hold/sell recommendations); this is a simple headline sentiment tag for a news feed.
"""

import re

POSITIVE_WORDS = [
    "profit",
    "profits",
    "profitable",
    "growth",
    "grew",
    "increase",
    "increased",
    "record",
    "expansion",
    "expand",
    "expands",
    "award",
    "awarded",
    "approval",
    "approved",
    "recovery",
    "upgrade",
    "upgraded",
    "surplus",
    "bonus",
    "improvement",
    "improved",
    "resumption",
    "resume",
    "resumed",
    "successful",
    "achievement",
]

# Deliberately excludes "closure"/"closed": real backfill output on this pilot's 91 real
# announcements showed these are overwhelmingly false positives from PSX's own standard
# securities terminology ("Book Closure", "Closed Period" -- a routine share-transfer-book/
# insider-trading blackout window, not a facility shutdown). "shutdown" below still catches
# genuine operational-closure events without that collision.
NEGATIVE_WORDS = [
    "loss",
    "losses",
    "suspension",
    "suspended",
    "decline",
    "declined",
    "default",
    "resignation",
    "resign",
    "resigns",
    "penalty",
    "penalties",
    "shortfall",
    "delay",
    "delayed",
    "disruption",
    "downgrade",
    "downgraded",
    "termination",
    "terminated",
    "dispute",
    "litigation",
    "fire",
    "accident",
    "explosion",
    "strike",
    "shutdown",
    "cancel",
    "cancelled",
    "cancellation",
    "breach",
    "fraud",
    "investigation",
    "warning",
    "deficit",
]

# Each net keyword hit shifts the score by this much; capped at +/-1.0.
_STEP = 0.5


def _count_matches(text: str, words: list[str]) -> int:
    lowered = text.lower()
    return sum(1 for w in words if re.search(rf"\b{re.escape(w)}\b", lowered))


def classify_sentiment(title: str) -> float:
    """Returns a score in [-1, 1] from an announcement title.

    0.0 means neutral / no sentiment-bearing keywords found -- the expected, correct outcome
    for the large share of purely procedural PSX announcement titles, not a missing value.
    """
    positive = _count_matches(title, POSITIVE_WORDS)
    negative = _count_matches(title, NEGATIVE_WORDS)
    net = positive - negative
    return max(-1.0, min(1.0, net * _STEP))
