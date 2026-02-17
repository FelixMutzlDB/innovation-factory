import { createFileRoute } from "@tanstack/react-router";
import { Suspense } from "react";
import { ErrorBoundary } from "react-error-boundary";
import { QueryErrorResetBoundary } from "@tanstack/react-query";
import { useMac_getDashboardEmbedSuspense } from "@/lib/api";
import selector from "@/lib/selector";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { BarChart3, ExternalLink, AlertCircle } from "lucide-react";

export const Route = createFileRoute("/projects/mol-asm-cockpit/explorer")({
  component: () => <ExplorerPage />,
});

function ExplorerPage() {
  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] min-h-[400px]">
      <QueryErrorResetBoundary>
        {({ reset }) => (
          <ErrorBoundary
            onReset={reset}
            fallbackRender={({ resetErrorBoundary }) => (
              <Card className="flex-1 flex flex-col">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-destructive">
                    <AlertCircle className="h-5 w-5" />
                    Failed to Load Dashboard
                  </CardTitle>
                  <CardDescription>
                    There was an error loading the dashboard configuration.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Button variant="outline" onClick={resetErrorBoundary}>
                    Try Again
                  </Button>
                </CardContent>
              </Card>
            )}
          >
            <Suspense fallback={<ExplorerSkeleton />}>
              <ExplorerContent />
            </Suspense>
          </ErrorBoundary>
        )}
      </QueryErrorResetBoundary>
    </div>
  );
}

function ExplorerContent() {
  const { data: embedInfo } = useMac_getDashboardEmbedSuspense(selector());

  if (!embedInfo.configured || !embedInfo.embed_url) {
    return (
      <Card className="flex-1 flex flex-col border-dashed">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-amber-500/20 flex items-center justify-center">
              <BarChart3 className="h-5 w-5 text-amber-500" />
            </div>
            <div>
              <CardTitle>Demand & Inventory Explorer</CardTitle>
              <CardDescription>
                AI/BI dashboard not yet configured
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="flex-1 flex items-center justify-center border-2 border-dashed rounded-lg m-4 border-muted-foreground/25">
          <div className="text-center text-muted-foreground max-w-lg">
            <BarChart3 className="h-16 w-16 mx-auto mb-4 opacity-30" />
            <p className="text-lg font-medium mb-2">Dashboard Setup Required</p>
            <p className="text-sm mb-4">
              Run the dashboard creation script to create and publish the AI/BI
              dashboard, then set the <code className="bg-muted px-1 rounded text-xs">MAC_DASHBOARD_ID</code> environment
              variable.
            </p>
            <pre className="text-xs bg-muted p-3 rounded-lg text-left">
              {`# 1. Create the dashboard\nuv run python scripts/create_asm_cockpit_dashboard.py\n\n# 2. Set the dashboard ID\nexport MAC_DASHBOARD_ID=<dashboard_id>`}
            </pre>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="flex flex-col h-full gap-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-lg bg-amber-500/20 flex items-center justify-center">
            <BarChart3 className="h-5 w-5 text-amber-500" />
          </div>
          <div>
            <h2 className="font-semibold text-lg">
              Demand & Inventory Explorer
            </h2>
            <p className="text-sm text-muted-foreground">
              AI/BI dashboard &mdash; fuel, non-fuel, pricing &amp; workforce
            </p>
          </div>
        </div>
        <a
          href={embedInfo.embed_url.replace("/embed/", "/sql/")}
          target="_blank"
          rel="noopener noreferrer"
        >
          <Button variant="outline" size="sm" className="gap-1.5">
            <ExternalLink className="h-3.5 w-3.5" />
            Open in Databricks
          </Button>
        </a>
      </div>
      <div className="flex-1 rounded-lg border overflow-hidden bg-white">
        <iframe
          src={embedInfo.embed_url}
          className="w-full h-full border-0"
          title="ASM Cockpit - Demand & Inventory Explorer"
          allow="fullscreen"
        />
      </div>
    </div>
  );
}

function ExplorerSkeleton() {
  return (
    <Card className="flex-1 flex flex-col">
      <CardHeader>
        <div className="flex items-center gap-3">
          <Skeleton className="h-10 w-10 rounded-lg" />
          <div className="space-y-2">
            <Skeleton className="h-5 w-48" />
            <Skeleton className="h-4 w-72" />
          </div>
        </div>
      </CardHeader>
      <CardContent className="flex-1">
        <Skeleton className="w-full h-full rounded-lg" />
      </CardContent>
    </Card>
  );
}
