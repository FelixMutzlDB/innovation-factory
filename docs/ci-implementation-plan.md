# Innovation Factory — Customer CI Implementation Plan

> Status: Plan (not yet implemented).
> Owner: Felix Mutzl.
> Created: 2026-05-11.
> Scope: Apply each customer's brand-adjacent corporate identity to its accelerator route so the UI visually evokes the target customer — **without using any protected marks**.

## 1. Why

Each accelerator already targets an obfuscated real customer (see each `docs/projects/*.md`, "Customer inspiration" callout). Today the UI is a single shadcn/Tailwind theme. Demos land harder when the SA can say "this is what it could look like running in *your* environment." Brand-adjacent CI gives us that without legal risk:

- **Names** are already obfuscated (ViDistrictOne, ASM Cockpit, HB Product Center, …).
- **Visuals** should be too — close enough to evoke, far enough to be safe.

## 2. Legal & ethical rails (non-negotiable)

| Asset | Rule |
|-------|------|
| **Logos / wordmarks** | Never use the customer's actual logo. Use a styled text wordmark of the *obfuscated* project name only. |
| **Colors** | Use brand-*adjacent* (close hue/value, not pixel-perfect Pantone match). |
| **Fonts** | Use an open-source Google Font with similar character. Never embed a licensed brand font. |
| **Photography** | Use generic stock or AI-generated imagery — never lift from customer marketing. |
| **Slogans / claims** | Never reuse customer slogans or product-name strings. |
| **Internal vs external** | Internal `docs/projects/*.md` may name the real customer (audience: Databricks employees). Customer-facing artifacts (running UI, screenshots in slides) must not. |

## 3. Research findings

Researched via corporate sites and brand-color aggregators (encycolorpedia.com, logotyp.us, 1000logos.net, brandcolorcode.com). Colors marked "approximate" lack official published guidelines and are best-effort matches from logo SVG inspection.

### 3.1 Viessmann → ViDistrictOne

- **Primary:** Vitorange `#EE4221` — red-orange, Stankowski heritage
- **Secondary:** Warm gray `#687373`
- **Typography:** Sans-serif close to Enamelplate B. Brand-adjacent Google Font: **DM Sans** (preferred) or IBM Plex Sans
- **Logo style:** Iconic double-S wordmark (1969, Anton Stankowski). Our wordmark: "ViDistrictOne" set in primary color, with subtly customized S glyphs.
- **Tone:** Warm, industrial, German engineering trust. Heating/energy.

### 3.2 BSH Hausgeräte / Home Connect → BSH Remote Assist

BSH's current corporate identity (post-2018 redesign by wirDesign) is built on a vibrant coral-orange and near-black palette — distinct from parent Bosch's red. Hex values below were lifted directly from bsh-group.com's compiled CSS bundle.

