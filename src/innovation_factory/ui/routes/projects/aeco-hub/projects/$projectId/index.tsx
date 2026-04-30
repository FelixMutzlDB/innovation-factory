import { createFileRoute, useParams } from "@tanstack/react-router";
import { Suspense } from "react";
import { ErrorBoundary } from "react-error-boundary";
import { QueryErrorResetBoundary } from "@tanstack/react-query";
import {
  useAeco_getProjectKpisSuspense,
  useAeco_getIssueStatsSuspense,
  useAeco_getDocumentStatsSuspense,
} from "@/lib/api";
import { selector } from "@/lib/selector";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Building2,
  Layers,
  Users,
  AlertCircle,
  FileText,
} from "lucide-react";

export const Route = createFileRoute("/projects/aeco-hub/projects/$projectId/")({
  component: () => <OverviewPage />,
});

function OverviewPage() {
  const { projectId } = useParams({ from: "/projects/aeco-hub/projects/$projectId/" });
  const pid = Number(projectId);

  return (
    <div className="space-y-6">
      <QueryErrorResetBoundary>
        {({ reset }) => (
          <ErrorBoundary
            onReset={reset}
            fallbackRender={() => (
              <Card>
                <CardContent className="p-6 text-destructive">
                  Failed to load overview.
                </CardContent>
              </Card>
            )}
          >
            <Suspense fallback={<OverviewSkeleton />}>
              <KpiBlock pid={pid} />
              <SummaryBlocks pid={pid} />
            </Suspense>
          </ErrorBoundary>
        )}
      </QueryErrorResetBoundary>
    </div>
  );
}

function KpiBlock({ pid }: { pid: number }) {
  const { data: kpis } = useAeco_getProjectKpisSuspense({
    params: { project_id: pid },
    ...selector(),
  });

  const items = [
    { label: "Buildings", value: kpis.building_count, icon: <Building2 size={16} /> },
    { label: "Floors", value: kpis.floor_count, icon: <Layers size={16} /> },
    { label: "Spaces", value: kpis.space_count, icon: <Layers size={16} /> },
    { label: "Members", value: kpis.member_count, icon: <Users size={16} /> },
    { label: "Open Issues", value: kpis.open_issues, icon: <AlertCircle size={16} /> },
    { label: "Documents", value: kpis.documents_count, icon: <FileText size={16} /> },
  ];

  return (
    <div>
      <h2 className="text-lg font-semibold mb-3">Project KPIs</h2>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {items.map((item) => (
          <Card key={item.label}>
            <CardContent className="p-4">
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                {item.icon}
                {item.label}
              </div>
              <p className="text-2xl font-bold mt-1">{item.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>
      <div className="mt-3 grid grid-cols-1 md:grid-cols-3 gap-3">
        <Card>
          <CardContent className="p-4">
            <div className="text-xs text-muted-foreground">Cost variance</div>
            <p
              className={`text-xl font-bold mt-1 ${kpis.cost_variance_pct > 5 ? "text-red-600" : kpis.cost_variance_pct < -5 ? "text-green-600" : ""}`}
            >
              {kpis.cost_variance_pct > 0 ? "+" : ""}
              {kpis.cost_variance_pct.toFixed(1)}%
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="text-xs text-muted-foreground">Budget</div>
            <p className="text-xl font-bold mt-1">{formatEuro(kpis.budget_eur)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="text-xs text-muted-foreground">Spent to date</div>
            <p className="text-xl font-bold mt-1">{formatEuro(kpis.actual_cost_eur)}</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function SummaryBlocks({ pid }: { pid: number }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <IssueSummary pid={pid} />
      <DocumentSummary pid={pid} />
    </div>
  );
}

function IssueSummary({ pid }: { pid: number }) {
  const { data: stats } = useAeco_getIssueStatsSuspense({
    params: { project_id: pid },
    ...selector(),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <AlertCircle size={16} />
          Issues
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="grid grid-cols-4 gap-2 text-center">
          <div>
            <div className="text-xl font-bold">{stats.total}</div>
            <div className="text-xs text-muted-foreground">Total</div>
          </div>
          <div>
            <div className="text-xl font-bold text-amber-600">{stats.open}</div>
            <div className="text-xs text-muted-foreground">Open</div>
          </div>
          <div>
            <div className="text-xl font-bold">{stats.in_progress}</div>
            <div className="text-xs text-muted-foreground">In progress</div>
          </div>
          <div>
            <div className="text-xl font-bold text-red-600">{stats.critical}</div>
            <div className="text-xs text-muted-foreground">Critical</div>
          </div>
        </div>
        <div className="pt-2 text-xs text-muted-foreground">
          Top categories:{" "}
          {Object.entries(stats.by_category)
            .filter(([_, n]) => n > 0)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 3)
            .map(([k, v]) => `${k} (${v})`)
            .join(" · ")}
        </div>
      </CardContent>
    </Card>
  );
}

function DocumentSummary({ pid }: { pid: number }) {
  const { data: stats } = useAeco_getDocumentStatsSuspense({
    params: { project_id: pid },
    ...selector(),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <FileText size={16} />
          Documents
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold mb-3">{stats.total}</div>
        <div className="grid grid-cols-2 gap-2 text-xs">
          {Object.entries(stats.by_phase)
            .filter(([_, n]) => n > 0)
            .map(([phase, n]) => (
              <div key={phase} className="flex items-center justify-between">
                <span className="text-muted-foreground capitalize">{phase}</span>
                <span className="font-medium">{n}</span>
              </div>
            ))}
        </div>
      </CardContent>
    </Card>
  );
}

function OverviewSkeleton() {
  return (
    <div className="space-y-3">
      <Skeleton className="h-6 w-32" />
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <Card key={i}>
            <CardContent className="p-4 space-y-2">
              <Skeleton className="h-3 w-16" />
              <Skeleton className="h-7 w-12" />
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

function formatEuro(value: number): string {
  if (value >= 1_000_000) return `€${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `€${(value / 1_000).toFixed(0)}K`;
  return `€${value.toFixed(0)}`;
}
