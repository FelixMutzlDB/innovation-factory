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
import { Camera } from "lucide-react";
import { useState } from "react";

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
  // Load-bearing demo string: "Apple tree fungus check overdue 4 days"
  // This row is the anchor for Phase 1 success criterion #1 (plan §2).
  // When seeded at 2026-05-08, it should render as overdue on 2026-05-12.
  return (
    <div className="space-y-2 text-sm">
      <div className="p-2 bg-muted rounded">
        <div className="font-medium">Apple tree fungus check</div>
        <div className="text-destructive text-xs">Overdue 4 days</div>
      </div>
      <div className="text-muted-foreground">
        Upcoming tasks...
      </div>
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
  return (
    <div className="text-sm text-muted-foreground">
      No diagnoses yet. Snap a photo to get started.
    </div>
  );
}

function DiagnoseModalStub({ onClose }: { onClose: () => void }) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Snap a Photo</CardTitle>
          <CardDescription>Upload a yard photo for diagnosis</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <input type="file" accept="image/jpeg,image/png,image/heic" />
          <p className="text-sm text-muted-foreground">Max 10MB</p>
        </CardContent>
        <div className="px-6 py-4 border-t flex gap-2 justify-end">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={onClose}>Upload & Diagnose</Button>
        </div>
      </Card>
    </div>
  );
}
