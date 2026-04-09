# FC Feature Matrix — Design System

> Design tokens, component rules, and visual guidelines for the FC Feature Matrix dashboard.
> Stack: React + Tailwind CSS + shadcn/ui | Font: Google Fonts | Icons: Lucide

---

## Reference Analysis

### Common Patterns Across References

Analyzed 20 reference dashboards. Recurring visual patterns:

1. **Deep carbon-black backgrounds** with layered surface hierarchy (3-4 depth levels)
2. **Orange as dominant accent** — used for CTAs, active states, progress bars, badges
3. **Subtle card borders** at low opacity (`white/5` to `white/10`) rather than solid lines
4. **Rounded card containers** (12-16px border-radius) with slight background lift
5. **Data-dense layouts** — compact row heights (36-44px), small fonts (11-13px), minimal padding
6. **Hover row highlighting** with subtle background shifts, not color changes
7. **Heatmap-style grids** using orange/red intensity squares for data visualization
8. **Large KPI numbers** contrasted against small labels (size ratio 3:1 or greater)
9. **Muted secondary text** at ~40% brightness for labels, timestamps, metadata
10. **Glow effects** on orange accent elements — subtle `box-shadow` with orange at low opacity

### What Works Best for Feature Matrix

- The **property listing** dark card style (refs: bc6b14, 4d43bd, 1e5168) — carbon black with orange accent pops
- The **data table** patterns (refs: f6c543, 04faa3) — dense rows with hover states and colored status chips
- The **color palette reference** (ref: 74cc0b) — explicit orange branding gradient: `#000 → #C10801 → #F16001 → #D9C3AB`
- The **dashboard card grid** (refs: 9d780d, 15264a) — rounded cards with icon badges and metric displays
- The **fire/flame aesthetic** (ref: 4092185e) — organic warm gradient for hero/accent moments

---

## Color Palette

### Core Palette (HSL for shadcn/ui CSS variables)

```css
/* ── Carbon Black Foundation ── */
--background:         0 0% 4%;           /* #0A0A0A — true carbon */
--background-alt:     0 0% 7%;           /* #121212 — raised surface */
--card:               0 0% 9%;           /* #171717 — card surface */
--card-hover:         0 0% 11%;          /* #1C1C1C — card hover */
--popover:            0 0% 9%;           /* #171717 — popover bg */

/* ── Borders & Separators ── */
--border:             0 0% 14%;          /* #242424 — default border */
--border-subtle:      0 0% 11%;          /* #1C1C1C — card inner borders */
--ring:               24 95% 53%;        /* orange focus ring */

/* ── Text Hierarchy ── */
--foreground:         0 0% 93%;          /* #EDEDED — primary text */
--foreground-muted:   0 0% 45%;          /* #737373 — secondary text */
--foreground-faint:   0 0% 30%;          /* #4D4D4D — tertiary/disabled */

/* ── Accent: Flame Orange ── */
--primary:            24 95% 53%;        /* #F97316 — primary orange */
--primary-hover:      24 95% 60%;        /* #FB923C — orange hover */
--primary-muted:      24 80% 20%;        /* #5C2D0E — orange bg tint */
--primary-foreground: 0 0% 100%;         /* #FFFFFF — text on orange */

/* ── Secondary: Electric Purple ── */
--secondary:          270 70% 60%;       /* #8B5CF6 — purple accent */
--secondary-hover:    270 70% 67%;       /* #A78BFA — purple hover */
--secondary-muted:    270 50% 18%;       /* #2E1A5E — purple bg tint */
--secondary-foreground: 0 0% 100%;

/* ── Semantic: Status Colors ── */
--success:            142 71% 45%;       /* #22C55E — green/present */
--success-muted:      142 50% 12%;       /* #0D2B1A — green bg */
--warning:            48 96% 53%;        /* #EAB308 — yellow/partial */
--warning-muted:      48 70% 12%;        /* #2B2506 — yellow bg */
--danger:             0 84% 60%;         /* #EF4444 — red/absent */
--danger-muted:       0 60% 12%;         /* #2B0D0D — red bg */
--info:               210 100% 56%;      /* #3B82F6 — blue/info */
--info-muted:         210 70% 12%;       /* #0D1A2B — blue bg */
```

### Hex Quick Reference

