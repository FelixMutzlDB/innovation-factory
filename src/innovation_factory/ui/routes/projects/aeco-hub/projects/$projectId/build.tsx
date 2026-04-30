import { createFileRoute, useParams } from "@tanstack/react-router";
import { Suspense } from "react";
import { ErrorBoundary } from "react-error-boundary";
import { QueryErrorResetBoundary } from "@tanstack/react-query";
import {
  useAeco_listScheduleActivitiesSuspense,
  useAeco_getScheduleSummarySuspense,
  useAeco_listCostItemsSuspense,
  useAeco_getCostSummarySuspense,
  useAeco_listSiteReportsSuspense,
  useAeco_listChangeOrdersSuspense,
} from "@/lib/api";
import { selector } from "@/lib/selector";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { CalendarDays, Wallet, FileText, Replace } from "lucide-react";

export const Route = createFileRoute("/projects/aeco-hub/projects/$projectId/build")({
  component: () => <BuildPage />,
});

function BuildPage() {
  const { projectId } = useParams({ from: "/projects/aeco-hub/projects/$projectId/build" });
  const pid = Number(projectId);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Wrap>
          <Suspense fallback={<MiniSkeleton />}>
            <ScheduleSummary pid={pid} />
          </Suspense>
        </Wrap>
        <Wrap>
          <Suspense fallback={<MiniSkeleton />}>
            <CostSummary pid={pid} />
          </Suspense>
        </Wrap>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <CalendarDays size={16} />
            Schedule
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <Wrap>
            <Suspense fallback={<RowSkeleton />}>
              <ScheduleTable pid={pid} />
            </Suspense>
          </Wrap>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Wallet size={16} />
            Cost items
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <Wrap>
            <Suspense fallback={<RowSkeleton />}>
              <CostTable pid={pid} />
            </Suspense>
          </Wrap>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <FileText size={16} />
              Site reports
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <Wrap>
              <Suspense fallback={<RowSkeleton />}>
                <SiteReportsTable pid={pid} />
              </Suspense>
            </Wrap>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Replace size={16} />
              Change orders
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <Wrap>
              <Suspense fallback={<RowSkeleton />}>
                <ChangeOrdersTable pid={pid} />
              </Suspense>
            </Wrap>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function Wrap({ children }: { children: React.ReactNode }) {
  return (
    <QueryErrorResetBoundary>
      {({ reset }) => (
        <ErrorBoundary
          onReset={reset}
          fallbackRender={() => (
            <div className="p-6 text-destructive text-sm">Failed to load.</div>
          )}
        >
          {children}
        </ErrorBoundary>
      )}
    </QueryErrorResetBoundary>
  );
}

function ScheduleSummary({ pid }: { pid: number }) {
  const { data } = useAeco_getScheduleSummarySuspense({
    params: { project_id: pid },
    ...selector(),
  });
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Schedule</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-4 gap-2 text-center">
          <Stat n={data.not_started} label="Not started" />
          <Stat n={data.in_progress} label="In progress" />
          <Stat n={data.completed} label="Completed" />
          <Stat n={data.delayed} label="Delayed" tone="red" />
        </div>
        <div className="mt-3 text-xs text-muted-foreground">
          Avg progress: {data.avg_progress_pct.toFixed(0)}% ({data.total} activities)
        </div>
      </CardContent>
    </Card>
  );
}

function CostSummary({ pid }: { pid: number }) {
  const { data } = useAeco_getCostSummarySuspense({
    params: { project_id: pid },
    ...selector(),
  });
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Cost</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 gap-2 text-center">
          <Stat n={formatEuro(data.total_estimated_eur)} label="Estimated" />
          <Stat n={formatEuro(data.total_actual_eur)} label="Actual" />
          <Stat
            n={`${data.variance_pct > 0 ? "+" : ""}${data.variance_pct.toFixed(1)}%`}
            label="Variance"
            tone={data.variance_pct > 5 ? "red" : data.variance_pct < -5 ? "green" : undefined}
          />
        </div>
        <div className="mt-3 text-xs text-muted-foreground">{data.item_count} cost items</div>
      </CardContent>
    </Card>
  );
}

function Stat({ n, label, tone }: { n: number | string; label: string; tone?: "red" | "green" }) {
  const color =
    tone === "red"
      ? "text-red-600"
      : tone === "green"
        ? "text-green-600"
        : "";
  return (
    <div>
      <div className={`text-xl font-bold ${color}`}>{n}</div>
      <div className="text-xs text-muted-foreground">{label}</div>
    </div>
  );
}

