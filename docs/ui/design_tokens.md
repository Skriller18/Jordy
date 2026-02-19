# UI Tokens and Component Guidelines

## Design Principles
1. Trust first: emphasize clarity, provenance, and risk visibility.
2. Beginner friendly: plain-language labels with optional advanced detail.
3. Dense but readable: structured cards over long text blocks.

## Token Set v0.1

### Typography
- font.family.display: "Space Grotesk", sans-serif
- font.family.body: "Source Sans 3", sans-serif
- font.size.xs: 12
- font.size.sm: 14
- font.size.md: 16
- font.size.lg: 20
- font.size.xl: 28
- font.weight.regular: 400
- font.weight.medium: 500
- font.weight.bold: 700

### Color
- color.bg.base: #F4F6F8
- color.bg.surface: #FFFFFF
- color.bg.panel: #EAF0F6
- color.text.primary: #102A43
- color.text.secondary: #486581
- color.border.muted: #D9E2EC
- color.brand.primary: #0B6E99
- color.brand.accent: #F0B429
- color.signal.positive: #1F9D55
- color.signal.negative: #D64545
- color.signal.warning: #F29D35
- color.signal.neutral: #7B8794

### Spacing
- space.2xs: 4
- space.xs: 8
- space.sm: 12
- space.md: 16
- space.lg: 24
- space.xl: 32

### Radius and Elevation
- radius.sm: 6
- radius.md: 10
- radius.lg: 14
- shadow.card: 0 2px 8px rgba(16, 42, 67, 0.08)

## Core Components

### Ask Bar
- Includes prompt input, market selector, horizon selector, submit button.
- Must preserve latest selected market/horizon in session state.

### Score Card
- Fields: composite, quant, qual, recommendation chip.
- Must include data freshness tag and confidence indicator.

### Drivers Card
- Two columns: positives and negatives.
- Each item can open source evidence.

### Risk Card
- Group by risk type: valuation, leverage, volatility, regulatory, sentiment.
- Show severity badge and short action note.

### Evidence List
- Fields: source, title, date, relevance tag.
- Must display if source fetch failed or is stale.

### Ideas Table
- Columns: ticker, sector, composite, recommendation, volatility, updated_at.
- Supports sorting, filtering, and row details.

## Accessibility Rules
1. Minimum contrast ratio 4.5:1 for body text.
2. Do not encode meaning by color only; include icon/text badge.
3. Keyboard navigation for all interactive controls.
4. Focus outlines always visible.
5. Tap targets minimum 44x44 px on mobile.
