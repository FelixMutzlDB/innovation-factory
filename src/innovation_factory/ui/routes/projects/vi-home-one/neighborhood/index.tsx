import { createFileRoute, Link } from '@tanstack/react-router'
import { Suspense } from 'react'
import { ErrorBoundary } from 'react-error-boundary'
import {
  Zap,
  Battery,
  Home,
  ArrowRight,
  Sun,
  Plug
} from 'lucide-react'
import { useVh_get_neighborhood_summarySuspense } from '@/lib/api'
import selector from '@/lib/selector'
import { Card } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

export const Route = createFileRoute('/projects/vi-home-one/neighborhood/')({
  component: NeighborhoodDashboard,
})

function NeighborhoodDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">ViDistrictOne</h1>
        <p className="text-muted-foreground">
          Neighborhood Energy Management System
        </p>
      </div>

      <ErrorBoundary
        fallbackRender={({ error, resetErrorBoundary }) => (
          <Card className="p-6">
            <div className="text-center">
              <p className="text-destructive mb-4">Error loading neighborhood data: {error.message}</p>
              <Button onClick={resetErrorBoundary}>Try Again</Button>
            </div>
          </Card>
        )}
      >
        <Suspense fallback={<DashboardSkeleton />}>
          <DashboardContent />
        </Suspense>
      </ErrorBoundary>
    </div>
  )
}

function DashboardContent() {
  // Using neighborhood ID 1 (ViDistrictOne)
  const { data: summary } = useVh_get_neighborhood_summarySuspense({
    params: { neighborhood_id: 1 },
    ...selector()
  })

  return (
    <>
      {/* Energy Metrics Cards */}
      <div className="grid gap-6 md:grid-cols-3">
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">
                Total Consumption
              </p>
              <h3 className="text-3xl font-bold mt-2">
                {summary.total_consumption_kwh.toFixed(1)} kWh
              </h3>
              <p className="text-xs text-muted-foreground mt-1">Last 24 hours</p>
            </div>
            <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
              <Zap className="h-6 w-6 text-primary" />
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">
                Total Generation
              </p>
              <h3 className="text-3xl font-bold mt-2">
                {summary.total_generation_kwh.toFixed(1)} kWh
              </h3>
              <p className="text-xs text-muted-foreground mt-1">Solar production</p>
            </div>
            <div className="h-12 w-12 rounded-full bg-amber-500/10 flex items-center justify-center">
              <Sun className="h-6 w-6 text-amber-500" />
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">
                Total Storage
              </p>
              <h3 className="text-3xl font-bold mt-2">
                {summary.total_storage_capacity_kwh.toFixed(1)} kWh
              </h3>
              <p className="text-xs text-muted-foreground mt-1">Battery capacity</p>
            </div>
            <div className="h-12 w-12 rounded-full bg-green-500/10 flex items-center justify-center">
              <Battery className="h-6 w-6 text-green-500" />
            </div>
          </div>
        </Card>
      </div>

      {/* Neighborhood Overview */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-semibold">{summary.name}</h2>
            <p className="text-sm text-muted-foreground">{summary.location}</p>
          </div>
          <Badge variant="secondary" className="text-sm">
            <Home className="h-3 w-3 mr-1" />
            {summary.total_households} Households
          </Badge>
        </div>

        {/* Household Grid */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-muted-foreground">Households</h3>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {summary.households.map((household) => (
              <Link
                key={household.id}
                to="/projects/vi-home-one/households/$householdId"
                params={{ householdId: household.id.toString() }}
                className="block"
              >
                <Card className="p-4 hover:border-primary transition-colors cursor-pointer">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h4 className="font-semibold">{household.owner_name}</h4>
                      <p className="text-xs text-muted-foreground line-clamp-1">
                        {household.address}
                      </p>
                    </div>
                    <ArrowRight className="h-4 w-4 text-muted-foreground" />
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Consumption</span>
                      <span className="font-medium">
                        {household.current_consumption_kw.toFixed(2)} kW
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Generation</span>
                      <span className="font-medium text-green-600">
                        {household.current_generation_kw.toFixed(2)} kW
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Battery</span>
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-2 bg-secondary rounded-full overflow-hidden">
                          <div
                            className="h-full bg-green-500 transition-all"
                            style={{ width: `${household.battery_level_percent}%` }}
                          />
                        </div>
                        <span className="font-medium text-xs">
                          {household.battery_level_percent.toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="mt-3 pt-3 border-t">
                    <Badge
                      variant={
                        household.optimization_mode === 'energy_saver'
                          ? 'default'
                          : 'secondary'
                      }
                      className="text-xs"
                    >
                      {household.optimization_mode === 'energy_saver'
                        ? 'Energy Saver'
                        : 'Cost Saver'}
                    </Badge>
                  </div>
                </Card>
              </Link>
            ))}
          </div>
        </div>
      </Card>

      {/* Energy Flow Visualization */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Neighborhood Energy Balance</h3>
        <div className="flex items-center justify-center gap-8 py-8">
          <div className="text-center">
            <div className="h-16 w-16 rounded-full bg-amber-500/10 flex items-center justify-center mb-2 mx-auto">
              <Sun className="h-8 w-8 text-amber-500" />
            </div>
            <p className="text-sm font-medium">Solar</p>
            <p className="text-2xl font-bold text-green-600">
              {summary.total_generation_kwh.toFixed(0)}
            </p>
            <p className="text-xs text-muted-foreground">kWh/24h</p>
          </div>

          <ArrowRight className="h-8 w-8 text-muted-foreground" />

          <div className="text-center">
            <div className="h-16 w-16 rounded-full bg-green-500/10 flex items-center justify-center mb-2 mx-auto">
              <Battery className="h-8 w-8 text-green-500" />
            </div>
            <p className="text-sm font-medium">Storage</p>
            <p className="text-2xl font-bold">
              {summary.total_storage_capacity_kwh.toFixed(0)}
            </p>
            <p className="text-xs text-muted-foreground">kWh capacity</p>
          </div>

          <ArrowRight className="h-8 w-8 text-muted-foreground" />

          <div className="text-center">
            <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center mb-2 mx-auto">
              <Home className="h-8 w-8 text-primary" />
            </div>
            <p className="text-sm font-medium">Consumption</p>
            <p className="text-2xl font-bold text-primary">
              {summary.total_consumption_kwh.toFixed(0)}
            </p>
            <p className="text-xs text-muted-foreground">kWh/24h</p>
          </div>

          <ArrowRight className="h-8 w-8 text-muted-foreground" />

          <div className="text-center">
            <div className="h-16 w-16 rounded-full bg-blue-500/10 flex items-center justify-center mb-2 mx-auto">
              <Plug className="h-8 w-8 text-blue-500" />
            </div>
            <p className="text-sm font-medium">Grid</p>
            <p className="text-2xl font-bold">
              {(summary.total_consumption_kwh - summary.total_generation_kwh).toFixed(0)}
            </p>
            <p className="text-xs text-muted-foreground">kWh import</p>
          </div>
        </div>
      </Card>
    </>
  )
}

function DashboardSkeleton() {
  return (
    <>
      <div className="grid gap-6 md:grid-cols-3">
        {[1, 2, 3].map((i) => (
          <Card key={i} className="p-6">
            <Skeleton className="h-24" />
          </Card>
        ))}
      </div>
      <Card className="p-6">
        <Skeleton className="h-64" />
      </Card>
    </>
  )
}
