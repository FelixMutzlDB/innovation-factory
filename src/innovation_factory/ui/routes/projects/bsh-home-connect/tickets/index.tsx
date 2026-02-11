import { createFileRoute, Link } from "@tanstack/react-router";
import { useBsh_listTicketsSuspense } from "@/lib/api";
import selector from "@/lib/selector";
import { Suspense } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Ticket, Plus, ArrowRight, AlertCircle } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { QueryErrorResetBoundary } from "@tanstack/react-query";
import { ErrorBoundary } from "react-error-boundary";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

export const Route = createFileRoute("/projects/bsh-home-connect/tickets/")({
  component: () => (
    <QueryErrorResetBoundary>
      {({ reset }) => (
        <ErrorBoundary
          onReset={reset}
          fallbackRender={({ error, resetErrorBoundary }) => (
            <div className="container mx-auto p-6">
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>Error loading tickets</AlertTitle>
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
          <Suspense fallback={<TicketsSkeleton />}>
            <TicketsPage />
          </Suspense>
        </ErrorBoundary>
      )}
    </QueryErrorResetBoundary>
  ),
});

function TicketsPage() {
  const { data: tickets } = useBsh_listTicketsSuspense({
    params: { role: "customer" },
    ...selector()
  });

  // selector() already extracts .data, so tickets is the array directly
  const ticketList = Array.isArray(tickets) ? tickets : [];

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Support Tickets</h1>
          <p className="text-muted-foreground">
            Track your support requests and repairs
          </p>
        </div>
        <Link to="/projects/bsh-home-connect/support">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            New Support Request
          </Button>
        </Link>
      </div>

      {ticketList.length === 0 ? (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-12">
              <Ticket className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No support tickets</h3>
              <p className="text-muted-foreground mb-4">
                Create your first support request to get help with your appliances
              </p>
              <Link to="/projects/bsh-home-connect/support">
                <Button>
                  <Plus className="mr-2 h-4 w-4" />
                  Create Support Request
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {ticketList.map((ticket) => (
            <Card key={ticket.id} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <CardTitle className="text-xl">{ticket.title}</CardTitle>
                      <Badge variant={getStatusVariant(ticket.status)}>
                        {formatStatus(ticket.status)}
                      </Badge>
                      <Badge variant="outline">{ticket.priority}</Badge>
                    </div>
                    <CardDescription>
                      {ticket.customer_device?.device?.brand}{" "}
                      {ticket.customer_device?.device?.name} •{" "}
                      {ticket.customer_device?.device?.model_number}
                    </CardDescription>
                  </div>
                  <Link to="/projects/bsh-home-connect/tickets/$ticketId" params={{ ticketId: ticket.id.toString() }}>
                    <Button variant="ghost" size="sm">
                      View Details
                      <ArrowRight className="ml-2 h-4 w-4" />
                    </Button>
                  </Link>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground line-clamp-2 mb-4">
                  {ticket.description}
                </p>
                <div className="flex items-center justify-between text-sm">
                  <div className="text-muted-foreground">
                    Created {new Date(ticket.created_at).toLocaleDateString()}
                  </div>
                  <div className="text-muted-foreground">
                    Last updated {new Date(ticket.updated_at).toLocaleDateString()}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

function getStatusVariant(status: string): "default" | "secondary" | "destructive" | "outline" {
  switch (status) {
    case "completed":
      return "default";
    case "in_repair":
      return "secondary";
    case "cancelled":
      return "destructive";
    default:
      return "outline";
  }
}

function formatStatus(status: string): string {
  return status
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function TicketsSkeleton() {
  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <Skeleton className="h-9 w-48 mb-2" />
          <Skeleton className="h-5 w-96" />
        </div>
        <Skeleton className="h-10 w-48" />
      </div>
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <Card key={i}>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="space-y-2 flex-1">
                  <div className="flex items-center gap-2">
                    <Skeleton className="h-6 w-64" />
                    <Skeleton className="h-5 w-20" />
                    <Skeleton className="h-5 w-16" />
                  </div>
                  <Skeleton className="h-4 w-96" />
                </div>
                <Skeleton className="h-9 w-32" />
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <Skeleton className="h-10 w-full" />
              <div className="flex justify-between">
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-4 w-32" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
