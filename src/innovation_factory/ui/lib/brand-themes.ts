/**
 * Brand-adjacent customer themes per accelerator.
 *
 * Each entry maps an accelerator slug to brand-*adjacent* visual identity
 * tokens that evoke the real (obfuscated) target customer without using
 * any protected marks. See docs/ci-implementation-plan.md for sources and
 * the legal/ethical rails.
 *
 * The actual CSS token overrides live in `styles/themes/<slug>.css` —
 * keyed off `[data-project-theme="<slug>"]` set by ProjectThemeScope.
 */

export interface BrandTheme {
  slug: string;
  displayName: string;
  /** Reference customer (internal docs only — never render in UI). */
  customerRef: string;
  /** Brand-adjacent primary color, hex form (for documentation / tests). */
  primaryHex: string;
  /** Brand-adjacent secondary color, hex form. */
  secondaryHex: string;
  /** Google Font family for UI text. */
  fontUi: string;
  /** Optional display/serif font for headlines. */
  fontDisplay?: string;
}

export const BRAND_THEMES: Record<string, BrandTheme> = {
  "vi-home-one": {
    slug: "vi-home-one",
    displayName: "ViDistrictOne",
    customerRef: "Viessmann",
    primaryHex: "#EE4221",
    secondaryHex: "#687373",
    fontUi: "DM Sans",
  },
  "bsh-home-connect": {
    slug: "bsh-home-connect",
    displayName: "BSH Remote Assist",
    customerRef: "BSH Hausgeräte",
    primaryHex: "#FF6840",
    secondaryHex: "#1A1A1A",
    fontUi: "Inter",
  },
  "mol-asm-cockpit": {
    slug: "mol-asm-cockpit",
    displayName: "ASM Cockpit",
    customerRef: "MOL Group",
    primaryHex: "#DA1A26",
    secondaryHex: "#6CB52D",
    fontUi: "Manrope",
  },
  "adtech-intelligence": {
    slug: "adtech-intelligence",
    displayName: "AdTech Intelligence",
    customerRef: "Ströer SE",
    primaryHex: "#000C36",
    secondaryHex: "#EB690B",
    fontUi: "Space Grotesk",
  },
  "hb-product-center": {
    slug: "hb-product-center",
    displayName: "HB Product Center",
    customerRef: "HB",
    primaryHex: "#231F20",
    secondaryHex: "#A8894D",
    fontUi: "Inter",
    fontDisplay: "Playfair Display",
  },
  "aeco-hub": {
    slug: "aeco-hub",
    displayName: "AECO Hub",
    customerRef: "Nemetschek Group",
    primaryHex: "#1A1A1A",
    secondaryHex: "#00A0E0",
    fontUi: "Inter",
  },
  "yard-pro": {
    slug: "yard-pro",
    displayName: "yard-pro",
    customerRef: "Stihl",
    primaryHex: "#D9541F",
    secondaryHex: "#2B2F33",
    fontUi: "Inter",
    fontDisplay: "Saira Condensed",
  },
};

export type BrandThemeSlug = keyof typeof BRAND_THEMES;

export function getBrandTheme(slug: string): BrandTheme | undefined {
  return BRAND_THEMES[slug];
}
