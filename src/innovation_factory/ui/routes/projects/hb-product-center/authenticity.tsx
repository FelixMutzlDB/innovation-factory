import { createFileRoute } from "@tanstack/react-router";
import { Suspense, useState } from "react";
import { ErrorBoundary } from "react-error-boundary";
import { QueryErrorResetBoundary, useQueryClient } from "@tanstack/react-query";
import {
  useHb_listVerificationsSuspense,
  useHb_listAlertsSuspense,
  useHb_createVerification,
  useHb_getDatabricksResourcesSuspense,
} from "@/lib/api";
import { selector } from "@/lib/selector";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Fingerprint,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Loader2,
  Send,
  BarChart3,
  Sparkles,
  ExternalLink,
} from "lucide-react";

export const Route = createFileRoute(
  "/projects/hb-product-center/authenticity",
)({
  component: () => <AuthenticityPage />,
});

function AuthenticityPage() {
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
          <Fingerprint className="h-6 w-6" />
          Authenticity Verification Center
        </h1>
        <p className="text-muted-foreground mt-1">
          Brand protection through counterfeit detection and product
          authentication.
        </p>
      </div>

      <QueryErrorResetBoundary>
        {({ reset }) => (
          <ErrorBoundary
            onReset={reset}
            fallbackRender={({ resetErrorBoundary }) => (
              <Card>
                <CardContent className="p-6">
                  <p className="text-destructive">
                    Failed to load authenticity data.
                  </p>
                  <button
                    onClick={resetErrorBoundary}
                    className="mt-2 text-sm underline"
                  >
                    Retry
                  </button>
                </CardContent>
              </Card>
            )}
          >
            <Tabs defaultValue="dashboard">
              <TabsList>
                <TabsTrigger value="dashboard">
                  <BarChart3 className="h-4 w-4 mr-2" />
                  AI/BI Dashboard
                </TabsTrigger>
                <TabsTrigger value="verifications">Verifications</TabsTrigger>
                <TabsTrigger value="alerts">Alerts</TabsTrigger>
                <TabsTrigger value="new">New Request</TabsTrigger>
              </TabsList>

              <TabsContent value="dashboard" className="space-y-4">
                <Suspense
                  fallback={<Skeleton className="h-[70vh] w-full rounded-lg" />}
                >
                  <AuthenticityDashboard />
                </Suspense>
              </TabsContent>

              <TabsContent value="verifications" className="space-y-4">
                <Suspense fallback={<TableSkeleton />}>
                  <VerificationsList />
                </Suspense>
              </TabsContent>

              <TabsContent value="alerts" className="space-y-4">
                <Suspense fallback={<TableSkeleton />}>
                  <AlertsList />
                </Suspense>
              </TabsContent>

              <TabsContent value="new" className="space-y-4">
                <NewVerificationForm />
              </TabsContent>
            </Tabs>
          </ErrorBoundary>
        )}
      </QueryErrorResetBoundary>
    </div>
  );
}

const verificationStatusConfig: Record<string, { icon: React.ReactNode; variant: "default" | "secondary" | "destructive" | "outline" }> = {
  verified: { icon: <CheckCircle2 className="h-3 w-3" />, variant: "default" },
  suspicious: { icon: <AlertTriangle className="h-3 w-3" />, variant: "secondary" },
  counterfeit: { icon: <ShieldAlert className="h-3 w-3" />, variant: "destructive" },
  pending: { icon: <Clock className="h-3 w-3" />, variant: "outline" },
};

