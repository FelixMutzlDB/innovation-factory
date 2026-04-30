import { createFileRoute, useParams } from "@tanstack/react-router";
import { Suspense, lazy, useMemo, useRef } from "react";
import { ErrorBoundary } from "react-error-boundary";
import { QueryErrorResetBoundary } from "@tanstack/react-query";
import { useAeco_getRelationshipGraphSuspense } from "@/lib/api";
import { selector } from "@/lib/selector";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Network } from "lucide-react";

// Lazy-load the force-directed graph — keeps the main bundle slim per
// plan §10 / §11. The component pulls in d3-force which is ~200KB.
const ForceGraph2D = lazy(() => import("react-force-graph-2d"));

export const Route = createFileRoute("/projects/aeco-hub/projects/$projectId/relationships")({
  component: () => <RelationshipsPage />,
});

const NODE_COLOR: Record<string, string> = {
  project: "#F59E0B", // amber
  building: "#3B82F6", // blue
  floor: "#10B981", // green
  space: "#8B5CF6", // violet
  sensor: "#EC4899", // pink
  member: "#64748B", // slate
};

function RelationshipsPage() {
  const { projectId } = useParams({
    from: "/projects/aeco-hub/projects/$projectId/relationships",
  });
  const pid = Number(projectId);

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <Network size={18} />
          Relationship graph
        </h2>
        <p className="text-sm text-muted-foreground">
          Force-directed view of how project entities connect. Drag nodes to
          rearrange; scroll to zoom.
        </p>
      </div>

      <Legend />

      <QueryErrorResetBoundary>
        {({ reset }) => (
          <ErrorBoundary
            onReset={reset}
            fallbackRender={() => (
              <Card>
                <CardContent className="p-6 text-destructive">
                  Failed to load relationship graph.
                </CardContent>
              </Card>
            )}
          >
            <Suspense fallback={<GraphSkeleton />}>
              <Graph pid={pid} />
            </Suspense>
          </ErrorBoundary>
        )}
      </QueryErrorResetBoundary>
    </div>
  );
}

function Graph({ pid }: { pid: number }) {
  const { data: graph } = useAeco_getRelationshipGraphSuspense({
    params: { project_id: pid, limit: 500 },
    ...selector(),
  });

  // ForceGraph2D expects { nodes: [{id, ...}], links: [{source, target}] }.
  // Our backend already uses `id` strings (e.g. "building:1") so the
  // transform is just renaming `edges` → `links`.
  const data = useMemo(
    () => ({
      nodes: graph.nodes.map((n) => ({
        id: n.id,
        label: n.label,
        type: n.type,
      })),
      links: graph.edges.map((e) => ({
        source: e.source,
        target: e.target,
        label: e.relationship_type,
      })),
    }),
    [graph],
  );

  const containerRef = useRef<HTMLDivElement>(null);

  return (
    <Card>
      <CardContent className="p-0 relative">
        <div
          ref={containerRef}
          className="h-[600px] w-full bg-card relative overflow-hidden"
        >
          <Suspense fallback={<GraphSkeleton />}>
            <ForceGraph2D
              graphData={data}
              width={containerRef.current?.clientWidth || 800}
              height={600}
              nodeColor={(node: any) => NODE_COLOR[node.type] ?? "#94a3b8"}
              nodeLabel={(node: any) => node.label}
              nodeRelSize={5}
              linkColor={() => "rgba(148, 163, 184, 0.3)"}
              linkDirectionalArrowLength={4}
              linkDirectionalArrowRelPos={0.95}
              cooldownTicks={120}
              backgroundColor="transparent"
            />
          </Suspense>
        </div>
        <div className="px-4 py-2 border-t text-xs text-muted-foreground flex items-center justify-between">
          <span>
            {graph.nodes.length} nodes, {graph.edges.length} edges
            {graph.truncated && (
              <span className="ml-1 text-amber-600">
                · showing {graph.edges.length} of {graph.total_edges} edges (capped)
              </span>
            )}
          </span>
        </div>
      </CardContent>
    </Card>
  );
}

function Legend() {
  return (
    <div className="flex flex-wrap gap-2 items-center text-xs">
      {Object.entries(NODE_COLOR).map(([type, color]) => (
        <Badge
          key={type}
          variant="outline"
          className="capitalize"
          style={{ borderColor: color, color }}
        >
          <span
            className="inline-block w-2 h-2 rounded-full mr-1.5"
            style={{ background: color }}
          />
          {type}
        </Badge>
      ))}
    </div>
  );
}

function GraphSkeleton() {
  return (
    <Card>
      <CardContent className="p-0">
        <Skeleton className="h-[600px] w-full" />
      </CardContent>
    </Card>
  );
}