- **Primary:** BSH Orange `#FF6840` — vibrant coral-orange (verified via `bsh-group.com/corporate-design` CSS). For implementation we use `oklch(0.66 0.22 42)` (≈ `#E5602C`): a touch deeper than the raw brand hex so white text on primary meets WCAG AA Large Text / UI 3:1 (raw `#FF6840` only reaches 2.81:1 with white), and shifted slightly toward orange (hue 42° vs Viessmann's 35°) so the two warm-red themes stay visually distinct in the sidebar.
- **Primary hover / deep variant:** `#D74000`
- **Secondary:** Near-black `#1A1A1A`
- **Accent / tint scale:** `#FF8666`, `#FFC3B3`, `#FFD2C6`, `#FFE1D9`, `#FFF0EC` (use for surfaces, hovers, light backgrounds)
- **Coral / display accent:** `#EE7753`
- **Semantic (from BSH CSS):** success `#006B31`, error `#AE0505`, warning `#996401`, info `#0A439C`
- **Neutrals:** `#262626`, `#333333`, `#4D4D4D`, `#666666`, `#999999`, `#B2B2B2`, `#CCCCCC`, `#E5E5E5`, `#F5F5F5`
- **Typography:** Clean geometric sans-serif. Brand-adjacent Google Font: **Inter** (preferred) or Manrope.
- **Logo style:** All-caps wordmark "BSH" in black on white, with orange used as supporting brand-system color rather than in the logotype itself.
- **Tone:** Premium European domestic appliance, confident, modern. Orange brings the warmth; black the engineering trust.

### 3.3 MOL Group → MOL ASM Cockpit

- **Primary:** Red `#DA1A26` (approximate, derived from MOL "M" mark)
- **Secondary:** Green `#6CB52D` (approximate)
- **Typography:** Modern sans-serif. Brand-adjacent: **Manrope** (preferred) or Plus Jakarta Sans
- **Logo style:** Stylized two-color "M" + uppercase wordmark.
- **Tone:** "Energy of positive change" — bold, optimistic, CEE fuel & retail.

### 3.4 Ströer SE → AdTech Intelligence

- **Primary:** Navy `#000C36`
- **Secondary:** Orange `#EB690B`
- **Typography:** Refined geometric sans-serif. Brand-adjacent: **Space Grotesk** (preferred) or DM Sans
- **Logo style:** Two-color wordmark, navy + orange.
- **Tone:** Confident, modern media. OOH/DOOH advertising in Germany.

### 3.5 HB (German premium-fashion brand) → HB Product Center

- **Primary:** Black `#000000` / `#231F20`
- **Secondary:** White `#FFFFFF`
- **Optional accent:** Champagne / muted gold `#A8894D` for editorial flair (the reference brand uses warm metallics in editorial)
- **Typography:** Modified Univers historically; current group identity uses geometric sans. Brand-adjacent: **Inter** (UI) + **Playfair Display** (display) for editorial contrast.
- **Logo style:** All-caps wordmark, tight letter-spacing, no mark.
- **Tone:** Premium, monochrome, fashion-editorial.

### 3.6 Nemetschek Group → AECO Hub

- **Primary:** Dark gray `#1A1A1A`
- **Secondary:** Group blue `#00A0E0` (approximate — vibrant tech blue used in Nemetschek Group marketing)
- **Accent:** Mid gray `#878787`
- **Typography:** Modern sans-serif. Brand-adjacent: **Inter** (preferred) or DM Sans
- **Logo style:** Wordmark in gray; sub-brands (Allplan, Bluebeam, Graphisoft, …) each get a colored modifier.
- **Tone:** Tech-minimal, AEC/BIM software, multi-brand parent — fits the "AECO ecosystem hub" framing.

### 3.7 Cross-cut summary

| Slug | Primary | Secondary | Font (UI) | Font (display) |
|------|---------|-----------|-----------|----------------|
| vi-home-one | `#EE4221` | `#687373` | DM Sans | DM Sans |
| bsh-home-connect | `#FF6840` | `#1A1A1A` | Inter | Inter |
| mol-asm-cockpit | `#DA1A26` | `#6CB52D` | Manrope | Manrope |
| adtech-intelligence | `#000C36` | `#EB690B` | Space Grotesk | Space Grotesk |
| hb-product-center | `#231F20` | `#A8894D` | Inter | Playfair Display |
| aeco-hub | `#1A1A1A` | `#00A0E0` | Inter | Inter |

Three fonts (DM Sans, Inter, Manrope) cover 5/6 projects — bundle stays small.

## 4. Architecture

### 4.1 Current state

`src/innovation_factory/ui/styles/globals.css` defines a single set of shadcn semantic tokens (`--primary`, `--accent`, `--sidebar-*`, etc.) in oklch under `:root` and `.dark`. `ThemeProvider` (in `components/apx/theme-provider.tsx`) toggles only `light`/`dark` on `documentElement`. There is no per-project theming.

### 4.2 Target

Per-project token overrides via attribute selector, scoped to the route subtree. Pattern:

```css
/* ui/styles/themes/vi-home-one.css */
[data-project-theme="vi-home-one"] {
  --primary: oklch(0.65 0.22 35);          /* Vitorange-adjacent */
  --primary-foreground: oklch(1 0 0);
  --accent: oklch(0.51 0.025 200);         /* warm gray */
  --sidebar-primary: oklch(0.65 0.22 35);
  --ring: oklch(0.65 0.22 35 / 0.5);
  --radius: 0.5rem;

  --brand-font-family: "DM Sans", system-ui, sans-serif;
}

[data-project-theme="vi-home-one"].dark,
.dark [data-project-theme="vi-home-one"] {
  /* dark-mode tuned tokens */
  --primary: oklch(0.72 0.22 35);
  /* ... */
}
```

All themes imported once at the bottom of `globals.css`:

```css
@import "./themes/vi-home-one.css";
@import "./themes/bsh-home-connect.css";
@import "./themes/mol-asm-cockpit.css";
@import "./themes/adtech-intelligence.css";
@import "./themes/hb-product-center.css";
@import "./themes/aeco-hub.css";
```

Each project's route wraps content in a scope component:

```tsx
// ui/routes/projects/vi-home-one/route.tsx
import { ProjectThemeScope } from "@/components/apx/project-theme-scope";

function Layout() {
  return (
    <ProjectThemeScope slug="vi-home-one">
      <SidebarLayout>{/* ... */}</SidebarLayout>
    </ProjectThemeScope>
  );
}
```

`ProjectThemeScope` sets `data-project-theme="<slug>"` on a wrapper div, applies a CSS variable for `font-family`, and looks up brand metadata from a registry. Fonts loaded via `<link>` tags in `index.html` (`preconnect` + `display=swap`).

### 4.3 Why attribute selector (not class)

- shadcn already uses `.dark` on `<html>`. Stacking more theme classes there muddies global state.
- Attribute selector on a wrapper div is route-local — leaves the global navbar/sidebar untouched if we want, or includes them via the wrapper if we want full theming.
- Easy to undo: navigating away unmounts the scope and tokens fall back to root.
- Composes cleanly with `.dark` since the wrapper is below `<html>` in the cascade.

### 4.4 Open: scope of theming

| Option | Scope | Pro | Con |
|--------|-------|-----|-----|
| A | Content area only (inside `<SidebarLayout>`) | Sidebar/navbar consistent across products | Less immersive |
| B | Whole sidebar layout including top navbar | Most dramatic; navbar shows project color | Risks visual conflict with global app chrome |
| **C (recommended)** | Sidebar + content; top navbar stays global | Best of both — immersive page, neutral chrome | Slightly more route wrapping |

## 5. Implementation phases

### P0 — Foundation (1 PR)

- Create `ui/styles/themes/` directory with stub files for all 6 projects.
- Implement `<ProjectThemeScope slug={...}>` component.
- Create `BRAND_THEMES` registry in `ui/lib/brand-themes.ts`: `slug → {primary, secondary, fontUi, fontDisplay, displayName}`.
- Wire one project (ViDistrictOne) end-to-end as the working example.
- Land unit + integration test scaffold (§6.1, §6.2).

### P1 — Per-project tokens

- Fill in each `themes/<slug>.css` with brand-adjacent palette in **both** light and dark.
- Add Google Fonts `<link>` tags to `index.html` (preconnect + `display=swap`).
- Update each project route's `route.tsx` to wrap with `<ProjectThemeScope>`.
- One PR per project, or a single batched PR — author's call based on review load.

### P2 — Wordmark & detail polish

- Per-project wordmark component (text only, project name, styled with brand font).
- Update navbar to render a project wordmark slot when inside a project route.
- Per-project chart palette: re-derive `--chart-1..5` for visual harmony with each brand.

### P3 — Visual regression baselines

- Snapshot tests per project home page (Playwright).
- Baselines committed to `tests/visual/baselines/<slug>/`.
- CI compares with `pixelmatch` at ~0.1 % tolerance.

## 6. Test design

Tests are designed up-front per the working-mode rule in `CLAUDE.md`.

### 6.1 Unit tests — `tests/ui/theme/`
- `<ProjectThemeScope slug="vi-home-one">` sets `data-project-theme="vi-home-one"` on its root.
- Unknown slug falls back to default (no attribute, no console error).
- Font-family CSS variable is set correctly from the registry.

### 6.2 Integration tests
- Mounting `/projects/vi-home-one` causes a probe element's computed `--primary` to be the Vitorange-adjacent value, not the default zinc.
- Navigating away from the project route clears the override (probe reverts).
- Vitest + happy-dom (or `@testing-library/react` with a CSSStyleSheet polyfill).

### 6.3 Visual regression
- Playwright screenshot per route on the home page (1280×800, light + dark).
- Baselines committed to `tests/visual/baselines/`.
- CI compares with `pixelmatch` at 0.1 % tolerance.
- First-PR baselines reviewed manually.

### 6.4 A11y / contrast
- For each token pair (`--primary`/`--primary-foreground`, `--sidebar-primary`/`--sidebar-primary-foreground`), assert WCAG AA contrast ratio ≥ 4.5 for body text, ≥ 3 for large text.
- Use `wcag-contrast` npm package on the parsed oklch values, or `axe-core` on rendered DOM.
- Auto-derived dark-mode tokens must also pass.
- Regression test name: `test_contrast_meets_wcag_aa_per_project_theme`.

### 6.5 Regression guard for the obfuscation rule
- New test `tests/docs/test_customer_callouts.py`: assert each `docs/projects/*.md` contains a "Customer inspiration" line.
- Reason: prevent accidental obfuscation drift where someone removes the callout and we lose the mapping.

### 6.6 Manual UAT checklist (per project, light + dark)
- Primary buttons, links, focus rings use the brand color
- Sidebar active state uses the brand color
- Body text remains readable (no contrast regression)
- Brand font has loaded within 1 s (no flash of unstyled text)
- No leakage: navigating to `/` after a project route resets tokens
- No legal red flag: take a screenshot, hold it next to the real customer's homepage at 50 % opacity. They should *evoke*, not match.

## 7. File changes

```
src/innovation_factory/ui/
  styles/
    globals.css                       # MOD: add @import lines at bottom
    themes/                           # NEW
      vi-home-one.css
      bsh-home-connect.css
      mol-asm-cockpit.css
      adtech-intelligence.css
      hb-product-center.css
      aeco-hub.css
  components/apx/
    project-theme-scope.tsx           # NEW
    project-wordmark.tsx              # NEW (P2)
  lib/
    brand-themes.ts                   # NEW: registry of slug → metadata
  index.html                          # MOD: add Google Fonts <link> tags
  routes/projects/<slug>/
    route.tsx                         # MOD: wrap with ProjectThemeScope

tests/
  ui/
    theme/
      test_project_theme_scope.tsx    # NEW: unit
      test_routing_applies_theme.tsx  # NEW: integration
    visual/
      baselines/<slug>/home.png       # NEW: visual regression
      test_visual.spec.ts             # NEW: Playwright
    a11y/
      test_contrast.test.ts           # NEW: contrast checks
  docs/
    test_customer_callouts.py         # NEW: obfuscation regression guard
```

## 8. Risks

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Trademark / brand exposure | Low (mitigated by §2 rules) | Hard rules in §2; PR template asks "any protected marks used?" |
| Color contrast failures in dark mode | Medium | Per-token contrast tests in §6.4 — must pass to merge |
| Font FOUT on slow networks | Medium | `font-display: swap`, preload critical fonts, fallback chain to `system-ui` |
| Visual regression noise | Medium | Tight tolerance + manual baseline review on first PR |
| Theme leak: tokens bleed into shared chrome | Low | Use attribute selector scoped to wrapper, never to `html` |
| Bundle-size growth from fonts | Low–medium | 3 shared fonts (DM Sans, Inter, Manrope) cover 5/6; only HB and AdTech add a unique extra |
| Approximate colors drift from real CI over time | Low | Sources cited per project in §3 — review yearly during refinement |

## 9. Open questions

1. **Scope decision (§4.4)** — Recommended Option C (sidebar + content, navbar stays global). Confirm before P0.
2. **Wordmark rendering** — Plain text with brand font (P2 default) or simple SVG (P3 nice-to-have)?
3. **Dark mode strategy** — Mirror light tokens with reduced saturation, or hand-tune per brand? Recommended hand-tune for 6 projects (one-time effort).
4. **Chart palette** — Re-derive `--chart-1..5` per project (better visual harmony) or keep global (less maintenance)?
5. **MOL secondary green** — MOL uses both red and green prominently. Plan currently treats red as primary, green as accent; confirm.
6. **HB editorial accent** — Use the optional champagne `#A8894D` for editorial flair, or stay strictly monochrome?

## 10. Implementation ordering (P0 → P3)

**P0 — must-have for first ship:**
- `themes/` skeleton + `<ProjectThemeScope>` + ViDistrictOne pilot
- Unit + integration test scaffold
- This document + new-project.md update (already shipped 2026-05-11)

**P1 — next pass:**
- Remaining 5 projects' token overrides + route wrapping
- Font loading
- Visual regression baselines

**P2 — polish:**
- Per-project chart palette
- Per-project wordmarks
- Dark-mode hand-tuning per project

**P3 — deferred:**
- Per-project illustration / hero imagery
- Theme-toggle utility in dev for screenshot generation

## 11. Sources

- Viessmann colors: [encycolorpedia.com/companies/germany/viessmann](https://encycolorpedia.com/companies/germany/viessmann), [1000logos.net/viessmann-logo](https://1000logos.net/viessmann-logo/)
- BSH Hausgeräte: live corporate-design page at [bsh-group.com/corporate-design](https://www.bsh-group.com/corporate-design) (hex values extracted from compiled CSS bundle 2026-05-11), supported by [logotyp.us/logo/bsh](https://logotyp.us/logo/bsh/) and the 2018 redesign case study at [behance.net/gallery/58901119/BSH-Corporate-Redesign](https://www.behance.net/gallery/58901119/BSH-Corporate-Redesign)
- MOL Group: tagline "Energy of positive change" + visual inspection of [molgroup.info](https://molgroup.info/en) (colors approximate)
- Ströer: [logotyp.us/logo/stroer](https://logotyp.us/logo/stroer/) (navy `#000C36`, orange `#EB690B`)
- HB (German premium-fashion brand): [encycolorpedia.com/companies/germany/hugo-boss](https://encycolorpedia.com/companies/germany/hugo-boss), [brandcolorcode.com/hugo-boss](https://www.brandcolorcode.com/hugo-boss), [logos-world.net/hugo-boss-logo](https://logos-world.net/hugo-boss-logo/)
- Nemetschek: [logotyp.us/logo/nemetschek](https://logotyp.us/logo/nemetschek/), [nemetschek.com/en/news-media/images-logos](https://www.nemetschek.com/en/news-media/images-logos) (blue approximate from group marketing)
