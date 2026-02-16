import { createFileRoute } from "@tanstack/react-router";
import { Suspense, useState } from "react";
import { QueryErrorResetBoundary } from "@tanstack/react-query";
import { ErrorBoundary } from "react-error-boundary";
import {
  useAt_listCampaignsSuspense,
  useAt_listInventorySuspense,
  useAt_getDatabricksResourcesSuspense,
} from "@/lib/api";
import selector from "@/lib/selector";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  AlertCircle,
  BarChart3,
  ExternalLink,
  Globe,
  MapPin,
  Monitor,
  Sparkles,
  TrendingUp,
} from "lucide-react";

export const Route = createFileRoute(
  "/projects/adtech-intelligence/dashboard",
)({
  component: () => <DashboardPage />,
});

const statusColors: Record<string, string> = {
  active: "bg-green-500/10 text-green-700 border-green-200",
  completed: "bg-blue-500/10 text-blue-700 border-blue-200",
  paused: "bg-yellow-500/10 text-yellow-700 border-yellow-200",
  draft: "bg-gray-500/10 text-gray-700 border-gray-200",
  cancelled: "bg-red-500/10 text-red-700 border-red-200",
  available: "bg-green-500/10 text-green-700 border-green-200",
  booked: "bg-blue-500/10 text-blue-700 border-blue-200",
  maintenance: "bg-orange-500/10 text-orange-700 border-orange-200",
  inactive: "bg-gray-500/10 text-gray-700 border-gray-200",
};

function EmbeddedDashboard() {
  const { data: resources } = useAt_getDatabricksResourcesSuspense(selector());

  return (
    <div className="rounded-lg border overflow-hidden bg-white" style={{ height: "70vh" }}>
      <iframe
        src={resources.dashboard_embed_url}
        className="w-full h-full border-0"
        title="AdTech AI/BI Dashboard"
        allow="fullscreen"
      />
    </div>
  );
}

