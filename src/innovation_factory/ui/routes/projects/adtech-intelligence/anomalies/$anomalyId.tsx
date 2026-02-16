import { createFileRoute, Link } from "@tanstack/react-router";
import { Suspense } from "react";
import { QueryErrorResetBoundary } from "@tanstack/react-query";
import { ErrorBoundary } from "react-error-boundary";
import { useAt_getAnomalySuspense, useAt_updateAnomaly } from "@/lib/api";
import type { AnomalyStatus } from "@/lib/api";
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
import { Separator } from "@/components/ui/separator";
import {
  AlertCircle,
  ArrowLeft,
  CheckCircle,
  ChevronRight,
  Clock,
  Eye,
  Lightbulb,
  Search,
  TrendingDown,
  TrendingUp,
  XCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";

export const Route = createFileRoute(
  "/projects/adtech-intelligence/anomalies/$anomalyId",
)({
  component: () => <AnomalyDetailPage />,
});

const severityColors: Record<string, string> = {
  critical: "text-red-600 bg-red-500/10 border-red-200",
  high: "text-orange-600 bg-orange-500/10 border-orange-200",
  medium: "text-yellow-600 bg-yellow-500/10 border-yellow-200",
  low: "text-blue-600 bg-blue-500/10 border-blue-200",
};

const statusConfig: Record<string, { icon: typeof Clock; label: string }> = {
  new: { icon: AlertCircle, label: "New" },
  acknowledged: { icon: Eye, label: "Acknowledged" },
  investigating: { icon: Search, label: "Investigating" },
  resolved: { icon: CheckCircle, label: "Resolved" },
  dismissed: { icon: XCircle, label: "Dismissed" },
};

function AnomalyDetail() {
  const { anomalyId } = Route.useParams();
  const { data: anomaly } = useAt_getAnomalySuspense({
    params: { anomaly_id: Number(anomalyId) },
    ...selector(),
  });
  const updateMutation = useAt_updateAnomaly();

  const handleStatusChange = (newStatus: string) => {
    updateMutation.mutate({
      params: { anomaly_id: Number(anomalyId) },
      data: { status: newStatus as AnomalyStatus },
    });
  };

  const StatusIcon = statusConfig[anomaly.status]?.icon || Clock;

  return (
    <div className="space-y-6 p-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Link
          to="/projects/adtech-intelligence/anomalies"
          className="hover:text-foreground flex items-center gap-1"
        >
          <ArrowLeft className="h-4 w-4" />
          Anomaly Center
        </Link>
        <ChevronRight className="h-3 w-3" />
        <span className="text-foreground">Anomaly #{anomaly.id}</span>
      </div>

      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <Badge
              variant="outline"
              className={cn(
                "capitalize text-sm px-3 py-1",
                severityColors[anomaly.severity],
              )}
            >
              {anomaly.severity}
            </Badge>
            <Badge variant="outline" className="capitalize">
              {anomaly.anomaly_type?.replace(/_/g, " ")}
            </Badge>
          </div>
          <h1 className="text-2xl font-bold">{anomaly.title}</h1>
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <span className="flex items-center gap-1">
              <StatusIcon className="h-4 w-4" />
              {statusConfig[anomaly.status]?.label || anomaly.status}
            </span>
            <span>
              Detected: {new Date(anomaly.detected_at).toLocaleString("de-DE")}
            </span>
            {anomaly.resolved_at && (
              <span>
                Resolved: {new Date(anomaly.resolved_at).toLocaleString("de-DE")}
              </span>
            )}
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex gap-2">
          {anomaly.status === "new" && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleStatusChange("acknowledged")}
            >
              <Eye className="h-4 w-4 mr-1" />
              Acknowledge
            </Button>
          )}
          {(anomaly.status === "new" || anomaly.status === "acknowledged") && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleStatusChange("investigating")}
            >
              <Search className="h-4 w-4 mr-1" />
              Investigate
            </Button>
          )}
          {anomaly.status !== "resolved" && anomaly.status !== "dismissed" && (
            <>
              <Button
                variant="default"
                size="sm"
                onClick={() => handleStatusChange("resolved")}
              >
                <CheckCircle className="h-4 w-4 mr-1" />
                Resolve
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleStatusChange("dismissed")}
              >
                <XCircle className="h-4 w-4 mr-1" />
                Dismiss
              </Button>
            </>
          )}
        </div>
      </div>

      <Separator />

      <div className="grid gap-6 md:grid-cols-3">
        {/* Description */}
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle className="text-lg">Description</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm leading-relaxed">{anomaly.description}</p>
          </CardContent>
        </Card>

        {/* Metric Details */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Metric Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-xs text-muted-foreground uppercase tracking-wide">
                Metric
              </p>
              <p className="font-medium capitalize">
                {anomaly.metric_name?.replace(/_/g, " ")}
              </p>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-muted-foreground uppercase tracking-wide">
                  Expected
                </p>
                <p className="font-medium">
                  {anomaly.expected_value?.toLocaleString("de-DE", {
                    maximumFractionDigits: 2,
                  })}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground uppercase tracking-wide">
                  Actual
                </p>
                <p className="font-medium">
                  {anomaly.actual_value?.toLocaleString("de-DE", {
                    maximumFractionDigits: 2,
                  })}
                </p>
              </div>
            </div>
            <div>
              <p className="text-xs text-muted-foreground uppercase tracking-wide">
                Deviation
              </p>
              <p
                className={cn(
                  "text-2xl font-bold",
                  anomaly.deviation_pct < 0 ? "text-red-600" : "text-green-600",
                )}
              >
                {anomaly.deviation_pct < 0 ? (
                  <TrendingDown className="h-5 w-5 inline mr-1" />
                ) : (
                  <TrendingUp className="h-5 w-5 inline mr-1" />
                )}
                {anomaly.deviation_pct > 0 ? "+" : ""}
                {anomaly.deviation_pct?.toFixed(1)}%
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Suggested Actions */}
      {anomaly.suggested_actions && anomaly.suggested_actions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Lightbulb className="h-5 w-5 text-amber-500" />
              Suggested Actions
            </CardTitle>
            <CardDescription>
              AI-recommended steps to investigate and mitigate this anomaly.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {anomaly.suggested_actions.map((action, i) => (
                <div
                  key={i}
                  className="flex items-start gap-3 p-3 rounded-lg bg-muted/50"
                >
                  <div className="w-6 h-6 rounded-full bg-amber-500/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <span className="text-xs font-bold text-amber-600">
                      {i + 1}
                    </span>
                  </div>
                  <p className="text-sm">{String(action)}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function AnomalyDetailPage() {
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
                    Failed to Load Anomaly
                  </CardTitle>
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
          <Suspense
            fallback={
              <div className="p-6 space-y-6">
                <Skeleton className="h-8 w-48" />
                <Skeleton className="h-6 w-96" />
                <Skeleton className="h-[300px] w-full" />
              </div>
            }
          >
            <AnomalyDetail />
          </Suspense>
        </ErrorBoundary>
      )}
    </QueryErrorResetBoundary>
  );
}
