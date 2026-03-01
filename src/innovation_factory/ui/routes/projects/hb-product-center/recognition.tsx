import { createFileRoute } from "@tanstack/react-router";
import { useState, useRef } from "react";
import {
  useHb_findSimilarImages,
  type SimilarImageResult,
} from "@/lib/api";
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
  ScanSearch,
  Upload,
  Camera,
  XCircle,
  Loader2,
  ImageIcon,
} from "lucide-react";

export const Route = createFileRoute(
  "/projects/hb-product-center/recognition",
)({
  component: () => <RecognitionPage />,
});

function RecognitionPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [results, setResults] = useState<SimilarImageResult[] | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const findSimilar = useHb_findSimilarImages();

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    setPreview(URL.createObjectURL(file));
    setResults(null);
  };

  const clearFile = () => {
    setSelectedFile(null);
    if (preview) URL.revokeObjectURL(preview);
    setPreview(null);
    setResults(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleSearch = async () => {
    if (!selectedFile) return;
    const buffer = await selectedFile.arrayBuffer();
    const base64 = btoa(
      new Uint8Array(buffer).reduce((s, b) => s + String.fromCharCode(b), ""),
    );
    findSimilar.mutate(
      { image_base64: base64, top_k: 5 },
      { onSuccess: (res) => setResults(res.data.results) },
    );
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file && file.type.startsWith("image/")) handleFileSelect(file);
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
          <ScanSearch className="h-6 w-6" />
          Visual Product Recognition
        </h1>
        <p className="text-muted-foreground mt-1">
          Upload a product image to find visually similar items using AI-powered
          image embeddings and vector search.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Upload className="h-4 w-4" />
            Upload Image
          </CardTitle>
          <CardDescription>
            Drag and drop or click to upload a product image
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col sm:flex-row gap-4">
            <div
              className={`flex-1 border-2 border-dashed rounded-lg p-6 text-center transition-colors cursor-pointer ${
                isDragging
                  ? "border-primary bg-primary/5"
                  : selectedFile
                    ? "border-primary/50 bg-muted/30"
                    : "hover:bg-muted/50"
              }`}
              onClick={() => !selectedFile && fileInputRef.current?.click()}
              onDragOver={(e) => {
                e.preventDefault();
                setIsDragging(true);
              }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={handleDrop}
            >
              {preview && selectedFile ? (
                <div className="space-y-3">
                  <img
                    src={preview}
                    alt="Query"
                    className="mx-auto max-h-48 rounded-md object-contain"
                  />
                  <p className="text-sm font-medium truncate">
                    {selectedFile.name}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {(selectedFile.size / 1024).toFixed(0)} KB
                  </p>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      clearFile();
                    }}
                  >
                    <XCircle className="h-3 w-3 mr-1" />
                    Remove
                  </Button>
                </div>
              ) : (
                <>
                  <Camera className="h-10 w-10 mx-auto text-muted-foreground mb-3" />
                  <p className="text-sm text-muted-foreground mb-1">
                    Drop product image here or click to browse
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Supports JPG, PNG, WebP up to 10MB
                  </p>
                </>
              )}
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) handleFileSelect(file);
                }}
              />
            </div>

            <div className="flex sm:flex-col justify-center">
              <Button
                size="lg"
                onClick={handleSearch}
                disabled={findSimilar.isPending || !selectedFile}
                className="min-w-[160px]"
              >
                {findSimilar.isPending ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <ScanSearch className="h-4 w-4 mr-2" />
                )}
                Find Similar
              </Button>
            </div>
          </div>

          {findSimilar.isError && (
            <p className="text-sm text-destructive mt-3">
              Search failed. Please try again.
            </p>
          )}
        </CardContent>
      </Card>

      {findSimilar.isPending && <ResultsSkeleton />}

      {results && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <ImageIcon className="h-4 w-4" />
              Similar Images
            </CardTitle>
            <CardDescription>
              {results.length} result{results.length !== 1 ? "s" : ""} found
            </CardDescription>
          </CardHeader>
          <CardContent>
            {results.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-8">
                No similar images found.
              </p>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
                {results.map((result, idx) => (
                  <ResultCard key={result.id} result={result} rank={idx + 1} />
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function ResultCard({
  result,
  rank,
}: {
  result: SimilarImageResult;
  rank: number;
}) {
  const scorePercent = Math.round(result.score * 100);
  const variant =
    scorePercent >= 90
      ? "default"
      : scorePercent >= 70
        ? "secondary"
        : "outline";

  return (
    <div className="rounded-lg border bg-card overflow-hidden">
      <div className="aspect-square bg-muted relative">
        <img
          src={result.image_url}
          alt={result.file_name}
          className="w-full h-full object-contain"
          loading="lazy"
        />
        <Badge className="absolute top-2 left-2 text-xs" variant="secondary">
          #{rank}
        </Badge>
        <Badge className={`absolute top-2 right-2 text-xs`} variant={variant}>
          {scorePercent}%
        </Badge>
      </div>
      <div className="p-3 space-y-1">
        <p
          className="text-sm font-medium truncate"
          title={result.file_name}
        >
          {result.file_name}
        </p>
        <div className="flex items-center justify-between">
          <Badge variant="outline" className="text-xs capitalize">
            {result.category}
          </Badge>
          <span
            className="text-xs text-muted-foreground font-mono"
            title={result.id}
          >
            {result.id.slice(0, 8)}...
          </span>
        </div>
      </div>
    </div>
  );
}

function ResultsSkeleton() {
  return (
    <Card>
      <CardHeader>
        <Skeleton className="h-6 w-36" />
        <Skeleton className="h-4 w-24 mt-1" />
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="rounded-lg border overflow-hidden">
              <Skeleton className="aspect-square w-full" />
              <div className="p-3 space-y-2">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-4 w-1/2" />
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
