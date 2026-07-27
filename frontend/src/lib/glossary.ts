/** Plain-language, beginner-friendly explanations for metric labels shown around the app.
 * Intentionally short (one sentence) and jargon-free where possible — this is a glossary
 * tooltip, not a finance course. Keyed by the exact label text used at the call site.
 */
export const GLOSSARY: Record<string, string> = {
  "Market Cap": "Total market value of all outstanding shares — share price × shares outstanding.",
  "Trailing P/E": "Price-to-Earnings ratio: how many years of current profit it would take to 'pay back' the share price at today's price. Lower can mean cheaper, but only compare within the same sector.",
  "Dividend Yield": "The annual dividend paid per share, as a percentage of the current share price.",
  EPS: "Earnings Per Share — profit after tax divided by the number of shares outstanding.",
  ROE: "Return on Equity — how efficiently a company turns shareholders' own money into profit.",
  ROA: "Return on Assets — how efficiently a company turns everything it owns (assets) into profit.",
  "Debt-to-Equity": "Total liabilities divided by shareholder equity. Higher means more of the business is funded by debt rather than owners' capital.",
  "Current Ratio": "Current assets divided by current liabilities — a rough check on whether a company can cover its bills due within a year.",
  "Free Float": "The percentage of shares actually available for public trading, excluding stakes held by founders, insiders, or the government.",
  "Volume (last session)": "The number of shares that changed hands in the most recent trading session.",
  "Beta (vs KSE-100)": "How much a stock tends to move relative to the wider market (the KSE-100 index). Above 1 means historically more volatile than the market; below 1 means less.",
  "RSI (14)": "Relative Strength Index — a momentum gauge from 0 to 100 based on the last 14 sessions. Traditionally, above 70 is read as 'overbought', below 30 as 'oversold'.",
  MACD: "Moving Average Convergence Divergence — compares two moving averages of price to gauge trend direction and momentum. The 'signal' line smooths it further.",
  "ATR (14)": "Average True Range — the typical size of a stock's daily price swing over the last 14 sessions, i.e. how volatile it's been recently.",
  "SMA 20": "20-day Simple Moving Average — the average closing price over the last 20 trading sessions, a common trend reference line.",
  "52-Week Range": "The lowest and highest closing price over roughly the past year of trading.",
  "Day Change": "How much the price has moved since the previous trading session's close, in percent.",
};
