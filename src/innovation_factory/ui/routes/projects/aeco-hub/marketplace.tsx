import { createFileRoute } from "@tanstack/react-router";
import { Suspense, useState } from "react";
import { ErrorBoundary } from "react-error-boundary";
import { QueryErrorResetBoundary } from "@tanstack/react-query";
import { useAeco_listMarketplaceAppsSuspense } from "@/lib/api";
import { selector } from "@/lib/selector";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Star } from "lucide-react";

export const Route = createFileRoute("/projects/aeco-hub/marketplace")({
  component: () => <MarketplacePage />,
});

const SEGMENT_LABEL: Record<string, string> = {
  design: "Design",
  qa_qc: "QA / QC",
  requirements: "Requirements",
  build: "Build",
  operate: "Operate",
  visualize: "Visualize",
};

function MarketplacePage() {
  const [segment, setSegment] = useState<string>("");

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">AECO Marketplace</h1>
          <p className="text-muted-foreground mt-1 max-w-3xl">
            Partner connectors and pre-built apps that plug into the AECO Hub
            digital twin.
          </p>
        </div>
        <Select
          value={segment || "all"}
          onValueChange={(v) => setSegment(v === "all" ? "" : v)}
        >
          <SelectTrigger className="w-44">
            <SelectValue placeholder="All segments" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All segments</SelectItem>
            {Object.entries(SEGMENT_LABEL).map(([k, l]) => (
              <SelectItem key={k} value={k}>{l}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <QueryErrorResetBoundary>
        {({ reset }) => (
          <ErrorBoundary
            onReset={reset}
            fallbackRender={() => (
              <Card>
                <CardContent className="p-6 text-destructive">
                  Failed to load marketplace.
                </CardContent>
              </Card>
            )}
          >
            <Suspense fallback={<GridSkeleton />}>
              <AppsGrid segment={segment} />
            </Suspense>
          </ErrorBoundary>
        )}
      </QueryErrorResetBoundary>
    </div>
  );
}

function AppsGrid({ segment }: { segment: string }) {
  const { data: apps } = useAeco_listMarketplaceAppsSuspense({
    params: segment ? { lifecycle_segment: segment as never } : undefined,
    ...selector(),
  });

  if (apps.length === 0) {
    return (
      <Card>
        <CardContent className="p-6 text-center text-muted-foreground">
          No apps in this segment.
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {apps.map((app) => (
        <Card key={app.id} className="hover:border-amber-500/50 transition-colors">
          <CardContent className="p-4 space-y-3">
            <div className="flex items-start justify-between gap-2">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold">{app.name}</h3>
                  {app.is_featured && (
                    <Star size={14} className="text-amber-500 fill-amber-500" />
                  )}
                </div>
                <div className="text-xs text-muted-foreground">{app.partner_name}</div>
              </div>
              <Badge variant="outline" className="text-xs capitalize whitespace-nowrap">
                {app.lifecycle_segment.replace(/_/g, " ")}
              </Badge>
            </div>
            <p className="text-sm text-muted-foreground line-clamp-3">
              {app.description}
            </p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function GridSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {Array.from({ length: 6 }).map((_, i) => (
        <Card key={i}>
          <CardContent className="p-4 space-y-3">
            <Skeleton className="h-5 w-3/4" />
            <Skeleton className="h-3 w-1/3" />
            <Skeleton className="h-12 w-full" />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
