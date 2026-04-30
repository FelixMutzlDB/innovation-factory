import { CheckCircle2, Circle, CircleDot } from "lucide-react";
import { cn } from "@/lib/utils";

const PHASES = [
  { key: "design", label: "Design", color: "text-blue-600" },
  { key: "build", label: "Build", color: "text-orange-600" },
  { key: "operate", label: "Operate", color: "text-green-600" },
  { key: "demolish", label: "Demolish", color: "text-red-600" },
];

const PHASE_ORDER: Record<string, number> = {
  design: 0,
  build: 1,
  operate: 2,
  demolish: 3,
};

export function PhaseStepper({
  currentPhase,
}: {
  currentPhase: string;
}) {
  const currentIndex = PHASE_ORDER[currentPhase] ?? 0;

  return (
    <div className="flex items-stretch gap-0">
      {PHASES.map((phase, i) => {
        const isCompleted = i < currentIndex;
        const isCurrent = i === currentIndex;
        const isFuture = i > currentIndex;
        return (
          <div key={phase.key} className="flex-1 flex items-center gap-2 min-w-0">
            <div
              className={cn(
                "flex items-center gap-2 px-3 py-2 rounded-md min-w-0",
                isCompleted && "bg-muted/40",
                isCurrent && "bg-amber-500/10 border border-amber-500/30",
              )}
            >
              {isCompleted && (
                <CheckCircle2 size={14} className="text-green-600 flex-shrink-0" />
              )}
              {isCurrent && (
                <CircleDot size={14} className={cn("flex-shrink-0", phase.color)} />
              )}
              {isFuture && (
                <Circle size={14} className="text-muted-foreground/40 flex-shrink-0" />
              )}
              <span
                className={cn(
                  "text-xs font-medium truncate",
                  isFuture && "text-muted-foreground/60",
                  isCurrent && phase.color,
                )}
              >
                {phase.label}
              </span>
            </div>
            {i < PHASES.length - 1 && (
              <div
                className={cn(
                  "h-px flex-1",
                  i < currentIndex ? "bg-green-600/30" : "bg-muted-foreground/20",
                )}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
