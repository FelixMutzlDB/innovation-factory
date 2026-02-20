import { createFileRoute } from "@tanstack/react-router";
import { Suspense, useState, useRef } from "react";
import { ErrorBoundary } from "react-error-boundary";
import { QueryErrorResetBoundary, useQueryClient } from "@tanstack/react-query";
import {
  useHb_listRecognitionJobsSuspense,
  useHb_createRecognitionJob,
  useHb_identifyProduct,
  type ProductIdentifyResponse,
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
  ScanSearch,
  Upload,
  Camera,
  Layers,
  CheckCircle2,
  Clock,
  XCircle,
  Loader2,
  Sparkles,
  Package,
} from "lucide-react";

export const Route = createFileRoute(
  "/projects/hb-product-center/recognition",
)({
  component: () => <RecognitionPage />,
});

function RecognitionPage() {
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
          <ScanSearch className="h-6 w-6" />
          Visual Product Recognition Hub
        </h1>
        <p className="text-muted-foreground mt-1">
          Upload product images to instantly identify SKU, style, color, and
          size. Supports single and batch processing.
        </p>
      </div>

      <UploadSection />

      <QueryErrorResetBoundary>
        {({ reset }) => (
          <ErrorBoundary
            onReset={reset}
            fallbackRender={({ resetErrorBoundary }) => (
              <Card>
                <CardContent className="p-6">
                  <p className="text-destructive">
                    Failed to load recognition jobs.
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
            <Suspense fallback={<JobsSkeleton />}>
              <JobsList />
            </Suspense>
          </ErrorBoundary>
        )}
      </QueryErrorResetBoundary>
    </div>
  );
}

function UploadSection() {
  const [mode, setMode] = useState<"single" | "batch">("single");
  const [description, setDescription] = useState("");
  const [identifyResult, setIdentifyResult] = useState<ProductIdentifyResponse | null>(null);
  const queryClient = useQueryClient();
  const createJob = useHb_createRecognitionJob();
  const identifyProduct = useHb_identifyProduct();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleUpload = () => {
    createJob.mutate(
      {
        job_type: mode,
        image_count: mode === "batch" ? 10 : 1,
        user_role: "store_associate",
        submitted_by: "Current User",
      },
      {
        onSuccess: () => {
          queryClient.invalidateQueries({ queryKey: ["hb_listRecognitionJobs"] });
        },
      },
    );
  };

  const handleIdentify = () => {
    if (!description.trim()) return;
    identifyProduct.mutate(
      { description: description.trim() },
      {
        onSuccess: (result) => {
          setIdentifyResult(result.data);
        },
      },
    );
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Upload className="h-4 w-4" />
              Upload Image
            </CardTitle>
            <CardDescription>
              Drag and drop or click to upload product images
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div
              className="border-2 border-dashed rounded-lg p-8 text-center hover:bg-muted/50 transition-colors cursor-pointer"
              onClick={() => fileInputRef.current?.click()}
            >
              <Camera className="h-10 w-10 mx-auto text-muted-foreground mb-3" />
              <p className="text-sm text-muted-foreground mb-1">
                Drop product image here or click to browse
              </p>
              <p className="text-xs text-muted-foreground">
                Supports JPG, PNG, WebP up to 10MB
              </p>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) {
                    setDescription(
                      `Product image: ${file.name.replace(/\.[^.]+$/, "").replace(/[-_]/g, " ")}`,
                    );
                  }
                }}
              />
            </div>
            <div className="flex gap-2 mt-4">
              <Button
                variant={mode === "single" ? "default" : "outline"}
                size="sm"
                onClick={() => setMode("single")}
              >
                <Camera className="h-3 w-3 mr-1" />
                Single
              </Button>
              <Button
                variant={mode === "batch" ? "default" : "outline"}
                size="sm"
                onClick={() => setMode("batch")}
              >
                <Layers className="h-3 w-3 mr-1" />
                Batch
              </Button>
            </div>
            <Button
              className="w-full mt-4"
              onClick={handleUpload}
              disabled={createJob.isPending}
            >
              {createJob.isPending ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <ScanSearch className="h-4 w-4 mr-2" />
              )}
              {mode === "batch"
                ? "Start Batch Recognition"
                : "Submit Recognition Job"}
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Sparkles className="h-4 w-4" />
              AI Product Identification
            </CardTitle>
            <CardDescription>
              Describe a product or paste image details to identify it using AI
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <textarea
              className="w-full rounded-md border px-3 py-2 text-sm min-h-[100px] resize-none"
              placeholder="Describe the product... e.g. 'Black slim fit suit jacket, wool blend, BOSS branding on inner label'"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
            <Button
              className="w-full"
              onClick={handleIdentify}
              disabled={identifyProduct.isPending || !description.trim()}
            >
              {identifyProduct.isPending ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <ScanSearch className="h-4 w-4 mr-2" />
              )}
              Identify Product
            </Button>
          </CardContent>
        </Card>
      </div>

      {identifyResult && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Package className="h-4 w-4" />
              Identification Results
            </CardTitle>
            <CardDescription>
              {identifyResult.matches.length} potential match
              {identifyResult.matches.length !== 1 ? "es" : ""} found
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {identifyResult.ai_analysis && (
              <div className="p-4 rounded-lg bg-muted/50 border">
                <p className="text-sm font-medium flex items-center gap-2 mb-2">
                  <Sparkles className="h-4 w-4 text-purple-500" />
                  AI Analysis
                </p>
                <p className="text-sm text-muted-foreground">
                  {identifyResult.ai_analysis}
                </p>
              </div>
            )}
            {identifyResult.matches.length > 0 && (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>SKU</TableHead>
                    <TableHead>Style</TableHead>
                    <TableHead>Category</TableHead>
                    <TableHead>Color</TableHead>
                    <TableHead>Material</TableHead>
                    <TableHead>Confidence</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {identifyResult.matches.map((match) => (
                    <TableRow key={match.product_id}>
                      <TableCell className="font-mono text-sm">
                        {match.sku}
                      </TableCell>
                      <TableCell className="text-sm font-medium">
                        {match.style_name}
                      </TableCell>
                      <TableCell className="text-sm">{match.category}</TableCell>
                      <TableCell className="text-sm">{match.color ?? "-"}</TableCell>
                      <TableCell className="text-sm">{match.material ?? "-"}</TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            match.confidence === "high"
                              ? "default"
                              : match.confidence === "medium"
                                ? "secondary"
                                : "outline"
                          }
                        >
                          {match.confidence}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

const statusConfig: Record<string, { icon: React.ReactNode; variant: "default" | "secondary" | "destructive" | "outline" }> = {
  completed: {
    icon: <CheckCircle2 className="h-3 w-3" />,
    variant: "default",
  },
  processing: {
    icon: <Loader2 className="h-3 w-3 animate-spin" />,
    variant: "secondary",
  },
  pending: {
    icon: <Clock className="h-3 w-3" />,
    variant: "outline",
  },
  failed: {
    icon: <XCircle className="h-3 w-3" />,
    variant: "destructive",
  },
};

function JobsList() {
  const { data: jobs } = useHb_listRecognitionJobsSuspense(selector());

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Recognition Jobs</CardTitle>
        <CardDescription>
          {jobs.length} jobs found
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Images</TableHead>
              <TableHead>Submitted By</TableHead>
              <TableHead>Created</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {jobs.map((job) => {
              const cfg = statusConfig[job.status] ?? statusConfig.pending;
              return (
                <TableRow key={job.id}>
                  <TableCell className="font-mono text-sm">#{job.id}</TableCell>
                  <TableCell>
                    <Badge variant="outline" className="capitalize">
                      {job.job_type}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant={cfg.variant} className="gap-1">
                      {cfg.icon}
                      {job.status}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    {job.completed_count}/{job.image_count}
                  </TableCell>
                  <TableCell className="text-sm">
                    {job.submitted_by ?? "-"}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {new Date(job.created_at).toLocaleDateString()}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

function JobsSkeleton() {
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
