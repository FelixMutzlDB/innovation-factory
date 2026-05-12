import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Loader2, Check } from "lucide-react";

interface MarkAsDoneProps {
  /**
   * Action ID from yp_action_log for a coach-recommendation or telemetry-nudge.
   * If null, creates a fresh user-action row.
   */
  actionId: number | null;
  /** Display label for the action. */
  label: string;
  /** Optional callback when confirmation succeeds. */
  onConfirmed?: () => void;
}

/**
 * GDPR Art. 22 affordance — the ONLY UI path that writes confirmed actions.
 *
 * When source != 'user' (i.e., coach recommendation or telemetry nudge),
 * the backend enforces that human_confirmed_at is set before persisting.
 * This component surfaces the affordance to the user.
 *
 * Two execution paths:
 * 1. If actionId is provided: PATCH /api/projects/yard-pro/actions/{id}/confirm
 * 2. If actionId is null: POST /api/projects/yard-pro/actions with source='user'
 */
export function MarkAsDone({
  actionId,
  label,
  onConfirmed,
}: MarkAsDoneProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [isConfirmed, setIsConfirmed] = useState(false);

  const handleConfirm = async () => {
    setIsLoading(true);
    try {
      const opts: RequestInit = {
        credentials: "include",
        headers: { "Content-Type": "application/json" },
      };
      let res: Response;
      if (actionId !== null) {
        res = await fetch(
          `/api/projects/yard-pro/actions/${actionId}/confirm`,
          { ...opts, method: "PATCH" },
        );
      } else {
        res = await fetch(`/api/projects/yard-pro/actions`, {
          ...opts,
          method: "POST",
          body: JSON.stringify({
            action_type: "other",
            notes: label,
            source: "user",
            human_confirmed_at: new Date().toISOString(),
          }),
        });
      }
      if (!res.ok) {
        throw new Error(`mark-as-done failed: ${res.status}`);
      }
      setIsConfirmed(true);
      if (onConfirmed) {
        onConfirmed();
      }
    } finally {
      setIsLoading(false);
    }
  };

  if (isConfirmed) {
    return (
      <Button disabled size="sm" variant="outline" className="gap-1">
        <Check size={14} />
        Done
      </Button>
    );
  }

  return (
    <Button
      onClick={handleConfirm}
      disabled={isLoading}
      size="sm"
      variant="outline"
      className="gap-1"
    >
      {isLoading ? (
        <Loader2 size={14} className="animate-spin" />
      ) : null}
      Mark as done
    </Button>
  );
}
