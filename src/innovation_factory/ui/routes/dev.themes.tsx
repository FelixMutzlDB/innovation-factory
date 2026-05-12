import { createFileRoute } from "@tanstack/react-router";
import { BRAND_THEMES } from "@/lib/brand-themes";
import { ProjectThemeScope } from "@/components/apx/project-theme-scope";
import { ProjectWordmark } from "@/components/apx/project-wordmark";
import { ProjectHeroPattern } from "@/components/apx/project-hero-pattern";

export const Route = createFileRoute("/dev/themes")({
  component: ThemesGallery,
});

// Dev/design gallery — renders every brand theme side-by-side so a designer
// can compare wordmarks, primary/secondary, chart slots, and the hero
// pattern without spinning up six dashboard routes. Not linked from the app
// nav; reach it directly at /dev/themes.
function ThemesGallery() {
  const slugs = Object.keys(BRAND_THEMES);

  return (
    <div className="min-h-screen bg-background p-8">
      <header className="mx-auto mb-8 max-w-6xl">
        <h1 className="text-2xl font-semibold">Brand themes gallery</h1>
        <p className="text-sm text-muted-foreground">
          One card per brand. Each card is wrapped in {`<ProjectThemeScope>`}
          {" "}so its tokens (--primary, --secondary, --chart-*, brand font) are
          live. Useful for visual comparison of wordmark, primary/secondary,
          and chart palette without navigating between project routes.
        </p>
      </header>

      <div className="mx-auto grid max-w-6xl grid-cols-1 gap-6 md:grid-cols-2">
        {slugs.map((slug) => (
          <ProjectThemeScope key={slug} slug={slug}>
            <BrandCard slug={slug} />
          </ProjectThemeScope>
        ))}
      </div>
    </div>
  );
}

function BrandCard({ slug }: { slug: string }) {
  const theme = BRAND_THEMES[slug];

  return (
    <article className="overflow-hidden rounded-lg border bg-card">
      <div className="relative h-32 w-full">
        <ProjectHeroPattern slug={slug} className="absolute inset-0 h-full w-full" />
      </div>

      <div className="space-y-4 p-5">
        <div>
          <ProjectWordmark slug={slug} className="text-xl" />
          <p className="mt-1 text-xs text-muted-foreground">
            {theme.customerRef} · {theme.fontUi}
            {theme.fontDisplay ? ` + ${theme.fontDisplay}` : ""}
          </p>
        </div>

        <Swatches slug={slug} />
      </div>
    </article>
  );
}

function Swatches({ slug }: { slug: string }) {
  // Solid hex from registry for primary/secondary (deterministic across
  // light/dark); chart slots use the live CSS vars so they reflect the
  // active mode.
  const theme = BRAND_THEMES[slug];
  return (
    <div className="space-y-2">
      <div className="flex gap-2 text-[10px]">
        <Swatch label="primary" color={theme.primaryHex} />
        <Swatch label="secondary" color={theme.secondaryHex} />
      </div>
      <div className="flex gap-1.5">
        {[1, 2, 3, 4, 5].map((n) => (
          <div
            key={n}
            className="h-6 flex-1 rounded"
            style={{ backgroundColor: `var(--chart-${n})` }}
            title={`--chart-${n}`}
          />
        ))}
      </div>
    </div>
  );
}

function Swatch({ label, color }: { label: string; color: string }) {
  return (
    <div className="flex flex-1 items-center gap-2">
      <div
        className="h-6 w-6 rounded border"
        style={{ backgroundColor: color }}
      />
      <div className="font-mono">
        <div className="text-muted-foreground">{label}</div>
        <div>{color}</div>
      </div>
    </div>
  );
}