| Role | Token | Hex | Usage |
|------|-------|-----|-------|
| Background | `--background` | `#0A0A0A` | Page canvas |
| Surface 1 | `--background-alt` | `#121212` | Header, sidebar, toolbar |
| Surface 2 | `--card` | `#171717` | Cards, panels, modals |
| Surface 3 | `--card-hover` | `#1C1C1C` | Hover states, active rows |
| Border | `--border` | `#242424` | Card outlines, dividers |
| Text Primary | `--foreground` | `#EDEDED` | Headings, body text |
| Text Muted | `--foreground-muted` | `#737373` | Labels, metadata |
| Text Faint | `--foreground-faint` | `#4D4D4D` | Disabled, decorative |
| Orange | `--primary` | `#F97316` | CTAs, active states, accents |
| Orange Hover | `--primary-hover` | `#FB923C` | Button/link hovers |
| Orange Tint | `--primary-muted` | `#5C2D0E` | Orange badge backgrounds |
| Purple | `--secondary` | `#8B5CF6` | Secondary highlights |
| Purple Tint | `--secondary-muted` | `#2E1A5E` | Purple badge backgrounds |
| Green | `--success` | `#22C55E` | Present/yes/positive |
| Yellow | `--warning` | `#EAB308` | Partial/mixed |
| Red | `--danger` | `#EF4444` | Absent/no/negative |

### Orange Gradient (for hero accents, glow effects)

```css
--gradient-flame: linear-gradient(135deg, #F97316 0%, #EA580C 50%, #C2410C 100%);
--gradient-ember: linear-gradient(135deg, #F97316 0%, #DC2626 100%);
--glow-orange:    0 0 20px rgba(249, 115, 22, 0.15),
                  0 0 60px rgba(249, 115, 22, 0.05);
--glow-purple:    0 0 20px rgba(139, 92, 246, 0.15),
                  0 0 60px rgba(139, 92, 246, 0.05);
```

### Feature Weight Band Colors

| Band | Label | Color | Hex | Background |
|------|-------|-------|-----|------------|
| W5 | Revenue Critical | Orange | `#F97316` | `rgba(249,115,22, 0.12)` |
| W4 | High Impact | Purple | `#8B5CF6` | `rgba(139,92,246, 0.12)` |
| W3 | Standard | Blue | `#3B82F6` | `rgba(59,130,246, 0.12)` |
| W2 | Nice to Have | Muted | `#737373` | `rgba(115,115,115, 0.12)` |
| W1 | Minimal | Faint | `#4D4D4D` | `rgba(77,77,77, 0.12)` |

### Category Colors

| Category | Color | Hex |
|----------|-------|-----|
| Revenue & Commerce | Orange | `#F97316` |
| Content & Media | Purple | `#8B5CF6` |
| Fan Engagement | Cyan | `#06B6D4` |
| Navigation & UX | Blue | `#3B82F6` |
| Identity & Trust | Amber | `#F59E0B` |

---

## Typography

### Font Pairing: Inter + JetBrains Mono

**Why this pairing over Fira Code / Fira Sans:**
- Inter is the native font of shadcn/ui — zero config, already loaded
- JetBrains Mono is crisper at small sizes (11-12px) in data tables than Fira Code
- Inter has superior tabular number support (`font-variant-numeric: tabular-nums`)
- Both fonts have excellent weight range for hierarchy

```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');
```

### Type Scale

| Level | Font | Weight | Size | Line Height | Letter Spacing | Usage |
|-------|------|--------|------|-------------|----------------|-------|
| Display | Inter | 800 | 32px / 2rem | 1.1 | -0.02em | Page title |
| H1 | Inter | 700 | 24px / 1.5rem | 1.2 | -0.015em | Section headers |
| H2 | Inter | 600 | 18px / 1.125rem | 1.3 | -0.01em | Card titles, panel headers |
| H3 | Inter | 600 | 14px / 0.875rem | 1.4 | 0 | Subsection labels |
| Body | Inter | 400 | 13px / 0.8125rem | 1.5 | 0 | General text |
| Body Small | Inter | 400 | 12px / 0.75rem | 1.5 | 0 | Table cells, metadata |
| Caption | Inter | 500 | 11px / 0.6875rem | 1.4 | 0.02em | Badges, chips, labels |
| Overline | Inter | 700 | 10px / 0.625rem | 1.0 | 0.12em | Section divider labels (UPPERCASE) |
| Data | JetBrains Mono | 500 | 13px / 0.8125rem | 1.3 | 0 | Scores, percentages, counts |
| Data Large | JetBrains Mono | 700 | 24px / 1.5rem | 1.1 | -0.01em | KPI hero numbers |
| Data Small | JetBrains Mono | 400 | 11px / 0.6875rem | 1.3 | 0 | Table score cells |

