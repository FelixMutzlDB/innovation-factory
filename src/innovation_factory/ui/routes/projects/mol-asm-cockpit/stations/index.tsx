import { Suspense, useState, useMemo, useEffect } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { ErrorBoundary } from "react-error-boundary";
import { QueryErrorResetBoundary } from "@tanstack/react-query";
import {
  useMac_listStationsSuspense,
  useMac_listRegionsSuspense,
  useMac_listAnomalyAlertsSuspense,
  type MacStationOut,
} from "@/lib/api";
import selector from "@/lib/selector";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Search } from "lucide-react";
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";

export const Route = createFileRoute("/projects/mol-asm-cockpit/stations/")({
  component: () => <StationsPage />,
});

function StationsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Stations</h1>
        <p className="text-muted-foreground mt-2">
          Browse and filter stations across your network
        </p>
      </div>

      <QueryErrorResetBoundary>
        {({ reset }) => (
          <ErrorBoundary
            onReset={reset}
            fallbackRender={({ error, resetErrorBoundary }) => (
              <Card className="p-6">
                <div className="text-center">
                  <p className="text-destructive mb-4">
                    Error loading stations: {error.message}
                  </p>
                  <Button onClick={resetErrorBoundary}>Try Again</Button>
                </div>
              </Card>
            )}
          >
            <Suspense fallback={<StationsSkeleton />}>
              <StationsContent />
            </Suspense>
          </ErrorBoundary>
        )}
      </QueryErrorResetBoundary>
    </div>
  );
}

