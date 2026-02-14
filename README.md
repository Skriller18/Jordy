# Equity Research Bot (US + India)

This is a starter scaffold for a junior-level stock research bot that combines:
- Quantitative scoring (valuation, growth, quality, momentum, risk)
- Qualitative scoring (management, moat, governance, regulatory risk, sentiment)
- Ranked recommendations with explicit reasons and risk notes
- Live ingestion pipeline for US/India tickers (market/fundamental/news/filing signals)

## Important
This project is for research and education. It is **not** investment advice.

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
python scripts/run_demo.py
uvicorn app.api:app --reload
```

Then open:
- `http://127.0.0.1:8000/docs`

## API

### `POST /v1/rank`
Ranks the provided companies.

Example body:

```json
{
  "horizon": "long_term",
  "companies": []
}
```

### `GET /v1/sample`
Returns a prefilled sample universe across US and India.

### `POST /v1/ingest-and-rank`
Ingests live signals for ticker targets, converts them into model features, then ranks.

Example body:

```json
{
  "horizon": "long_term",
  "news_items": 10,
  "targets": [
    { "ticker": "AAPL", "country": "USA" },
    { "ticker": "MSFT", "country": "USA" },
    { "ticker": "TCS", "country": "INDIA", "yahoo_suffix": ".NS" }
  ]
}
```

### CLI Live Run

```bash
python scripts/run_ingest.py --targets AAPL:USA,MSFT:USA,TCS:INDIA --horizon long_term
```

## Data Source Notes
- US/India market + fundamental features: Yahoo Finance public endpoints.
- US filing risk signal: SEC EDGAR submissions (`sec.gov` and `data.sec.gov`).
- News sentiment proxy: Google News RSS headlines.

Set a proper user agent (recommended, especially for SEC):

```bash
export EQUITY_BOT_USER_AGENT=\"your-app-name/0.1 (email@domain.com)\"
```

## Next Build Steps
- Add NSE/BSE-specific filing + announcement adapters to reduce dependency on global providers.
- Add a scraper worker with source allowlist and robots/legal checks.
- Add backtesting and model calibration per market and horizon.
- Add portfolio constraints and allocation engine.
