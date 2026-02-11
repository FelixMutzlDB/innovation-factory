import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { Suspense, useState } from "react";
import { QueryErrorResetBoundary, useQueryClient } from "@tanstack/react-query";
import { ErrorBoundary } from "react-error-boundary";
import { useBsh_listMyDevicesSuspense, bsh_listTicketsKey } from "@/lib/api";
import selector from "@/lib/selector";
import { useDropzone } from "react-dropzone";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  AlertCircle,
  Upload,
  X,
  Image as ImageIcon,
  Video,
  Mic,
  FileText,
} from "lucide-react";
import { toast } from "sonner";

export const Route = createFileRoute("/projects/bsh-home-connect/support")({
  component: () => <Support />,
});

function SupportContent() {
  const { data: devices } = useBsh_listMyDevicesSuspense(selector());
  // selector() already extracts .data, so devices is the array directly
  const deviceList = Array.isArray(devices) ? devices : [];
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [selectedDevice, setSelectedDevice] = useState<number | null>(null);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState<"low" | "medium" | "high">("medium");
  const [files, setFiles] = useState<File[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      "image/*": [".png", ".jpg", ".jpeg", ".gif"],
      "video/*": [".mp4", ".mov", ".avi"],
      "audio/*": [".mp3", ".wav", ".m4a"],
    },
    maxSize: 50 * 1024 * 1024, // 50MB
    onDrop: (acceptedFiles) => {
      setFiles((prev) => [...prev, ...acceptedFiles]);
      toast.success(`${acceptedFiles.length} file(s) added`);
    },
    onDropRejected: (rejections) => {
      toast.error(`Some files were rejected: ${rejections[0]?.errors[0]?.message}`);
    },
  });

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const getFileIcon = (file: File) => {
    if (file.type.startsWith("image/")) return <ImageIcon className="h-4 w-4" />;
    if (file.type.startsWith("video/")) return <Video className="h-4 w-4" />;
    if (file.type.startsWith("audio/")) return <Mic className="h-4 w-4" />;
    return <FileText className="h-4 w-4" />;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!selectedDevice) {
      toast.error("Please select a device");
      return;
    }

    if (!title.trim()) {
      toast.error("Please enter a title");
      return;
    }

    if (!description.trim()) {
      toast.error("Please describe the issue");
      return;
    }

    setIsSubmitting(true);

    try {
      // Create ticket
      const response = await fetch("/api/tickets", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          customer_device_id: selectedDevice,
          title: title.trim(),
          description: description.trim(),
          priority,
        }),
      });

      if (!response.ok) throw new Error("Failed to create ticket");

      const ticket = await response.json();

      // Upload media files
      if (files.length > 0) {
        for (const file of files) {
          const formData = new FormData();
          formData.append("file", file);
          formData.append(
            "media_type",
            file.type.startsWith("image/")
              ? "image"
              : file.type.startsWith("video/")
                ? "video"
                : "audio"
          );

          await fetch(`/api/tickets/${ticket.id}/media`, {
            method: "POST",
            body: formData,
          });
        }
      }

      toast.success("Support ticket created successfully!");

      // Invalidate tickets query to refetch the list
      await queryClient.invalidateQueries({ queryKey: bsh_listTicketsKey({ role: "customer" }) });

      navigate({ to: "/projects/bsh-home-connect/tickets/$ticketId", params: { ticketId: ticket.id.toString() } });
    } catch (error) {
      console.error("Failed to create ticket:", error);
      toast.error("Failed to create support ticket. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (deviceList.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>No Devices Registered</CardTitle>
          <CardDescription>
            You need to register a device before requesting support.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button onClick={() => navigate({ to: "/projects/bsh-home-connect/devices/register" })}>
            Register a Device
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Get Support</h1>
        <p className="text-muted-foreground mt-1">
          Describe your issue and our AI assistant will help troubleshoot
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Device Selection */}
        <Card>
          <CardHeader>
            <CardTitle>Select Device</CardTitle>
            <CardDescription>
              Which appliance needs support?
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {deviceList.map((device) => (
              <div
                key={device.id}
                onClick={() => setSelectedDevice(device.id)}
                className={`p-4 rounded-lg border-2 cursor-pointer transition-colors ${
                  selectedDevice === device.id
                    ? "border-primary bg-primary/5"
                    : "border-border hover:border-primary/50"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold">
                        {device.device?.brand} {device.device?.name}
                      </h3>
                      <Badge variant="outline" className="text-xs">
                        {device.device?.category.replace("_", " ")}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      Model: {device.device?.model_number}
                    </p>
                  </div>
                  {selectedDevice === device.id && (
                    <div className="h-6 w-6 rounded-full bg-primary flex items-center justify-center">
                      <div className="h-3 w-3 rounded-full bg-background" />
                    </div>
                  )}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Issue Details */}
        <Card>
          <CardHeader>
            <CardTitle>Describe the Issue</CardTitle>
            <CardDescription>
              Provide as much detail as possible for better assistance
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">
                Title <span className="text-destructive">*</span>
              </label>
              <Input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g., Dishwasher not draining properly"
                maxLength={100}
                required
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">
                Description <span className="text-destructive">*</span>
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe what's happening, any error codes, when it started, etc."
                className="w-full min-h-32 px-3 py-2 rounded-md border border-input bg-background"
                required
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Priority</label>
              <div className="flex gap-2">
                {(["low", "medium", "high"] as const).map((p) => (
                  <Button
                    key={p}
                    type="button"
                    variant={priority === p ? "default" : "outline"}
                    size="sm"
                    onClick={() => setPriority(p)}
                  >
                    {p.charAt(0).toUpperCase() + p.slice(1)}
                  </Button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Media Upload */}
        <Card>
          <CardHeader>
            <CardTitle>Add Photos, Videos, or Audio</CardTitle>
            <CardDescription>
              Visual evidence helps diagnose issues faster (optional)
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                isDragActive
                  ? "border-primary bg-primary/5"
                  : "border-border hover:border-primary/50"
              }`}
            >
              <input {...getInputProps()} />
              <Upload className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
              {isDragActive ? (
                <p className="text-sm text-primary">Drop files here...</p>
              ) : (
                <>
                  <p className="text-sm mb-2">
                    Drag and drop files here, or click to browse
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Images, videos, and audio files (max 50MB each)
                  </p>
                </>
              )}
            </div>

            {files.length > 0 && (
              <div className="space-y-2">
                <label className="text-sm font-medium">Uploaded Files ({files.length})</label>
                <div className="space-y-2">
                  {files.map((file, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-3 rounded-lg border"
                    >
                      <div className="flex items-center gap-3">
                        {getFileIcon(file)}
                        <div className="text-sm">
                          <p className="font-medium">{file.name}</p>
                          <p className="text-muted-foreground text-xs">
                            {(file.size / 1024 / 1024).toFixed(2)} MB
                          </p>
                        </div>
                      </div>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => removeFile(index)}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Submit */}
        <div className="flex items-center justify-between">
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate({ to: "/projects/bsh-home-connect/dashboard" })}
            disabled={isSubmitting}
          >
            Cancel
          </Button>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Creating Ticket..." : "Create Support Ticket"}
          </Button>
        </div>
      </form>
    </div>
  );
}

function SupportSkeleton() {
  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <Skeleton className="h-8 w-64" />
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-48" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-32 w-full" />
        </CardContent>
      </Card>
    </div>
  );
}

function Support() {
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
                  Failed to Load Support Form
                </CardTitle>
                <CardDescription>
                  There was an error loading the support form.
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
          <Suspense fallback={<SupportSkeleton />}>
            <SupportContent />
          </Suspense>
        </ErrorBoundary>
      )}
    </QueryErrorResetBoundary>
  );
}
