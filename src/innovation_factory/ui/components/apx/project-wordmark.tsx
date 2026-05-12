import type { CSSProperties } from "react";
import { BRAND_THEMES } from "@/lib/brand-themes";
import { cn } from "@/lib/utils";

interface ProjectWordmarkProps {
  slug: string;
  className?: string;
  as?: "span" | "div";
}

/**
 * Pure-text wordmark for an accelerator's obfuscated display name.
 *
 * Renders `BRAND_THEMES[slug].displayName` styled with the project's brand
 * font (`var(--brand-font-family)`) and tinted with `var(--primary)`. Must
 * live inside a `<ProjectThemeScope>` so those custom properties resolve.
 *
 * Never renders an SVG logo — the legal rail in
 * docs/ci-implementation-plan.md §2 forbids customer marks. If the slug is
 * unknown the component renders nothing so partially-themed routes degrade
 * gracefully.
 */
export function ProjectWordmark({
  slug,
  className,
  as = "span",
}: ProjectWordmarkProps) {
  const theme = BRAND_THEMES[slug];
  if (!theme) {
    return null;
  }

  const style: CSSProperties = {
    fontFamily: "var(--brand-font-family, system-ui, sans-serif)",
    color: "var(--primary)",
  };

  const classes = cn(
    "font-semibold tracking-tight text-base leading-none",
    className,
  );

  const Tag = as;
  return (
    <Tag style={style} className={classes} data-project-wordmark={slug}>
      {theme.displayName}
    </Tag>
  );
}

export default ProjectWordmark;
