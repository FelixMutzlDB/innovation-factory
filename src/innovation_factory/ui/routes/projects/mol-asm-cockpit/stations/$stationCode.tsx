import { Suspense, useMemo } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { ErrorBoundary } from "react-error-boundary";
import { QueryErrorResetBoundary } from "@tanstack/react-query";
import {
  useMac_listStationsSuspense,
  useMac_listRegionsSuspense,
  useMac_listFuelSalesSuspense,
  useMac_listNonfuelSalesSuspense,
  useMac_listAnomalyAlertsSuspense,
  useMac_listWorkforceShiftsSuspense,
  type MacStationOut,
  type MacFuelSaleOut,
  type MacNonfuelSaleOut,
  type MacAnomalyAlertOut,
} from "@/lib/api";
import selector from "@/lib/selector";
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
  MapPin,
  Fuel,
  Coffee,
  AlertTriangle,
  Users,
  ArrowLeft,
  Plug,
  Store,
} from "lucide-react";

export const Route = createFileRoute(
  "/projects/mol-asm-cockpit/stations/$stationCode",
)({
  component: () => <StationDetailPage />,
});

function StationDetailPage() {
  const { stationCode } = Route.useParams();

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link to="/projects/mol-asm-cockpit/stations">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back to stations
          </Button>
        </Link>
      </div>

      <QueryErrorResetBoundary>
        {({ reset }) => (
          <ErrorBoundary
            onReset={reset}
            fallbackRender={({ error, resetErrorBoundary }) => (
              <Card className="p-6">
                <div className="text-center">
                  <p className="text-destructive mb-4">
                    Error loading station: {error.message}
                  </p>
                  <Button onClick={resetErrorBoundary}>Try Again</Button>
                </div>
              </Card>
            )}
          >
            <Suspense fallback={<StationDetailSkeleton />}>
              <StationDetailContent stationCode={stationCode} />
            </Suspense>
          </ErrorBoundary>
        )}
      </QueryErrorResetBoundary>
    </div>
  );
}

function StationDetailContent({ stationCode }: { stationCode: string }) {
  const { data: stations } = useMac_listStationsSuspense(selector());
  const { data: regions } = useMac_listRegionsSuspense(selector());

  const stationList = Array.isArray(stations) ? stations : [];
  const station = stationList.find(
    (s: MacStationOut) => s.station_code === stationCode,
  );

  if (!station) {
    return (
      <Card>
        <CardContent className="py-12 text-center text-muted-foreground">
          <MapPin className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p className="text-lg font-medium">Station not found</p>
          <p className="text-sm mt-2">
            No station with code &ldquo;{stationCode}&rdquo; was found.
          </p>
        </CardContent>
      </Card>
    );
  }

  const regionList = Array.isArray(regions) ? regions : [];
  const region = regionList.find(
    (r: { id: number }) => r.id === station.region_id,
  );

  return (
    <>
      {/* Station Header */}
      <div className="flex items-start gap-4">
        <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center">
          <MapPin className="h-6 w-6 text-primary" />
        </div>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{station.name}</h1>
          <p className="text-muted-foreground mt-1">
            {station.station_code} &bull; {station.city}
            {region ? ` &bull; ${region.name}` : ""}
          </p>
        </div>
      </div>

      {/* Station Info Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="border-l-4 border-l-primary/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Type</CardTitle>
            <Store className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold capitalize">
              {station.station_type}
            </div>
            <p className="text-xs text-muted-foreground">
              {station.num_pumps} pumps &bull;{" "}
              {station.shop_area_sqm}m&sup2; shop
            </p>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-green-500/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Fresh Corner</CardTitle>
            <Coffee className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {station.has_fresh_corner ? "Active" : "No"}
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-blue-500/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">EV Charging</CardTitle>
            <Plug className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {station.has_ev_charging ? "Available" : "No"}
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-amber-500/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Opened</CardTitle>
            <MapPin className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {station.opened_date
                ? new Date(station.opened_date).toLocaleDateString()
                : "—"}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Station Data Sections */}
      <Suspense fallback={<Skeleton className="h-[300px]" />}>
        <StationDataPanels stationId={station.id} />
      </Suspense>
    </>
  );
}

