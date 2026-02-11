import { createFileRoute, Link } from '@tanstack/react-router'
import { Suspense } from 'react'
import { ErrorBoundary } from 'react-error-boundary'
import { ArrowRight, Battery, Sun, Zap } from 'lucide-react'
import { useVh_get_neighborhood_summarySuspense } from '@/lib/api'
import selector from '@/lib/selector'
import { Card } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

export const Route = createFileRoute('/projects/vi-home-one/households/')({
  component: HouseholdsPage,
})

function HouseholdsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Households</h1>
        <p className="text-muted-foreground">
          View and manage household energy systems
        </p>
      </div>

      <ErrorBoundary
        fallbackRender={({ error, resetErrorBoundary }) => (
          <Card className="p-6">
            <div className="text-center">
              <p className="text-destructive mb-4">Error loading households: {error.message}</p>
              <Button onClick={resetErrorBoundary}>Try Again</Button>
            </div>
          </Card>
        )}
      >
        <Suspense fallback={<HouseholdsSkeleton />}>
          <HouseholdsContent />
        </Suspense>
      </ErrorBoundary>
    </div>
  )
}

function HouseholdsContent() {
  // Using neighborhood ID 1 (ViDistrictOne)
  const { data: summary } = useVh_get_neighborhood_summarySuspense({
    params: { neighborhood_id: 1 },
    ...selector()
  })

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {summary.households.map((household) => (
        <Link
          key={household.id}
          to="/projects/vi-home-one/households/$householdId"
          params={{ householdId: household.id.toString() }}
          className="block"
        >
          <Card className="p-6 hover:border-primary transition-colors cursor-pointer h-full">
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <h3 className="text-xl font-semibold">{household.owner_name}</h3>
                <p className="text-sm text-muted-foreground line-clamp-1">
                  {household.address}
                </p>
              </div>
              <ArrowRight className="h-5 w-5 text-muted-foreground flex-shrink-0 ml-2" />
            </div>

            <div className="space-y-3">
              {/* Current Metrics */}
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 rounded-lg bg-blue-50 dark:bg-blue-950">
                  <div className="flex items-center gap-2 text-blue-600 dark:text-blue-400 mb-1">
                    <Zap className="h-4 w-4" />
                    <span className="text-xs font-medium">Consumption</span>
                  </div>
                  <p className="text-lg font-bold text-blue-900 dark:text-blue-100">
                    {household.current_consumption_kw.toFixed(2)} kW
                  </p>
                </div>

                <div className="p-3 rounded-lg bg-green-50 dark:bg-green-950">
                  <div className="flex items-center gap-2 text-green-600 dark:text-green-400 mb-1">
                    <Sun className="h-4 w-4" />
                    <span className="text-xs font-medium">Generation</span>
                  </div>
                  <p className="text-lg font-bold text-green-900 dark:text-green-100">
                    {household.current_generation_kw.toFixed(2)} kW
                  </p>
                </div>
              </div>

              {/* Battery Level */}
              <div className="p-3 rounded-lg bg-muted">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Battery className="h-4 w-4" />
                    <span className="text-sm font-medium">Battery</span>
                  </div>
                  <span className="text-sm font-bold">
                    {household.battery_level_percent.toFixed(0)}%
                  </span>
                </div>
                <div className="w-full h-2 bg-secondary rounded-full overflow-hidden">
                  <div
                    className="h-full bg-green-500 transition-all"
                    style={{ width: `${household.battery_level_percent}%` }}
                  />
                </div>
              </div>

              {/* Optimization Mode */}
              <div className="pt-2">
                <Badge
                  variant={
                    household.optimization_mode === 'energy_saver'
                      ? 'default'
                      : 'secondary'
                  }
                  className="w-full justify-center"
                >
                  {household.optimization_mode === 'energy_saver'
                    ? 'Energy Saver Mode'
                    : 'Cost Saver Mode'}
                </Badge>
              </div>
            </div>
          </Card>
        </Link>
      ))}
    </div>
  )
}

function HouseholdsSkeleton() {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {[1, 2, 3, 4, 5].map((i) => (
        <Skeleton key={i} className="h-64" />
      ))}
    </div>
  )
}
