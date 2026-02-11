import { createFileRoute, Link } from "@tanstack/react-router";
import { useBsh_listMyDevicesSuspense } from "@/lib/api";
import selector from "@/lib/selector";
import { Suspense } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Plus, Package, AlertCircle } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { QueryErrorResetBoundary } from "@tanstack/react-query";
import { ErrorBoundary } from "react-error-boundary";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

export const Route = createFileRoute("/projects/bsh-home-connect/devices/")({
  component: () => (
    <QueryErrorResetBoundary>
      {({ reset }) => (
        <ErrorBoundary
          onReset={reset}
          fallbackRender={({ error, resetErrorBoundary }) => (
            <div className="container mx-auto p-6">
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>Error loading devices</AlertTitle>
                <AlertDescription>
                  {error.message}
                  <Button onClick={resetErrorBoundary} variant="outline" className="mt-2">
                    Try again
                  </Button>
                </AlertDescription>
              </Alert>
            </div>
          )}
        >
          <Suspense fallback={<DevicesSkeleton />}>
            <DevicesPage />
          </Suspense>
        </ErrorBoundary>
      )}
    </QueryErrorResetBoundary>
  ),
});

function DevicesPage() {
  const { data: devices } = useBsh_listMyDevicesSuspense(selector());

  // selector() already extracts .data, so devices is the array directly
  const deviceList = Array.isArray(devices) ? devices : [];

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">My Devices</h1>
          <p className="text-muted-foreground">
            Manage your registered BSH kitchen appliances
          </p>
        </div>
        <Link to="/projects/bsh-home-connect/devices/register">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Register Device
          </Button>
        </Link>
      </div>

      {deviceList.length === 0 ? (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-12">
              <Package className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No devices registered</h3>
              <p className="text-muted-foreground mb-4">
                Register your first BSH kitchen appliance to get started
              </p>
              <Link to="/projects/bsh-home-connect/devices/register">
                <Button>
                  <Plus className="mr-2 h-4 w-4" />
                  Register Your First Device
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {deviceList.map((customerDevice) => (
            <Card key={customerDevice.id} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="w-16 h-16 bg-muted rounded-lg flex items-center justify-center">
                    <Package className="h-8 w-8 text-muted-foreground" />
                  </div>
                  <div className="flex-1">
                    <CardTitle className="text-lg">
                      {customerDevice.device?.name}
                    </CardTitle>
                    <CardDescription>
                      {customerDevice.device?.brand} • {customerDevice.device?.category}
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="text-sm space-y-1">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Model:</span>
                    <span className="font-medium">
                      {customerDevice.device?.model_number}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Serial:</span>
                    <span className="font-mono text-xs">
                      {customerDevice.serial_number}
                    </span>
                  </div>
                  {customerDevice.purchase_date && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Purchased:</span>
                      <span>
                        {new Date(customerDevice.purchase_date).toLocaleDateString()}
                      </span>
                    </div>
                  )}
                  {customerDevice.warranty_expiry_date && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Warranty:</span>
                      <span className={
                        new Date(customerDevice.warranty_expiry_date) > new Date()
                          ? "text-green-600 font-medium"
                          : "text-red-600 font-medium"
                      }>
                        {new Date(customerDevice.warranty_expiry_date) > new Date()
                          ? "Active"
                          : "Expired"}
                      </span>
                    </div>
                  )}
                </div>
                <Button variant="outline" className="w-full" size="sm">
                  View Details
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

function DevicesSkeleton() {
  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <Skeleton className="h-9 w-48 mb-2" />
          <Skeleton className="h-5 w-96" />
        </div>
        <Skeleton className="h-10 w-40" />
      </div>
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {[1, 2, 3].map((i) => (
          <Card key={i}>
            <CardHeader>
              <div className="flex items-center gap-3">
                <Skeleton className="w-16 h-16 rounded-lg" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="h-5 w-full" />
                  <Skeleton className="h-4 w-3/4" />
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="space-y-2">
                {[1, 2, 3, 4].map((j) => (
                  <Skeleton key={j} className="h-4 w-full" />
                ))}
              </div>
              <Skeleton className="h-9 w-full" />
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
