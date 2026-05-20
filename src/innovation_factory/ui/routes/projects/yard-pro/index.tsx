import { createFileRoute } from "@tanstack/react-router";
import { Suspense } from "react";
import { ErrorBoundary } from "react-error-boundary";
import { QueryErrorResetBoundary } from "@tanstack/react-query";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Camera, Sprout, AlertTriangle, CheckCircle2, Clock } from "lucide-react";
import { useState } from "react";
import {
  useYp_listDiagnosesSuspense,
  useYp_listCalendarSuspense,
} from "@/lib/api";
import selector from "@/lib/selector";

export const Route = createFileRoute("/projects/yard-pro/")({
  component: () => <CockpitPage />,
});

function CockpitPage() {
  const [diagnoseOpen, setDiagnoseOpen] = useState(false);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Martin's Yard</h1>
          <p className="text-muted-foreground mt-1">
            Stuttgart, partly cloudy, 18°C
          </p>
        </div>
        <Button
          onClick={() => setDiagnoseOpen(true)}
          className="gap-2"
        >
          <Camera size={16} />
          Snap a photo
        </Button>
      </div>

      {/* Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Calendar Card */}
        <Card>
          <CardHeader>
            <CardTitle>Today & Upcoming</CardTitle>
            <CardDescription>Your seasonal calendar</CardDescription>
          </CardHeader>
          <CardContent>
            <QueryErrorResetBoundary>
              {({ reset }) => (
                <ErrorBoundary
                  onReset={reset}
                  fallbackRender={({ resetErrorBoundary }) => (
                    <div className="text-destructive text-sm p-2">
                      <p>Failed to load calendar</p>
                      <Button
                        size="sm"
                        onClick={resetErrorBoundary}
                        className="mt-2"
                      >
                        Retry
                      </Button>
                    </div>
                  )}
                >
                  <Suspense
                    fallback={
                      <div className="space-y-2">
                        {[...Array(5)].map((_, i) => (
                          <Skeleton key={i} className="h-8 w-full" />
                        ))}
                      </div>
                    }
                  >
                    <CalendarCardContent />
                  </Suspense>
                </ErrorBoundary>
              )}
            </QueryErrorResetBoundary>
          </CardContent>
        </Card>

        {/* Inventory Card */}
        <Card>
          <CardHeader>
            <CardTitle>Inventory</CardTitle>
            <CardDescription>Tools & consumables</CardDescription>
          </CardHeader>
          <CardContent>
            <QueryErrorResetBoundary>
              {({ reset }) => (
                <ErrorBoundary
                  onReset={reset}
                  fallbackRender={({ resetErrorBoundary }) => (
                    <div className="text-destructive text-sm p-2">
                      <p>Failed to load inventory</p>
                      <Button
                        size="sm"
                        onClick={resetErrorBoundary}
                        className="mt-2"
                      >
                        Retry
                      </Button>
                    </div>
                  )}
                >
                  <Suspense
                    fallback={
                      <div className="space-y-2">
                        {[...Array(4)].map((_, i) => (
                          <Skeleton key={i} className="h-6 w-full" />
                        ))}
                      </div>
                    }
                  >
                    <InventoryCardContent />
                  </Suspense>
                </ErrorBoundary>
              )}
            </QueryErrorResetBoundary>
          </CardContent>
        </Card>

        {/* Recent Diagnoses Card */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Diagnoses</CardTitle>
            <CardDescription>Snap-and-diagnose history</CardDescription>
          </CardHeader>
          <CardContent>
            <QueryErrorResetBoundary>
              {({ reset }) => (
                <ErrorBoundary
                  onReset={reset}
                  fallbackRender={({ resetErrorBoundary }) => (
                    <div className="text-destructive text-sm p-2">
                      <p>Failed to load diagnoses</p>
                      <Button
                        size="sm"
                        onClick={resetErrorBoundary}
                        className="mt-2"
                      >
                        Retry
                      </Button>
                    </div>
                  )}
                >
                  <Suspense
                    fallback={
                      <div className="space-y-2">
                        {[...Array(3)].map((_, i) => (
                          <Skeleton key={i} className="h-6 w-full" />
                        ))}
                      </div>
                    }
                  >
                    <DiagnosesCardContent />
                  </Suspense>
                </ErrorBoundary>
              )}
            </QueryErrorResetBoundary>
          </CardContent>
        </Card>
      </div>

      {/* Diagnose Modal Placeholder */}
      {diagnoseOpen && (
        <DiagnoseModalStub onClose={() => setDiagnoseOpen(false)} />
      )}
    </div>
  );
}

