import { createFileRoute } from "@tanstack/react-router";
import { Suspense } from "react";
import { QueryErrorResetBoundary } from "@tanstack/react-query";
import { ErrorBoundary } from "react-error-boundary";
import { useCurrentUserSuspense } from "@/lib/api";
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
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { AlertCircle } from "lucide-react";

export const Route = createFileRoute(
  "/projects/adtech-intelligence/profile",
)({
  component: () => <ProfilePage />,
});

function ProfileContent() {
  const { data: user } = useCurrentUserSuspense(selector()) as any;
  const initials = user.displayName
    ? user.displayName
        .split(" ")
        .map((n: string) => n[0])
        .join("")
        .toUpperCase()
    : "?";

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold tracking-tight">Profile</h1>

      <Card className="max-w-lg">
        <CardHeader>
          <div className="flex items-center gap-4">
            <Avatar className="h-16 w-16">
              <AvatarFallback className="text-lg">{initials}</AvatarFallback>
            </Avatar>
            <div>
              <CardTitle>{user.displayName}</CardTitle>
              <CardDescription>{user.userName}</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">User ID</span>
            <span className="font-mono">{user.id}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Status</span>
            <span>{user.active ? "Active" : "Inactive"}</span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function ProfilePage() {
  return (
    <QueryErrorResetBoundary>
      {({ reset }) => (
        <ErrorBoundary
          onReset={reset}
          fallbackRender={({ resetErrorBoundary }) => (
            <div className="p-6">
              <Card className="border-destructive/50 max-w-lg">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-destructive">
                    <AlertCircle className="h-5 w-5" />
                    Failed to Load Profile
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
                <Skeleton className="h-8 w-32" />
                <Card className="max-w-lg">
                  <CardHeader>
                    <div className="flex items-center gap-4">
                      <Skeleton className="h-16 w-16 rounded-full" />
                      <div className="space-y-2">
                        <Skeleton className="h-6 w-40" />
                        <Skeleton className="h-4 w-56" />
                      </div>
                    </div>
                  </CardHeader>
                </Card>
              </div>
            }
          >
            <ProfileContent />
          </Suspense>
        </ErrorBoundary>
      )}
    </QueryErrorResetBoundary>
  );
}
