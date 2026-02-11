import { createFileRoute, Link } from "@tanstack/react-router";
import { Suspense } from "react";
import { QueryErrorResetBoundary } from "@tanstack/react-query";
import { ErrorBoundary } from "react-error-boundary";
import {
  useBsh_listMyDevicesSuspense,
  useBsh_listTicketsSuspense,
  useBsh_getCurrentCustomerSuspense
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
  Package,
  Plus,
  AlertCircle,
  Wrench,
  Clock,
  CheckCircle2,
} from "lucide-react";

export const Route = createFileRoute("/projects/bsh-home-connect/dashboard")({
  component: () => <Dashboard />,
});

function DashboardContent() {
  const { data: customer } = useBsh_getCurrentCustomerSuspense(selector());
  const { data: devices } = useBsh_listMyDevicesSuspense(selector());
  const { data: tickets } = useBsh_listTicketsSuspense({
    params: { role: "customer" },
    ...selector(),
  });

  const activeTickets = tickets.filter(
    (t) => !["completed", "cancelled"].includes(t.status)
  );
  const recentTickets = tickets.slice(0, 5);

  return (
    <div className="space-y-6">
      {/* Welcome Header */}
      <div className="pb-2">
        <h1 className="text-3xl font-bold tracking-tight">
          Welcome back, <span className="text-primary">{customer.first_name}</span>!
        </h1>
        <p className="text-muted-foreground mt-2">
          Manage your connected appliances and support tickets
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="border-l-4 border-l-primary">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Registered Devices
            </CardTitle>
            <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center">
              <Package className="h-4 w-4 text-primary" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-primary">{devices.length}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Connected appliances
            </p>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-accent">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Active Tickets
            </CardTitle>
            <div className="h-8 w-8 rounded-lg bg-accent/10 flex items-center justify-center">
              <Wrench className="h-4 w-4 text-accent" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-accent">{activeTickets.length}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Support requests in progress
            </p>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-muted-foreground">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Total Tickets
            </CardTitle>
            <div className="h-8 w-8 rounded-lg bg-muted flex items-center justify-center">
              <Clock className="h-4 w-4 text-muted-foreground" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{tickets.length}</div>
            <p className="text-xs text-muted-foreground mt-1">All time</p>
          </CardContent>
        </Card>
      </div>

      {/* Registered Devices */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Your Devices</CardTitle>
              <CardDescription>
                Registered BSH kitchen appliances
              </CardDescription>
            </div>
            <Button asChild size="sm">
              <Link to="/projects/bsh-home-connect/devices/register">
                <Plus className="h-4 w-4 mr-2" />
                Register Device
              </Link>
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {devices.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Package className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No devices registered yet</p>
              <Button asChild variant="outline" size="sm" className="mt-4">
                <Link to="/projects/bsh-home-connect/devices/register">Register your first device</Link>
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              {devices.map((device) => (
                <div
                  key={device.id}
                  className="flex items-center gap-4 p-4 rounded-lg border hover:bg-accent transition-colors"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold">
                        {device.device?.brand} {device.device?.name}
                      </h3>
                      <Badge variant="outline" className="text-xs">
                        {device.device?.category?.replace("_", " ")}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      Model: {device.device?.model_number} • Serial:{" "}
                      {device.serial_number}
                    </p>
                    {device.warranty_expiry_date && (
                      <p className="text-xs text-muted-foreground mt-1">
                        Warranty expires:{" "}
                        {new Date(device.warranty_expiry_date).toLocaleDateString()}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Recent Tickets */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Recent Support Tickets</CardTitle>
              <CardDescription>Your latest support requests</CardDescription>
            </div>
            <Button asChild variant="outline" size="sm">
              <Link to="/projects/bsh-home-connect/tickets">View All</Link>
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {recentTickets.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <CheckCircle2 className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No support tickets yet</p>
              <Button asChild variant="outline" size="sm" className="mt-4">
                <Link to="/projects/bsh-home-connect/support">Get support</Link>
              </Button>
            </div>
          ) : (
            <div className="space-y-3">
              {recentTickets.map((ticket) => (
                <Link
                  key={ticket.id}
                  to="/projects/bsh-home-connect/tickets/$ticketId"
                  params={{ ticketId: ticket.id.toString() }}
                  className="block"
                >
                  <div className="flex items-center gap-4 p-3 rounded-lg border hover:bg-accent transition-colors">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h4 className="font-medium">{ticket.title}</h4>
                        <StatusBadge status={ticket.status} />
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {ticket.customer_device?.device?.brand}{" "}
                        {ticket.customer_device?.device?.name}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Created{" "}
                        {new Date(ticket.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <Button variant="ghost" size="sm">
                      View
                    </Button>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>Common tasks</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 md:grid-cols-2">
            <Button asChild variant="outline" className="h-auto py-4">
              <Link to="/projects/bsh-home-connect/support">
                <div className="flex flex-col items-center gap-2">
                  <Wrench className="h-6 w-6" />
                  <span>Get Support</span>
                </div>
              </Link>
            </Button>
            <Button asChild variant="outline" className="h-auto py-4">
              <Link to="/projects/bsh-home-connect/devices/register">
                <div className="flex flex-col items-center gap-2">
                  <Plus className="h-6 w-6" />
                  <span>Register Device</span>
                </div>
              </Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const variants: Record<string, { className: string; label: string }> = {
    new: {
      className: "bg-primary text-primary-foreground",
      label: "New"
    },
    troubleshooting: {
      className: "bg-accent text-accent-foreground",
      label: "Troubleshooting"
    },
    awaiting_shipment: {
      className: "bg-secondary text-secondary-foreground",
      label: "Awaiting Shipment"
    },
    in_repair: {
      className: "bg-accent text-accent-foreground",
      label: "In Repair"
    },
    completed: {
      className: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100",
      label: "Completed"
    },
    cancelled: {
      className: "bg-muted text-muted-foreground",
      label: "Cancelled"
    },
  };

  const config = variants[status] || variants.new;

  return <Badge className={config.className}>{config.label}</Badge>;
}

function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <div>
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-4 w-96 mt-2" />
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {[1, 2, 3].map((i) => (
          <Card key={i}>
            <CardHeader>
              <Skeleton className="h-4 w-32" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-16" />
              <Skeleton className="h-3 w-24 mt-2" />
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-4 w-64" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-32 w-full" />
        </CardContent>
      </Card>
    </div>
  );
}

function Dashboard() {
  return (
    <QueryErrorResetBoundary>
      {({ reset }) => (
        <ErrorBoundary
          onReset={reset}
          fallbackRender={({ resetErrorBoundary }) => (
            <Card className="border-destructive/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-destructive">
                  <AlertCircle className="h-5 w-5" />
                  Failed to Load Dashboard
                </CardTitle>
                <CardDescription>
                  There was an error loading your dashboard. Please try again.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button variant="outline" onClick={resetErrorBoundary}>
                  Try Again
                </Button>
              </CardContent>
            </Card>
          )}
        >
          <Suspense fallback={<DashboardSkeleton />}>
            <DashboardContent />
          </Suspense>
        </ErrorBoundary>
      )}
    </QueryErrorResetBoundary>
  );
}
