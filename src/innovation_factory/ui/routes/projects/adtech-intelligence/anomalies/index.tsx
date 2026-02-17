import { createFileRoute, Link } from "@tanstack/react-router";
import { Suspense, useState } from "react";
import { QueryErrorResetBoundary } from "@tanstack/react-query";
import { ErrorBoundary } from "react-error-boundary";
import {
  useAt_listAnomaliesSuspense,
  useAt_getAnomalyCountsSuspense,
} from "@/lib/api";
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
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  AlertCircle,
  AlertTriangle,
  ChevronRight,
  Shield,
  ShieldAlert,
  Info,
} from "lucide-react";
import { cn } from "@/lib/utils";

export const Route = createFileRoute(
  "/projects/adtech-intelligence/anomalies/",
)({
  component: () => <AnomaliesPage />,
});

const severityConfig: Record<
  string,
  { icon: typeof AlertTriangle; color: string; bg: string }
> = {
  critical: {
    icon: ShieldAlert,
    color: "text-red-600",
    bg: "bg-red-500/10 border-red-200",
  },
  high: {
    icon: AlertTriangle,
    color: "text-orange-600",
    bg: "bg-orange-500/10 border-orange-200",
  },
  medium: {
    icon: Shield,
    color: "text-yellow-600",
    bg: "bg-yellow-500/10 border-yellow-200",
  },
  low: {
    icon: Info,
    color: "text-blue-600",
    bg: "bg-blue-500/10 border-blue-200",
  },
};

const statusColors: Record<string, string> = {
  new: "bg-red-500/10 text-red-700 border-red-200",
  acknowledged: "bg-yellow-500/10 text-yellow-700 border-yellow-200",
  investigating: "bg-blue-500/10 text-blue-700 border-blue-200",
  resolved: "bg-green-500/10 text-green-700 border-green-200",
  dismissed: "bg-gray-500/10 text-gray-700 border-gray-200",
};