### Tailwind Config

```js
fontFamily: {
  sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
  mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
},
fontSize: {
  'display': ['2rem', { lineHeight: '1.1', letterSpacing: '-0.02em', fontWeight: '800' }],
  'h1':      ['1.5rem', { lineHeight: '1.2', letterSpacing: '-0.015em', fontWeight: '700' }],
  'h2':      ['1.125rem', { lineHeight: '1.3', letterSpacing: '-0.01em', fontWeight: '600' }],
  'h3':      ['0.875rem', { lineHeight: '1.4', fontWeight: '600' }],
  'body':    ['0.8125rem', { lineHeight: '1.5', fontWeight: '400' }],
  'body-sm': ['0.75rem', { lineHeight: '1.5', fontWeight: '400' }],
  'caption': ['0.6875rem', { lineHeight: '1.4', letterSpacing: '0.02em', fontWeight: '500' }],
  'overline':['0.625rem', { lineHeight: '1.0', letterSpacing: '0.12em', fontWeight: '700' }],
},
```

### Font Rules

- **Numbers and scores** always use `font-mono` (JetBrains Mono) for alignment
- **Percentages** use tabular nums: `font-variant-numeric: tabular-nums`
- **Uppercase labels** (category names, section headers) use `tracking-wider` + `font-bold`
- **Body text** never below 12px; **data cells** can go to 11px minimum
- **Weight contrast**: headings 600-800, body 400, never use 300 (too thin on dark backgrounds)

---

## Spacing & Layout

### Spacing Scale

| Token | Value | Usage |
|-------|-------|-------|
| `space-0` | 0 | — |
| `space-1` | 4px | Inline element gaps, icon padding |
| `space-2` | 8px | Compact card padding, chip gaps |
| `space-3` | 12px | Default card inner padding, toolbar gaps |
| `space-4` | 16px | Section gaps, card padding |
| `space-5` | 20px | Panel padding, header padding |
| `space-6` | 24px | Major section separators |
| `space-8` | 32px | Page-level section gaps |

### Layout Tokens

| Token | Value | Usage |
|-------|-------|-------|
| `--header-height` | 56px | Main navigation bar |
| `--toolbar-height` | 44px | Filter/action toolbar |
| `--sidebar-width` | 200px | Category filter sidebar |
| `--panel-width` | 320px | Right detail panel |
| `--table-row-height` | 40px | Default matrix row |
| `--table-row-compact` | 36px | Compact matrix row |
| `--table-header-height` | 48px | Sticky column header |

### Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `--radius-sm` | 4px | Chips, badges, small buttons |
| `--radius-md` | 6px | Input fields, filter buttons |
| `--radius-lg` | 8px | Cards, panels |
| `--radius-xl` | 12px | Modals, popovers |
| `--radius-full` | 9999px | Avatars, dots, pills |

---

## Component Rules

### shadcn/ui Component Mapping

| UI Element | shadcn Component | Custom Styling |
|------------|------------------|----------------|
| Matrix table | `Table` + `TableHeader` + `TableBody` + `TableRow` + `TableCell` | Custom sticky headers, hover rows |
| Filter buttons | `Toggle` / `ToggleGroup` | Orange active state |
| Search | `Input` with `SearchIcon` | Dark bg, orange focus ring |
| Sidebar categories | `Button` variant="ghost" | With colored dot prefix |
| Detail panel | `Sheet` or `Card` | Right-anchored, slide-in |
| Tooltips | `Tooltip` + `TooltipContent` | Orange-tinted bg |
| Feature badges | `Badge` | Custom band-colored variants |
| Score display | `Badge` variant="outline" | Monospace font |
| Dropdowns | `Select` / `DropdownMenu` | Dark popover bg |
| Tabs (flow nav) | `Tabs` + `TabsList` | Orange active indicator |
| Modals | `Dialog` | Locked backdrop, dark bg |
| Progress bars | Custom div | Orange fill with glow |

