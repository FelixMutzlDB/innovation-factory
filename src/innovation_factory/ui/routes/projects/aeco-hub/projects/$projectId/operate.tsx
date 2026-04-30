import { createFileRoute, useParams } from "@tanstack/react-router";
import { Suspense } from "react";
import { ErrorBoundary } from "react-error-boundary";
import { QueryErrorResetBoundary } from "@tanstack/react-query";
import {
  useAeco_listSensorsSuspense,
  useAeco_listMaintenanceOrdersSuspense,
  useAeco_getMaintenanceStatsSuspense,
  useAeco_getEnergyTrendSuspense,
  useAeco_getLiveSensorsSuspense,
  useAeco_listLeaseContractsSuspense,
  useAeco_getDatabricksResourcesSuspense,
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
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { Activity, Wrench, Zap, Receipt } from "lucide-react";

export const Route = createFileRoute("/projects/aeco-hub/projects/$projectId/operate")({
  component: () => <OperatePage />,
});

const PRIORITY_COLOR: Record<string, string> = {
  low: "bg-slate-500/15 text-slate-600 border-slate-500/30",
  medium: "bg-blue-500/15 text-blue-600 border-blue-500/30",
  high: "bg-amber-500/15 text-amber-600 border-amber-500/30",
  urgent: "bg-red-500/15 text-red-600 border-red-500/30",
};

function OperatePage() {
  const { projectId } = useParams({ from: "/projects/aeco-hub/projects/$projectId/operate" });
  const pid = Number(projectId);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Wrap>
          <Suspense fallback={<MiniSkeleton />}>
            <MaintenanceStatsCard pid={pid} />
          </Suspense>
        </Wrap>
        <Wrap>
          <Suspense fallback={<MiniSkeleton />}>
            <SensorCountCard pid={pid} />
          </Suspense>
        </Wrap>
        <Wrap>
          <Suspense fallback={<MiniSkeleton />}>
            <LeaseCountCard pid={pid} />
          </Suspense>
        </Wrap>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Activity size={16} />
            Live IoT feed (refreshes every 10s)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Wrap>
            <Suspense fallback={<Skeleton className="h-48 w-full" />}>
              <LiveSensorsPanel pid={pid} />
            </Suspense>
          </Wrap>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Zap size={16} />
            Daily energy consumption (last 30 days)
          </CardTitle>
        </CardHeader>
        <CardContent className="h-72">
          <Wrap>
            <Suspense fallback={<Skeleton className="h-full w-full" />}>
              <EnergyChart pid={pid} />
            </Suspense>
          </Wrap>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Wrench size={16} />
            Maintenance orders
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <Wrap>
            <Suspense fallback={<RowSkeleton />}>
              <MaintenanceTable pid={pid} />
            </Suspense>
          </Wrap>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Zap size={16} />
            Energy & Sustainability dashboard (AI/BI)
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <Wrap>
            <Suspense fallback={<Skeleton className="h-[600px] w-full" />}>
              <DashboardEmbed />
            </Suspense>
          </Wrap>
        </CardContent>
      </Card>
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

function MaintenanceStatsCard({ pid }: { pid: number }) {
  const { data: stats } = useAeco_getMaintenanceStatsSuspense({
    params: { project_id: pid },
    ...selector(),
  });
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <Wrench size={16} />
          Maintenance
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 gap-2 text-center">
          <Stat n={stats.open} label="Open" />
          <Stat n={stats.in_progress} label="In progress" />
          <Stat n={stats.overdue} label="Overdue" tone={stats.overdue > 0 ? "red" : undefined} />
        </div>
        <div className="mt-3 text-xs text-muted-foreground">
          Avg time to complete: {stats.avg_days_to_complete.toFixed(1)} days
        </div>
      </CardContent>
    </Card>
  );
}

function SensorCountCard({ pid }: { pid: number }) {
  const { data: sensors } = useAeco_listSensorsSuspense({
    params: { project_id: pid, limit: 500 },
    ...selector(),
  });
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <Activity size={16} />
          Sensors
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-3xl font-bold">{sensors.length}</div>
        <div className="text-xs text-muted-foreground mt-1">
          Across all building automation systems
        </div>
      </CardContent>
    </Card>
  );
}

function LeaseCountCard({ pid }: { pid: number }) {
  const { data: leases } = useAeco_listLeaseContractsSuspense({
    params: { project_id: pid, limit: 200 },
    ...selector(),
  });
  const active = leases.filter((l) => l.status === "active").length;
  const totalRent = leases
    .filter((l) => l.status === "active")
    .reduce((s, l) => s + l.monthly_rent_eur, 0);
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <Receipt size={16} />
          Leases
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-2 text-center">
          <Stat n={active} label="Active" />
          <Stat n={formatEuro(totalRent)} label="Monthly" />
        </div>
      </CardContent>
    </Card>
  );
}