/**
 * Placeholder components for seeded data.
 * In production, these consume useYp_getCockpitSuspense() and similar hooks
 * once the backend (B1/B2) exports them.
 */

function CalendarCardContent() {
  const { data: entries } = useYp_listCalendarSuspense({
    params: { limit: 6 },
    ...selector(),
  });
  if (entries.length === 0) {
    return (
      <div className="text-sm text-muted-foreground">
        No upcoming tasks yet. The seasonal coach will populate this.
      </div>
    );
  }
  const now = new Date();
  return (
    <div className="space-y-2 text-sm">
      {entries.slice(0, 5).map((entry) => {
        const scheduled = new Date(entry.scheduled_at);
        const overdue = entry.status === "planned" && scheduled < now;
        const daysDiff = Math.round(
          (scheduled.getTime() - now.getTime()) / (1000 * 60 * 60 * 24),
        );
        return (
          <div
            key={entry.id}
            className={`p-2 rounded border ${
              overdue ? "border-destructive/50 bg-destructive/5" : "bg-muted"
            }`}
          >
            <div className="font-medium">{entry.title}</div>
            <div
              className={`text-xs ${
                overdue ? "text-destructive" : "text-muted-foreground"
              }`}
            >
              {overdue
                ? `Overdue ${Math.abs(daysDiff)} day${
                    Math.abs(daysDiff) === 1 ? "" : "s"
                  }`
                : daysDiff === 0
                  ? "Today"
                  : daysDiff === 1
                    ? "Tomorrow"
                    : `In ${daysDiff} days`}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function InventoryCardContent() {
  return (
    <div className="space-y-2 text-sm">
      <div>
        <div className="font-medium">Tools</div>
        <div className="text-muted-foreground">Cordless trimmer, hedge cutter, chainsaw</div>
      </div>
      <div>
        <div className="font-medium">Consumables</div>
        <div className="text-muted-foreground">2.5kg fertilizer, blade oil</div>
      </div>
    </div>
  );
}

function DiagnosesCardContent() {
  const { data: diagnoses } = useYp_listDiagnosesSuspense({
    params: { limit: 5 },
    ...selector(),
  });
  if (diagnoses.length === 0) {
    return (
      <div className="text-sm text-muted-foreground">
        No diagnoses yet. Snap a photo to get started.
      </div>
    );
  }
  return (
    <div className="space-y-2 text-sm">
      {diagnoses.slice(0, 4).map((d) => {
        const created = new Date(d.created_at);
        const daysAgo = Math.round(
          (Date.now() - created.getTime()) / (1000 * 60 * 60 * 24),
        );
        const confidencePct = Math.round(d.top_confidence * 100);
        const StatusIcon =
          d.status === "pending"
            ? Clock
            : d.status === "acted_upon"
              ? CheckCircle2
              : AlertTriangle;
        const statusColor =
          d.status === "acted_upon"
            ? "text-emerald-600 dark:text-emerald-400"
            : d.status === "pending"
              ? "text-amber-600 dark:text-amber-400"
              : "text-muted-foreground";
        return (
          <div key={d.id} className="p-2 bg-muted rounded space-y-1">
            <div className="flex items-start justify-between gap-2">
              <div className="font-medium flex items-center gap-1.5">
                <Sprout size={14} className="text-primary shrink-0" />
                {d.top_label.replace(/_/g, " ")}
              </div>
              <Badge variant="outline" className="shrink-0 text-[10px]">
                {confidencePct}%
              </Badge>
            </div>
            <div className={`text-xs flex items-center gap-1 ${statusColor}`}>
              <StatusIcon size={11} />
              {d.status.replace(/_/g, " ")} ·{" "}
              {daysAgo === 0
                ? "today"
                : daysAgo === 1
                  ? "yesterday"
                  : `${daysAgo} days ago`}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function DiagnoseModalStub({ onClose }: { onClose: () => void }) {
  // Demo mode: skip the file picker and show the most-recent diagnosis
  // alongside the photo it was run against. Lets the presenter walk the
  // audience through the snap-and-diagnose flow without the vision endpoint
  // having to be up (yard-pro-vision-v1 is currently DEPLOYMENT_FAILED).
  const { data: diagnoses } = useYp_listDiagnosesSuspense({
    params: { limit: 1 },
    ...selector(),
  });
  const latest = diagnoses[0];

  if (!latest) {
    return (
      <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle>Snap a Photo</CardTitle>
            <CardDescription>No prior diagnoses yet.</CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            Run the demo seed script to populate a session.
          </CardContent>
          <div className="px-6 py-4 border-t flex justify-end">
            <Button onClick={onClose}>Close</Button>
          </div>
        </Card>
      </div>
    );
  }

  const labels =
    (latest.predictions as { labels?: { name: string; confidence: number }[] })
      ?.labels ?? [];
  const created = new Date(latest.created_at);
  const photoSrc = "/yard-pro/demo-yard-2026-05-17.jpeg";

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4 overflow-y-auto">
      <Card className="w-full max-w-3xl my-auto">
        <CardHeader>
          <div className="flex items-start justify-between gap-4">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Camera size={18} />
                Diagnose result
              </CardTitle>
              <CardDescription>
                {latest.model_version} · {created.toLocaleString()}
              </CardDescription>
            </div>
            <Badge variant="outline" className="gap-1">
              <AlertTriangle size={12} />
              advisory — review before acting
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded-lg overflow-hidden border bg-muted">
            <img
              src={photoSrc}
              alt="Martin's yard, 2026-05-17 morning"
              className="w-full h-auto max-h-[420px] object-cover"
            />
          </div>

          <div className="space-y-3">
            <div className="flex items-baseline justify-between gap-2">
              <h3 className="font-medium">Predictions</h3>
              <span className="text-xs text-muted-foreground">
                Vision endpoint: {latest.model_version}
              </span>
            </div>
            {labels.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No predictions on this diagnosis.
              </p>
            ) : (
              <div className="space-y-2">
                {labels.map((p, idx) => {
                  const pct = Math.round(p.confidence * 100);
                  const isTop = idx === 0;
                  return (
                    <div
                      key={p.name}
                      className={`p-3 rounded border ${
                        isTop ? "border-primary/40 bg-primary/5" : "bg-muted"
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1.5">
                        <div className="flex items-center gap-2">
                          <Sprout
                            size={14}
                            className={isTop ? "text-primary" : "text-muted-foreground"}
                          />
                          <span className={`text-sm ${isTop ? "font-semibold" : ""}`}>
                            {p.name.replace(/_/g, " ")}
                          </span>
                          {isTop && (
                            <Badge variant="secondary" className="text-[10px]">
                              top label
                            </Badge>
                          )}
                        </div>
                        <span className="text-sm font-mono">{pct}%</span>
                      </div>
                      <div className="h-1.5 bg-background rounded-full overflow-hidden">
                        <div
                          className={`h-full ${
                            isTop ? "bg-primary" : "bg-muted-foreground/40"
                          }`}
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          <div className="rounded-lg border bg-amber-50 dark:bg-amber-950/30 border-amber-200 dark:border-amber-900/50 p-3 text-sm">
            <p className="font-medium text-amber-900 dark:text-amber-200">
              GDPR Art. 22 review-and-confirm
            </p>
            <p className="text-amber-800 dark:text-amber-300/90 mt-0.5 text-xs">
              Status: <span className="font-mono">{latest.status}</span>. No
              irrigation, fertilization, or service-call action runs until you
              accept the top label. EU AI Act Art. 50 advisory chip stays
              visible above.
            </p>
          </div>
        </CardContent>
        <div className="px-6 py-4 border-t flex gap-2 justify-end">
          <Button variant="outline" onClick={onClose}>
            Dismiss
          </Button>
          <Button onClick={onClose} className="gap-2">
            <CheckCircle2 size={14} />
            Accept &amp; schedule action
          </Button>
        </div>
      </Card>
    </div>
  );
}
