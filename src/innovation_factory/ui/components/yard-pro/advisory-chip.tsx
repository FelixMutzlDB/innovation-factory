import { AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface AdvisoryChipProps {
  /** Render variant: inline (pill) or block (full width). */
  variant?: "inline" | "block";
  /** Optional CSS class name for additional styling. */
  className?: string;
}

/**
 * EU AI Act Art. 50 transparency chip.
 *
 * Renders a deterministic "AI-generated, advisory only" message
 * to indicate that the displayed content is AI-generated and should
 * not be treated as authoritative professional advice.
 *
 * Appears on every assistant turn in the coach chat and on every
 * diagnose result.
 */
export function AdvisoryChip({
  variant = "inline",
  className,
}: AdvisoryChipProps) {
  if (variant === "inline") {
    return (
      <span
        className={cn(
          "inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs bg-amber-50 text-amber-700 border border-amber-200",
          className
        )}
      >
        <AlertCircle size={12} />
        <span>AI-generated, advisory only</span>
      </span>
    );
  }

  return (
    <div
      className={cn(
        "flex items-start gap-2 p-3 rounded-lg bg-amber-50 border border-amber-200 text-sm text-amber-700",
        className
      )}
    >
      <AlertCircle size={16} className="mt-0.5 flex-shrink-0" />
      <span>This is an AI-generated response and should be treated as advisory only, not authoritative professional advice.</span>
    </div>
  );
}
