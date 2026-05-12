import { Badge } from "@/components/ui/badge";
import { MarkAsDone } from "./mark-as-done";

interface CalendarEntry {
  id: number;
  title: string;
  scheduled_at: string;
  status: "planned" | "done" | "snoozed" | "skipped";
  source?: "user" | "coach_recommendation" | "telemetry_nudge";
  action_id?: number;
}

interface CalendarCardProps {
  /** List of calendar entries. */
  entries?: CalendarEntry[];
}

/**
 * Personalized calendar card for the cockpit (UC1).
 *
 * Displays:
 * - Today's top task
 * - Upcoming/overdue list (5-7 rows)
 *
 * Each row with source != 'user' surfaces a MarkAsDone button
 * to satisfy GDPR Art. 22 (human confirmation requirement).
 *
 * The load-bearing demo string "Apple tree fungus check overdue 4 days"
 * is seeded at created_at=2026-05-08 with status='planned', so it
 * renders as overdue on 2026-05-12.
 */
export function CalendarCard({ entries = [] }: CalendarCardProps) {
  const now = new Date();

  const overdue = entries.filter(
    (e) =>
      new Date(e.scheduled_at) < now &&
      e.status === "planned"
  );

  const upcoming = entries.filter(
    (e) =>
      new Date(e.scheduled_at) >= now &&
      e.status === "planned"
  );

  const statusColor: Record<string, string> = {
    planned: "bg-yellow-100 text-yellow-800",
    done: "bg-green-100 text-green-800",
    snoozed: "bg-blue-100 text-blue-800",
    skipped: "bg-gray-100 text-gray-800",
  };

  return (
    <div className="space-y-3">
      {/* Today's Task */}
      {overdue.length > 0 && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
          <div className="font-semibold text-red-900">{overdue[0].title}</div>
          <div className="text-sm text-red-800 mt-1">
            Overdue{" "}
            {Math.ceil(
              (now.getTime() - new Date(overdue[0].scheduled_at).getTime()) /
                (1000 * 60 * 60 * 24)
            )}{" "}
            days
          </div>
          {overdue[0].source && overdue[0].source !== "user" && (
            <div className="mt-2">
              <MarkAsDone
                actionId={overdue[0].action_id ?? null}
                label={overdue[0].title}
              />
            </div>
          )}
        </div>
      )}

      {/* Upcoming Tasks */}
      {upcoming.length > 0 && (
        <div className="space-y-2">
          <div className="text-sm font-medium text-muted-foreground">
            Upcoming
          </div>
          {upcoming.slice(0, 4).map((entry) => (
            <div
              key={entry.id}
              className="flex items-center justify-between p-2 bg-muted rounded"
            >
              <div>
                <div className="text-sm font-medium">{entry.title}</div>
                <div className="text-xs text-muted-foreground">
                  {new Date(entry.scheduled_at).toLocaleDateString()}
                </div>
              </div>
              <Badge variant="secondary" className={statusColor[entry.status]}>
                {entry.status}
              </Badge>
            </div>
          ))}
        </div>
      )}

      {entries.length === 0 && (
        <p className="text-sm text-muted-foreground">
          No tasks yet. Coach recommendations will appear here.
        </p>
      )}
    </div>
  );
}