function SeverityCards() {
  const { data: counts } = useAt_getAnomalyCountsSuspense(selector());

  const severities = [
    { key: "critical", label: "Critical", Icon: ShieldAlert, color: "text-red-600", bg: "bg-red-50 dark:bg-red-950/20" },
    { key: "high", label: "High", Icon: AlertTriangle, color: "text-orange-600", bg: "bg-orange-50 dark:bg-orange-950/20" },
    { key: "medium", label: "Medium", Icon: Shield, color: "text-yellow-600", bg: "bg-yellow-50 dark:bg-yellow-950/20" },
    { key: "low", label: "Low", Icon: Info, color: "text-blue-600", bg: "bg-blue-50 dark:bg-blue-950/20" },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-4">
      {severities.map(({ key, label, Icon, color, bg }) => (
        <Card key={key} className={bg}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{label}</CardTitle>
            <Icon className={cn("h-4 w-4", color)} />
          </CardHeader>
          <CardContent>
            <div className={cn("text-3xl font-bold", color)}>
              {(counts as Record<string, number>)?.[key] ?? 0}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function AnomalyTable() {
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [severityFilter, setSeverityFilter] = useState<string>("all");

  const queryParams: Record<string, any> = { limit: 50 };
  if (statusFilter !== "all") queryParams.status = statusFilter;
  if (severityFilter !== "all") queryParams.severity = severityFilter;

  const { data: anomalies } = useAt_listAnomaliesSuspense({ params: queryParams, ...selector() });

  return (
    <div className="space-y-4">
      <div className="flex gap-3 flex-wrap">
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[160px]">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="new">New</SelectItem>
            <SelectItem value="acknowledged">Acknowledged</SelectItem>
            <SelectItem value="investigating">Investigating</SelectItem>
            <SelectItem value="resolved">Resolved</SelectItem>
            <SelectItem value="dismissed">Dismissed</SelectItem>
          </SelectContent>
        </Select>

        <Select value={severityFilter} onValueChange={setSeverityFilter}>
          <SelectTrigger className="w-[160px]">
            <SelectValue placeholder="Severity" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Severities</SelectItem>
            <SelectItem value="critical">Critical</SelectItem>
            <SelectItem value="high">High</SelectItem>
            <SelectItem value="medium">Medium</SelectItem>
            <SelectItem value="low">Low</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[40px]"></TableHead>
              <TableHead>Title</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Severity</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Deviation</TableHead>
              <TableHead>Detected</TableHead>
              <TableHead className="w-[40px]"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {anomalies.map((anomaly) => {
              const sev = severityConfig[anomaly.severity] || severityConfig.low;
              const SevIcon = sev.icon;
              return (
                <TableRow key={anomaly.id} className="group">
                  <TableCell>
                    <SevIcon className={cn("h-4 w-4", sev.color)} />
                  </TableCell>
                  <TableCell className="font-medium max-w-[300px]">
                    <Link
                      to={`/projects/adtech-intelligence/anomalies/${anomaly.id}` as any}
                      className="hover:underline"
                    >
                      {anomaly.title}
                    </Link>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" className="text-xs capitalize">
                      {anomaly.anomaly_type?.replace(/_/g, " ")}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" className={cn("capitalize", sev.bg)}>
                      {anomaly.severity}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant="outline"
                      className={cn("capitalize", statusColors[anomaly.status])}
                    >
                      {anomaly.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right font-mono">
                    <span
                      className={
                        anomaly.deviation_pct < 0
                          ? "text-red-600"
                          : "text-green-600"
                      }
                    >
                      {anomaly.deviation_pct > 0 ? "+" : ""}
                      {anomaly.deviation_pct?.toFixed(1)}%
                    </span>
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground whitespace-nowrap">
                    {new Date(anomaly.detected_at).toLocaleDateString("de-DE")}
                  </TableCell>
                  <TableCell>
                    <Link
                      to={`/projects/adtech-intelligence/anomalies/${anomaly.id}` as any}
                    >
                      <ChevronRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition" />
                    </Link>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}

function AnomaliesContent() {
  return (
    <div className="space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
          <AlertTriangle className="h-6 w-6" />
          Anomaly Notification Center
        </h1>
        <p className="text-muted-foreground mt-1">
          Monitor campaign performance anomalies and take action with AI-suggested mitigations.
        </p>
      </div>

      <Suspense
        fallback={
          <div className="grid gap-4 md:grid-cols-4">
            {[1, 2, 3, 4].map((i) => (
              <Card key={i}>
                <CardHeader className="pb-2">
                  <Skeleton className="h-4 w-16" />
                </CardHeader>
                <CardContent>
                  <Skeleton className="h-9 w-12" />
                </CardContent>
              </Card>
            ))}
          </div>
        }
      >
        <SeverityCards />
      </Suspense>

      <Suspense
        fallback={
          <div className="space-y-4">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-[400px] w-full" />
          </div>
        }
      >
        <AnomalyTable />
      </Suspense>
    </div>
  );
}

function AnomaliesPage() {
  return (
    <QueryErrorResetBoundary>
      {({ reset }) => (
        <ErrorBoundary
          onReset={reset}
          fallbackRender={({ resetErrorBoundary }) => (
            <div className="p-6 flex items-center justify-center min-h-[50vh]">
              <Card className="border-destructive/50 max-w-lg">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-destructive">
                    <AlertCircle className="h-5 w-5" />
                    Failed to Load Anomalies
                  </CardTitle>
                  <CardDescription>
                    Could not load anomaly data.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Button variant="outline" onClick={resetErrorBoundary}>
                    Try Again
                  </Button>
                </CardContent>
              </Card>
            </div>
          )}
        >
          <AnomaliesContent />
        </ErrorBoundary>
      )}
    </QueryErrorResetBoundary>
  );
}
