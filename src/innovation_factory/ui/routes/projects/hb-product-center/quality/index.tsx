import { createFileRoute, Link } from "@tanstack/react-router";
import { Suspense } from "react";
import { ErrorBoundary } from "react-error-boundary";
import { QueryErrorResetBoundary } from "@tanstack/react-query";
import {
  useHb_listInspectionsSuspense,
  useHb_getQualityStatsSuspense,
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
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Clock,
  Eye,
  BarChart3,
  Sparkles,
  ExternalLink,
} from "lucide-react";

export const Route = createFileRoute(
  "/projects/hb-product-center/quality/",
)({
  component: () => <QualityPage />,
});

function QualityPage() {
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
          <ShieldCheck className="h-6 w-6" />
          Quality Control Studio
        </h1>
        <p className="text-muted-foreground mt-1">
          AI-powered defect detection, quality scoring, and approval workflows.
        </p>
      </div>

      <QueryErrorResetBoundary>
        {({ reset }) => (
          <ErrorBoundary
            onReset={reset}
            fallbackRender={({ resetErrorBoundary }) => (
              <Card>
                <CardContent className="p-6">
                  <p className="text-destructive">Failed to load quality data.</p>
                  <button onClick={resetErrorBoundary} className="mt-2 text-sm underline">Retry</button>
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
                <TabsTrigger value="inspections">Inspections</TabsTrigger>
              </TabsList>

              <TabsContent value="dashboard" className="space-y-4">
                <Suspense
                  fallback={<Skeleton className="h-[70vh] w-full rounded-lg" />}
                >
                  <QualityDashboard />
                </Suspense>
              </TabsContent>

              <TabsContent value="inspections" className="space-y-6">
                <Suspense fallback={<QualitySkeleton />}>
                  <QualityStats />
                </Suspense>
                <Suspense fallback={<InspectionsSkeleton />}>
                  <InspectionsList />
                </Suspense>
              </TabsContent>
            </Tabs>
          </ErrorBoundary>
        )}
      </QueryErrorResetBoundary>
    </div>
  );
}

function QualityStats() {
  const { data: stats } = useHb_getQualityStatsSuspense(selector());

  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
      <Card>
        <CardContent className="p-4">
          <p className="text-xs text-muted-foreground font-medium">Total Inspections</p>
          <p className="text-2xl font-bold mt-1">{stats.total_inspections}</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-4">
          <p className="text-xs text-muted-foreground font-medium flex items-center gap-1">
            <CheckCircle2 className="h-3 w-3 text-green-500" /> Approved
          </p>
          <p className="text-2xl font-bold mt-1 text-green-600">{stats.approved}</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-4">
          <p className="text-xs text-muted-foreground font-medium flex items-center gap-1">
            <XCircle className="h-3 w-3 text-red-500" /> Rejected
          </p>
          <p className="text-2xl font-bold mt-1 text-red-600">{stats.rejected}</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-4">
          <p className="text-xs text-muted-foreground font-medium flex items-center gap-1">
            <Clock className="h-3 w-3 text-amber-500" /> Pending
          </p>
          <p className="text-2xl font-bold mt-1 text-amber-600">{stats.pending + stats.in_review}</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-4">
          <p className="text-xs text-muted-foreground font-medium flex items-center gap-1">
            <BarChart3 className="h-3 w-3 text-blue-500" /> Avg Score
          </p>
          <p className="text-2xl font-bold mt-1">{stats.avg_score}</p>
        </CardContent>
      </Card>
    </div>
  );
}

const statusVariant: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  approved: "default",
  rejected: "destructive",
  pending: "outline",
  in_review: "secondary",
};

const statusIcon: Record<string, React.ReactNode> = {
  approved: <CheckCircle2 className="h-3 w-3" />,
  rejected: <XCircle className="h-3 w-3" />,
  pending: <Clock className="h-3 w-3" />,
  in_review: <Eye className="h-3 w-3" />,
};

function InspectionsList() {
  const { data: inspections } = useHb_listInspectionsSuspense(selector());

  return (
    <Card>
      <CardHeader>
        <CardTitle>Quality Inspections</CardTitle>
        <CardDescription>{inspections.length} inspections found</CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>Batch</TableHead>
              <TableHead>Inspector</TableHead>
              <TableHead>Partner</TableHead>
              <TableHead>Score</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Date</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {inspections.map((insp) => (
              <TableRow key={insp.id}>
                <TableCell>
                  <Link
                    to="/projects/hb-product-center/quality/$inspectionId"
                    params={{ inspectionId: String(insp.id) }}
                    className="text-primary hover:underline font-mono text-sm"
                  >
                    #{insp.id}
                  </Link>
                </TableCell>
                <TableCell className="font-mono text-xs">{insp.batch_number}</TableCell>
                <TableCell className="text-sm">{insp.inspector}</TableCell>
                <TableCell className="text-sm">{insp.manufacturing_partner}</TableCell>
                <TableCell>
                  <span
                    className={
                      insp.overall_score >= 85
                        ? "text-green-600 font-semibold"
                        : insp.overall_score >= 70
                          ? "text-amber-600 font-semibold"
                          : "text-red-600 font-semibold"
                    }
                  >
                    {insp.overall_score}
                  </span>
                </TableCell>
                <TableCell>
                  <Badge variant={statusVariant[insp.status] ?? "outline"} className="gap-1">
                    {statusIcon[insp.status]}
                    {insp.status.replace("_", " ")}
                  </Badge>
                </TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {new Date(insp.created_at).toLocaleDateString()}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

function QualityDashboard() {
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
          title="Quality Control AI/BI Dashboard"
          allow="fullscreen"
        />
      </div>
    </div>
  );
}

function QualitySkeleton() {
  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
      {Array.from({ length: 5 }).map((_, i) => (
        <Card key={i}>
          <CardContent className="p-4 space-y-2">
            <Skeleton className="h-3 w-20" />
            <Skeleton className="h-8 w-12" />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function InspectionsSkeleton() {
  return (
    <Card>
      <CardHeader><Skeleton className="h-6 w-48" /></CardHeader>
      <CardContent className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full" />
        ))}
      </CardContent>
    </Card>
  );
}
