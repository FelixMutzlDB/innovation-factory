import type { CSSProperties, ReactNode } from "react";
import { BRAND_THEMES } from "@/lib/brand-themes";

interface ProjectThemeScopeProps {
  slug: string;
  children: ReactNode;
  className?: string;
}

/**
 * Wraps a project route in a brand-adjacent theme scope.
 *
 * Sets `data-project-theme="<slug>"` on a wrapper div. The matching CSS in
 * `styles/themes/<slug>.css` overrides shadcn semantic tokens for the
 * subtree, so primary/accent/ring etc. pick up the customer's brand-adjacent
 * palette without affecting the rest of the app.
 *
 * Unknown slugs render the children unwrapped (no attribute, no error) so
 * partially-themed routes degrade gracefully.
 */
export function ProjectThemeScope({
  slug,
  children,
  className,
}: ProjectThemeScopeProps) {
  const theme = BRAND_THEMES[slug];

  if (!theme) {
    return <>{children}</>;
  }

  const style: CSSProperties = {
    ["--brand-font-family" as string]:
      `"${theme.fontUi}", system-ui, sans-serif`,
    ...(theme.fontDisplay && {
      ["--brand-font-display" as string]:
        `"${theme.fontDisplay}", Georgia, serif`,
    }),
  };

  return (
    <div
      data-project-theme={slug}
      style={style}
      className={className}
    >
      {children}
    </div>
  );
}

export default ProjectThemeScope;
