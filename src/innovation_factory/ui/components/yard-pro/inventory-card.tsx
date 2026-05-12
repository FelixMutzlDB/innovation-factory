import { Badge } from "@/components/ui/badge";

interface Tool {
  id: number;
  kind: string;
  model_year: number;
  battery_family?: string;
  last_serviced_at?: string;
}

interface Consumable {
  id: number;
  kind: string;
  quantity: number;
  unit: string;
  last_restock_at?: string;
}

interface InventoryCardProps {
  /** List of tools owned. */
  tools?: Tool[];
  /** List of consumables in stock. */
  consumables?: Consumable[];
}

/**
 * Inventory card for the cockpit (UC1 and UC5).
 *
 * Displays:
 * - Tools: kind + battery_family + last_serviced_at
 * - Consumables: kind + quantity + unit + last_restock_at
 *
 * Sparse and scannable layout for quick reference.
 */
export function InventoryCard({
  tools = [],
  consumables = [],
}: InventoryCardProps) {
  return (
    <div className="space-y-4">
      {/* Tools Section */}
      {tools.length > 0 && (
        <div>
          <h4 className="font-semibold text-sm mb-2">Tools</h4>
          <div className="space-y-2">
            {tools.map((tool) => (
              <div
                key={tool.id}
                className="flex items-center justify-between p-2 bg-muted rounded text-sm"
              >
                <div>
                  <div className="font-medium">{tool.kind}</div>
                  <div className="text-xs text-muted-foreground">
                    {tool.model_year}
                    {tool.battery_family && ` · ${tool.battery_family}`}
                  </div>
                </div>
                {tool.last_serviced_at && (
                  <Badge variant="outline" className="text-xs">
                    {new Date(tool.last_serviced_at).toLocaleDateString()}
                  </Badge>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Consumables Section */}
      {consumables.length > 0 && (
        <div>
          <h4 className="font-semibold text-sm mb-2">Consumables</h4>
          <div className="space-y-2">
            {consumables.map((consumable) => (
              <div
                key={consumable.id}
                className="flex items-center justify-between p-2 bg-muted rounded text-sm"
              >
                <div className="font-medium">{consumable.kind}</div>
                <div className="text-xs">
                  {consumable.quantity} {consumable.unit}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {tools.length === 0 && consumables.length === 0 && (
        <p className="text-sm text-muted-foreground">
          No tools or consumables recorded yet.
        </p>
      )}
    </div>
  );
}
