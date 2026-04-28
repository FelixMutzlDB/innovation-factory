import { createFileRoute, Link } from "@tanstack/react-router";
import { Suspense } from "react";
import { ErrorBoundary } from "react-error-boundary";
import { QueryErrorResetBoundary } from "@tanstack/react-query";
import {
  useAeco_getPortfolioStatsSuspense,
  useAeco_listProjectsSuspense,
} from "@/lib/api";
import { selector } from "@/lib/selector";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Building2,
  Hammer,
  PencilRuler,
  Activity,
  Wallet,
  TrendingUp,
} from "lucide-react";

export const Route = createFileRoute("/projects/aeco-hub/")({
  component: () => <OverviewPage />,
});

function OverviewPage() {
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">AECO Hub</h1>
        <p className="text-muted-foreground mt-1">
          Building lifecycle digital-twin platform for the Schuster Bau AG
          portfolio — from design through operations.
        </p>
      </div>

      <QueryErrorResetBoundary>
        {({ reset }) => (
          <ErrorBoundary
            onReset={reset}
            fallbackRender={({ resetErrorBoundary }) => (
              <Card>
                <CardContent className="p-6">
                  <p className="text-destructive">
                    Failed to load portfolio data.
                  </p>
                  <button
                    onClick={resetErrorBoundary}
                    className="mt-2 text-sm underline"
                  >
                    Retry
                  </button>
                </CardContent>
              </Card>
            )}
          >
            <Suspense fallback={<KpiSkeleton />}>
              <PortfolioKpis />
            </Suspense>
            <Suspense fallback={<ProjectsSkeleton />}>
              <ProjectGrid />
            </Suspense>
          </ErrorBoundary>
        )}
      </QueryErrorResetBoundary>
    </div>
  );
}

function PortfolioKpis() {
  const { data: stats } = useAeco_getPortfolioStatsSuspense(selector());

  const kpis = [
    {
      label: "Active Projects",
      value: stats.active_projects.toString(),
      icon: <Activity className="text-amber-500" size={18} />,
    },
    {
      label: "Buildings",
      value: stats.total_buildings.toString(),
      icon: <Building2 className="text-amber-500" size={18} />,
    },
    {
      label: "In Design",
      value: stats.design_projects.toString(),
      icon: <PencilRuler className="text-blue-500" size={18} />,
    },
    {
      label: "In Construction",
      value: stats.constructing_projects.toString(),
      icon: <Hammer className="text-orange-500" size={18} />,
    },
    {
      label: "Operating",
      value: stats.operating_projects.toString(),
      icon: <TrendingUp className="text-green-500" size={18} />,
    },
    {
      label: "Total Budget",
      value: formatEuro(stats.total_budget_eur),
      icon: <Wallet className="text-amber-500" size={18} />,
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {kpis.map((kpi) => (
        <Card key={kpi.label}>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              {kpi.icon}
              {kpi.label}
            </div>
            <p className="text-2xl font-bold mt-1">{kpi.value}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function ProjectGrid() {
  const { data: projects } = useAeco_listProjectsSuspense(selector());

  return (
    <div>
      <h2 className="text-xl font-semibold mb-3">Portfolio</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {projects.map((project) => (
          <Link
            key={project.id}
            to="/projects/aeco-hub/projects/$projectId"
            params={{ projectId: String(project.id) }}
            className="block group"
          >
            <Card className="transition-shadow hover:shadow-md group-hover:border-amber-500/50">
            <CardHeader>
              <div className="flex items-start justify-between gap-2">
                <CardTitle className="text-base leading-tight">
                  {project.name}
                </CardTitle>
                <PhaseBadge phase={project.phase} />
              </div>
              <CardDescription className="text-xs">
                {project.code} · {project.city}, {project.country}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="text-sm text-muted-foreground line-clamp-2">
                {project.description}
              </p>
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs">
                  <span className="text-muted-foreground">Progress</span>
                  <span className="font-medium">
                    {project.progress_pct.toFixed(0)}%
                  </span>
                </div>
                <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full bg-amber-500 rounded-full"
                    style={{ width: `${project.progress_pct}%` }}
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs pt-1">
                <div>
                  <div className="text-muted-foreground">Budget</div>
                  <div className="font-medium">
                    {formatEuro(project.budget_eur)}
                  </div>
                </div>
                <div>
                  <div className="text-muted-foreground">Spent</div>
                  <div className="font-medium">
                    {formatEuro(project.actual_cost_eur)}
                  </div>
                </div>
              </div>
            </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}

function PhaseBadge({ phase }: { phase: string }) {
  const styles: Record<string, string> = {
    design: "bg-blue-500/15 text-blue-600 border-blue-500/30",
    build: "bg-orange-500/15 text-orange-600 border-orange-500/30",
    operate: "bg-green-500/15 text-green-600 border-green-500/30",
    demolish: "bg-red-500/15 text-red-600 border-red-500/30",
  };
  return (
    <Badge
      variant="outline"
      className={`text-xs capitalize ${styles[phase] ?? ""}`}
    >
      {phase}
    </Badge>
  );
}

function formatEuro(value: number): string {
  if (value >= 1_000_000) {
    return `€${(value / 1_000_000).toFixed(1)}M`;
  }
  if (value >= 1_000) {
    return `€${(value / 1_000).toFixed(0)}K`;
  }
  return `€${value.toFixed(0)}`;
}

function KpiSkeleton() {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {Array.from({ length: 6 }).map((_, i) => (
        <Card key={i}>
          <CardContent className="p-4 space-y-2">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-8 w-16" />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function ProjectsSkeleton() {
  return (
    <div>
      <h2 className="text-xl font-semibold mb-3">Portfolio</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <Card key={i}>
            <CardContent className="p-4 space-y-3">
              <Skeleton className="h-5 w-3/4" />
              <Skeleton className="h-3 w-1/2" />
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-2 w-full" />
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
