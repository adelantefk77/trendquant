---
name: Empirical Trend Architecture
colors:
  surface: '#10141a'
  surface-dim: '#10141a'
  surface-bright: '#353940'
  surface-container-lowest: '#0a0e14'
  surface-container-low: '#181c22'
  surface-container: '#1c2026'
  surface-container-high: '#262a31'
  surface-container-highest: '#31353c'
  on-surface: '#dfe2eb'
  on-surface-variant: '#c2c6d6'
  inverse-surface: '#dfe2eb'
  inverse-on-surface: '#2d3137'
  outline: '#8c909f'
  outline-variant: '#424754'
  surface-tint: '#adc6ff'
  primary: '#adc6ff'
  on-primary: '#002e6a'
  primary-container: '#4d8eff'
  on-primary-container: '#00285d'
  inverse-primary: '#005ac2'
  secondary: '#4edea3'
  on-secondary: '#003824'
  secondary-container: '#00a572'
  on-secondary-container: '#00311f'
  tertiary: '#ffb95f'
  on-tertiary: '#472a00'
  tertiary-container: '#ca8100'
  on-tertiary-container: '#3e2400'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#d8e2ff'
  primary-fixed-dim: '#adc6ff'
  on-primary-fixed: '#001a42'
  on-primary-fixed-variant: '#004395'
  secondary-fixed: '#6ffbbe'
  secondary-fixed-dim: '#4edea3'
  on-secondary-fixed: '#002113'
  on-secondary-fixed-variant: '#005236'
  tertiary-fixed: '#ffddb8'
  tertiary-fixed-dim: '#ffb95f'
  on-tertiary-fixed: '#2a1700'
  on-tertiary-fixed-variant: '#653e00'
  background: '#10141a'
  on-background: '#dfe2eb'
  surface-variant: '#31353c'
typography:
  display-lg:
    fontFamily: Space Grotesk
    fontSize: 48px
    fontWeight: '600'
    lineHeight: 56px
    letterSpacing: -0.03em
  display-lg-mobile:
    fontFamily: Space Grotesk
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Space Grotesk
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Space Grotesk
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Space Grotesk
    fontSize: 20px
    fontWeight: '500'
    lineHeight: 28px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: -0.005em
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 26px
    letterSpacing: -0.01em
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 22px
    letterSpacing: 0em
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 18px
    letterSpacing: 0em
  data-lg:
    fontFamily: JetBrains Mono
    fontSize: 24px
    fontWeight: '500'
    lineHeight: 32px
    letterSpacing: -0.02em
  data-md:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: -0.01em
  data-sm:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
    letterSpacing: 0em
  label-caps:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 14px
    letterSpacing: 0.06em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-desktop: 1.5rem
  margin: 1rem
  margin-desktop: 2.5rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

## Brand & Style
The design system establishes an academic, disciplined fintech interface tailored for quantitative cryptocurrency allocation. It deliberately avoids speculative hype, gamified visual cues, and aggressive marketing tropes common in retail crypto applications. The tone is sober, analytical, and grounded in empirical research (notably momentum literature like Han, Kang & Ryu), emphasizing systematic trend-following, risk budgeting, capital preservation, and drawdown minimization across Bitcoin and Ethereum.

The visual style blends **Technical Minimalism** and **High-Density Engineering** (drawing cues from Linear, TradingView, and Bloomberg Terminal). It relies on a pitch-black and graphite canvas, microscopic precision borders, structural alignment, and monospaced quantitative typography. Interface elements behave like surgical instruments: muted by default, illuminating only when systematic states change (e.g., trend confirmation, risk trigger, rebalancing execution).

## Colors
The palette is built for long-duration viewing in analytical environments, using a foundational obsidian scale, clinical data accents, and restrained semantic triggers.

- **Base Canvas & Surfaces:**
  - Base Background: `#080A0E` (Deep space obsidian)
  - Surface Primary / Panels: `#0D1117` (Subdued graphite)
  - Surface Elevated / Modals / Popovers: `#161B22`
  - Subtle Borders & Separators: `#21262D` and `#30363D`
- **Data & Brand Accents:**
  - **Primary (Analytical Indigo / Blue - `#3B82F6`):** Governs systematic telemetry, baseline trend indicators, benchmark comparisons, and non-directional structural data.
  - **Secondary (Algorithmic Emerald - `#10B981`):** Represents long exposure, verified trend regime, positive alpha, and Sharpe enhancement. Used strictly for confirmed systematic conditions, never for decorative celebratory flair.
  - **Tertiary (Sovereign Amber - `#F59E0B`):** Denotes signal transitions, volatility warnings, cash rebalancing pending, and maximum drawdown threshold proximity.
- **Text & Numeric Tiers:**
  - High Contrast (Values, Headings): `#F0F6FC`
  - Medium Contrast (Body, Metric Labels): `#8B949E`
  - Low Contrast (Disabled, Micro-captions): `#484F58`

## Typography
The system executes a deliberate tri-font hierarchy:
1. **Space Grotesk** serves macro titles and executive structural framing, injecting a modern, architectural geometry without sacrificing sobriety.
2. **Inter** handles continuous narrative, methodological documentation, parameter definitions, and long-form research citations.
3. **JetBrains Mono** governs all numerical data, tabular metrics, SMA indicators, Sharpe ratios, hash values, timestamps, and status chips. 

