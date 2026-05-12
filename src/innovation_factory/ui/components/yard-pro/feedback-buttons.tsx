import { useState } from "react";
import { ThumbsUp, ThumbsDown } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * Plan §8 advisory feedback loop affordance. Two one-tap thumbs next to
 * every coach assistant turn. POSTs to /api/projects/yard-pro/coach/feedback;
 * the backend upserts on (yard_id, response_id) so flipping thumbs_up →
 * thumbs_down stays a single row.
 *
 * Notes textarea is intentionally NOT here — keeps the tap surface small
 * for P1. A "tell us more" expansion is P2.
 */
interface FeedbackButtonsProps {
  /** Persisted YpCoachMessage.id stringified — matches the backend body. */
  responseId: string;
  /** Optional callback fired after a successful POST. */
  onSubmitted?: (signal: "thumbs_up" | "thumbs_down") => void;
}

type Signal = "thumbs_up" | "thumbs_down" | null;

export function FeedbackButtons({ responseId, onSubmitted }: FeedbackButtonsProps) {
  const [active, setActive] = useState<Signal>(null);
  const [pending, setPending] = useState<Signal>(null);

  const submit = async (signal: "thumbs_up" | "thumbs_down") => {
    setPending(signal);
    // Optimistic update — flip the UI immediately, revert on error.
    const previous = active;
    setActive(signal);
    try {
      const res = await fetch("/api/projects/yard-pro/coach/feedback", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ response_id: responseId, signal }),
      });
      if (!res.ok) {
        throw new Error(`feedback failed: ${res.status}`);
      }
      onSubmitted?.(signal);
    } catch {
      setActive(previous);
    } finally {
      setPending(null);
    }
  };

  return (
    <div className="flex items-center gap-1" role="group" aria-label="Feedback">
      <button
        type="button"
        aria-label="Helpful"
        disabled={pending !== null}
        onClick={() => submit("thumbs_up")}
        className={cn(
          "rounded-md p-1.5 transition-colors",
          active === "thumbs_up"
            ? "bg-primary/15 text-primary"
            : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
          active && active !== "thumbs_up" && "opacity-40",
        )}
      >
        <ThumbsUp size={14} aria-hidden="true" />
      </button>
      <button
        type="button"
        aria-label="Not helpful"
        disabled={pending !== null}
        onClick={() => submit("thumbs_down")}
        className={cn(
          "rounded-md p-1.5 transition-colors",
          active === "thumbs_down"
            ? "bg-destructive/15 text-destructive"
            : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
          active && active !== "thumbs_down" && "opacity-40",
        )}
      >
        <ThumbsDown size={14} aria-hidden="true" />
      </button>
    </div>
  );
}