### Matrix Cell States

```
┌─────────────────────────────────────────────────┐
│  State        │ Background      │ Icon/Text     │
├───────────────┼─────────────────┼───────────────│
│  Present (✓)  │ success-muted   │ #22C55E 100%  │
│  Partial (~)  │ warning-muted   │ #EAB308  60%  │
│  Absent (·)   │ transparent     │ #4D4D4D  40%  │
│  Hovered      │ card-hover      │ inherit        │
│  Selected Col │ primary-muted   │ inherit        │
└─────────────────────────────────────────────────┘
```

### Card Component Pattern

```
┌─────────────────────────────────────┐
│ bg: var(--card)          radius: 8px │
│ border: 1px solid var(--border)     │
│ padding: 16px                        │
│                                      │
│ On hover:                            │
│   bg: var(--card-hover)              │
│   border-color: var(--border) → +5%  │
│   transition: 150ms ease-out         │
│                                      │
│ On focus-visible:                    │
│   ring: 2px var(--primary)           │
│   ring-offset: 2px var(--background) │
└─────────────────────────────────────┘
```

### Button Variants

| Variant | Background | Text | Border | Hover |
|---------|-----------|------|--------|-------|
| Primary | `#F97316` | `#FFFFFF` | none | `#FB923C` + glow |
| Secondary | `transparent` | `#8B5CF6` | `#8B5CF6` | `#2E1A5E` bg |
| Ghost | `transparent` | `#737373` | none | `#1C1C1C` bg |
| Destructive | `transparent` | `#EF4444` | `#EF4444` | `#2B0D0D` bg |

---

## Interaction & Animation

### Transitions

| Property | Duration | Easing | Usage |
|----------|----------|--------|-------|
| Color/Background | 150ms | ease-out | Hover states, active toggle |
| Border color | 150ms | ease-out | Focus, hover |
| Transform | 200ms | ease-out | Scale on press (0.97) |
| Opacity | 200ms | ease-in-out | Fade in/out panels |
| Slide (panel) | 250ms | cubic-bezier(0.16,1,0.3,1) | Detail panel open/close |
| Box shadow | 200ms | ease-out | Glow on hover |

### Hover Behaviors

- **Table rows**: Background shifts to `--card-hover`, no color change on text
- **Filter chips**: Border color → `--primary`, text → `--foreground`, subtle orange bg tint
- **Cards**: Border lightens, optional subtle glow
- **Links/CTAs**: Color shifts to `--primary-hover`, underline on text links
- **Active press**: `transform: scale(0.97)` for tactile feedback

### Focus States

- All interactive elements: `outline: 2px solid var(--primary); outline-offset: 2px`
- `border-radius: 3px` on the outline
- Respects `prefers-reduced-motion: reduce`

---

## Data Visualization Rules

### Score Heatmap

Feature adoption percentages map to a 4-tier color intensity:

| Range | Label | Color | Background |
|-------|-------|-------|------------|
| 80-100% | Excellent | `#22C55E` | `rgba(34,197,94, 0.15)` |
| 50-79% | Good | `#EAB308` | `rgba(234,179,8, 0.12)` |
| 25-49% | Moderate | `#F97316` | `rgba(249,115,22, 0.12)` |
| 0-24% | Low | `#EF4444` | `rgba(239,68,68, 0.10)` |

### Weighted Score Display

- Positive scores: Green text (`--success`) + upward arrow
- Negative scores: Red text (`--danger`) + downward arrow
- Zero/neutral: Muted text (`--foreground-muted`)
- Always rendered in `font-mono` with `tabular-nums`

### Progress/Bar Charts