function ScheduleTable({ pid }: { pid: number }) {
  const { data: activities } = useAeco_listScheduleActivitiesSuspense({
    params: { project_id: pid, limit: 30 },
    ...selector(),
  });
  if (activities.length === 0) return <Empty msg="No schedule data." />;

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Activity</TableHead>
          <TableHead>Start</TableHead>
          <TableHead>End</TableHead>
          <TableHead>Progress</TableHead>
          <TableHead>Status</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {activities.slice(0, 30).map((a) => (
          <TableRow key={a.id}>
            <TableCell className="font-medium">{a.name}</TableCell>
            <TableCell className="text-sm">{a.start_date}</TableCell>
            <TableCell className="text-sm">{a.end_date}</TableCell>
            <TableCell className="text-sm">{a.progress_pct.toFixed(0)}%</TableCell>
            <TableCell>
              <Badge variant="outline" className="text-xs capitalize">
                {a.status.replace(/_/g, " ")}
              </Badge>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

function CostTable({ pid }: { pid: number }) {
  const { data: items } = useAeco_listCostItemsSuspense({
    params: { project_id: pid, limit: 30 },
    ...selector(),
  });
  if (items.length === 0) return <Empty msg="No cost items." />;
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Code</TableHead>
          <TableHead>Description</TableHead>
          <TableHead>Category</TableHead>
          <TableHead>Estimated</TableHead>
          <TableHead>Actual</TableHead>
          <TableHead>Status</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {items.map((i) => (
          <TableRow key={i.id}>
            <TableCell className="font-mono text-xs">{i.code}</TableCell>
            <TableCell className="text-sm">{i.description}</TableCell>
            <TableCell className="text-sm">{i.category}</TableCell>
            <TableCell className="text-sm">{formatEuro(i.estimated_eur)}</TableCell>
            <TableCell className="text-sm">
              {i.actual_eur > 0 ? formatEuro(i.actual_eur) : "—"}
            </TableCell>
            <TableCell>
              <Badge variant="outline" className="text-xs capitalize">
                {i.status}
              </Badge>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

function SiteReportsTable({ pid }: { pid: number }) {
  const { data: reports } = useAeco_listSiteReportsSuspense({
    params: { project_id: pid, limit: 10 },
    ...selector(),
  });
  if (reports.length === 0) return <Empty msg="No site reports." />;
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Date</TableHead>
          <TableHead>Type</TableHead>
          <TableHead>Author</TableHead>
          <TableHead>Workforce</TableHead>
          <TableHead>Issues</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {reports.map((r) => (
          <TableRow key={r.id}>
            <TableCell className="text-sm">{r.report_date}</TableCell>
            <TableCell className="text-sm capitalize">{r.report_type}</TableCell>
            <TableCell className="text-sm">{r.author}</TableCell>
            <TableCell className="text-sm">{r.workforce_count}</TableCell>
            <TableCell className="text-sm">{r.issues_count}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

function ChangeOrdersTable({ pid }: { pid: number }) {
  const { data: orders } = useAeco_listChangeOrdersSuspense({
    params: { project_id: pid, limit: 10 },
    ...selector(),
  });
  if (orders.length === 0) return <Empty msg="No change orders." />;
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Title</TableHead>
          <TableHead>Cost impact</TableHead>
          <TableHead>Sched ±d</TableHead>
          <TableHead>Status</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {orders.map((o) => (
          <TableRow key={o.id}>
            <TableCell className="text-sm font-medium max-w-xs truncate">{o.title}</TableCell>
            <TableCell className="text-sm">{formatEuro(o.cost_impact_eur)}</TableCell>
            <TableCell className="text-sm">{o.schedule_impact_days}</TableCell>
            <TableCell>
              <Badge variant="outline" className="text-xs capitalize">
                {o.status}
              </Badge>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

function formatEuro(value: number): string {
  const sign = value < 0 ? "-" : "";
  const abs = Math.abs(value);
  if (abs >= 1_000_000) return `${sign}€${(abs / 1_000_000).toFixed(1)}M`;
  if (abs >= 1_000) return `${sign}€${(abs / 1_000).toFixed(0)}K`;
  return `${sign}€${abs.toFixed(0)}`;
}

function Empty({ msg }: { msg: string }) {
  return <div className="p-6 text-center text-sm text-muted-foreground">{msg}</div>;
}

function MiniSkeleton() {
  return (
    <Card>
      <CardContent className="p-4 space-y-2">
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-12 w-full" />
      </CardContent>
    </Card>
  );
}

function RowSkeleton() {
  return (
    <div className="p-4 space-y-2">
      {Array.from({ length: 4 }).map((_, i) => (
        <Skeleton key={i} className="h-8 w-full" />
      ))}
    </div>
  );
}