function StationDataPanels({ stationId }: { stationId: number }) {
  const { data: fuelSales } = useMac_listFuelSalesSuspense({
    params: { station_id: stationId, days: 30, limit: 500 },
    ...selector(),
  });
  const { data: nonfuelSales } = useMac_listNonfuelSalesSuspense({
    params: { station_id: stationId, days: 30, limit: 500 },
    ...selector(),
  });
  const { data: alerts } = useMac_listAnomalyAlertsSuspense({
    params: { station_id: stationId, limit: 50 },
    ...selector(),
  });
  const { data: shifts } = useMac_listWorkforceShiftsSuspense({
    params: { station_id: stationId, days: 7 },
    ...selector(),
  });

  const fuelList = Array.isArray(fuelSales) ? fuelSales : [];
  const nonfuelList = Array.isArray(nonfuelSales) ? nonfuelSales : [];
  const alertList = Array.isArray(alerts) ? alerts : [];
  const shiftList = Array.isArray(shifts) ? shifts : [];

  const fuelSummary = useMemo(() => {
    const totalVolume = fuelList.reduce(
      (sum: number, s: MacFuelSaleOut) => sum + s.volume_liters,
      0,
    );
    const totalRevenue = fuelList.reduce(
      (sum: number, s: MacFuelSaleOut) => sum + s.revenue,
      0,
    );
    const totalMargin = fuelList.reduce(
      (sum: number, s: MacFuelSaleOut) => sum + s.margin,
      0,
    );
    return { totalVolume, totalRevenue, totalMargin };
  }, [fuelList]);

  const nonfuelSummary = useMemo(() => {
    const totalRevenue = nonfuelList.reduce(
      (sum: number, s: MacNonfuelSaleOut) => sum + s.revenue,
      0,
    );
    const totalMargin = nonfuelList.reduce(
      (sum: number, s: MacNonfuelSaleOut) => sum + s.margin,
      0,
    );
    return { totalRevenue, totalMargin };
  }, [nonfuelList]);

  const activeAlerts = alertList.filter(
    (a: MacAnomalyAlertOut) => a.status === "active",
  );

  return (
    <div className="space-y-6">
      {/* KPI Summary */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Fuel Volume (30d)
            </CardTitle>
            <Fuel className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {Math.round(fuelSummary.totalVolume).toLocaleString()}L
            </div>
            <p className="text-xs text-muted-foreground">
              Revenue: &euro;{Math.round(fuelSummary.totalRevenue).toLocaleString()}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Non-Fuel Revenue (30d)
            </CardTitle>
            <Coffee className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              &euro;{Math.round(nonfuelSummary.totalRevenue).toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">
              Margin: &euro;{Math.round(nonfuelSummary.totalMargin).toLocaleString()}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Alerts</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeAlerts.length}</div>
            <p className="text-xs text-muted-foreground">
              {alertList.length} total
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Shifts This Week
            </CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{shiftList.length}</div>
          </CardContent>
        </Card>
      </div>

      {/* Active Alerts */}
      {activeAlerts.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Active Alerts</CardTitle>
            <CardDescription>
              Unresolved alerts for this station
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {activeAlerts.map((alert: MacAnomalyAlertOut) => (
              <div
                key={alert.id}
                className="flex items-start gap-3 p-3 rounded-lg bg-muted/50"
              >
                <AlertTriangle className="h-5 w-5 text-amber-500 flex-shrink-0 mt-0.5" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="font-medium text-sm">{alert.title}</p>
                    <Badge
                      variant="outline"
                      className={
                        alert.severity === "critical"
                          ? "bg-red-500/20 text-red-600 dark:text-red-400"
                          : alert.severity === "high"
                            ? "bg-orange-500/20 text-orange-600 dark:text-orange-400"
                            : "bg-yellow-500/20 text-yellow-600 dark:text-yellow-400"
                      }
                    >
                      {alert.severity}
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground mt-1">
                    {alert.description}
                  </p>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Recent Fuel Sales by Type */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            Fuel Sales Summary (Last 30 Days)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 px-3 font-medium">
                    Fuel Type
                  </th>
                  <th className="text-right py-2 px-3 font-medium">
                    Volume (L)
                  </th>
                  <th className="text-right py-2 px-3 font-medium">Revenue</th>
                  <th className="text-right py-2 px-3 font-medium">Margin</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(
                  fuelList.reduce(
                    (
                      acc: Record<
                        string,
                        { volume: number; revenue: number; margin: number }
                      >,
                      s: MacFuelSaleOut,
                    ) => {
                      if (!acc[s.fuel_type]) {
                        acc[s.fuel_type] = {
                          volume: 0,
                          revenue: 0,
                          margin: 0,
                        };
                      }
                      acc[s.fuel_type].volume += s.volume_liters;
                      acc[s.fuel_type].revenue += s.revenue;
                      acc[s.fuel_type].margin += s.margin;
                      return acc;
                    },
                    {},
                  ),
                ).map(([type, data]) => (
                  <tr key={type} className="border-b">
                    <td className="py-2 px-3 capitalize">
                      {type.replace(/_/g, " ")}
                    </td>
                    <td className="py-2 px-3 text-right">
                      {Math.round(data.volume).toLocaleString()}
                    </td>
                    <td className="py-2 px-3 text-right">
                      &euro;{Math.round(data.revenue).toLocaleString()}
                    </td>
                    <td className="py-2 px-3 text-right">
                      &euro;{Math.round(data.margin).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function StationDetailSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-16 w-64" />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <Skeleton key={i} className="h-[100px]" />
        ))}
      </div>
      <Skeleton className="h-[300px]" />
    </div>
  );
}