function StationsContent() {
  const { data: stations } = useMac_listStationsSuspense(selector());
  const { data: regions } = useMac_listRegionsSuspense(selector());
  const { data: alerts } = useMac_listAnomalyAlertsSuspense({
    params: { status: "active", limit: 500 },
    ...selector(),
  });

  const regionMap = useMemo(() => {
    const map = new Map<number, string>();
    if (Array.isArray(regions)) {
      for (const r of regions) {
        map.set(r.id, r.name);
      }
    }
    return map;
  }, [regions]);

  const alertCountMap = useMemo(() => {
    const map = new Map<number, number>();
    if (Array.isArray(alerts)) {
      for (const a of alerts) {
        map.set(a.station_id, (map.get(a.station_id) ?? 0) + 1);
      }
    }
    return map;
  }, [alerts]);

  const regionNames = useMemo(() => {
    return Array.isArray(regions)
      ? regions.map((r: { name: string }) => r.name).sort()
      : [];
  }, [regions]);

  const [search, setSearch] = useState("");
  const [regionFilter, setRegionFilter] = useState<string>("all");
  const [typeFilter, setTypeFilter] = useState<string>("all");

  const stationList = Array.isArray(stations) ? stations : [];

  const filteredStations = useMemo(() => {
    return stationList.filter((s: MacStationOut) => {
      const regionName = regionMap.get(s.region_id) ?? "";
      const matchSearch =
        !search ||
        s.station_code.toLowerCase().includes(search.toLowerCase()) ||
        s.name.toLowerCase().includes(search.toLowerCase()) ||
        s.city.toLowerCase().includes(search.toLowerCase());
      const matchRegion =
        regionFilter === "all" || regionName === regionFilter;
      const matchType =
        typeFilter === "all" || s.station_type === typeFilter;
      return matchSearch && matchRegion && matchType;
    });
  }, [stationList, search, regionFilter, typeFilter, regionMap]);

  const typeColors: Record<string, string> = {
    highway: "#f59e0b",
    urban: "#3b82f6",
    suburban: "#10b981",
  };

  return (
    <>
      {/* Map */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Network Map</CardTitle>
          <CardDescription>
            {filteredStations.length} station(s) shown &mdash; color by type:
            <span className="inline-flex gap-3 ml-2">
              <span className="inline-flex items-center gap-1"><span className="inline-block w-2.5 h-2.5 rounded-full" style={{ background: "#f59e0b" }} />Highway</span>
              <span className="inline-flex items-center gap-1"><span className="inline-block w-2.5 h-2.5 rounded-full" style={{ background: "#3b82f6" }} />Urban</span>
              <span className="inline-flex items-center gap-1"><span className="inline-block w-2.5 h-2.5 rounded-full" style={{ background: "#10b981" }} />Suburban</span>
            </span>
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[380px] rounded-lg overflow-hidden border">
            <MapContainer
              center={[47.5, 17.5]}
              zoom={6}
              className="h-full w-full"
              scrollWheelZoom
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              <FitBounds stations={filteredStations} />
              {filteredStations.map((station: MacStationOut) => {
                const alertCount = alertCountMap.get(station.id) ?? 0;
                const color = typeColors[station.station_type] ?? "#6b7280";
                return (
                  <CircleMarker
                    key={station.id}
                    center={[station.latitude, station.longitude]}
                    radius={alertCount > 0 ? 9 : 7}
                    pathOptions={{
                      color: alertCount > 0 ? "#ef4444" : color,
                      fillColor: color,
                      fillOpacity: 0.85,
                      weight: alertCount > 0 ? 2.5 : 1.5,
                    }}
                  >
                    <Popup>
                      <div className="text-xs space-y-1 min-w-[160px]">
                        <p className="font-bold text-sm">{station.name}</p>
                        <p>{station.station_code} &middot; {station.city}</p>
                        <p className="capitalize">{station.station_type} &middot; {regionMap.get(station.region_id) ?? "—"}</p>
                        {station.has_fresh_corner && <p>Fresh Corner</p>}
                        {station.has_ev_charging && <p>EV Charging</p>}
                        {alertCount > 0 && (
                          <p className="text-red-600 font-medium">{alertCount} active alert(s)</p>
                        )}
                        <Link
                          to="/projects/mol-asm-cockpit/stations/$stationCode"
                          params={{ stationCode: station.station_code }}
                          className="text-primary underline block mt-1"
                        >
                          View details &rarr;
                        </Link>
                      </div>
                    </Popup>
                  </CircleMarker>
                );
              })}
            </MapContainer>
          </div>
        </CardContent>
      </Card>

      {/* Filters */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Search & Filter</CardTitle>
          <CardDescription>
            Search by code, name, or city. Filter by region and type.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-4">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search stations..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9"
            />
          </div>
          <Select value={regionFilter} onValueChange={setRegionFilter}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Region" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All regions</SelectItem>
              {regionNames.map((r: string) => (
                <SelectItem key={r} value={r}>
                  {r}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={typeFilter} onValueChange={setTypeFilter}>
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="Type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All types</SelectItem>
              <SelectItem value="urban">Urban</SelectItem>
              <SelectItem value="highway">Highway</SelectItem>
              <SelectItem value="suburban">Suburban</SelectItem>
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      {/* Station Table */}
      <Card>
        <CardHeader>
          <CardTitle>Station List</CardTitle>
          <CardDescription>
            {filteredStations.length} station(s) &bull; Click code for details
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4 font-medium">
                    Station Code
                  </th>
                  <th className="text-left py-3 px-4 font-medium">Name</th>
                  <th className="text-left py-3 px-4 font-medium">City</th>
                  <th className="text-left py-3 px-4 font-medium">Region</th>
                  <th className="text-left py-3 px-4 font-medium">Type</th>
                  <th className="text-left py-3 px-4 font-medium">
                    Fresh Corner
                  </th>
                  <th className="text-left py-3 px-4 font-medium">
                    EV Charging
                  </th>
                  <th className="text-left py-3 px-4 font-medium">
                    Active Alerts
                  </th>
                </tr>
              </thead>
              <tbody>
                {filteredStations.length === 0 ? (
                  <tr>
                    <td
                      colSpan={8}
                      className="py-12 text-center text-muted-foreground"
                    >
                      No stations match the current filters
                    </td>
                  </tr>
                ) : (
                  filteredStations.map((station: MacStationOut) => {
                    const alertCount = alertCountMap.get(station.id) ?? 0;
                    return (
                      <tr
                        key={station.station_code}
                        className="border-b hover:bg-muted/50 transition-colors"
                      >
                        <td className="py-3 px-4">
                          <Link
                            to="/projects/mol-asm-cockpit/stations/$stationCode"
                            params={{ stationCode: station.station_code }}
                            className="font-medium text-primary hover:underline"
                          >
                            {station.station_code}
                          </Link>
                        </td>
                        <td className="py-3 px-4">{station.name}</td>
                        <td className="py-3 px-4">{station.city}</td>
                        <td className="py-3 px-4">
                          {regionMap.get(station.region_id) ?? "—"}
                        </td>
                        <td className="py-3 px-4 capitalize">
                          {station.station_type}
                        </td>
                        <td className="py-3 px-4">
                          {station.has_fresh_corner ? (
                            <Badge
                              variant="outline"
                              className="bg-green-500/10 text-green-600 dark:text-green-400"
                            >
                              Yes
                            </Badge>
                          ) : (
                            <span className="text-muted-foreground">No</span>
                          )}
                        </td>
                        <td className="py-3 px-4">
                          {station.has_ev_charging ? (
                            <Badge
                              variant="outline"
                              className="bg-blue-500/10 text-blue-600 dark:text-blue-400"
                            >
                              Yes
                            </Badge>
                          ) : (
                            <span className="text-muted-foreground">No</span>
                          )}
                        </td>
                        <td className="py-3 px-4">
                          {alertCount > 0 ? (
                            <Badge
                              variant="destructive"
                              className="bg-destructive/20 text-destructive"
                            >
                              {alertCount}
                            </Badge>
                          ) : (
                            <span className="text-muted-foreground">0</span>
                          )}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </>
  );
}

function FitBounds({ stations }: { stations: MacStationOut[] }) {
  const map = useMap();
  useEffect(() => {
    if (stations.length === 0) return;
    const bounds = stations.map(
      (s) => [s.latitude, s.longitude] as [number, number],
    );
    map.fitBounds(bounds, { padding: [30, 30], maxZoom: 10 });
  }, [stations, map]);
  return null;
}

function StationsSkeleton() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-[140px]" />
      <Skeleton className="h-[400px]" />
    </div>
  );
}