All tabular financial statistics must leverage tabular figures (`font-variant-numeric: tabular-nums`) to ensure vertical grid alignment across real-time dynamic rerenders.

## Layout & Spacing
The layout model employs a strict 12-column responsive grid engineered for dense financial data synthesis.

- **Desktop (>= 1280px):** 12-column grid, 1.5rem (`24px`) gutters, 2.5rem (`40px`) outer safety margin. Dashboard panels favor side-by-side analytical comparisons (e.g., Regime Status | Asset Allocation Matrix | Chart Engine).
- **Tablet (768px - 1279px):** 8-column layout, 1rem (`16px`) gutters, 1.5rem (`24px`) outer margin. Side-by-side matrices convert to dual-stacked analytical cards.
- **Mobile (< 768px):** 4-column layout, 0.75rem (`12px`) gutters, 1rem (`16px`) canvas margin. Full reflow into vertical, sequential blocks prioritizing current asset exposure and system health.

Spacing strictly follows a 4px/8px modular base rhythm. Component interiors favor condensed padding (`space-xs` to `space-md`) to maximize vertical data visibility without forcing unnecessary viewports scrolls.

## Elevation & Depth
Depth is created through tonal surface stacking and hairline boundary structures rather than traditional floating drop shadows.

- **Surface Tiers:**
  - *Layer 0 (Canvas):* `#080A0E` (Base background).
  - *Layer 1 (Data Cards, Grid modules):* `#0D1117`, enclosed by a 1px border of `#21262D`.
  - *Layer 2 (Overlays, Flyouts, Metric Drawers):* `#161B22`, reinforced with a 1px border of `#30363D`.
- **Shadow Philosophy:**
  - Ambient shadows are reserved exclusively for floating modal dialogues and floating chart cursor crosshairs: `0 8px 32px -4px rgba(0, 0, 0, 0.65)`.
  - Card hover states do not physically elevate via Y-axis translation. Instead, elevation feedback is signaled via a crisp, hairline border shift from `#21262D` to `#3B82F6` or `#30363D`.

## Shapes
The design adopts a sharp, architectural shape system (`roundedness: 1`). 
- Default interactive modules, cards, and input fields utilize `0.25rem` (`4px`) corner radii.
- Larger parent dashboard containers and charting frames step up to `0.5rem` (`8px`) (`rounded-lg`).
- Circular pill geometry is strictly forbidden for interactive containers and cards; it is permitted only for micro-status indicators (e.g., active telemetry pulses or status dot indicators).

This controlled angularity reflects precision engineering, data tables, and high-frequency analytical terminals.

## Components

### Buttons & Interactive Triggers
- **Primary Action (Execute / Connect):** Solid `#3B82F6` with `#FFFFFF` text. Font: `JetBrains Mono`, 12px uppercase, medium weight. Height: 36px. Border radius: 4px. No soft blur; crisp single-pixel interaction state.
- **Secondary / Ghost (Filter / Timeline Selector):** Transparent background, 1px border `#30363D`, text `#8B949E`. Hover states shift text to `#F0F6FC` and border to `#8B949E`.
- **Systematic Switch / Toggle (Cash vs. In-Market):** Segmented horizontal rail in `#0D1117` with 1px border `#21262D`. Active segment highlights in `#161B22` with a 1px border `#3B82F6`.

### Data Cards & Metric Displays
- **Key Performance Indicator (KPI) Tile:** Bordered graphite container housing:
  - Metric label in `label-caps` (`#8B949E`).
  - Empirical value in `data-lg` (`JetBrains Mono`, `#F0F6FC`).
  - Contextual delta (e.g., Sharpe vs. Buy & Hold, Max DD reduction) indicated via monospaced micro-badges tagged in `#10B981` (Outperforming) or `#8B949E` (Neutral).

### Status Badges & Regime Chips
- Compact, flat badge with 1px border.
- *Bullish Regime (Above 200 SMA):* Background `rgba(16, 185, 129, 0.08)`, border `rgba(16, 185, 129, 0.3)`, text `#10B981`.
- *Defensive / Cash Preservation Regime:* Background `rgba(245, 158, 11, 0.08)`, border `rgba(245, 158, 11, 0.3)`, text `#F59E0B`.

### Tables & Asset Lists
- Borderless table interiors separated solely by 1px horizontal borders (`#21262D`).
- Row hover reveals subtle background tint `#161B22`.
- Numeric data columns (24h Volume, Distance to 50 SMA, Realized Volatility) strictly align right using `data-md` or `data-sm` with tabular numerals.

### Charts & Technical Visualizations
- Background: `#080A0E` continuous canvas.
- Gridlines: `#161B22` dashed at 1px.
- Trend Indicators:
  - 50 SMA: Solid `#3B82F6` (1.5px width).
  - 100 SMA: Solid `#8B5CF6` (1.5px width).
  - 200 SMA: Solid `#F59E0B` (2px width).
- Interactive crosshairs render fine dotted lines (`#484F58`) with floating monospaced price/date badges docked along the axes.

### Form Inputs & Parameter Sliders
- Background: `#080A0E`, 1px border `#30363D`, text `#F0F6FC` in `JetBrains Mono`. Focus rings are replaced by a direct border color transition to `#3B82F6` with zero outer shadow glow.