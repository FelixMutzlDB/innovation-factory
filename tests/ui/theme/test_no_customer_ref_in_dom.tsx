/**
 * Test: No customerRef values in rendered DOM (RT-013).
 *
 * For each accelerator theme in BRAND_THEMES, verify that mounting
 * ProjectThemeScope with that slug does NOT render the internal
 * customerRef (e.g., "Stihl", "Viessmann", "BSH Hausgeräte") in
 * the resulting HTML.
 *
 * This closes the build-time-vs-runtime obfuscation gap: a theme
 * can be registered with customerRef for documentation and internal
 * reference, but the DOM must never expose it.
 */

import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import { ProjectThemeScope } from "@/components/apx/project-theme-scope";
import { BRAND_THEMES } from "@/lib/brand-themes";

describe("ProjectThemeScope — customerRef obfuscation (RT-013)", () => {
  // All customerRef values from the registry
  const allCustomerRefs = Object.values(BRAND_THEMES).map((t) => t.customerRef);

  describe.each(Object.entries(BRAND_THEMES))(
    "theme: %s",
    (slug, theme) => {
      it(`does not render customerRef "${theme.customerRef}" in DOM`, () => {
        const { container } = render(
          <ProjectThemeScope slug={slug}>
            <div>Test content</div>
          </ProjectThemeScope>
        );

        const html = container.innerHTML;

        // The actual customerRef must not appear in the HTML
        expect(html).not.toContain(theme.customerRef);
      });

      it("does not render any customerRef value from the entire registry", () => {
        const { container } = render(
          <ProjectThemeScope slug={slug}>
            <div>Test content</div>
          </ProjectThemeScope>
        );

        const html = container.innerHTML;

        // Ensure none of the internal customerRef values leak
        for (const customerRef of allCustomerRefs) {
          expect(html).not.toContain(customerRef);
        }
      });
    }
  );
});