function EnergyChart({ pid }: { pid: number }) {
  const { data: trend } = useAeco_getEnergyTrendSuspense({
    params: { project_id: pid },
    ...selector(),
  });
  if (trend.length === 0) {
    return (
      <div className="h-full flex items-center justify-center text-sm text-muted-foreground">
        No energy data available for this project.
      </div>
    );
  }
  const data = trend.map((p) => ({
    date: new Date(p.period_start).toLocaleDateString(undefined, { month: "short", day: "numeric" }),
    kwh: p.kwh,
    cost: p.cost_eur,
  }));
  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
        <XAxis dataKey="date" tick={{ fontSize: 11 }} />
        <YAxis tick={{ fontSize: 11 }} />
        <Tooltip
          contentStyle={{
            background: "hsl(var(--card))",
            border: "1px solid hsl(var(--border))",
            borderRadius: 6,
            fontSize: 12,
          }}
        />
        <Line type="monotone" dataKey="kwh" stroke="#F59E0B" strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}

function MaintenanceTable({ pid }: { pid: number }) {
  const { data: orders } = useAeco_listMaintenanceOrdersSuspense({
    params: { project_id: pid, limit: 30 },
    ...selector(),
  });
  if (orders.length === 0) return <Empty msg="No maintenance orders for this project." />;

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Title</TableHead>
          <TableHead>Priority</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Technician</TableHead>
          <TableHead>Due</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {orders.map((o) => (
          <TableRow key={o.id}>
            <TableCell className="font-medium max-w-md truncate">{o.title}</TableCell>
            <TableCell>
              <Badge variant="outline" className={`text-xs capitalize ${PRIORITY_COLOR[o.priority] ?? ""}`}>
                {o.priority}
              </Badge>
            </TableCell>
            <TableCell className="text-sm capitalize">{o.status.replace(/_/g, " ")}</TableCell>
            <TableCell className="text-sm">{o.assigned_technician}</TableCell>
            <TableCell className="text-sm">{o.due_date ?? "—"}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

function DashboardEmbed() {
  const { data: resources } = useAeco_getDatabricksResourcesSuspense(selector());
  if (!resources.energy_dashboard_configured) {
    return (
      <div className="p-6 text-center text-sm text-muted-foreground">
        Energy dashboard ID not configured. Set
        <code className="mx-1 px-1 bg-muted rounded">AECO_ENERGY_DASHBOARD_ID</code>
        in app.yml after running the bootstrap.
      </div>
    );
  }
  return (
    <iframe
      src={resources.energy_dashboard_embed_url}
      title="AECO Hub — Energy & Sustainability dashboard"
      className="w-full h-[600px] border-0"
    />
  );
}

function LiveSensorsPanel({ pid }: { pid: number }) {
  const result = useAeco_getLiveSensorsSuspense({
    params: { project_id: pid },
    query: {
      refetchInterval: 10_000,
      ...selector().query,
    } as never,
  });
  // selector() unwraps `.data` at runtime, but TypeScript can't see through
  // the `as never` cast we need for the polling option, so cast here.
  const data = result.data as unknown as import("@/lib/api").DtLiveSensorsOut;

  if (data.series.length === 0) {
    return (
      <div className="text-sm text-muted-foreground p-4 text-center">
        Live IoT feed available only for operating projects.
      </div>
    );
  }

  const SENSOR_COLOR: Record<string, string> = {
    zone_temp: "#F59E0B",
    co2_concentration: "#3B82F6",
    relative_humidity: "#10B981",
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {data.series.map((s) => {
        const points = s.points.map((p) => ({
          t: new Date(p.ts).toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" }),
          v: p.value,
        }));
        const latest = s.points[s.points.length - 1];
        return (
          <div key={s.sensor_code} className="space-y-1">
            <div className="flex items-baseline justify-between">
              <span className="text-xs uppercase text-muted-foreground tracking-wide">
                {s.sensor_type.replace(/_/g, " ")}
              </span>
              <span className="text-lg font-bold">
                {latest?.value.toFixed(1)} {s.unit}
              </span>
            </div>
            <div className="h-24">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={points} margin={{ top: 4, right: 4, bottom: 0, left: 0 }}>
                  <Line
                    type="monotone"
                    dataKey="v"
                    stroke={SENSOR_COLOR[s.sensor_type] ?? "#888"}
                    strokeWidth={1.5}
                    dot={false}
                    isAnimationActive={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function Stat({ n, label, tone }: { n: number | string; label: string; tone?: "red" }) {
  return (
    <div>
      <div className={`text-xl font-bold ${tone === "red" ? "text-red-600" : ""}`}>{n}</div>
      <div className="text-xs text-muted-foreground">{label}</div>
    </div>
  );
}

function formatEuro(value: number): string {
  if (value >= 1_000_000) return `€${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `€${(value / 1_000).toFixed(0)}K`;
  return `€${value.toFixed(0)}`;
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
