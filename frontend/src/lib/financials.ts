export function latestValue(series: { period_end: string; value: number }[] | undefined): number | null {
  if (!series || series.length === 0) return null;
  return [...series].sort((a, b) => a.period_end.localeCompare(b.period_end)).slice(-1)[0].value;
}
