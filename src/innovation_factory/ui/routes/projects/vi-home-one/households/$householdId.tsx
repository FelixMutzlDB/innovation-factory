import { createFileRoute, Link } from '@tanstack/react-router'
import { Suspense, useState } from 'react'
import { ErrorBoundary } from 'react-error-boundary'
import { useQueryClient } from '@tanstack/react-query'
import {
  Battery,
  Home,
  Sun,
  Plug,
  Car,
  Thermometer,
  TrendingDown,
  Settings,
  AlertCircle,
  ArrowRight,
  ChevronRight,
  Activity,
} from 'lucide-react'
import {
  useVh_get_household_cockpitSuspense,
  useVh_update_optimization_mode,
  useVh_get_optimization_suggestionsSuspense,
  useVh_list_maintenance_alertsSuspense,
  vh_get_household_cockpitKey,
  vh_get_neighborhood_summaryKey,
} from '@/lib/api'
import selector from '@/lib/selector'
import { Card } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import {
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
} from 'recharts'

export const Route = createFileRoute('/projects/vi-home-one/households/$householdId')({
  component: HouseholdCockpit,
})

function HouseholdCockpit() {
  const { householdId } = Route.useParams()

  return (
    <div className="space-y-6">
      <ErrorBoundary
        fallbackRender={({ error, resetErrorBoundary }) => (
          <Card className="p-6">
            <div className="text-center">
              <p className="text-destructive mb-4">Error loading household data: {error.message}</p>
              <Button onClick={resetErrorBoundary}>Try Again</Button>
            </div>
          </Card>
        )}
      >
        <Suspense fallback={<CockpitSkeleton />}>
          <CockpitContent householdId={parseInt(householdId)} />
        </Suspense>
      </ErrorBoundary>
    </div>
  )
}

