import { createFileRoute } from "@tanstack/react-router";
import { Suspense } from "react";
import { ErrorBoundary } from "react-error-boundary";
import { QueryErrorResetBoundary } from "@tanstack/react-query";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  useYp_getDatabricksResourcesSuspense,
  useYp_listDealerCustomersAnonymizedSuspense,
} from "@/lib/api";
import { selector } from "@/lib/selector";
import {
  ExternalLink,
  Sparkles,
  Users,
  CheckCircle2,
  Bot,
  Store,
  Info,
  MessageCircleQuestion,
} from "lucide-react";
import { useState } from "react";

// Curated questions mirror the SAMPLE_QUESTIONS list in
// scripts/yard_pro/deploy_genie_space.py — kept in sync by convention.
// The first one is the plan §2 success-criterion #6 headline question.
const GENIE_SAMPLE_QUESTIONS = [
  "Which customers have a robotic mower 4+ years old that hasn't been serviced in the last 90 days?",
  "How many anonymized customers do I have in each region bucket?",
  "What is the distribution of yard sizes among my consented customers?",
  "Which tool inventory hashes appear most often in my customer base?",
  "How many of my customers have a robotic mower at all?",
  "Show me customers whose last service event was more than 6 months ago.",
];

/**
 * Dealer panel index page (UC6, P5).
 *
 * Layout:
 *   - Header: "Dealer panel — Klaus's view" + a privacy note ("anonymized")
 *   - Three count cards: active relationships, granted-consent households,
 *     robotic mowers > 4 years
 *   - Genie embed (or "Genie not configured" card per lessons §18) —
 *     `useYp_getDatabricksResourcesSuspense().dealer_genie_configured`
 *     drives the render.
 *   - Anonymized-customer table fed by `useYp_listDealerCustomersAnonymized`.
 *     RLS scopes rows to Klaus's dealer_id via `X-Forwarded-Dealer` (in
 *     production the Databricks Apps proxy sets the header; in local dev
 *     the backend's `_resolve_dealer_id` falls back to
 *     `dealer_stuttgart_nord` — the seeded dealer).
 *
 * No yard_id renders anywhere on this page — only yard_id_hash. This is
 * the surface-level enforcement of the plan §2 non-negotiable: "Klaus
 * never sees identifiable Martin data".
 */
export const Route = createFileRoute("/projects/yard-pro/dealer/")({
  component: () => <DealerPanelPage />,
});

function DealerPanelPage() {
  return (
    <div className="p-6 space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <Store size={28} className="text-primary" />
            Dealer panel
          </h1>
          <p className="text-muted-foreground mt-1 max-w-2xl">
            OEM-side view of your customer fleet. All rows are anonymized
            via HMAC at ingest — yard owners stay private unless they opt
            in for a specific service event.
          </p>
        </div>
        <Badge variant="outline" className="gap-1">
          <Info size={12} />
          yard_id_hash only
        </Badge>
      </div>

      <QueryErrorResetBoundary>
        {({ reset }) => (
          <ErrorBoundary
            onReset={reset}
            fallbackRender={({ resetErrorBoundary }) => (
              <Card>
                <CardContent className="p-6 text-destructive">
                  <p>Failed to load dealer panel.</p>
                  <Button
                    size="sm"
                    onClick={resetErrorBoundary}
                    className="mt-2"
                  >
                    Retry
                  </Button>
                </CardContent>
              </Card>
            )}
          >
            <Suspense fallback={<DealerSkeleton />}>
              <DealerPanelContent />
            </Suspense>
          </ErrorBoundary>
        )}
      </QueryErrorResetBoundary>
    </div>
  );
}

function DealerSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <Card key={i}>
            <CardContent className="p-4 space-y-2">
              <Skeleton className="h-3 w-24" />
              <Skeleton className="h-8 w-16" />
            </CardContent>
          </Card>
        ))}
      </div>
      <Skeleton className="h-[400px] w-full" />
    </div>
  );
}

