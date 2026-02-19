# Jordy Information Architecture

## Navigation Model
1. Dashboard
2. Analysis Workspace
3. Ideas Explorer
4. Watchlist
5. Settings

## Screen Responsibilities

### Dashboard
- Entry point for new session.
- Contains market toggle (USA/India), horizon toggle, and quick intent buttons.
- Shows recent analyses and watchlist alerts.

### Analysis Workspace
- Left pane: conversation timeline (Ask Jordy).
- Right pane: structured analysis cards.
- Card order: verdict -> scores -> drivers -> risks -> evidence -> next actions.

### Ideas Explorer
- Table view of ranked opportunities.
- Filters: market, sector, score threshold, recommendation, volatility range.
- Row click opens detail drawer tied to Analysis Workspace layout.

### Watchlist
- Saved symbols with latest score, change, and alerts.
- Supports add/remove and priority pinning.
- Shows event timeline (score drift, sentiment flips, risk spikes).

### Settings
- Preferences: default market, default horizon, risk preference.
- Data disclosure settings and compliance disclaimer visibility.

## Route Map (Proposed)
- `/` -> Dashboard
- `/analysis` -> Analysis Workspace
- `/ideas` -> Ideas Explorer
- `/watchlist` -> Watchlist
- `/settings` -> Settings

## State Flow
1. User submits intent in Dashboard or Analysis Workspace.
2. Frontend calls backend API (`/v1/rank` or `/v1/ingest-and-rank`).
3. Response normalized to session state.
4. Session state hydrates chat transcript + cards + table rows.
5. Watchlist actions create persistent user state updates.

## Global UI State
- selected_market
- selected_horizon
- active_ticker
- active_comparison_set
- session_messages
- latest_rank_results
- watchlist_items
- warnings

## Cross-Screen Linking
- Dashboard quick action -> Analysis Workspace prefilled prompt.
- Ideas row click -> Analysis Workspace detail mode.
- Watchlist item click -> Analysis Workspace with historical delta context.