function CockpitContent({ householdId }: { householdId: number }) {
  const queryClient = useQueryClient()
  const { data: cockpit } = useVh_get_household_cockpitSuspense({
    params: { household_id: householdId },
    ...selector()
  })
  const { data: suggestions } = useVh_get_optimization_suggestionsSuspense({
    params: { household_id: householdId },
    ...selector()
  })
  const { data: alerts } = useVh_list_maintenance_alertsSuspense({
    params: { household_id: householdId },
    ...selector()
  })
  const updateMode = useVh_update_optimization_mode()

  const [isTogglingMode, setIsTogglingMode] = useState(false)

  const household = cockpit.household
  const currentMode = household.optimization_mode

  // Get battery level from most recent reading
  const latestReading = cockpit.recent_readings?.[0]
  const batteryDevice = cockpit.devices.find(d => d.device_type === 'battery')
  const batteryCapacityKwh = batteryDevice?.capacity_kw || 10 // Default to 10 kWh if not found
  const batteryLevelKwh = latestReading?.battery_level_kwh || 0
  const batteryLevelPercent = batteryCapacityKwh > 0 ? (batteryLevelKwh / batteryCapacityKwh) * 100 : 0

  const handleToggleMode = async () => {
    setIsTogglingMode(true)
    try {
      const newMode = currentMode === 'energy_saver' ? 'cost_saver' : 'energy_saver'
      await updateMode.mutateAsync({
        params: { household_id: householdId },
        data: { optimization_mode: newMode },
      })

      // Invalidate related queries to refresh data
      queryClient.invalidateQueries({ queryKey: vh_get_household_cockpitKey({ household_id: householdId }) })
      queryClient.invalidateQueries({ queryKey: vh_get_neighborhood_summaryKey({ neighborhood_id: 1 }) })
    } catch (error) {
      console.error('Failed to update optimization mode:', error)
    } finally {
      setIsTogglingMode(false)
    }
  }

  // Prepare data for consumption breakdown pie chart
  const consumptionData = cockpit.consumption_breakdown.map((item, index) => ({
    name: item.category.replace('_', ' '),
    value: item.value_kwh,
    percentage: item.percentage,
    color: [
      '#3b82f6', // blue
      '#10b981', // green
      '#f59e0b', // amber
      '#ef4444', // red
      '#8b5cf6', // purple
      '#ec4899', // pink
    ][index % 6],
  }))

  const activeAlerts = alerts?.filter(a => !a.is_acknowledged) || []

  return (
    <>
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
            <Link to="/projects/vi-home-one/neighborhood" className="hover:text-foreground">
              Neighborhood
            </Link>
            <ChevronRight className="h-4 w-4" />
            <span>Household Cockpit</span>
          </div>
          <h1 className="text-3xl font-bold">{household.owner_name}'s Home</h1>
          <p className="text-muted-foreground">{household.address}</p>
        </div>
        <Button
          onClick={handleToggleMode}
          disabled={isTogglingMode}
          variant={currentMode === 'energy_saver' ? 'default' : 'secondary'}
          className="gap-2"
        >
          <Settings className="h-4 w-4" />
          {currentMode === 'energy_saver' ? 'Energy Saver' : 'Cost Saver'}
        </Button>
      </div>

      {/* Active Alerts */}
      {activeAlerts.length > 0 && (
        <Card className="p-4 border-amber-500 bg-amber-50 dark:bg-amber-950">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-amber-600 dark:text-amber-400 mt-0.5" />
            <div className="flex-1">
              <h3 className="font-semibold text-amber-900 dark:text-amber-100">
                {activeAlerts.length} Maintenance {activeAlerts.length === 1 ? 'Alert' : 'Alerts'}
              </h3>
              <div className="space-y-1 mt-2">
                {activeAlerts.slice(0, 2).map((alert) => (
                  <p key={alert.id} className="text-sm text-amber-800 dark:text-amber-200">
                    • {alert.message}
                  </p>
                ))}
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Current Energy Flow */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-6">Current Energy Flow</h2>

        <div className="flex items-center justify-center gap-6 flex-wrap">
          {/* Solar Generation */}
          {household.has_pv && (
            <>
              <EnergyFlowNode
                icon={<Sun className="h-8 w-8" />}
                label="Solar"
                value={cockpit.energy_sources.pv_generation_kw.toFixed(2)}
                unit="kW"
                color="amber"
                isActive={cockpit.energy_sources.pv_generation_kw > 0}
              />
              <ArrowRight className="h-6 w-6 text-muted-foreground" />
            </>
          )}

          {/* Battery */}
          {household.has_battery && (
            <>
              <EnergyFlowNode
                icon={<Battery className="h-8 w-8" />}
                label="Battery"
                value={
                  cockpit.energy_sources.battery_discharge_kw > 0
                    ? `↓ ${cockpit.energy_sources.battery_discharge_kw.toFixed(2)}`
                    : '0.00'
                }
                unit="kW"
                color="green"
                isActive={cockpit.energy_sources.battery_discharge_kw > 0}
                subtitle={`${batteryLevelPercent.toFixed(0)}%`}
              />
              <ArrowRight className="h-6 w-6 text-muted-foreground" />
            </>
          )}

          {/* Home Consumption */}
          <EnergyFlowNode
            icon={<Home className="h-8 w-8" />}
            label="Home"
            value={cockpit.current_consumption_kw.toFixed(2)}
            unit="kW"
            color="blue"
            isActive={true}
          />

          {/* Grid */}
          <ArrowRight className="h-6 w-6 text-muted-foreground" />
          <EnergyFlowNode
            icon={<Plug className="h-8 w-8" />}
            label="Grid"
            value={
              cockpit.energy_sources.grid_import_kw > 0
                ? `← ${cockpit.energy_sources.grid_import_kw.toFixed(2)}`
                : '0.00'
            }
            unit="kW"
            color={cockpit.energy_sources.grid_import_kw > 0 ? 'red' : 'green'}
            isActive={cockpit.energy_sources.grid_import_kw > 0}
          />
        </div>
      </Card>

      {/* Consumption Breakdown & Cost */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Consumption Breakdown */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Consumption Breakdown</h3>

          {consumptionData.length > 0 ? (
            <div className="flex items-center gap-6">
              <div className="flex-1">
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie
                      data={consumptionData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={2}
                      dataKey="value"
                    >
                      {consumptionData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
              </div>

              <div className="space-y-2">
                {consumptionData.map((item) => (
                  <div key={item.name} className="flex items-center gap-2 text-sm">
                    <div
                      className="h-3 w-3 rounded-full"
                      style={{ backgroundColor: item.color }}
                    />
                    <span className="capitalize">{item.name}</span>
                    <span className="text-muted-foreground ml-auto">
                      {item.percentage.toFixed(1)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-center text-muted-foreground py-8">No consumption data</p>
          )}
        </Card>

        {/* Cost Summary */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Cost Summary</h3>

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Today's Cost</span>
              <span className="text-2xl font-bold">
                €{cockpit.cost_today_eur.toFixed(2)}
              </span>
            </div>

            <Separator />

            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">This Month</span>
              <span className="text-xl font-semibold">
                €{cockpit.cost_this_month_eur.toFixed(2)}
              </span>
            </div>
          </div>
        </Card>
      </div>

      {/* Devices & Optimization */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Connected Devices */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Connected Devices</h3>

          <div className="space-y-3">
            {household.has_heat_pump && (
              <DeviceCard
                icon={<Thermometer className="h-5 w-5" />}
                name="Heat Pump"
                status="Active"
                color="blue"
              />
            )}
            {household.has_pv && (
              <DeviceCard
                icon={<Sun className="h-5 w-5" />}
                name="Solar Panels"
                status={cockpit.energy_sources.pv_generation_kw > 0 ? 'Generating' : 'Idle'}
                color="amber"
              />
            )}
            {household.has_battery && (
              <DeviceCard
                icon={<Battery className="h-5 w-5" />}
                name="Battery Storage"
                status={`${batteryLevelPercent.toFixed(0)}% Charged`}
                color="green"
              />
            )}
            {household.has_ev && (
              <DeviceCard
                icon={<Car className="h-5 w-5" />}
                name="Electric Vehicle"
                status="Connected"
                color="purple"
              />
            )}
          </div>
        </Card>

        {/* Optimization Suggestions */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">
            Optimization Suggestions
          </h3>

          {suggestions && suggestions.length > 0 ? (
            <div className="space-y-3">
              {suggestions.map((suggestion) => (
                <div
                  key={suggestion.id}
                  className="p-3 rounded-lg border bg-muted/50"
                >
                  <div className="flex items-start gap-2">
                    <Activity className="h-4 w-4 text-primary mt-0.5" />
                    <div className="flex-1 text-sm">
                      <p className="font-medium">{suggestion.title}</p>
                      <p className="text-muted-foreground mt-1">
                        {suggestion.description}
                      </p>
                      {suggestion.potential_savings_eur && suggestion.potential_savings_eur > 0 && (
                        <p className="text-green-600 dark:text-green-400 mt-2 flex items-center gap-1">
                          <TrendingDown className="h-3 w-3" />
                          Save €{suggestion.potential_savings_eur.toFixed(2)}/day
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-center text-muted-foreground py-8">
              No suggestions at this time
            </p>
          )}
        </Card>
      </div>
    </>
  )
}

function EnergyFlowNode({
  icon,
  label,
  value,
  unit,
  color,
  isActive,
  subtitle,
}: {
  icon: React.ReactNode
  label: string
  value: string
  unit: string
  color: string
  isActive: boolean
  subtitle?: string
}) {
  const colorClasses = {
    amber: 'bg-amber-500/10 text-amber-500 border-amber-500/20',
    green: 'bg-green-500/10 text-green-500 border-green-500/20',
    blue: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
    red: 'bg-red-500/10 text-red-500 border-red-500/20',
    purple: 'bg-purple-500/10 text-purple-500 border-purple-500/20',
  }

  return (
    <div className="flex flex-col items-center gap-2">
      <div
        className={`h-20 w-20 rounded-full flex items-center justify-center border-2 ${
          isActive ? colorClasses[color as keyof typeof colorClasses] : 'bg-muted text-muted-foreground border-muted'
        }`}
      >
        {icon}
      </div>
      <div className="text-center">
        <p className="text-sm font-medium">{label}</p>
        <p className="text-lg font-bold">
          {value} <span className="text-sm text-muted-foreground">{unit}</span>
        </p>
        {subtitle && <p className="text-xs text-muted-foreground">{subtitle}</p>}
      </div>
    </div>
  )
}

function DeviceCard({
  icon,
  name,
  status,
  color,
}: {
  icon: React.ReactNode
  name: string
  status: string
  color: string
}) {
  const colorClasses = {
    amber: 'text-amber-500',
    green: 'text-green-500',
    blue: 'text-blue-500',
    purple: 'text-purple-500',
  }

  return (
    <div className="flex items-center gap-3 p-3 rounded-lg border">
      <div className={colorClasses[color as keyof typeof colorClasses]}>
        {icon}
      </div>
      <div className="flex-1">
        <p className="font-medium">{name}</p>
        <p className="text-sm text-muted-foreground">{status}</p>
      </div>
    </div>
  )
}

function CockpitSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-20" />
      <Skeleton className="h-64" />
      <div className="grid gap-6 md:grid-cols-2">
        <Skeleton className="h-64" />
        <Skeleton className="h-64" />
      </div>
    </div>
  )
}