function DealerPanelContent() {
  const { data: resources } = useYp_getDatabricksResourcesSuspense(selector());
  const { data: rows } = useYp_listDealerCustomersAnonymizedSuspense(selector());

  const total = rows.length;
  const granted = rows.filter((r) => r.consent_state === "granted").length;
  const agedMowers = rows.filter(
    (r) => (r.robotic_mower_age_years ?? 0) >= 4,
  ).length;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <CountCard
          icon={<Users size={16} />}
          label="Active relationships"
          value={total}
          hint="Anonymized customers in your scope"
        />
        <CountCard
          icon={<CheckCircle2 size={16} />}
          label="Granted-consent households"
          value={granted}
          hint="Households whose latest transition is granted"
        />
        <CountCard
          icon={<Bot size={16} />}
          label="Robotic mowers 4+ years old"
          value={agedMowers}
          hint={`The plan §2 #6 sample question target`}
        />
      </div>

      <GenieEmbedCard
        configured={resources.dealer_genie_configured ?? false}
        workspaceUrl={resources.workspace_url}
        spaceId={resources.dealer_genie_space_id}
      />

      <AnonymizedCustomersTable rows={rows} />
    </div>
  );
}

interface CountCardProps {
  icon: React.ReactNode;
  label: string;
  value: number;
  hint: string;
}

function CountCard({ icon, label, value, hint }: CountCardProps) {
  return (
    <Card>
      <CardContent className="p-4 space-y-1">
        <div className="text-xs text-muted-foreground flex items-center gap-1">
          {icon}
          {label}
        </div>
        <div className="text-3xl font-bold tracking-tight">{value}</div>
        <div className="text-xs text-muted-foreground">{hint}</div>
      </CardContent>
    </Card>
  );
}

interface GenieEmbedCardProps {
  configured: boolean;
  workspaceUrl: string;
  spaceId: string;
}

