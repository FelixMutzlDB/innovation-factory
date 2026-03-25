import { createFileRoute } from "@tanstack/react-router";
import { Suspense } from "react";
import { ErrorBoundary } from "react-error-boundary";
import { QueryErrorResetBoundary } from "@tanstack/react-query";
import { useCurrentUserSuspense } from "@/lib/api";
import { selector } from "@/lib/selector";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { User, Mail, Shield } from "lucide-react";

export const Route = createFileRoute(
  "/projects/hb-product-center/profile",
)({
  component: () => <ProfilePage />,
});

function ProfilePage() {
  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold tracking-tight">Profile</h1>

      <QueryErrorResetBoundary>
        {({ reset }) => (
          <ErrorBoundary
            onReset={reset}
            fallbackRender={({ resetErrorBoundary }) => (
              <Card>
                <CardContent className="p-6">
                  <p className="text-destructive">Failed to load profile.</p>
                  <button onClick={resetErrorBoundary} className="mt-2 text-sm underline">Retry</button>
                </CardContent>
              </Card>
            )}
          >
            <Suspense fallback={<Skeleton className="h-48 w-full" />}>
              <ProfileContent />
            </Suspense>
          </ErrorBoundary>
        )}
      </QueryErrorResetBoundary>
    </div>
  );
}

function ProfileContent() {
  const { data: user } = useCurrentUserSuspense(selector());

  return (
    <Card className="max-w-lg">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <User className="h-5 w-5" />
          User Information
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-3">
          <User className="h-4 w-4 text-muted-foreground" />
          <div>
            <p className="text-sm font-medium">Display Name</p>
            <p className="text-sm text-muted-foreground">
              {(user as Record<string, unknown>)?.display_name as string ?? "N/A"}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Mail className="h-4 w-4 text-muted-foreground" />
          <div>
            <p className="text-sm font-medium">Email</p>
            <p className="text-sm text-muted-foreground">
              {(user as Record<string, unknown>)?.user_name as string ?? "N/A"}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Shield className="h-4 w-4 text-muted-foreground" />
          <div>
            <p className="text-sm font-medium">Status</p>
            <p className="text-sm text-muted-foreground">
              {(user as Record<string, unknown>)?.active ? "Active" : "Inactive"}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
