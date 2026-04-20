# Design Tokens Reference

## Overview

All design tokens are sourced from the Figma Design System and defined in `app/globals.css` as CSS custom properties (variables). These tokens ensure consistency across the FC Benchmark application.

Figma Design System: https://www.figma.com/design/0H4RyhlgKKRwfc9CGlytzS?node-id=43-36

## Color Tokens

All color tokens defined in `:root`:

| Token | Value | Usage |
|-------|-------|-------|
| `--bg-page` | `#0F0F0F` | Page background, darkest surface |
| `--bg-cell` | `#1A1A1A` | Cell/card background |
| `--bg-hover` | `#383838` | Hover state background |
| `--border` | `#262626` | Border and divider color |
| `--accent` | `#FF490C` | Primary CTA, brand orange |
| `--text` | `#FFFFFF` | Primary text color |
| `--text-secondary` | `#ABABAB` | Alias for `--muted` |
| `--muted` | `#ABABAB` | Secondary text, disabled state |
| `--green` | `#22c55e` | Positive/success indicator |
| `--yellow` | `#eab308` | Warning indicator |
| `--orange` | `#f97316` | Medium importance indicator |
| `--red` | `#ef4444` | Negative/error indicator |

## Typography Tokens

All typography tokens defined in `:root`. Each scale includes family, size, weight, line-height, and letter-spacing.

### Web/H5 — Display/Hero Text
```css
--font-h5-family: var(--font-body, 'Suisse Int\'l'), system-ui, sans-serif
--font-h5-size: 22px
--font-h5-weight: 500
--font-h5-height: 1.4
--font-h5-spacing: -2px
```

### Web/Body Reg — Large Body Text
```css
--font-body-reg-family: var(--font-body, 'Suisse Int\'l'), system-ui, sans-serif
--font-body-reg-size: 16px
--font-body-reg-weight: 400
--font-body-reg-height: 24px
--font-body-reg-spacing: -0.3px
```

### Web/Body S — Default Body Text (Primary)
Used for body text, labels, and general content.
```css
--font-body-s-family: var(--font-body, 'Suisse Int\'l'), system-ui, sans-serif
--font-body-s-size: 14px
--font-body-s-weight: 400
--font-body-s-height: 1.4
--font-body-s-spacing: -0.3px
```

### Web/Body XS — Small Body Text
Used for form fields, secondary text, and compact layouts.
```css
--font-body-xs-family: var(--font-body, 'Suisse Int\'l'), system-ui, sans-serif
--font-body-xs-size: 12px
--font-body-xs-weight: 400
--font-body-xs-height: 1.3
--font-body-xs-spacing: -0.3px
```

### Web/Links — Monospace Links/Captions
Used for links, monospace text, and UI labels.
```css
--font-links-family: var(--font-mono, 'Roboto Mono'), ui-monospace, monospace
--font-links-size: 12px
--font-links-weight: 500
--font-links-height: 13px
--font-links-spacing: -1px
```

### Web/Caption — Small Monospace Labels
Used for captions, status badges, and small UI text.
```css
--font-caption-family: var(--font-mono, 'Roboto Mono'), ui-monospace, monospace
--font-caption-size: 10px
--font-caption-weight: 500
--font-caption-height: 13px
--font-caption-spacing: -1px
```

### Additional Utility Size
For UI buttons and small interactive elements.
```css
--font-ui-size: 11px
--font-ui-weight: 500
```

## Using Tokens in CSS

### In Global Styles (app/globals.css)
```css
body {
  font-family: var(--font-body-s-family);
  font-size: var(--font-body-s-size);
  font-weight: var(--font-body-s-weight);
  line-height: var(--font-body-s-height);
  letter-spacing: var(--font-body-s-spacing);
  color: var(--text);
  background: var(--bg-page);
}
```

### In CSS Modules (app/components/matrix/*.module.css)
```css
.label {
  font-family: var(--font-body-s-family);
  font-size: var(--font-body-s-size);
  font-weight: var(--font-body-s-weight);
  line-height: var(--font-body-s-height);
  letter-spacing: var(--font-body-s-spacing);
  color: var(--text);
}
```

CSS custom properties are inherited from `:root` in `app/globals.css`, so they work seamlessly in component CSS modules.

## Token Consistency Rules

1. **Never use hardcoded colors** — Always reference color tokens (e.g., `var(--accent)` not `#FF490C`)
2. **Never use hardcoded font sizes** — Always reference typography tokens (e.g., `var(--font-body-s-size)` not `14px`)
3. **Use complete typography scales** — When using a typography token, apply the full scale (family, size, weight, height, spacing)
4. **Single accent per surface** — Only one CTA per page/modal should use `var(--accent)`; secondary actions use border or text-only styling

## Font Families

- **Suisse Int'l** (body): Regular (400), Medium (500), SemiBold (600), Bold (700)
  - Exposed as `--font-body` CSS variable via `next/font/local`
  - Loaded from `public/fonts/suisse/`

- **Roboto Mono** (monospace): Regular (400), Medium (500)
  - Exposed as `--font-mono` CSS variable via Google Fonts
  - Used for captions, links, and UI labels

## Updates and Maintenance

When Figma tokens change:
1. Update the CSS custom properties in `app/globals.css` :root
2. Update this reference document
3. Test across all UI surfaces to verify consistency
4. Commit with message: `refactor: update design tokens from Figma`

Last updated: 2026-04-20
Source: Figma Design System — https://www.figma.com/design/0H4RyhlgKKRwfc9CGlytzS?node-id=43-36
