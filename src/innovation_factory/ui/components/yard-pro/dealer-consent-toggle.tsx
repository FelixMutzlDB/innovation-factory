import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import {
  useYp_listDealerRelationships,
  useYp_createDealerRelationship,
  useYp_revokeDealerRelationship,
  yp_listDealerRelationshipsKey,
} from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Loader2, Store, Info } from "lucide-react";

/**
 * Consumer-side dealer-consent toggle (UC6, P5).
 *
 * Renders on the cockpit (Martin's view), NOT the dealer view. This is
 * the only path to grant consent for the dealer relationship — plan §2
 * non-negotiable: "Dealer data-sharing is **opt-in per household**".
 *
 * Three-state clarity (plan §2 + §8 consent state machine):
 *   - none / revoked → "not connected" (CTA: "Share with my dealer")
 *   - pending → "pending"             (CTA: "Cancel")
 *   - granted → "sharing"             (CTA: "Stop sharing")
 *
 * The transition `pending → granted` is dealer-driven (the dealer
 * confirms the request in their workspace) and is NOT exposed in this
 * component — Martin only opens or revokes; the consent state machine
 * is the validator.
 *
 * No "do it for me" affordance: every state change is an explicit click
 * by the household. The component never auto-transitions.
 */
interface DealerConsentToggleProps {
  /** The dealer Martin is sharing with. Defaults to the seeded
   *  `dealer_stuttgart_nord` — Klaus's dealer code. */
  dealerId?: string;
}

export function DealerConsentToggle({
  dealerId = "dealer_stuttgart_nord",
}: DealerConsentToggleProps) {
  const queryClient = useQueryClient();
  const { data, isLoading } = useYp_listDealerRelationships();
  const createMutation = useYp_createDealerRelationship();
  const revokeMutation = useYp_revokeDealerRelationship();
  const [error, setError] = useState<string | null>(null);

  const relationships = data?.data ?? [];
  const rel = relationships.find((r) => r.dealer_id === dealerId);
  const state = rel?.consent_state ?? "none";

  const invalidate = () =>
    queryClient.invalidateQueries({
      queryKey: yp_listDealerRelationshipsKey(),
    });

  const handleShare = async () => {
    setError(null);
    try {
      await createMutation.mutateAsync({ dealer_id: dealerId });
      invalidate();
    } catch (e: any) {
      setError(e?.message ?? "Failed to open dealer relationship");
    }
  };

  const handleStop = async () => {
    if (!rel) return;
    setError(null);
    try {
      await revokeMutation.mutateAsync({
        params: { relationship_id: rel.id },
      });
      invalidate();
    } catch (e: any) {
      setError(e?.message ?? "Failed to revoke dealer relationship");
    }
  };

  const busy =
    createMutation.isPending || revokeMutation.isPending || isLoading;

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <Store size={18} />
          Share with my dealer
        </CardTitle>
        <CardDescription>
          Klaus (your dealer) can see <em>anonymized</em> info about your yard
          — never your name, location, or photos.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-center justify-between">
          <StateLabel state={state} />
          <ToggleAction
            state={state}
            busy={busy}
            onShare={handleShare}
            onStop={handleStop}
          />
        </div>
        <p className="text-xs text-muted-foreground flex items-start gap-1">
          <Info size={12} className="mt-0.5 flex-shrink-0" />
          You can revoke anytime. Anonymized rows already in your dealer's
          view will disappear within minutes.
        </p>
        {error && (
          <p className="text-xs text-destructive" role="alert">
            {error}
          </p>
        )}
      </CardContent>
    </Card>
  );
}

function StateLabel({ state }: { state: string }) {
  if (state === "granted") {
    return (
      <Badge className="bg-green-100 text-green-800 border-green-300">
        Sharing
      </Badge>
    );
  }
  if (state === "pending") {
    return (
      <Badge variant="secondary">Pending dealer confirmation</Badge>
    );
  }
  return <Badge variant="outline">Not connected</Badge>;
}

interface ToggleActionProps {
  state: string;
  busy: boolean;
  onShare: () => void;
  onStop: () => void;
}

function ToggleAction({ state, busy, onShare, onStop }: ToggleActionProps) {
  if (state === "granted") {
    return (
      <Button
        variant="outline"
        size="sm"
        onClick={onStop}
        disabled={busy}
      >
        {busy ? <Loader2 size={14} className="animate-spin mr-1" /> : null}
        Stop sharing
      </Button>
    );
  }
  if (state === "pending") {
    return (
      <Button
        variant="outline"
        size="sm"
        onClick={onStop}
        disabled={busy}
      >
        {busy ? <Loader2 size={14} className="animate-spin mr-1" /> : null}
        Cancel
      </Button>
    );
  }
  return (
    <Button size="sm" onClick={onShare} disabled={busy}>
      {busy ? <Loader2 size={14} className="animate-spin mr-1" /> : null}
      Share with my dealer
    </Button>
  );
}
