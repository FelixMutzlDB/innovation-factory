import type { CSSProperties } from "react";
import { BRAND_THEMES } from "@/lib/brand-themes";

interface ProjectHeroPatternProps {
  slug: string;
  className?: string;
  ariaLabel?: string;
}

// Abstract SVG hero pattern, brand-tinted from --primary / --secondary.
// Pure decoration — no photography, no SVG that resembles a customer mark.
// Routes opt in by mounting this where they want a hero element; the home
// route currently does not auto-mount it (P4 deferral in
// docs/ci-implementation-plan.md §10).
export function ProjectHeroPattern({
  slug,
  className,
  ariaLabel,
}: ProjectHeroPatternProps) {
  const theme = BRAND_THEMES[slug];
  if (!theme) return null;

  const style: CSSProperties = {
    color: "var(--primary)",
  };

  return (
    <svg
      aria-hidden={ariaLabel ? undefined : true}
      aria-label={ariaLabel}
      role={ariaLabel ? "img" : undefined}
      className={className}
      viewBox="0 0 800 240"
      preserveAspectRatio="xMidYMid slice"
      style={style}
    >
      <defs>
        <linearGradient id={`phpat-${slug}-fade`} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="currentColor" stopOpacity="0.18" />
          <stop offset="100%" stopColor="var(--secondary)" stopOpacity="0.08" />
        </linearGradient>
        <pattern
          id={`phpat-${slug}-dots`}
          width="32"
          height="32"
          patternUnits="userSpaceOnUse"
        >
          <circle cx="2" cy="2" r="1.3" fill="currentColor" fillOpacity="0.22" />
        </pattern>
      </defs>
      <rect width="800" height="240" fill={`url(#phpat-${slug}-fade)`} />
      <rect width="800" height="240" fill={`url(#phpat-${slug}-dots)`} />
      <g fill="none" stroke="currentColor" strokeOpacity="0.35" strokeWidth="1.2">
        <path d="M0,160 Q200,80 400,160 T800,160" />
        <path d="M0,200 Q200,120 400,200 T800,200" strokeOpacity="0.2" />
      </g>
    </svg>
  );
}
