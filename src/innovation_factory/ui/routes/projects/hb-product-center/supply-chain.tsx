import { createFileRoute } from "@tanstack/react-router";
import { Suspense, useState } from "react";
import { ErrorBoundary } from "react-error-boundary";
import { QueryErrorResetBoundary } from "@tanstack/react-query";
import {
  useHb_listSupplyChainEventsSuspense,
  useHb_listSustainabilityMetricsSuspense,
  useHb_listProductsSuspense,
  useHb_getProductJourneySuspense,
  useHb_getDatabricksResourcesSuspense,
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Truck,
  Leaf,
  MapPin,
  Factory,
  Package,
  ArrowRight,
  Droplets,
  Wind,
  Recycle,
  CheckCircle2,
  Clock,
  XCircle,
  BarChart3,
  Sparkles,
  ExternalLink,
} from "lucide-react";

export const Route = createFileRoute(
  "/projects/hb-product-center/supply-chain",
)({
  component: () => <SupplyChainPage />,
});

function SupplyChainPage() {
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
          <Truck className="h-6 w-6" />
          Supply Chain Intelligence Dashboard
        </h1>
        <p className="text-muted-foreground mt-1">
          Track products from manufacturing to retail and monitor sustainability
          metrics.
        </p>
      </div>

      <QueryErrorResetBoundary>
        {({ reset }) => (
          <ErrorBoundary
            onReset={reset}
            fallbackRender={({ resetErrorBoundary }) => (
              <Card>
                <CardContent className="p-6">
                  <p className="text-destructive">
                    Failed to load supply chain data.
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
            <Tabs defaultValue="dashboard">
              <TabsList>
                <TabsTrigger value="dashboard">
                  <BarChart3 className="h-4 w-4 mr-2" />
                  AI/BI Dashboard
                </TabsTrigger>
                <TabsTrigger value="events">Supply Chain Events</TabsTrigger>
                <TabsTrigger value="sustainability">Sustainability</TabsTrigger>
                <TabsTrigger value="journey">Product Journey</TabsTrigger>
              </TabsList>

              <TabsContent value="dashboard" className="space-y-4">
                <Suspense
                  fallback={<Skeleton className="h-[70vh] w-full rounded-lg" />}
                >
                  <SupplyChainDashboard />
                </Suspense>
              </TabsContent>

              <TabsContent value="events" className="space-y-4">
                <Suspense fallback={<TableSkeleton />}>
                  <EventsList />
                </Suspense>
              </TabsContent>

              <TabsContent value="sustainability" className="space-y-4">
                <Suspense fallback={<TableSkeleton />}>
                  <SustainabilityMetrics />
                </Suspense>
              </TabsContent>

              <TabsContent value="journey" className="space-y-4">
                <Suspense fallback={<TableSkeleton />}>
                  <ProductJourneySelector />
                </Suspense>
              </TabsContent>
            </Tabs>
          </ErrorBoundary>
        )}
      </QueryErrorResetBoundary>
    </div>
  );
}

const eventTypeConfig: Record<string, { icon: React.ReactNode; color: string }> = {
  manufactured: { icon: <Factory className="h-3 w-3" />, color: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400" },
  quality_checked: { icon: <CheckCircle2 className="h-3 w-3" />, color: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400" },
  shipped: { icon: <Truck className="h-3 w-3" />, color: "bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-400" },
  received_warehouse: { icon: <Package className="h-3 w-3" />, color: "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400" },
  inspected: { icon: <CheckCircle2 className="h-3 w-3" />, color: "bg-teal-100 text-teal-800 dark:bg-teal-900/30 dark:text-teal-400" },
  distributed: { icon: <ArrowRight className="h-3 w-3" />, color: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400" },
  received_store: { icon: <MapPin className="h-3 w-3" />, color: "bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400" },
  sold: { icon: <Package className="h-3 w-3" />, color: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400" },
  returned: { icon: <XCircle className="h-3 w-3" />, color: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400" },
};

function EventsList() {
  const { data: events } = useHb_listSupplyChainEventsSuspense(selector());

  return (
    <Card>
      <CardHeader>
        <CardTitle>Supply Chain Events</CardTitle>
        <CardDescription>{events.length} events tracked</CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Event</TableHead>
              <TableHead>Location</TableHead>
              <TableHead>Country</TableHead>
              <TableHead>Partner</TableHead>
              <TableHead>Date</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {events.slice(0, 50).map((event) => {
              const cfg = eventTypeConfig[event.event_type] ?? { icon: <Clock className="h-3 w-3" />, color: "" };
              return (
                <TableRow key={event.id}>
                  <TableCell>
                    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${cfg.color}`}>
                      {cfg.icon}
                      {event.event_type.replace(/_/g, " ")}
                    </span>
                  </TableCell>
                  <TableCell className="text-sm flex items-center gap-1">
                    <MapPin className="h-3 w-3 text-muted-foreground" />
                    {event.location}
                  </TableCell>
                  <TableCell className="text-sm">{event.country}</TableCell>
                  <TableCell className="text-sm">{event.partner_name}</TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {new Date(event.event_date).toLocaleDateString()}
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

const complianceConfig: Record<string, { icon: React.ReactNode; variant: "default" | "secondary" | "destructive" | "outline" }> = {
  compliant: { icon: <CheckCircle2 className="h-3 w-3" />, variant: "default" },
  non_compliant: { icon: <XCircle className="h-3 w-3" />, variant: "destructive" },
  pending_review: { icon: <Clock className="h-3 w-3" />, variant: "outline" },
  exempted: { icon: <CheckCircle2 className="h-3 w-3" />, variant: "secondary" },
};

function SustainabilityMetrics() {
  const { data: metrics } = useHb_listSustainabilityMetricsSuspense(selector());

  const avgCarbon = metrics.length > 0 ? (metrics.reduce((s, m) => s + m.carbon_footprint_kg, 0) / metrics.length).toFixed(1) : "0";
  const avgWater = metrics.length > 0 ? (metrics.reduce((s, m) => s + m.water_usage_liters, 0) / metrics.length).toFixed(0) : "0";
  const avgRecycled = metrics.length > 0 ? (metrics.reduce((s, m) => s + m.recycled_content_pct, 0) / metrics.length).toFixed(1) : "0";

  return (
    <>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="p-2 rounded-full bg-slate-100 dark:bg-slate-800">
              <Wind className="h-5 w-5 text-slate-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{avgCarbon} kg</p>
              <p className="text-xs text-muted-foreground">Avg Carbon Footprint</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="p-2 rounded-full bg-blue-100 dark:bg-blue-900/30">
              <Droplets className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{avgWater} L</p>
              <p className="text-xs text-muted-foreground">Avg Water Usage</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="p-2 rounded-full bg-green-100 dark:bg-green-900/30">
              <Recycle className="h-5 w-5 text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{avgRecycled}%</p>
              <p className="text-xs text-muted-foreground">Avg Recycled Content</p>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Leaf className="h-5 w-5" />
            Sustainability Metrics by Product
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Product ID</TableHead>
                <TableHead>Carbon (kg)</TableHead>
                <TableHead>Water (L)</TableHead>
                <TableHead>Recycled %</TableHead>
                <TableHead>Organic %</TableHead>
                <TableHead>Compliance</TableHead>
                <TableHead>Last Audit</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {metrics.slice(0, 30).map((m) => {
                const cfg = complianceConfig[m.compliance_status] ?? complianceConfig.pending_review;
                return (
                  <TableRow key={m.id}>
                    <TableCell className="font-mono text-sm">#{m.product_id}</TableCell>
                    <TableCell>{m.carbon_footprint_kg.toFixed(1)}</TableCell>
                    <TableCell>{m.water_usage_liters.toFixed(0)}</TableCell>
                    <TableCell>{m.recycled_content_pct.toFixed(1)}%</TableCell>
                    <TableCell>{m.organic_material_pct.toFixed(1)}%</TableCell>
                    <TableCell>
                      <Badge variant={cfg.variant} className="gap-1">
                        {cfg.icon}
                        {m.compliance_status.replace("_", " ")}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {m.last_audit_date ? new Date(m.last_audit_date).toLocaleDateString() : "-"}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </>
  );
}

function ProductJourneySelector() {
  const { data: products } = useHb_listProductsSuspense(selector());
  const [selectedProductId, setSelectedProductId] = useState<number | null>(null);

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Track Product Journey</CardTitle>
          <CardDescription>Select a product to view its complete supply chain journey</CardDescription>
        </CardHeader>
        <CardContent>
          <select
            className="w-full max-w-md rounded-md border px-3 py-2 text-sm"
            value={selectedProductId ?? ""}
            onChange={(e) => setSelectedProductId(e.target.value ? Number(e.target.value) : null)}
          >
            <option value="">Select a product...</option>
            {products.slice(0, 50).map((p) => (
              <option key={p.id} value={p.id}>
                {p.sku} - {p.style_name} ({p.color})
              </option>
            ))}
          </select>
        </CardContent>
      </Card>

      {selectedProductId && (
        <QueryErrorResetBoundary>
          {({ reset }) => (
            <ErrorBoundary
              onReset={reset}
              fallbackRender={({ resetErrorBoundary }) => (
                <Card>
                  <CardContent className="p-6">
                    <p className="text-destructive">Failed to load journey.</p>
                    <button onClick={resetErrorBoundary} className="mt-2 text-sm underline">Retry</button>
                  </CardContent>
                </Card>
              )}
            >
              <Suspense fallback={<Skeleton className="h-64 w-full" />}>
                <ProductJourneyTimeline productId={selectedProductId} />
              </Suspense>
            </ErrorBoundary>
          )}
        </QueryErrorResetBoundary>
      )}
    </div>
  );
}

function ProductJourneyTimeline({ productId }: { productId: number }) {
  const { data: journey } = useHb_getProductJourneySuspense({
    params: { product_id: productId },
    ...selector(),
  });

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">{journey.product.sku}</CardTitle>
          <CardDescription>
            {journey.product.style_name} &bull; {journey.product.color} &bull;{" "}
            {journey.product.collection}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {journey.events.length === 0 ? (
            <p className="text-muted-foreground text-center py-8">
              No supply chain events recorded for this product.
            </p>
          ) : (
            <div className="relative">
              <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-border" />
              <div className="space-y-4">
                {journey.events.map((event) => {
                  const cfg = eventTypeConfig[event.event_type] ?? { icon: <Clock className="h-3 w-3" />, color: "" };
                  return (
                    <div key={event.id} className="relative flex items-start gap-4 pl-10">
                      <div className="absolute left-2.5 top-1.5 w-3 h-3 rounded-full bg-background border-2 border-primary" />
                      <div className="flex-1 bg-muted/50 rounded-lg p-3">
                        <div className="flex items-center gap-2 mb-1">
                          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${cfg.color}`}>
                            {cfg.icon}
                            {event.event_type.replace(/_/g, " ")}
                          </span>
                          <span className="text-xs text-muted-foreground">
                            {new Date(event.event_date).toLocaleDateString()}
                          </span>
                        </div>
                        <p className="text-sm">
                          <MapPin className="h-3 w-3 inline mr-1" />
                          {event.location} &bull; {event.partner_name}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {journey.sustainability && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Leaf className="h-5 w-5" />
              Sustainability Profile
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <p className="text-muted-foreground">Carbon Footprint</p>
                <p className="text-lg font-semibold">{journey.sustainability.carbon_footprint_kg.toFixed(1)} kg</p>
              </div>
              <div>
                <p className="text-muted-foreground">Water Usage</p>
                <p className="text-lg font-semibold">{journey.sustainability.water_usage_liters.toFixed(0)} L</p>
              </div>
              <div>
                <p className="text-muted-foreground">Recycled Content</p>
                <p className="text-lg font-semibold">{journey.sustainability.recycled_content_pct.toFixed(1)}%</p>
              </div>
              <div>
                <p className="text-muted-foreground">Compliance</p>
                <Badge variant={complianceConfig[journey.sustainability.compliance_status]?.variant ?? "outline"}>
                  {journey.sustainability.compliance_status.replace("_", " ")}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function SupplyChainDashboard() {
  const { data: resources } = useHb_getDatabricksResourcesSuspense(selector());
  const dashboardUrl = `https://${resources.workspace_url}/sql/dashboardsv3/${resources.sc_dashboard_id}`;
  const genieUrl = `https://${resources.workspace_url}/genie/rooms/${resources.sc_genie_space_id}`;

  return (
    <div className="space-y-4">
      <div className="flex gap-3 flex-wrap">
        <a href={dashboardUrl} target="_blank" rel="noopener noreferrer">
          <Button variant="outline" size="sm">
            <BarChart3 className="h-4 w-4 mr-2" />
            Open in Databricks
            <ExternalLink className="h-3 w-3 ml-2" />
          </Button>
        </a>
        <a href={genieUrl} target="_blank" rel="noopener noreferrer">
          <Button variant="outline" size="sm">
            <Sparkles className="h-4 w-4 mr-2" />
            Ask Genie
            <ExternalLink className="h-3 w-3 ml-2" />
          </Button>
        </a>
      </div>
      <div
        className="rounded-lg border overflow-hidden bg-white"
        style={{ height: "70vh" }}
      >
        <iframe
          src={resources.sc_dashboard_embed_url}
          className="w-full h-full border-0"
          title="Supply Chain AI/BI Dashboard"
          allow="fullscreen"
        />
      </div>
    </div>
  );
}

function TableSkeleton() {
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
