import { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Loader2, Upload, X } from "lucide-react";
import { AdvisoryChip } from "./advisory-chip";

interface DiagnoseModalProps {
  /** Whether the modal is open. */
  open: boolean;
  /** Callback when modal should close. */
  onOpenChange: (open: boolean) => void;
  /** Optional callback when diagnosis is submitted. */
  onSubmit?: (file: File) => void;
}

/**
 * Snap-and-diagnose modal (UC3).
 *
 * Opens from the cockpit "Snap a photo" button. Allows upload of yard
 * imagery for CV-based plant/lawn/pest diagnosis.
 *
 * File input: image/jpeg, image/png, image/heic; max 10MB hint.
 *
 * POSTs to /api/projects/yard-pro/diagnose (multipart) once backend is ready.
 *
 * Response shapes:
 * - Success (>0.8 confidence): top label + confidence + recommendation
 * - Unsure (0.4-0.8 confidence): "Unsure — we can't confidently identify this"
 * - Not configured (backend 503): clean "Coach is in setup mode" state
 *
 * Every result renders an AdvisoryChip. When unsure, the primary copy is
 * "Unsure", and the "Get a second opinion (free dealer chat)" CTA has equal
 * visual weight to any diagnosis action.
 */
export function DiagnoseModal({
  open,
  onOpenChange,
  onSubmit,
}: DiagnoseModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!open) return null;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      // Validate size (10MB hint)
      if (selectedFile.size > 10 * 1024 * 1024) {
        alert("File size exceeds 10MB");
        return;
      }
      setFile(selectedFile);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setIsLoading(true);
    try {
      // TODO: Wire to backend API once B2 exports POST /api/projects/yard-pro/diagnose
      // For now, simulates the upload.
      await new Promise((resolve) => setTimeout(resolve, 1000));

      if (onSubmit) {
        onSubmit(file);
      }

      // Close modal after submission
      onOpenChange(false);
      setFile(null);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    onOpenChange(false);
    setFile(null);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <Card className="w-full max-w-md">
        <div className="flex items-center justify-between p-6 border-b">
          <div>
            <h2 className="text-lg font-semibold">Snap a Photo</h2>
            <p className="text-sm text-muted-foreground">Upload a yard photo for AI diagnosis</p>
          </div>
          <button
            onClick={handleClose}
            className="text-muted-foreground hover:text-foreground"
          >
            <X size={20} />
          </button>
        </div>

        <CardContent className="pt-6 space-y-4">
          {/* File Input */}
          <div
            className="border-2 border-dashed rounded-lg p-6 text-center cursor-pointer hover:bg-muted transition-colors"
            onClick={() => fileInputRef.current?.click()}
          >
            <Upload className="mx-auto mb-2 text-muted-foreground" size={24} />
            <p className="text-sm font-medium">
              {file ? file.name : "Click to upload or drag and drop"}
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              PNG, JPG, HEIC • Max 10MB
            </p>
          </div>

          <Input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/png,image/heic"
            onChange={handleFileChange}
            className="hidden"
          />

          {/* Advisory Chip */}
          <AdvisoryChip variant="block" />

          {/* Actions */}
          <div className="flex gap-2 justify-end pt-2">
            <Button
              variant="outline"
              onClick={handleClose}
            >
              Cancel
            </Button>
            <Button
              onClick={handleUpload}
              disabled={!file || isLoading}
              className="gap-1"
            >
              {isLoading ? (
                <Loader2 size={16} className="animate-spin" />
              ) : null}
              {isLoading ? "Diagnosing..." : "Upload & Diagnose"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