function CampaignExplorer() {
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [typeFilter, setTypeFilter] = useState<string>("all");

  const queryParams: Record<string, any> = { limit: 50 };
  if (statusFilter !== "all") queryParams.status = statusFilter;
  if (typeFilter !== "all") queryParams.campaign_type = typeFilter;

  const { data: campaigns } = useAt_listCampaignsSuspense({ params: queryParams, ...selector() });

  return (
    <div className="space-y-4">
      <div className="flex gap-3 flex-wrap">
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[160px]">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
            <SelectItem value="paused">Paused</SelectItem>
            <SelectItem value="draft">Draft</SelectItem>
            <SelectItem value="cancelled">Cancelled</SelectItem>
          </SelectContent>
        </Select>

        <Select value={typeFilter} onValueChange={setTypeFilter}>
          <SelectTrigger className="w-[160px]">
            <SelectValue placeholder="Type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value="online">Online</SelectItem>
            <SelectItem value="outdoor">Outdoor</SelectItem>
            <SelectItem value="crossmedia">Crossmedia</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Campaign</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Budget</TableHead>
              <TableHead className="text-right">Spent</TableHead>
              <TableHead className="text-right">Utilization</TableHead>
              <TableHead>Period</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {campaigns.map((campaign) => {
              const utilization = campaign.budget
                ? ((campaign.spent / campaign.budget) * 100).toFixed(1)
                : "0.0";
              return (
                <TableRow key={campaign.id}>
                  <TableCell className="font-medium max-w-[250px] truncate">
                    {campaign.name}
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" className="capitalize">
                      {campaign.campaign_type === "online" && (
                        <Globe className="h-3 w-3 mr-1" />
                      )}
                      {campaign.campaign_type === "outdoor" && (
                        <MapPin className="h-3 w-3 mr-1" />
                      )}
                      {campaign.campaign_type === "crossmedia" && (
                        <Monitor className="h-3 w-3 mr-1" />
                      )}
                      {campaign.campaign_type}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant="outline"
                      className={statusColors[campaign.status] || ""}
                    >
                      {campaign.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    €{campaign.budget?.toLocaleString("de-DE", { minimumFractionDigits: 0 })}
                  </TableCell>
                  <TableCell className="text-right">
                    €{campaign.spent?.toLocaleString("de-DE", { minimumFractionDigits: 0 })}
                  </TableCell>
                  <TableCell className="text-right">
                    <span
                      className={
                        Number(utilization) > 90
                          ? "text-red-600 font-medium"
                          : Number(utilization) > 70
                            ? "text-yellow-600"
                            : "text-green-600"
                      }
                    >
                      {utilization}%
                    </span>
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground whitespace-nowrap">
                    {campaign.start_date} — {campaign.end_date}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}

function InventoryExplorer() {
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [cityFilter, setCityFilter] = useState<string>("all");

  const queryParams: Record<string, any> = { limit: 100 };
  if (typeFilter !== "all") queryParams.location_type = typeFilter;
  if (cityFilter !== "all") queryParams.city = cityFilter;

  const { data: inventory } = useAt_listInventorySuspense({ params: queryParams, ...selector() });

  const cities = [
    ...new Set(
      inventory.filter((i) => i.city).map((i) => i.city as string),
    ),
  ].sort();

  return (
    <div className="space-y-4">
      <div className="flex gap-3 flex-wrap">
        <Select value={typeFilter} onValueChange={setTypeFilter}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Location Type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Locations</SelectItem>
            <SelectItem value="online">Online</SelectItem>
            <SelectItem value="train_station">Train Station</SelectItem>
            <SelectItem value="mall">Mall</SelectItem>
            <SelectItem value="pedestrian_zone">Pedestrian Zone</SelectItem>
            <SelectItem value="highway">Highway</SelectItem>
            <SelectItem value="bus_stop">Bus Stop</SelectItem>
            <SelectItem value="airport">Airport</SelectItem>
            <SelectItem value="subway">Subway</SelectItem>
          </SelectContent>
        </Select>

        <Select value={cityFilter} onValueChange={setCityFilter}>
          <SelectTrigger className="w-[160px]">
            <SelectValue placeholder="City" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Cities</SelectItem>
            {(cities as string[]).map((city) => (
              <SelectItem key={city} value={city}>
                {city}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Location</TableHead>
              <TableHead>City</TableHead>
              <TableHead className="text-right">Daily Impressions</TableHead>
              <TableHead className="text-right">CPM (€)</TableHead>
              <TableHead>Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {inventory.map((item) => (
              <TableRow key={item.id}>
                <TableCell className="font-medium max-w-[250px] truncate">
                  {item.name}
                </TableCell>
                <TableCell>
                  <Badge variant="outline" className="text-xs capitalize">
                    {item.inventory_type?.replace(/_/g, " ")}
                  </Badge>
                </TableCell>
                <TableCell className="text-xs capitalize">
                  {item.location_type?.replace(/_/g, " ")}
                </TableCell>
                <TableCell>{item.city || "—"}</TableCell>
                <TableCell className="text-right">
                  {item.daily_impressions_est?.toLocaleString("de-DE")}
                </TableCell>
                <TableCell className="text-right">
                  €{item.cpm_rate?.toFixed(2)}
                </TableCell>
                <TableCell>
                  <Badge
                    variant="outline"
                    className={statusColors[item.status] || ""}
                  >
                    {item.status}
                  </Badge>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}

function DatabricksLinks() {
  const { data: resources } = useAt_getDatabricksResourcesSuspense(selector());
  const dashboardUrl = `https://${resources.workspace_url}/sql/dashboardsv3/${resources.dashboard_id}`;
  const genieUrl = `https://${resources.workspace_url}/genie/rooms/${resources.genie_space_id}`;

  return (
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
  );
}

function DashboardContent() {
  return (
    <div className="space-y-6 p-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <BarChart3 className="h-6 w-6" />
            Demand & Inventory Explorer
          </h1>
          <p className="text-muted-foreground mt-1">
            Analyze campaigns, placements, and ad inventory across online and outdoor channels.
          </p>
        </div>
        <Suspense fallback={null}>
          <DatabricksLinks />
        </Suspense>
      </div>

      <Tabs defaultValue="dashboard" className="space-y-4">
        <TabsList>
          <TabsTrigger value="dashboard">
            <BarChart3 className="h-4 w-4 mr-2" />
            AI/BI Dashboard
          </TabsTrigger>
          <TabsTrigger value="campaigns">
            <TrendingUp className="h-4 w-4 mr-2" />
            Campaigns
          </TabsTrigger>
          <TabsTrigger value="inventory">
            <Monitor className="h-4 w-4 mr-2" />
            Inventory
          </TabsTrigger>
        </TabsList>

        <TabsContent value="dashboard">
          <Suspense
            fallback={<Skeleton className="h-[70vh] w-full rounded-lg" />}
          >
            <EmbeddedDashboard />
          </Suspense>
        </TabsContent>

        <TabsContent value="campaigns">
          <Suspense
            fallback={
              <div className="space-y-4">
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-[400px] w-full" />
              </div>
            }
          >
            <CampaignExplorer />
          </Suspense>
        </TabsContent>

        <TabsContent value="inventory">
          <Suspense
            fallback={
              <div className="space-y-4">
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-[400px] w-full" />
              </div>
            }
          >
            <InventoryExplorer />
          </Suspense>
        </TabsContent>
      </Tabs>
    </div>
  );
}

function DashboardPage() {
  return (
    <QueryErrorResetBoundary>
      {({ reset }) => (
        <ErrorBoundary
          onReset={reset}
          fallbackRender={({ resetErrorBoundary }) => (
            <div className="p-6 flex items-center justify-center min-h-[50vh]">
              <Card className="border-destructive/50 max-w-lg">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-destructive">
                    <AlertCircle className="h-5 w-5" />
                    Failed to Load Dashboard
                  </CardTitle>
                  <CardDescription>
                    Could not load the dashboard data.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Button variant="outline" onClick={resetErrorBoundary}>
                    Try Again
                  </Button>
                </CardContent>
              </Card>
            </div>
          )}
        >
          <DashboardContent />
        </ErrorBoundary>
      )}
    </QueryErrorResetBoundary>
  );
}