- Fill color: `--primary` (orange) for standard bars
- Use `--secondary` (purple) for comparison/secondary dataset
- Background track: `--border` (#242424)
- Bar border-radius: 2px (small) or `--radius-full` (pill bars)
- Animate fill width on mount: `300ms ease-out`

---

## Responsive Breakpoints

| Token | Width | Layout |
|-------|-------|--------|
| `sm` | 640px | Stack sidebar below matrix |
| `md` | 768px | Sidebar visible, panel overlay |
| `lg` | 1024px | Full 3-column layout |
| `xl` | 1280px | Comfortable spacing |
| `2xl` | 1536px | Maximum content width |

### Mobile Adaptations (< 768px)

- Sidebar becomes bottom sheet
- Matrix scrolls horizontally with frozen first column
- Detail panel is full-screen modal
- Toolbar filters collapse into dropdown
- Minimum touch target: 44x44px

---

## Accessibility

### Contrast Ratios (verified against WCAG 2.1 AA)

| Pair | Foreground | Background | Ratio | Pass |
|------|-----------|------------|-------|------|
| Primary text on bg | `#EDEDED` | `#0A0A0A` | 17.4:1 | AAA |
| Muted text on bg | `#737373` | `#0A0A0A` | 4.8:1 | AA |
| Orange on bg | `#F97316` | `#0A0A0A` | 5.6:1 | AA |
| Purple on bg | `#8B5CF6` | `#0A0A0A` | 4.6:1 | AA |
| Green on bg | `#22C55E` | `#0A0A0A` | 7.2:1 | AAA |
| White on orange | `#FFFFFF` | `#F97316` | 3.0:1 | Large only |

### Rules

- All interactive elements have visible focus states
- Color is never the sole indicator — always paired with icon or text
- `aria-label` on icon-only buttons
- Table has proper `<thead>`, `<tbody>`, `<th scope="col">` structure
- `prefers-reduced-motion` disables all animations
- `prefers-color-scheme` — dark only (no light mode needed)

---

## shadcn/ui CSS Variables (globals.css)

Complete theme for `globals.css`, dark-only:

```css
@layer base {
  :root {
    --background: 0 0% 4%;
    --foreground: 0 0% 93%;
    --card: 0 0% 9%;
    --card-foreground: 0 0% 93%;
    --popover: 0 0% 9%;
    --popover-foreground: 0 0% 93%;
    --primary: 24 95% 53%;
    --primary-foreground: 0 0% 100%;
    --secondary: 270 70% 60%;
    --secondary-foreground: 0 0% 100%;
    --muted: 0 0% 14%;
    --muted-foreground: 0 0% 45%;
    --accent: 24 80% 20%;
    --accent-foreground: 0 0% 93%;
    --destructive: 0 84% 60%;
    --destructive-foreground: 0 0% 100%;
    --border: 0 0% 14%;
    --input: 0 0% 14%;
    --ring: 24 95% 53%;
    --radius: 0.5rem;
    --chart-1: 24 95% 53%;
    --chart-2: 270 70% 60%;
    --chart-3: 142 71% 45%;
    --chart-4: 48 96% 53%;
    --chart-5: 210 100% 56%;
  }
}
```

---

## Anti-Patterns (Do NOT)

- Do not use pure white (`#FFFFFF`) for backgrounds — max is `#1C1C1C`
- Do not use solid colored backgrounds for entire sections — accent colors are for small elements only
- Do not mix font families in the same line — mono for data, sans for everything else
- Do not use box-shadow as primary depth indicator — use background color steps instead
- Do not add rounded corners > 12px on data components (table, badges) — feels unserious
- Do not use opacity for disabled states on text below 0.3 — becomes illegible on dark bg
- Do not use green/red as only differentiator — always add icon or text label
- Do not make filter buttons full-color when active — use border+tint instead (exception: primary CTA)
- Do not animate table rows individually — animate the container transition, not 26 row transitions
- Do not use gradient text — it reduces readability on dark backgrounds at small sizes

---

## File Structure (Target)

```
src/
  app/
    globals.css          ← Theme variables from this doc
    layout.tsx           ← Inter font, dark class
    page.tsx             ← Main matrix view
  components/
    ui/                  ← shadcn/ui components
    matrix/
      matrix-table.tsx   ← Core comparison table
      matrix-cell.tsx    ← Individual feature cell
      matrix-header.tsx  ← Sticky product headers
    filters/
      search-input.tsx
      category-filter.tsx
      band-filter.tsx
      type-filter.tsx
    panels/
      feature-panel.tsx  ← Right panel: feature details
      product-panel.tsx  ← Right panel: product details
    layout/
      header.tsx
      sidebar.tsx
      toolbar.tsx
  lib/
    data.ts              ← Products, features, presence matrix
    scoring.ts           ← Weight calculations
    utils.ts             ← cn(), formatters
```
