import { createFileRoute, Link } from "@tanstack/react-router";
import { Suspense } from "react";
import { QueryErrorResetBoundary } from "@tanstack/react-query";
import { ErrorBoundary } from "react-error-boundary";
import { useBsh_getTicketSuspense, useBsh_listTicketNotesSuspense } from "@/lib/api";
import selector from "@/lib/selector";
import { ChatInterface } from "@/components/chat/chat-interface";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import {
  AlertCircle,
  ArrowLeft,
  Package,
  Calendar,
  User,
  Truck,
  MessageSquare,
  Clock,
  CheckCircle2,
} from "lucide-react";

export const Route = createFileRoute("/projects/bsh-home-connect/tickets/$ticketId")({
  component: () => <TicketDetail />,
});

function TicketDetailContent() {
  const { ticketId } = Route.useParams();
  const { data: ticket } = useBsh_getTicketSuspense({
    params: { ticket_id: parseInt(ticketId) },
    ...selector()
  });
  const { data: notes } = useBsh_listTicketNotesSuspense({
    params: { ticket_id: parseInt(ticketId) },
    ...selector()
  });

  // selector() already extracts .data, so notes is the array directly
  const notesList = Array.isArray(notes) ? notes : [];

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      new: "bg-blue-500",
      troubleshooting: "bg-yellow-500",
      awaiting_shipment: "bg-orange-500",
      in_repair: "bg-purple-500",
      completed: "bg-green-500",
      cancelled: "bg-gray-500",
    };
    return colors[status] || colors.new;
  };

  const getStatusLabel = (status: string) => {
    return status.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());
  };

  const statusSteps = [
    { key: "new", label: "New", icon: MessageSquare },
    { key: "troubleshooting", label: "Troubleshooting", icon: Clock },
    { key: "awaiting_shipment", label: "Awaiting Shipment", icon: Package },
    { key: "in_repair", label: "In Repair", icon: Package },
    { key: "completed", label: "Completed", icon: CheckCircle2 },
  ];

  const currentStepIndex = statusSteps.findIndex((s) => s.key === ticket.status);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" asChild>
              <Link to="/projects/bsh-home-connect/tickets">
                <ArrowLeft className="h-4 w-4 mr-1" />
                Back to Tickets
              </Link>
            </Button>
          </div>
          <h1 className="text-3xl font-bold">{ticket.title}</h1>
          <p className="text-muted-foreground">
            Ticket #{ticket.id} • Created{" "}
            {new Date(ticket.created_at).toLocaleDateString()}
          </p>
        </div>
        <Badge className={getStatusColor(ticket.status)}>
          {getStatusLabel(ticket.status)}
        </Badge>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Main Content - Chat & Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Status Timeline */}
          <Card>
            <CardHeader>
              <CardTitle>Status Timeline</CardTitle>
              <CardDescription>Track your repair progress</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="relative">
                <div className="flex justify-between">
                  {statusSteps.map((step, idx) => {
                    const Icon = step.icon;
                    const isCompleted = idx <= currentStepIndex;
                    const isCurrent = idx === currentStepIndex;

                    return (
                      <div key={step.key} className="flex flex-col items-center flex-1">
                        <div
                          className={`h-10 w-10 rounded-full flex items-center justify-center ${
                            isCompleted
                              ? "bg-primary text-primary-foreground"
                              : "bg-muted text-muted-foreground"
                          } ${isCurrent ? "ring-4 ring-primary/20" : ""}`}
                        >
                          <Icon className="h-5 w-5" />
                        </div>
                        <p className="text-xs mt-2 text-center font-medium">
                          {step.label}
                        </p>
                      </div>
                    );
                  })}
                </div>
                {/* Progress Line */}
                <div className="absolute top-5 left-0 right-0 h-0.5 bg-muted -z-10">
                  <div
                    className="h-full bg-primary transition-all"
                    style={{
                      width: `${(currentStepIndex / (statusSteps.length - 1)) * 100}%`,
                    }}
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Chat Interface */}
          <Card className="flex flex-col h-[600px]">
            <CardHeader>
              <CardTitle>AI Troubleshooting Assistant</CardTitle>
              <CardDescription>
                Chat with our AI to diagnose and resolve your issue
              </CardDescription>
            </CardHeader>
            <div className="flex-1 flex flex-col overflow-hidden">
              <ChatInterface
                ticketId={parseInt(ticketId)}
                sessionType="customer_support"
              />
            </div>
          </Card>

          {/* Notes */}
          {notesList.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Notes & Updates</CardTitle>
                <CardDescription>Communication history</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {notesList.map((note) => (
                    <div key={note.id} className="border-l-2 border-primary pl-4">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge variant="outline" className="text-xs">
                          {note.author_role}
                        </Badge>
                        <p className="text-xs text-muted-foreground">
                          {new Date(note.created_at).toLocaleString()}
                        </p>
                      </div>
                      <p className="text-sm whitespace-pre-wrap">{note.content}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Sidebar - Device & Shipping Info */}
        <div className="space-y-6">
          {/* Device Info */}
          <Card>
            <CardHeader>
              <CardTitle>Device Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-start gap-3">
                <Package className="h-5 w-5 text-muted-foreground mt-0.5" />
                <div className="flex-1">
                  <p className="font-medium">
                    {ticket.customer_device?.device?.brand}{" "}
                    {ticket.customer_device?.device?.name}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {ticket.customer_device?.device?.model_number}
                  </p>
                </div>
              </div>

              <Separator />

              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Serial Number:</span>
                  <span className="font-mono">
                    {ticket.customer_device?.serial_number}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Purchase Date:</span>
                  <span>
                    {ticket.customer_device?.purchase_date && new Date(
                      ticket.customer_device.purchase_date
                    ).toLocaleDateString()}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Warranty:</span>
                  <span>
                    {ticket.customer_device?.warranty_expiry_date && (new Date(ticket.customer_device.warranty_expiry_date) >
                    new Date() ? (
                      <Badge variant="outline" className="text-green-600">
                        Active
                      </Badge>
                    ) : (
                      <Badge variant="outline" className="text-red-600">
                        Expired
                      </Badge>
                    ))}
                  </span>
                </div>
              </div>

              <Button variant="outline" size="sm" className="w-full" asChild>
                <Link to="/projects/bsh-home-connect/devices">
                  View Full Details
                </Link>
              </Button>
            </CardContent>
          </Card>

          {/* Shipping Information */}
          {(ticket.shipping_label_url || ticket.tracking_number) && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Truck className="h-5 w-5" />
                  Shipping Information
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {ticket.tracking_number && (
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">
                      Tracking Number
                    </p>
                    <p className="font-mono text-sm">{ticket.tracking_number}</p>
                  </div>
                )}

                {ticket.shipping_label_url && (
                  <Button variant="outline" size="sm" className="w-full" asChild>
                    <a
                      href={ticket.shipping_label_url}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      Download Shipping Label
                    </a>
                  </Button>
                )}
              </CardContent>
            </Card>
          )}

          {/* Ticket Details */}
          <Card>
            <CardHeader>
              <CardTitle>Ticket Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div className="flex items-start gap-2">
                <Calendar className="h-4 w-4 text-muted-foreground mt-0.5" />
                <div className="flex-1">
                  <p className="text-muted-foreground">Created</p>
                  <p>{new Date(ticket.created_at).toLocaleString()}</p>
                </div>
              </div>

              {ticket.updated_at !== ticket.created_at && (
                <div className="flex items-start gap-2">
                  <Clock className="h-4 w-4 text-muted-foreground mt-0.5" />
                  <div className="flex-1">
                    <p className="text-muted-foreground">Last Updated</p>
                    <p>{new Date(ticket.updated_at).toLocaleString()}</p>
                  </div>
                </div>
              )}

              {ticket.technician_id && (
                <div className="flex items-start gap-2">
                  <User className="h-4 w-4 text-muted-foreground mt-0.5" />
                  <div className="flex-1">
                    <p className="text-muted-foreground">Assigned Technician</p>
                    <p>Technician ID: {ticket.technician_id}</p>
                  </div>
                </div>
              )}

              {ticket.priority && (
                <div>
                  <p className="text-muted-foreground mb-1">Priority</p>
                  <Badge variant="outline">{ticket.priority}</Badge>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Issue Description */}
          <Card>
            <CardHeader>
              <CardTitle>Issue Description</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm whitespace-pre-wrap">{ticket.description}</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

function TicketDetailSkeleton() {
  return (
    <div className="space-y-6">
      <div>
        <Skeleton className="h-8 w-64 mb-2" />
        <Skeleton className="h-4 w-96" />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <Skeleton className="h-6 w-48" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-32 w-full" />
            </CardContent>
          </Card>
        </div>
        <div>
          <Card>
            <CardHeader>
              <Skeleton className="h-6 w-32" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-48 w-full" />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

function TicketDetail() {
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
                  Failed to Load Ticket
                </CardTitle>
                <CardDescription>
                  There was an error loading the ticket details.
                </CardDescription>
              </CardHeader>
              <CardContent className="flex gap-2">
                <Button variant="outline" onClick={resetErrorBoundary}>
                  Try Again
                </Button>
                <Button variant="outline" asChild>
                  <Link to="/projects/bsh-home-connect/tickets">Back to Tickets</Link>
                </Button>
              </CardContent>
            </Card>
          )}
        >
          <Suspense fallback={<TicketDetailSkeleton />}>
            <TicketDetailContent />
          </Suspense>
        </ErrorBoundary>
      )}
    </QueryErrorResetBoundary>
  );
}
