import { createFileRoute } from '@tanstack/react-router'
import { Suspense, useState } from 'react'
import { ErrorBoundary } from 'react-error-boundary'
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { useVh_get_energy_readingsSuspense, useVh_get_householdSuspense } from '@/lib/api'
import selector from '@/lib/selector'
import { Card } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

export const Route = createFileRoute('/projects/vi-home-one/households/$householdId/history')({
  component: EnergyHistoryPage,
})

function EnergyHistoryPage() {
  const { householdId } = Route.useParams()

  return (
    <div className="space-y-6">
      <ErrorBoundary
        fallbackRender={({ error, resetErrorBoundary }) => (
          <Card className="p-6">
            <div className="text-center">
              <p className="text-destructive mb-4">Error loading energy history: {error.message}</p>
              <Button onClick={resetErrorBoundary}>Try Again</Button>
            </div>
          </Card>
        )}
      >
        <Suspense fallback={<HistorySkeleton />}>
          <HistoryContent householdId={parseInt(householdId)} />
        </Suspense>
      </ErrorBoundary>
    </div>
  )
}

function HistoryContent({ householdId }: { householdId: number }) {
  const [timeRange, setTimeRange] = useState<'24h' | '7d' | '30d'>('24h')

  const hours = timeRange === '24h' ? 24 : timeRange === '7d' ? 168 : 720

  const { data: household } = useVh_get_householdSuspense({
    params: { household_id: householdId },
    ...selector()
  })
  const { data: readings } = useVh_get_energy_readingsSuspense({
    params: { household_id: householdId, hours },
    ...selector()
  })

  // Transform data for charts
  const chartData = readings.map((reading, _index) => {
    const timestamp = new Date(reading.timestamp)

    let timeLabel: string
    if (timeRange === '24h') {
      timeLabel = timestamp.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
      })
    } else if (timeRange === '7d') {
      timeLabel = timestamp.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric'
      })
    } else {
      timeLabel = timestamp.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric'
      })
    }

    return {
      time: timeLabel,
      consumption: reading.total_consumption_kwh,
      generation: reading.pv_generation_kwh,
      gridImport: reading.grid_import_kwh,
      gridExport: reading.grid_export_kwh,
      batteryLevel: reading.battery_level_kwh,
      evCharging: reading.ev_consumption_kwh || 0,
      heatPump: reading.heat_pump_consumption_kwh || 0,
      household: reading.household_consumption_kwh || 0,
    }
  }).reverse() // Show chronological order

  // Sample every N points for better chart performance
  const sampleRate = timeRange === '30d' ? 6 : timeRange === '7d' ? 2 : 1
  const sampledData = chartData.filter((_, index) => index % sampleRate === 0)

  // Calculate totals
  const totalConsumption = readings.reduce((sum, r) => sum + r.total_consumption_kwh, 0)
  const totalGeneration = readings.reduce((sum, r) => sum + r.pv_generation_kwh, 0)
  const totalGridImport = readings.reduce((sum, r) => sum + r.grid_import_kwh, 0)
  const selfSufficiency = totalGeneration > 0
    ? ((totalGeneration / totalConsumption) * 100).toFixed(1)
    : '0.0'

  return (
    <>
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold">Energy History</h1>
          <p className="text-muted-foreground">{household.owner_name}'s consumption & generation</p>
        </div>

        <div className="flex gap-2">
          <Button
            variant={timeRange === '24h' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setTimeRange('24h')}
          >
            24 Hours
          </Button>
          <Button
            variant={timeRange === '7d' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setTimeRange('7d')}
          >
            7 Days
          </Button>
          <Button
            variant={timeRange === '30d' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setTimeRange('30d')}
          >
            30 Days
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card className="p-4">
          <p className="text-sm text-muted-foreground">Total Consumption</p>
          <p className="text-2xl font-bold mt-1">{totalConsumption.toFixed(1)} kWh</p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-muted-foreground">Total Generation</p>
          <p className="text-2xl font-bold mt-1 text-green-600">{totalGeneration.toFixed(1)} kWh</p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-muted-foreground">Grid Import</p>
          <p className="text-2xl font-bold mt-1 text-blue-600">{totalGridImport.toFixed(1)} kWh</p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-muted-foreground">Self-Sufficiency</p>
          <p className="text-2xl font-bold mt-1">{selfSufficiency}%</p>
        </Card>
      </div>

      {/* Charts */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="breakdown">Breakdown</TabsTrigger>
          <TabsTrigger value="battery">Battery</TabsTrigger>
          <TabsTrigger value="grid">Grid Flow</TabsTrigger>
        </TabsList>

        {/* Overview Chart */}
        <TabsContent value="overview">
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Consumption vs Generation</h3>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={sampledData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="time"
                  tick={{ fontSize: 12 }}
                  interval={Math.floor(sampledData.length / 8)}
                />
                <YAxis
                  label={{ value: 'kWh', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="consumption"
                  stroke="#3b82f6"
                  name="Consumption"
                  strokeWidth={2}
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="generation"
                  stroke="#10b981"
                  name="Generation"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </TabsContent>

        {/* Breakdown Chart */}
        <TabsContent value="breakdown">
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Consumption Breakdown</h3>
            <ResponsiveContainer width="100%" height={400}>
              <AreaChart data={sampledData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="time"
                  tick={{ fontSize: 12 }}
                  interval={Math.floor(sampledData.length / 8)}
                />
                <YAxis
                  label={{ value: 'kWh', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="household"
                  stackId="1"
                  stroke="#8b5cf6"
                  fill="#8b5cf6"
                  name="Household"
                />
                <Area
                  type="monotone"
                  dataKey="heatPump"
                  stackId="1"
                  stroke="#3b82f6"
                  fill="#3b82f6"
                  name="Heat Pump"
                />
                <Area
                  type="monotone"
                  dataKey="evCharging"
                  stackId="1"
                  stroke="#10b981"
                  fill="#10b981"
                  name="EV Charging"
                />
              </AreaChart>
            </ResponsiveContainer>
          </Card>
        </TabsContent>

        {/* Battery Chart */}
        <TabsContent value="battery">
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Battery Level</h3>
            <ResponsiveContainer width="100%" height={400}>
              <AreaChart data={sampledData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="time"
                  tick={{ fontSize: 12 }}
                  interval={Math.floor(sampledData.length / 8)}
                />
                <YAxis
                  label={{ value: 'kWh', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="batteryLevel"
                  stroke="#10b981"
                  fill="#10b981"
                  name="Battery Level"
                />
              </AreaChart>
            </ResponsiveContainer>
          </Card>
        </TabsContent>

        {/* Grid Flow Chart */}
        <TabsContent value="grid">
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Grid Import/Export</h3>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={sampledData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="time"
                  tick={{ fontSize: 12 }}
                  interval={Math.floor(sampledData.length / 8)}
                />
                <YAxis
                  label={{ value: 'kWh', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip />
                <Legend />
                <Bar
                  dataKey="gridImport"
                  fill="#ef4444"
                  name="Grid Import"
                />
                <Bar
                  dataKey="gridExport"
                  fill="#10b981"
                  name="Grid Export"
                />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </TabsContent>
      </Tabs>
    </>
  )
}

function HistorySkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-20" />
      <div className="grid gap-4 md:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <Skeleton key={i} className="h-24" />
        ))}
      </div>
      <Skeleton className="h-96" />
    </div>
  )
}
