import { createFileRoute, useParams } from "@tanstack/react-router";
import { Suspense, useState } from "react";
import { ErrorBoundary } from "react-error-boundary";
import { QueryErrorResetBoundary } from "@tanstack/react-query";
import {
  useAeco_getProjectTwinSuspense,
  type DtTwinBuildingOut,
  type DtTwinFloorOut,
  type DtTwinSpaceOut,
} from "@/lib/api";
import { selector } from "@/lib/selector";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Building2, Layers, Square, ChevronRight, ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/projects/aeco-hub/projects/$projectId/twin")({
  component: () => <TwinPage />,
});

function TwinPage() {
  const { projectId } = useParams({ from: "/projects/aeco-hub/projects/$projectId/twin" });
  const pid = Number(projectId);

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold">Spatial twin</h2>
        <p className="text-sm text-muted-foreground">
          Drill down through the spatial hierarchy: project → building → floor → space.
          For an entity-relationship view, see the <span className="font-medium">Graph</span> tab.
        </p>
      </div>

      <QueryErrorResetBoundary>
        {({ reset }) => (
          <ErrorBoundary
            onReset={reset}
            fallbackRender={() => (
              <Card>
                <CardContent className="p-6 text-destructive">
                  Failed to load twin.
                </CardContent>
              </Card>
            )}
          >
            <Suspense fallback={<TreeSkeleton />}>
              <TwinTree pid={pid} />
            </Suspense>
          </ErrorBoundary>
        )}
      </QueryErrorResetBoundary>
    </div>
  );
}

function TwinTree({ pid }: { pid: number }) {
  const { data: twin } = useAeco_getProjectTwinSuspense({
    params: { project_id: pid },
    ...selector(),
  });

  const totalSpaces = twin.buildings.reduce(
    (s, b) => s + b.floors.reduce((s2, f) => s2 + f.spaces.length, 0),
    0,
  );
  const totalFloors = twin.buildings.reduce((s, b) => s + b.floors.length, 0);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <Building2 size={16} />
          {twin.project_name}
        </CardTitle>
        <p className="text-xs text-muted-foreground">
          {twin.buildings.length} buildings · {totalFloors} floors · {totalSpaces} spaces
        </p>
      </CardHeader>
      <CardContent className="space-y-1">
        {twin.buildings.map((b) => (
          <BuildingNode key={b.id} building={b} />
        ))}
      </CardContent>
    </Card>
  );
}

function BuildingNode({ building }: { building: DtTwinBuildingOut }) {
  const [open, setOpen] = useState(true);

  return (
    <div>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 w-full text-left p-2 rounded hover:bg-muted/50 transition-colors"
      >
        {open ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        <Building2 size={14} className="text-amber-500" />
        <span className="font-medium text-sm">{building.name}</span>
        <Badge variant="outline" className="text-xs capitalize ml-2">
          {building.building_type.replace(/_/g, " ")}
        </Badge>
        <span className="text-xs text-muted-foreground ml-auto">
          {building.gross_floor_area_sqm.toLocaleString()} m² · {building.floors.length} floors
        </span>
      </button>
      {open && (
        <div className="ml-5 border-l pl-3 space-y-1">
          {building.floors.map((f) => (
            <FloorNode key={f.id} floor={f} />
          ))}
        </div>
      )}
    </div>
  );
}

function FloorNode({ floor }: { floor: DtTwinFloorOut }) {
  const [open, setOpen] = useState(false);

  return (
    <div>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 w-full text-left p-1.5 rounded hover:bg-muted/50 transition-colors text-sm"
      >
        {open ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
        <Layers size={13} className="text-blue-500" />
        <span>{floor.name}</span>
        <span className="text-xs text-muted-foreground">L{floor.level}</span>
        <span className="text-xs text-muted-foreground ml-auto">
          {floor.area_sqm.toLocaleString()} m² · {floor.spaces.length} spaces
        </span>
      </button>
      {open && (
        <div className="ml-5 border-l pl-3 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-1.5 py-1">
          {floor.spaces.map((s) => (
            <SpaceNode key={s.id} space={s} />
          ))}
        </div>
      )}
    </div>
  );
}

function SpaceNode({ space }: { space: DtTwinSpaceOut }) {
  return (
    <div
      className={cn(
        "flex items-start gap-1.5 p-1.5 text-xs rounded border bg-card hover:bg-muted/50 transition-colors",
      )}
    >
      <Square size={11} className="mt-0.5 text-muted-foreground" />
      <div className="flex-1 min-w-0">
        <div className="font-medium truncate">{space.name}</div>
        <div className="text-muted-foreground capitalize truncate">
          {space.space_type.replace(/_/g, " ")} · {space.area_sqm}m²
        </div>
      </div>
    </div>
  );
}

function TreeSkeleton() {
  return (
    <Card>
      <CardContent className="p-4 space-y-2">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-8 w-full" />
        ))}
      </CardContent>
    </Card>
  );
}
