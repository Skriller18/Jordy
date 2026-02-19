# Jordy Intent Catalog and Response Contracts

## Intent 1: Analyze Stock
- User examples:
  - "Analyze TCS for long-term in India"
  - "Should I study AAPL now?"
- Required input:
  - Ticker, market/country, horizon.
- Optional input:
  - Risk preference, portfolio context.
- Jordy response contract:
1. Verdict (strong candidate/watchlist/avoid).
2. Composite score + quant/qual split.
3. Top positives (max 5).
4. Top negatives (max 5).
5. Risk notes.
6. Evidence summary (news/filings/data freshness).
7. Suggested next action.

## Intent 2: Compare Stocks
- User examples:
  - "Compare MSFT, AAPL, NVDA for 1-3 years"
  - "Which is better between TCS and Infosys?"
- Required input:
  - 2+ tickers, common horizon.
- Jordy response contract:
1. Ranked comparison table.
2. Strength/weakness per stock.
3. Why rank #1 beat rank #2.
4. Sensitivity note (what could change ranking).
5. Recommended follow-up analysis.

## Intent 3: Sector Idea Scan
- User examples:
  - "Best banking ideas in India"
  - "Find US AI software names with balanced risk"
- Required input:
  - Sector/industry, market, horizon.
- Jordy response contract:
1. Top candidates list with filters shown.
2. Risk-diversified shortlist.
3. Outliers with caution tags.
4. Coverage caveats (missing names/data).

## Intent 4: Explain Risk
- User examples:
  - "Explain why this is risky"
  - "What can go wrong with this thesis?"
- Required input:
  - Existing analyzed ticker.
- Jordy response contract:
1. Risk taxonomy (valuation, leverage, regulatory, sentiment, volatility).
2. Severity and confidence per risk.
3. What to monitor next (events/metrics).
4. De-risking alternatives.

## Intent 5: Watchlist Update
- User examples:
  - "Add TCS and MSFT to watchlist"
  - "What changed since last week?"
- Required input:
  - Watchlist symbol(s).
- Jordy response contract:
1. Change summary since last snapshot.
2. Score/risk deltas.
3. Alert flags triggered.
4. Suggested action (hold/watch/remove/research more).

## Fallback Rules
1. Missing ticker: ask one clarifying question and suggest examples.
2. Missing horizon: default to long term and disclose default.
3. Insufficient data: return partial analysis with explicit missing fields.
4. Source failure: return warning with retry suggestion.
5. Compliance boundary: avoid direct "buy/sell" phrasing; keep research framing.