function VerificationsList() {
  const { data: verifications } = useHb_listVerificationsSuspense(selector());

  const counts = {
    verified: verifications.filter((v) => v.status === "verified").length,
    suspicious: verifications.filter((v) => v.status === "suspicious").length,
    counterfeit: verifications.filter((v) => v.status === "counterfeit").length,
  };

  return (
    <>
      <div className="grid grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="p-2 rounded-full bg-green-100 dark:bg-green-900/30">
              <ShieldCheck className="h-5 w-5 text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-green-600">{counts.verified}</p>
              <p className="text-xs text-muted-foreground">Verified Authentic</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="p-2 rounded-full bg-amber-100 dark:bg-amber-900/30">
              <AlertTriangle className="h-5 w-5 text-amber-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-amber-600">{counts.suspicious}</p>
              <p className="text-xs text-muted-foreground">Suspicious</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="p-2 rounded-full bg-red-100 dark:bg-red-900/30">
              <ShieldAlert className="h-5 w-5 text-red-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-red-600">{counts.counterfeit}</p>
              <p className="text-xs text-muted-foreground">Counterfeit</p>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Verifications</CardTitle>
          <CardDescription>{verifications.length} total</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>ID</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Method</TableHead>
                <TableHead>Requester</TableHead>
                <TableHead>Region</TableHead>
                <TableHead>Confidence</TableHead>
                <TableHead>Date</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {verifications.map((v) => {
                const cfg = verificationStatusConfig[v.status] ?? verificationStatusConfig.pending;
                return (
                  <TableRow key={v.id}>
                    <TableCell className="font-mono text-sm">#{v.id}</TableCell>
                    <TableCell>
                      <Badge variant={cfg.variant} className="gap-1">
                        {cfg.icon}
                        {v.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm capitalize">
                      {v.verification_method.replace("_", " ")}
                    </TableCell>
                    <TableCell className="text-sm">{v.requester_name}</TableCell>
                    <TableCell className="text-sm">{v.region}</TableCell>
                    <TableCell>
                      {v.confidence_score != null ? (
                        <span className="font-mono text-sm">
                          {(v.confidence_score * 100).toFixed(1)}%
                        </span>
                      ) : (
                        "-"
                      )}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {new Date(v.created_at).toLocaleDateString()}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </>
  );
}

const alertSeverityColors: Record<string, string> = {
  low: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
  medium: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400",
  high: "bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400",
  critical: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
};

function AlertsList() {
  const { data: alerts } = useHb_listAlertsSuspense(selector());

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <AlertTriangle className="h-5 w-5" />
          Counterfeit Alerts
        </CardTitle>
        <CardDescription>{alerts.length} alerts</CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Severity</TableHead>
              <TableHead>Region</TableHead>
              <TableHead>Resolution</TableHead>
              <TableHead>Investigator</TableHead>
              <TableHead>Date</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {alerts.map((alert) => (
              <TableRow key={alert.id}>
                <TableCell className="font-mono text-sm">#{alert.id}</TableCell>
                <TableCell className="text-sm">{alert.alert_type}</TableCell>
                <TableCell>
                  <span
                    className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${alertSeverityColors[alert.severity] ?? ""}`}
                  >
                    {alert.severity}
                  </span>
                </TableCell>
                <TableCell className="text-sm">{alert.region}</TableCell>
                <TableCell>
                  <Badge variant="outline" className="capitalize">
                    {alert.resolution.replace("_", " ")}
                  </Badge>
                </TableCell>
                <TableCell className="text-sm">
                  {alert.investigated_by ?? "-"}
                </TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {new Date(alert.created_at).toLocaleDateString()}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

function NewVerificationForm() {
  const [requesterName, setRequesterName] = useState("");
  const queryClient = useQueryClient();
  const createVerification = useHb_createVerification();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createVerification.mutate(
      {
        requester_type: "internal",
        requester_name: requesterName || "Current User",
        verification_method: "image_analysis",
        region: "EMEA",
      },
      {
        onSuccess: () => {
          queryClient.invalidateQueries({
            queryKey: ["hb_listVerifications"],
          });
          setRequesterName("");
        },
      },
    );
  };

  return (
    <Card className="max-w-lg">
      <CardHeader>
        <CardTitle>New Verification Request</CardTitle>
        <CardDescription>
          Submit a product for authenticity verification
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-sm font-medium">Requester Name</label>
            <input
              type="text"
              className="mt-1 w-full rounded-md border px-3 py-2 text-sm"
              placeholder="Your name or department"
              value={requesterName}
              onChange={(e) => setRequesterName(e.target.value)}
            />
          </div>
          <div className="border-2 border-dashed rounded-lg p-6 text-center">
            <Fingerprint className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
            <p className="text-sm text-muted-foreground">
              Drop product image for verification
            </p>
          </div>
          <Button
            type="submit"
            className="w-full"
            disabled={createVerification.isPending}
          >
            {createVerification.isPending ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Send className="h-4 w-4 mr-2" />
            )}
            Submit Verification
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

function AuthenticityDashboard() {
  const { data: resources } = useHb_getDatabricksResourcesSuspense(selector());
  const dashboardUrl = `https://${resources.workspace_url}/sql/dashboardsv3/${resources.aq_dashboard_id}`;
  const genieUrl = `https://${resources.workspace_url}/genie/rooms/${resources.aq_genie_space_id}`;

  return (
    <div className="space-y-4">
      <div className="flex gap-3 flex-wrap">
        <a href={dashboardUrl} target="_blank" rel="noopener noreferrer">
          <Button variant="outline" size="sm">
            <BarChart3 className="h-4 w-4 mr-2" />
            Open in Databricks
            <ExternalLink className="h-3 w-3 ml-2" />
          </Button>
        </a>
        <a href={genieUrl} target="_blank" rel="noopener noreferrer">
          <Button variant="outline" size="sm">
            <Sparkles className="h-4 w-4 mr-2" />
            Ask Genie
            <ExternalLink className="h-3 w-3 ml-2" />
          </Button>
        </a>
      </div>
      <div
        className="rounded-lg border overflow-hidden bg-white"
        style={{ height: "70vh" }}
      >
        <iframe
          src={resources.aq_dashboard_embed_url}
          className="w-full h-full border-0"
          title="Authenticity & Quality AI/BI Dashboard"
          allow="fullscreen"
        />
      </div>
    </div>
  );
}

function TableSkeleton() {
  return (
    <Card>
      <CardHeader>
        <Skeleton className="h-6 w-48" />
      </CardHeader>
      <CardContent className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full" />
        ))}
      </CardContent>
    </Card>
  );
}
