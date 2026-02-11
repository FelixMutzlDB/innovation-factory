import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useBsh_listDevicesSuspense, useBsh_registerDevice, bsh_listMyDevicesKey } from "@/lib/api";
import selector from "@/lib/selector";
import { Suspense, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { QueryErrorResetBoundary, useQueryClient } from "@tanstack/react-query";
import { ErrorBoundary } from "react-error-boundary";
import { AlertCircle, ArrowLeft, Package } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

export const Route = createFileRoute("/projects/bsh-home-connect/devices/register")({
  component: () => (
    <QueryErrorResetBoundary>
      {({ reset }) => (
        <ErrorBoundary
          onReset={reset}
          fallbackRender={({ error, resetErrorBoundary }) => (
            <div className="container mx-auto p-6">
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>Error</AlertTitle>
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
          <Suspense fallback={<RegisterDeviceSkeleton />}>
            <RegisterDevicePage />
          </Suspense>
        </ErrorBoundary>
      )}
    </QueryErrorResetBoundary>
  ),
});

function RegisterDevicePage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { data: devices } = useBsh_listDevicesSuspense(selector());
  const registerDevice = useBsh_registerDevice();

  // selector() already extracts .data, so devices is the array directly
  const deviceList = Array.isArray(devices) ? devices : [];

  const [selectedDeviceId, setSelectedDeviceId] = useState<string>("");
  const [serialNumber, setSerialNumber] = useState("");
  const [purchaseDate, setPurchaseDate] = useState("");
  const [warrantyExpiryDate, setWarrantyExpiryDate] = useState("");
  const [batchNumber] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!selectedDeviceId || !serialNumber || !purchaseDate || !warrantyExpiryDate) {
      setError("Please fill in all required fields");
      return;
    }

    try {
      await registerDevice.mutateAsync({
        params: {},
        data: {
          device_id: parseInt(selectedDeviceId),
          serial_number: serialNumber,
          purchase_date: purchaseDate,
          warranty_expiry_date: warrantyExpiryDate,
          batch_number: batchNumber || undefined,
        },
      });

      // Invalidate the list of registered devices so it refetches
      await queryClient.invalidateQueries({ queryKey: bsh_listMyDevicesKey() });

      navigate({ to: "/projects/bsh-home-connect/devices" });
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to register device");
    }
  };

  const selectedDevice = deviceList.find((d) => d.id === parseInt(selectedDeviceId));

  return (
    <div className="container mx-auto p-6 max-w-2xl">
      <div className="mb-6">
        <Button variant="ghost" onClick={() => navigate({ to: "/projects/bsh-home-connect/devices" })}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to My Devices
        </Button>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center">
              <Package className="h-6 w-6 text-primary" />
            </div>
            <div>
              <CardTitle className="text-2xl">Register New Device</CardTitle>
              <CardDescription>
                Add a BSH kitchen appliance to your account
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <div className="space-y-2">
              <Label htmlFor="device">Device Type *</Label>
              <Select value={selectedDeviceId} onValueChange={setSelectedDeviceId}>
                <SelectTrigger id="device">
                  <SelectValue placeholder="Select a device" />
                </SelectTrigger>
                <SelectContent>
                  {deviceList.length > 0 ? (
                    deviceList.map((device) => (
                      <SelectItem key={device.id} value={device.id.toString()}>
                        {device.brand} {device.name} ({device.model_number})
                      </SelectItem>
                    ))
                  ) : (
                    <SelectItem value="no-devices" disabled>
                      No devices available
                    </SelectItem>
                  )}
                </SelectContent>
              </Select>
            </div>

            {selectedDevice && (
              <div className="p-4 bg-muted rounded-lg space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Category:</span>
                  <span className="font-medium">{selectedDevice.category}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Model:</span>
                  <span className="font-medium">{selectedDevice.model_number}</span>
                </div>
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="serial">Serial Number *</Label>
              <Input
                id="serial"
                placeholder="e.g., SN123456789"
                value={serialNumber}
                onChange={(e) => setSerialNumber(e.target.value)}
                required
              />
              <p className="text-xs text-muted-foreground">
                Find this on the product label or documentation
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="purchase">Purchase Date *</Label>
              <Input
                id="purchase"
                type="date"
                value={purchaseDate}
                onChange={(e) => setPurchaseDate(e.target.value)}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="warranty">Warranty Expiry Date *</Label>
              <Input
                id="warranty"
                type="date"
                value={warrantyExpiryDate}
                onChange={(e) => setWarrantyExpiryDate(e.target.value)}
                required
              />
            </div>

            <div className="flex gap-3 pt-4">
              <Button
                type="button"
                variant="outline"
                className="flex-1"
                onClick={() => navigate({ to: "/projects/bsh-home-connect/devices" })}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                className="flex-1"
                disabled={registerDevice.isPending}
              >
                {registerDevice.isPending ? "Registering..." : "Register Device"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

function RegisterDeviceSkeleton() {
  return (
    <div className="container mx-auto p-6 max-w-2xl">
      <Skeleton className="h-10 w-48 mb-6" />
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <Skeleton className="w-12 h-12 rounded-lg" />
            <div className="space-y-2">
              <Skeleton className="h-7 w-64" />
              <Skeleton className="h-5 w-96" />
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="space-y-2">
              <Skeleton className="h-5 w-32" />
              <Skeleton className="h-10 w-full" />
            </div>
          ))}
          <div className="flex gap-3">
            <Skeleton className="h-10 flex-1" />
            <Skeleton className="h-10 flex-1" />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