function GenieEmbedCard({
  configured,
  workspaceUrl,
  spaceId,
}: GenieEmbedCardProps) {
  const [showInline, setShowInline] = useState(false);

  if (!configured || !workspaceUrl || !spaceId) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles size={18} />
            Genie space
          </CardTitle>
          <CardDescription>
            Ask natural-language questions over your anonymized customer view.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-lg border border-dashed p-6 text-sm text-muted-foreground">
            <p className="font-medium text-foreground">Genie not configured.</p>
            <p className="mt-1">
              Run <code className="text-xs bg-muted px-1 py-0.5 rounded">
                uv run python -m scripts.yard_pro.deploy_genie_space
              </code> and set <code className="text-xs bg-muted px-1 py-0.5 rounded">
                YARD_PRO_DEALER_GENIE_SPACE_ID
              </code> in <code className="text-xs">app.yml</code>.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Open the Genie space directly in the workspace. We don't try to
  // prefill the question via query string — Databricks doesn't publicly
  // document a stable `?q=` parameter for Genie, so the user clicks
  // through and the curated suggestions are already pinned inside the
  // space by deploy_genie_space.py.
  const genieUrl = `https://${workspaceUrl}/genie/rooms/${spaceId}`;
  const embedUrl = `${genieUrl}?embed=true`;

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between space-y-0 gap-4">
        <div className="flex-1">
          <CardTitle className="flex items-center gap-2">
            <Sparkles size={18} />
            Talk to your data — Genie
          </CardTitle>
          <CardDescription className="mt-1">
            Ask natural-language questions over the anonymized customer view.
            Genie translates each question to SQL against{" "}
            <code className="text-xs bg-muted px-1 py-0.5 rounded">
              yard_pro_gold.dealer_customer_summary
            </code>{" "}
            and inherits your UC row-level filter.
          </CardDescription>
        </div>
        <a href={genieUrl} target="_blank" rel="noopener noreferrer">
          <Button size="sm" className="gap-1.5 whitespace-nowrap">
            Open in Databricks
            <ExternalLink className="h-3 w-3" />
          </Button>
        </a>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-xs uppercase tracking-wider text-muted-foreground">
            <MessageCircleQuestion size={12} />
            Try asking
          </div>
          <div className="grid gap-2 md:grid-cols-2">
            {GENIE_SAMPLE_QUESTIONS.map((q, idx) => (
              <a
                key={idx}
                href={genieUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="group block"
              >
                <div className="p-3 rounded-lg border bg-muted/40 hover:bg-muted hover:border-primary/40 transition-colors text-sm">
                  <div className="flex items-start justify-between gap-2">
                    <span className="text-foreground">{q}</span>
                    <ExternalLink className="h-3 w-3 mt-0.5 shrink-0 text-muted-foreground group-hover:text-primary" />
                  </div>
                </div>
              </a>
            ))}
          </div>
        </div>

        <div className="border-t pt-4">
          <button
            type="button"
            onClick={() => setShowInline((v) => !v)}
            className="text-xs text-muted-foreground hover:text-foreground underline underline-offset-2"
          >
            {showInline ? "Hide inline Genie" : "Show inline Genie (beta)"}
          </button>
          {showInline && (
            <>
              <div
                className="rounded-lg border overflow-hidden bg-white mt-3"
                style={{ height: "60vh" }}
              >
                <iframe
                  src={embedUrl}
                  className="w-full h-full border-0"
                  title="yard-pro dealer Genie space"
                  allow="clipboard-write; fullscreen"
                  sandbox="allow-same-origin allow-scripts allow-forms allow-popups allow-popups-to-escape-sandbox"
                />
              </div>
              <p className="text-xs text-muted-foreground mt-2">
                Inline embed requires the workspace admin to allowlist this
                Databricks Apps host under{" "}
                <span className="font-medium">
                  Settings → Security → External access → Embed dashboards
                </span>
                . If you see an auth loop or blank panel, click{" "}
                <span className="font-medium">Open in Databricks</span> above.
              </p>
            </>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

interface AnonymizedRow {
  yard_id_hash: string;
  dealer_id: string;
  region_bucket: string;
  yard_size_bucket: string;
  tool_inventory_hash: string;
  robotic_mower_age_years: number;
  last_service_event_age_days: number;
  consent_state: string;
}

function AnonymizedCustomersTable({ rows }: { rows: AnonymizedRow[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Anonymized customers</CardTitle>
        <CardDescription>
          One row per household whose latest consent transition is granted.
          yard_id_hash is the only join key.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {rows.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No anonymized customers yet. Households opt in via the cockpit's
            "Share with my dealer" toggle.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-xs uppercase text-muted-foreground border-b">
                <tr>
                  <th className="text-left py-2 pr-4">yard_id_hash</th>
                  <th className="text-left py-2 pr-4">Region</th>
                  <th className="text-left py-2 pr-4">Size bucket</th>
                  <th className="text-left py-2 pr-4">Tool inventory hash</th>
                  <th className="text-right py-2 pr-4">Mower age (yr)</th>
                  <th className="text-right py-2 pr-4">Last service (d)</th>
                  <th className="text-left py-2 pr-4">Consent</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.yard_id_hash} className="border-b">
                    <td className="py-2 pr-4 font-mono text-xs">
                      {r.yard_id_hash}
                    </td>
                    <td className="py-2 pr-4 font-mono text-xs">
                      {r.region_bucket}
                    </td>
                    <td className="py-2 pr-4">{r.yard_size_bucket}</td>
                    <td className="py-2 pr-4 font-mono text-xs">
                      {r.tool_inventory_hash}
                    </td>
                    <td className="py-2 pr-4 text-right">
                      {r.robotic_mower_age_years}
                    </td>
                    <td className="py-2 pr-4 text-right">
                      {r.last_service_event_age_days}
                    </td>
                    <td className="py-2 pr-4">
                      <Badge variant="secondary">{r.consent_state}</Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
