import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { Suspense } from 'react'
import { ErrorBoundary } from 'react-error-boundary'
import {
  Plus,
  Ticket as TicketIcon,
  Clock,
  CheckCircle,
  XCircle,
  MessageCircle,
} from 'lucide-react'
import { useVh_list_ticketsSuspense, useVh_get_neighborhood_summarySuspense } from '@/lib/api'
import selector from '@/lib/selector'
import { Card } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

export const Route = createFileRoute('/projects/vi-home-one/support/')({
  component: SupportPage,
})

function SupportPage() {
  const navigate = useNavigate()

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold">Support</h1>
          <p className="text-muted-foreground">
            Create tickets and get help with your energy system
          </p>
        </div>
        <Button
          onClick={() => navigate({ to: '/projects/vi-home-one/support/new' })}
          className="gap-2"
        >
          <Plus className="h-4 w-4" />
          Create Ticket
        </Button>
      </div>

      <ErrorBoundary
        fallbackRender={({ error, resetErrorBoundary }) => (
          <Card className="p-6">
            <div className="text-center">
              <p className="text-destructive mb-4">Error loading tickets: {error.message}</p>
              <Button onClick={resetErrorBoundary}>Try Again</Button>
            </div>
          </Card>
        )}
      >
        <Suspense fallback={<TicketsSkeleton />}>
          <TicketsContent />
        </Suspense>
      </ErrorBoundary>
    </div>
  )
}

function TicketsContent() {
  // Get first household for demo (in a real app, would get current user's household)
  const { data: summary } = useVh_get_neighborhood_summarySuspense({
    params: { neighborhood_id: 1 },
    ...selector()
  })
  const householdId = summary.households[0]?.id || 1

  const { data: tickets } = useVh_list_ticketsSuspense({
    params: { household_id: householdId },
    ...selector()
  })

  if (tickets.length === 0) {
    return (
      <Card className="p-12">
        <div className="text-center">
          <TicketIcon className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">No support tickets</h3>
          <p className="text-muted-foreground mb-4">
            Create a ticket to get help with your energy system
          </p>
          <Button asChild>
            <Link to="/projects/vi-home-one/support/new">
              <Plus className="h-4 w-4 mr-2" />
              Create Ticket
            </Link>
          </Button>
        </div>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      {tickets.map((ticket) => (
        <Link
          key={ticket.id}
          to="/projects/vi-home-one/support/$ticketId"
          params={{ ticketId: ticket.id.toString() }}
        >
          <Card className="p-6 hover:border-primary transition-colors cursor-pointer">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <h3 className="text-lg font-semibold">{ticket.title}</h3>
                  <TicketStatusBadge status={ticket.status} />
                </div>
                <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
                  {ticket.description}
                </p>
                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                  <div className="flex items-center gap-1">
                    <Clock className="h-4 w-4" />
                    {new Date(ticket.created_at).toLocaleDateString()}
                  </div>
                </div>
              </div>
              <MessageCircle className="h-5 w-5 text-muted-foreground ml-4" />
            </div>
          </Card>
        </Link>
      ))}
    </div>
  )
}

function TicketStatusBadge({ status }: { status: string }) {
  const config = {
    open: { icon: Clock, variant: 'default' as const, label: 'Open' },
    in_progress: { icon: Clock, variant: 'secondary' as const, label: 'In Progress' },
    resolved: { icon: CheckCircle, variant: 'outline' as const, label: 'Resolved' },
    closed: { icon: XCircle, variant: 'outline' as const, label: 'Closed' },
  }

  const { icon: Icon, variant, label } = config[status as keyof typeof config] || config.open

  return (
    <Badge variant={variant} className="gap-1">
      <Icon className="h-3 w-3" />
      {label}
    </Badge>
  )
}

function TicketsSkeleton() {
  return (
    <div className="space-y-4">
      {[1, 2, 3].map((i) => (
        <Skeleton key={i} className="h-32" />
      ))}
    </div>
  )
}
