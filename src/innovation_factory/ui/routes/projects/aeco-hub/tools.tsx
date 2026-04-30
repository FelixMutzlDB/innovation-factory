import { createFileRoute } from "@tanstack/react-router";
import { Suspense, useState } from "react";
import { ErrorBoundary } from "react-error-boundary";
import { QueryErrorResetBoundary } from "@tanstack/react-query";
import {
  useAeco_listToolsSuspense,
  type DtMarketplacePartnerOut,
} from "@/lib/api";
import { selector } from "@/lib/selector";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";

export const Route = createFileRoute("/projects/aeco-hub/tools")({
  component: () => <ToolsPage />,
});

const SEGMENTS: { key: string; label: string; description: string }[] = [
  { key: "design", label: "Design", description: "BIM authoring and architectural design tools" },
  { key: "qa_qc", label: "QA / QC", description: "Clash detection and rule-based model validation" },
  { key: "requirements", label: "Requirements", description: "Room data sheets and equipment briefs" },
  { key: "build", label: "Build", description: "Cost, schedule, site reports, and construction docs" },
  { key: "operate", label: "Operate", description: "Facility management, IoT, and lease management" },
  { key: "visualize", label: "Visualize", description: "Renderings, walkthroughs, and marketing assets" },
];

function ToolsPage() {
  const [selected, setSelected] = useState<DtMarketplacePartnerOut | null>(null);

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">AECO Tooling Ecosystem</h1>
        <p className="text-muted-foreground mt-1 max-w-3xl">
          The AECO Hub digital twin pulls data from a multi-vendor toolchain
          across the building lifecycle. Click any tool to see what data it
          contributes and its current integration status.
        </p>
      </div>

      <QueryErrorResetBoundary>
        {({ reset }) => (
          <ErrorBoundary
            onReset={reset}
            fallbackRender={() => (
              <Card>
                <CardContent className="p-6 text-destructive">Failed to load tools.</CardContent>
              </Card>
            )}
          >
            <Suspense fallback={<ToolsSkeleton />}>
              <ToolsBySegment onSelect={setSelected} />
            </Suspense>
          </ErrorBoundary>
        )}
      </QueryErrorResetBoundary>

      <Sheet open={selected !== null} onOpenChange={(open) => !open && setSelected(null)}>
        <SheetContent className="w-full sm:max-w-md">
          {selected && <ToolDetail partner={selected} />}
        </SheetContent>
      </Sheet>
    </div>
  );
}

function ToolsBySegment({ onSelect }: { onSelect: (p: DtMarketplacePartnerOut) => void }) {
  const { data: tools } = useAeco_listToolsSuspense(selector());
  const bySegment: Record<string, DtMarketplacePartnerOut[]> = {};
  for (const tool of tools) {
    (bySegment[tool.lifecycle_segment] ??= []).push(tool);
  }

  return (
    <div className="space-y-6">
      {SEGMENTS.map((segment) => {
        const segmentTools = bySegment[segment.key] ?? [];
        if (segmentTools.length === 0) return null;
        return (
          <section key={segment.key}>
            <div className="mb-3">
              <h2 className="text-lg font-semibold capitalize">{segment.label}</h2>
              <p className="text-sm text-muted-foreground">{segment.description}</p>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
              {segmentTools.map((tool) => (
                <button
                  key={tool.id}
                  onClick={() => onSelect(tool)}
                  className="text-left p-3 border rounded-lg bg-card hover:bg-muted/50 hover:border-amber-500/50 transition-colors"
                >
                  <div className="font-medium text-sm">{tool.name}</div>
                  <div className="text-xs text-muted-foreground line-clamp-2 mt-1">
                    {tool.description}
                  </div>
                </button>
              ))}
            </div>
          </section>
        );
      })}
    </div>
  );
}

function ToolDetail({ partner }: { partner: DtMarketplacePartnerOut }) {
  return (
    <>
      <SheetHeader>
        <SheetTitle>{partner.name}</SheetTitle>
        <SheetDescription className="capitalize">
          <Badge variant="outline" className="text-xs">
            {partner.lifecycle_segment.replace(/_/g, " ")}
          </Badge>
        </SheetDescription>
      </SheetHeader>
      <div className="py-4 space-y-4 text-sm">
        <p>{partner.description}</p>
        <div>
          <div className="text-xs uppercase text-muted-foreground tracking-wide">
            Data contributed to the twin
          </div>
          <p className="mt-1">{describeContribution(partner.lifecycle_segment)}</p>
        </div>
        <div>
          <div className="text-xs uppercase text-muted-foreground tracking-wide">
            Integration status
          </div>
          <p className="mt-1 text-muted-foreground">
            Status varies per project — see the Marketplace tab for per-project
            integration state.
          </p>
        </div>
        {partner.website && (
          <a
            href={partner.website}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-block text-amber-600 hover:underline text-xs"
          >
            {partner.website} ↗
          </a>
        )}
      </div>
    </>
  );
}

function describeContribution(segment: string): string {
  switch (segment) {
    case "design":
      return "IFC models, floor plans, 3D geometry. Lands in dt_bim_models + dt_model_elements.";
    case "qa_qc":
      return "Clash detection reports and rule validation results. Lands in dt_clash_reports.";
    case "requirements":
      return "Room data sheets and equipment specifications. Lands in dt_room_requirements.";
    case "build":
      return "Markups, cost estimates, site reports, progress. Feeds dt_cost_items, dt_schedule_activities, dt_site_reports.";
    case "operate":
      return "IoT data, space utilization, lease management. Feeds dt_sensor_readings, dt_space_utilization, dt_lease_contracts.";
    case "visualize":
      return "Renderings, walkthroughs, and marketing assets. Stored in the dt_documents library.";
    default:
      return "—";
  }
}

function ToolsSkeleton() {
  return (
    <div className="space-y-6">
      {Array.from({ length: 3 }).map((_, i) => (
        <div key={i}>
          <Skeleton className="h-5 w-32 mb-3" />
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {Array.from({ length: 4 }).map((_, j) => (
              <Skeleton key={j} className="h-20 w-full" />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
