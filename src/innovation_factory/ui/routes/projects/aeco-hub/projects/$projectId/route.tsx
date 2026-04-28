import { createFileRoute, Link, Outlet, useLocation, useParams } from "@tanstack/react-router";
import { Suspense } from "react";
import { ErrorBoundary } from "react-error-boundary";
import { QueryErrorResetBoundary } from "@tanstack/react-query";
import { useAeco_getProjectSuspense } from "@/lib/api";
import { selector } from "@/lib/selector";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ChevronLeft } from "lucide-react";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/projects/aeco-hub/projects/$projectId")({
  component: () => <ProjectLayout />,
});

const TABS = [
  { slug: "", label: "Overview" },
  { slug: "twin", label: "Twin" },
  { slug: "design", label: "Design" },
  { slug: "build", label: "Build" },
  { slug: "operate", label: "Operate" },
  { slug: "documents", label: "Documents" },
  { slug: "issues", label: "Issues" },
];

function ProjectLayout() {
  const { projectId } = useParams({ from: "/projects/aeco-hub/projects/$projectId" });

  return (
    <div className="p-6 space-y-6">
      <Link
        to="/projects/aeco-hub"
        className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
      >
        <ChevronLeft size={14} />
        Portfolio
      </Link>

      <QueryErrorResetBoundary>
        {({ reset }) => (
          <ErrorBoundary
            onReset={reset}
            fallbackRender={() => (
              <Card>
                <CardContent className="p-6 text-destructive">
                  Failed to load project.
                </CardContent>
              </Card>
            )}
          >
            <Suspense fallback={<ProjectHeaderSkeleton />}>
              <ProjectHeader projectId={Number(projectId)} />
            </Suspense>
          </ErrorBoundary>
        )}
      </QueryErrorResetBoundary>

      <ProjectTabs projectId={projectId} />

      <Outlet />
    </div>
  );
}

function ProjectHeader({ projectId }: { projectId: number }) {
  const { data: project } = useAeco_getProjectSuspense({
    params: { project_id: projectId },
    ...selector(),
  });

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-bold tracking-tight">{project.name}</h1>
        <PhaseBadge phase={project.phase} />
      </div>
      <p className="text-sm text-muted-foreground">
        {project.code} · {project.client_name} · {project.city}, {project.country}
      </p>
      <p className="text-sm text-muted-foreground max-w-3xl">{project.description}</p>
      <div className="flex items-center gap-4 pt-2 text-xs">
        <div className="flex items-center gap-2">
          <span className="text-muted-foreground">Progress</span>
          <span className="font-medium">{project.progress_pct.toFixed(0)}%</span>
          <div className="w-32 h-1.5 bg-muted rounded-full overflow-hidden">
            <div
              className="h-full bg-amber-500 rounded-full"
              style={{ width: `${project.progress_pct}%` }}
            />
          </div>
        </div>
        <div className="text-muted-foreground">
          Budget {formatEuro(project.budget_eur)} · Spent{" "}
          <span className="font-medium text-foreground">{formatEuro(project.actual_cost_eur)}</span>
        </div>
      </div>
    </div>
  );
}

function ProjectTabs({ projectId }: { projectId: string }) {
  const location = useLocation();
  const base = `/projects/aeco-hub/projects/${projectId}`;

  return (
    <nav className="border-b">
      <div className="flex gap-1 -mb-px overflow-x-auto">
        {TABS.map((tab) => {
          const to = tab.slug ? `${base}/${tab.slug}` : base;
          const isActive =
            tab.slug === ""
              ? location.pathname === base || location.pathname === `${base}/`
              : location.pathname.startsWith(`${base}/${tab.slug}`);
          return (
            <Link
              key={tab.slug}
              to={to}
              className={cn(
                "px-4 py-2 text-sm font-medium border-b-2 transition-colors",
                isActive
                  ? "border-amber-500 text-foreground"
                  : "border-transparent text-muted-foreground hover:text-foreground hover:border-muted-foreground/30",
              )}
            >
              {tab.label}
            </Link>
          );
        })}
      </div>
    </nav>
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
    <Badge variant="outline" className={`text-xs capitalize ${styles[phase] ?? ""}`}>
      {phase}
    </Badge>
  );
}

function formatEuro(value: number): string {
  if (value >= 1_000_000) return `€${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `€${(value / 1_000).toFixed(0)}K`;
  return `€${value.toFixed(0)}`;
}

function ProjectHeaderSkeleton() {
  return (
    <div className="space-y-2">
      <Skeleton className="h-8 w-1/2" />
      <Skeleton className="h-4 w-1/3" />
      <Skeleton className="h-4 w-2/3" />
    </div>
  );
}
