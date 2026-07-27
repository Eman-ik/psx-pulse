/**
 * Maps a computed sentiment_score (see backend/app/etl/sentiment.py — keyword-based, not
 * ML/LLM) to a display label. `score == null` means the classifier hasn't run on that row;
 * `score === 0` is a real "neutral" classification, not a missing value — keep those distinct.
 */
export function sentimentLabel(score: number | null): string | null {
  if (score == null) return null;
  if (score > 0.2) return "Positive";
  if (score < -0.2) return "Negative";
  return "Neutral";
}

export const SENTIMENT_TONE: Record<string, string> = {
  Positive: "bg-positive/10 text-positive",
  Negative: "bg-negative/10 text-negative",
  Neutral: "bg-muted/10 text-muted",
};
