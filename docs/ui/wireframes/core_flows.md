# Low-Fidelity Wireframes (Core Flows)

## 1) First-Run Onboarding

### Desktop
```
+--------------------------------------------------------------+
| Jordy                                                        |
| "Research assistant for US + India equities"                |
|                                                              |
| [Market: USA v] [Horizon: Long Term v] [Risk: Balanced v]   |
|                                                              |
| Suggested prompts:                                           |
| - Analyze a stock                                            |
| - Compare 2 stocks                                           |
| - Find sector ideas                                          |
|                                                              |
| [Start with: Analyze TCS in India]                           |
+--------------------------------------------------------------+
```

### Mobile
```
+---------------------------+
| Jordy                     |
| Market [USA v]            |
| Horizon [Long v]          |
| Risk [Balanced v]         |
|---------------------------|
| Suggested prompts         |
| [Analyze a stock]         |
| [Compare stocks]          |
| [Find ideas]              |
|---------------------------|
| [Start]                   |
+---------------------------+
```

## 2) Analyze Stock Flow

### Desktop
```
+---------------------------+--------------------------------------+
| Chat                      | Analysis Panel                        |
|---------------------------|--------------------------------------|
| User: Analyze MSFT        | Verdict: Watchlist                   |
| Jordy: ...                | Composite: 66.8                      |
|                           | Quant: 55.9 | Qual: 83.1            |
| [Prompt input............]| Positives | Negatives | Risks       |
| [Send]                    | Evidence (news/filings/freshness)   |
+---------------------------+--------------------------------------+
```

### Mobile
```
+---------------------------+
| Chat + Input              |
| [Analyze MSFT ...] [Send] |
|---------------------------|
| Tabs: Summary | Risks | Evidence |
| Verdict + Score           |
| Key Drivers               |
+---------------------------+
```

## 3) Compare Stocks Flow

### Desktop
```
+--------------------------------------------------------------+
| Compare: [MSFT] [AAPL] [NVDA] [Horizon: Long] [Run]         |
|--------------------------------------------------------------|
| Rank | Ticker | Composite | Quant | Qual | Risk Tag          |
| 1    | MSFT   | 66.8      | 55.9  | 83.1 | Medium            |
| 2    | AAPL   | 64.1      | 51.8  | 82.5 | Medium            |
| 3    | NVDA   | ...                                        ... |
|--------------------------------------------------------------|
| Why #1 > #2: concise differential explanation                |
+--------------------------------------------------------------+
```

### Mobile
```
+---------------------------+
| Compare                   |
| MSFT, AAPL, NVDA [Run]    |
|---------------------------|
| #1 MSFT 66.8              |
| #2 AAPL 64.1              |
| #3 NVDA ...               |
| [View Why]                |
+---------------------------+
```

## 4) Watchlist Flow

### Desktop
```
+--------------------------------------------------------------+
| Watchlist: [Add Symbol]                                      |
|--------------------------------------------------------------|
| Ticker | Last Score | 7d Delta | Alert | Last Updated        |
| TCS    | 68.3       | +1.2     | None  | 2026-02-19          |
| TSLA   | 43.4       | -3.9     | Risk↑ | 2026-02-19          |
|--------------------------------------------------------------|
| Selected item detail: trend + changed drivers                |
+--------------------------------------------------------------+
```

### Mobile
```
+---------------------------+
| Watchlist [+]             |
|---------------------------|
| TCS 68.3  (+1.2)          |
| TSLA 43.4 (Risk↑)         |
|---------------------------|
| Tap item -> detail sheet  |
+---------------------------+
```

## Handoff Notes
- Keep analysis panel structure stable across intents to build trust.
- Keep chat and structured data synchronized on same event timestamp.
- Mobile defaults to tabbed cards to reduce scroll depth.
