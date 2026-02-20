import { createFileRoute, Link } from "@tanstack/react-router";
import { Suspense } from "react";
import { ErrorBoundary } from "react-error-boundary";
import { QueryErrorResetBoundary, useQueryClient } from "@tanstack/react-query";
import type { HbInspectionDetailOut } from "@/lib/api";
import {
  useHb_getInspectionSuspense,
  useHb_updateInspection,
  hb_getInspectionKey,
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
import {
  ArrowLeft,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  ShieldCheck,
} from "lucide-react";

export const Route = createFileRoute(
  "/projects/hb-product-center/quality/$inspectionId",
)({
  component: () => <InspectionDetailPage />,
});

function InspectionDetailPage() {
  const { inspectionId } = Route.useParams();

  return (
    <div className="p-6 space-y-6">
      <Link
        to="/projects/hb-product-center/quality"
        className="text-sm text-muted-foreground hover:text-foreground flex items-center gap-1"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Quality Control
      </Link>

      <QueryErrorResetBoundary>
        {({ reset }) => (
          <ErrorBoundary
            onReset={reset}
            fallbackRender={({ resetErrorBoundary }) => (
              <Card>
                <CardContent className="p-6">
                  <p className="text-destructive">
                    Failed to load inspection details.
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
            <Suspense fallback={<DetailSkeleton />}>
              <InspectionDetail inspectionId={Number(inspectionId)} />
            </Suspense>
          </ErrorBoundary>
        )}
      </QueryErrorResetBoundary>
    </div>
  );
}

const severityColors: Record<string, string> = {
  minor: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400",
  moderate: "bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400",
  major: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
  critical: "bg-red-200 text-red-900 dark:bg-red-900/50 dark:text-red-300",
};

function InspectionDetail({ inspectionId }: { inspectionId: number }) {
  const { data: detail } = useHb_getInspectionSuspense({
    params: { inspection_id: inspectionId },
    ...selector<HbInspectionDetailOut>(),
  });
  const queryClient = useQueryClient();
  const updateInspection = useHb_updateInspection();

  const handleStatusUpdate = (status: "approved" | "rejected") => {
    updateInspection.mutate(
      { params: { inspection_id: inspectionId }, data: { status } },
      {
        onSuccess: () => {
          queryClient.invalidateQueries({
            queryKey: hb_getInspectionKey({ inspection_id: inspectionId }),
          });
        },
      },
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <ShieldCheck className="h-6 w-6" />
            Inspection #{detail.id}
          </h1>
          <p className="text-muted-foreground mt-1">
            Batch: {detail.batch_number} &bull; Inspector: {detail.inspector}
          </p>
        </div>
        {(detail.status === "pending" || detail.status === "in_review") && (
          <div className="flex gap-2">
            <Button
              variant="default"
              onClick={() => handleStatusUpdate("approved")}
              disabled={updateInspection.isPending}
            >
              <CheckCircle2 className="h-4 w-4 mr-1" />
              Approve
            </Button>
            <Button
              variant="destructive"
              onClick={() => handleStatusUpdate("rejected")}
              disabled={updateInspection.isPending}
            >
              <XCircle className="h-4 w-4 mr-1" />
              Reject
            </Button>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Overall Score</CardTitle>
          </CardHeader>
          <CardContent>
            <p
              className={`text-4xl font-bold ${
                detail.overall_score >= 85
                  ? "text-green-600"
                  : detail.overall_score >= 70
                    ? "text-amber-600"
                    : "text-red-600"
              }`}
            >
              {detail.overall_score}
            </p>
            <p className="text-xs text-muted-foreground mt-1">/ 100</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Status</CardTitle>
          </CardHeader>
          <CardContent>
            <Badge
              variant={
                detail.status === "approved"
                  ? "default"
                  : detail.status === "rejected"
                    ? "destructive"
                    : "outline"
              }
              className="text-base px-3 py-1"
            >
              {detail.status.replace("_", " ")}
            </Badge>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Manufacturing Partner</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-lg font-medium">
              {detail.manufacturing_partner}
            </p>
          </CardContent>
        </Card>
      </div>

      {detail.product && (
        <Card>
          <CardHeader>
            <CardTitle>Product Details</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <p className="text-muted-foreground">SKU</p>
                <p className="font-mono font-medium">{detail.product.sku}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Style</p>
                <p className="font-medium">{detail.product.style_name}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Color</p>
                <p className="font-medium">{detail.product.color}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Collection</p>
                <p className="font-medium">{detail.product.collection}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5" />
            Detected Defects
          </CardTitle>
          <CardDescription>
            {(detail.defects ?? []).length} defect{(detail.defects ?? []).length !== 1 && "s"}{" "}
            found
          </CardDescription>
        </CardHeader>
        <CardContent>
          {(detail.defects ?? []).length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <CheckCircle2 className="h-10 w-10 mx-auto mb-2 text-green-500" />
              <p>No defects detected</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Type</TableHead>
                  <TableHead>Severity</TableHead>
                  <TableHead>Location</TableHead>
                  <TableHead>Confidence</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(detail.defects ?? []).map((defect) => (
                  <TableRow key={defect.id}>
                    <TableCell className="capitalize">
                      {defect.defect_type.replace("_", " ")}
                    </TableCell>
                    <TableCell>
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${severityColors[defect.severity] ?? ""}`}
                      >
                        {defect.severity}
                      </span>
                    </TableCell>
                    <TableCell className="text-sm">
                      {defect.location_description}
                    </TableCell>
                    <TableCell>
                      <span className="font-mono text-sm">
                        {(defect.confidence_score * 100).toFixed(1)}%
                      </span>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function DetailSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-8 w-64" />
      <div className="grid grid-cols-3 gap-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-32" />
        ))}
      </div>
      <Skeleton className="h-64" />
    </div>
  );
}
