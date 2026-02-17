import { Suspense } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { ErrorBoundary } from "react-error-boundary";
import { QueryErrorResetBoundary, useQueryClient } from "@tanstack/react-query";
import {
  useMac_listAnomalyAlertsSuspense,
  useMac_listStationsSuspense,
  useMac_updateAnomalyAlert,
  mac_listAnomalyAlertsKey,
  type MacAnomalyAlertOut,
  type MacAlertStatus,
} from "@/lib/api";
import selector from "@/lib/selector";
import { useState, useMemo } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertTriangle, CheckCircle2, XCircle, Bell } from "lucide-react";

export const Route = createFileRoute("/projects/mol-asm-cockpit/anomalies/")({
  component: () => <AnomaliesPage />,
});

const severityConfig: Record<string, { className: string; label: string }> = {
  critical: {
    className:
      "bg-red-500/20 text-red-600 dark:text-red-400 border-red-500/30",
    label: "Critical",
  },
  high: {
    className:
      "bg-orange-500/20 text-orange-600 dark:text-orange-400 border-orange-500/30",
    label: "High",
  },
  medium: {
    className:
      "bg-yellow-500/20 text-yellow-600 dark:text-yellow-400 border-yellow-500/30",
    label: "Medium",
  },
  low: {
    className:
      "bg-blue-500/20 text-blue-600 dark:text-blue-400 border-blue-500/30",
    label: "Low",
  },
};

const statusConfig: Record<string, { className: string; label: string }> = {
  active: {
    className: "bg-destructive/20 text-destructive border-destructive/30",
    label: "Active",
  },
  acknowledged: {
    className:
      "bg-amber-500/20 text-amber-600 dark:text-amber-400 border-amber-500/30",
    label: "Acknowledged",
  },
  resolved: {
    className:
      "bg-green-500/20 text-green-600 dark:text-green-400 border-green-500/30",
    label: "Resolved",
  },
  dismissed: {
    className: "bg-muted text-muted-foreground border-muted",
    label: "Dismissed",
  },
};

const severityBorderColor: Record<string, string> = {
  critical: "rgb(239 68 68)",
  high: "rgb(249 115 22)",
  medium: "rgb(234 179 8)",
  low: "rgb(59 130 246)",
};

function AnomaliesPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">
          Anomaly Notification Center
        </h1>
        <p className="text-muted-foreground mt-2">
          Monitor and triage alerts across your station network
        </p>
      </div>

      <QueryErrorResetBoundary>
        {({ reset }) => (
          <ErrorBoundary
            onReset={reset}
            fallbackRender={({ error, resetErrorBoundary }) => (
              <Card className="p-6">
                <div className="text-center">
                  <p className="text-destructive mb-4">
                    Error loading anomalies: {error.message}
                  </p>
                  <Button onClick={resetErrorBoundary}>Try Again</Button>
                </div>
              </Card>
            )}
          >
            <Suspense fallback={<AnomaliesSkeleton />}>
              <AnomaliesContent />
            </Suspense>
          </ErrorBoundary>
        )}
      </QueryErrorResetBoundary>
    </div>
  );
}

function AnomaliesContent() {
  const queryClient = useQueryClient();
  const { data: alerts } = useMac_listAnomalyAlertsSuspense({
    params: { limit: 100 },
    ...selector(),
  });
  const { data: stations } = useMac_listStationsSuspense(selector());
  const updateAlert = useMac_updateAnomalyAlert();

  const stationMap = useMemo(() => {
    const map = new Map<number, string>();
    if (Array.isArray(stations)) {
      for (const s of stations) {
        map.set(s.id, s.station_code);
      }
    }
    return map;
  }, [stations]);

  const [severityFilter, setSeverityFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  const filteredAlerts = useMemo(() => {
    const list = Array.isArray(alerts) ? alerts : [];
    return list.filter(
      (a: MacAnomalyAlertOut) =>
        (severityFilter === "all" || a.severity === severityFilter) &&
        (statusFilter === "all" || a.status === statusFilter),
    );
  }, [alerts, severityFilter, statusFilter]);

  const handleUpdateStatus = async (
    alertId: number,
    newStatus: MacAlertStatus,
  ) => {
    await updateAlert.mutateAsync({
      params: { alert_id: alertId },
      data: { status: newStatus },
    });
    queryClient.invalidateQueries({ queryKey: mac_listAnomalyAlertsKey() });
  };

  return (
    <>
      {/* Filter Bar */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Filters</CardTitle>
          <CardDescription>
            Filter alerts by severity and status
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-4">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">Severity:</span>
            <Select
              value={severityFilter}
              onValueChange={setSeverityFilter}
            >
              <SelectTrigger className="w-[140px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                <SelectItem value="critical">Critical</SelectItem>
                <SelectItem value="high">High</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="low">Low</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">Status:</span>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[140px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="acknowledged">Acknowledged</SelectItem>
                <SelectItem value="resolved">Resolved</SelectItem>
                <SelectItem value="dismissed">Dismissed</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Alert Cards */}
      <div className="space-y-4">
        {filteredAlerts.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center text-muted-foreground">
              <AlertTriangle className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No alerts match the current filters</p>
            </CardContent>
          </Card>
        ) : (
          filteredAlerts.map((alert: MacAnomalyAlertOut) => {
            const sev = severityConfig[alert.severity] ?? severityConfig.low;
            const st = statusConfig[alert.status] ?? statusConfig.active;
            const stationCode = stationMap.get(alert.station_id) ?? `#${alert.station_id}`;
            return (
              <Card
                key={alert.id}
                className="border-l-4"
                style={{
                  borderLeftColor:
                    severityBorderColor[alert.severity] ?? severityBorderColor.low,
                }}
              >
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <CardTitle className="text-lg">{alert.title}</CardTitle>
                      <CardDescription className="mt-1">
                        {stationCode} &bull;{" "}
                        {new Date(alert.detected_at).toLocaleString()}
                      </CardDescription>
                    </div>
                    <div className="flex gap-2 flex-shrink-0">
                      <Badge variant="outline" className={sev.className}>
                        {sev.label}
                      </Badge>
                      <Badge variant="outline" className={st.className}>
                        {st.label}
                      </Badge>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-sm">{alert.description}</p>
                  <div className="rounded-lg bg-muted/50 p-3">
                    <p className="text-xs font-medium text-muted-foreground mb-1">
                      Suggested action
                    </p>
                    <p className="text-sm">{alert.suggested_action}</p>
                  </div>
                  {alert.status !== "resolved" &&
                    alert.status !== "dismissed" && (
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() =>
                            handleUpdateStatus(alert.id, "acknowledged")
                          }
                          disabled={
                            alert.status === "acknowledged" ||
                            updateAlert.isPending
                          }
                        >
                          <Bell className="h-4 w-4 mr-1" />
                          Acknowledge
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() =>
                            handleUpdateStatus(alert.id, "resolved")
                          }
                          disabled={updateAlert.isPending}
                        >
                          <CheckCircle2 className="h-4 w-4 mr-1" />
                          Resolve
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() =>
                            handleUpdateStatus(alert.id, "dismissed")
                          }
                          disabled={updateAlert.isPending}
                        >
                          <XCircle className="h-4 w-4 mr-1" />
                          Dismiss
                        </Button>
                      </div>
                    )}
                </CardContent>
              </Card>
            );
          })
        )}
      </div>
    </>
  );
}

function AnomaliesSkeleton() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-[120px]" />
      {[1, 2, 3, 4].map((i) => (
        <Skeleton key={i} className="h-[200px]" />
      ))}
    </div>
  );
}
