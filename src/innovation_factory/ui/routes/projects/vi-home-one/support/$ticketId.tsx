import { createFileRoute } from '@tanstack/react-router'
import { Suspense, useState, useEffect, useRef } from 'react'
import { ErrorBoundary } from 'react-error-boundary'
import ReactMarkdown from 'react-markdown'
import {
  Send,
  Bot,
  User as UserIcon,
  Loader2,
  CheckCircle,
  Clock,
} from 'lucide-react'
import {
  useVh_get_ticketSuspense,
  useVh_get_chat_historySuspense,
} from '@/lib/api'
import selector from '@/lib/selector'
import { Card } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Separator } from '@/components/ui/separator'

export const Route = createFileRoute('/projects/vi-home-one/support/$ticketId')({
  component: TicketDetailPage,
})

interface Message {
  id: number
  role: 'user' | 'assistant' | 'system'
  content: string
  created_at: string
}

function TicketDetailPage() {
  const { ticketId } = Route.useParams()

  return (
    <div className="space-y-6">
      <ErrorBoundary
        fallbackRender={({ error, resetErrorBoundary }) => (
          <Card className="p-6">
            <div className="text-center">
              <p className="text-destructive mb-4">Error loading ticket: {error.message}</p>
              <Button onClick={resetErrorBoundary}>Try Again</Button>
            </div>
          </Card>
        )}
      >
        <Suspense fallback={<TicketSkeleton />}>
          <TicketContent ticketId={parseInt(ticketId)} />
        </Suspense>
      </ErrorBoundary>
    </div>
  )
}

function TicketContent({ ticketId }: { ticketId: number }) {
  const { data: ticket } = useVh_get_ticketSuspense({
    params: { ticket_id: ticketId },
    ...selector()
  })
  const { data: chatHistory } = useVh_get_chat_historySuspense({
    params: { ticket_id: ticketId },
    ...selector()
  })

  const [messages, setMessages] = useState<Message[]>(
    chatHistory.messages
      .filter(msg => msg.role !== 'system')
      .map(msg => ({ ...msg, role: msg.role as 'user' | 'assistant' | 'system' })) || []
  )
  const [input, setInput] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingMessage, setStreamingMessage] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const accumulatedMessageRef = useRef('')

  useEffect(() => {
    if (chatHistory) {
      setMessages(
        chatHistory.messages
          .filter(msg => msg.role !== 'system')
          .map(msg => ({ ...msg, role: msg.role as 'user' | 'assistant' | 'system' }))
      )
    }
  }, [chatHistory])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingMessage])

  const handleSendMessage = async () => {
    if (!input.trim() || isStreaming) return

    const userMessage: Message = {
      id: Date.now(),
      role: 'user',
      content: input,
      created_at: new Date().toISOString(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setIsStreaming(true)
    setStreamingMessage('')
    accumulatedMessageRef.current = ''

    try {
      // Use EventSource for SSE streaming
      const eventSource = new EventSource(
        `/api/chat/tickets/${ticketId}/chat?message=${encodeURIComponent(input)}`
      )

      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data)

        if (data.done) {
          // Stream complete - use ref value
          const assistantMessage: Message = {
            id: Date.now(),
            role: 'assistant',
            content: accumulatedMessageRef.current,
            created_at: new Date().toISOString(),
          }
          setMessages((prev) => [...prev, assistantMessage])
          setStreamingMessage('')
          accumulatedMessageRef.current = ''
          setIsStreaming(false)
          eventSource.close()
        } else {
          // Accumulate streaming content in ref
          accumulatedMessageRef.current += (data.content || '')
          setStreamingMessage(accumulatedMessageRef.current)
        }
      }

      eventSource.onerror = () => {
        setIsStreaming(false)
        setStreamingMessage('')
        accumulatedMessageRef.current = ''
        eventSource.close()
      }
    } catch (error) {
      console.error('Chat error:', error)
      setIsStreaming(false)
      setStreamingMessage('')
      accumulatedMessageRef.current = ''
    }
  }

  const getStatusConfig = (status: string) => {
    const configs = {
      open: { icon: Clock, color: 'text-blue-500', bg: 'bg-blue-50 dark:bg-blue-950', label: 'Open' },
      in_progress: { icon: Loader2, color: 'text-amber-500', bg: 'bg-amber-50 dark:bg-amber-950', label: 'In Progress' },
      resolved: { icon: CheckCircle, color: 'text-green-500', bg: 'bg-green-50 dark:bg-green-950', label: 'Resolved' },
      closed: { icon: CheckCircle, color: 'text-gray-500', bg: 'bg-gray-50 dark:bg-gray-950', label: 'Closed' },
    }
    return configs[status as keyof typeof configs] || configs.open
  }

  const statusConfig = getStatusConfig(ticket.status)
  const StatusIcon = statusConfig.icon

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      {/* Ticket Details */}
      <Card className="p-6 lg:col-span-1">
        <div className="space-y-6">
          <div>
            <h2 className="text-2xl font-bold mb-2">{ticket.title}</h2>
            <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full ${statusConfig.bg}`}>
              <StatusIcon className={`h-4 w-4 ${statusConfig.color}`} />
              <span className={`text-sm font-medium ${statusConfig.color}`}>
                {statusConfig.label}
              </span>
            </div>
          </div>

          <Separator />

          <div>
            <h3 className="text-sm font-medium text-muted-foreground mb-2">Description</h3>
            <p className="text-sm">{ticket.description}</p>
          </div>

          <Separator />

          <div>
            <h3 className="text-sm font-medium text-muted-foreground mb-2">Created</h3>
            <p className="text-sm">
              {new Date(ticket.created_at).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
              })}
            </p>
          </div>
        </div>
      </Card>

      {/* Chat Interface */}
      <Card className="p-6 lg:col-span-2 flex flex-col h-[calc(100vh-12rem)]">
        <div className="mb-4">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Bot className="h-5 w-5" />
            AI Assistant
          </h3>
          <p className="text-sm text-muted-foreground">
            Get instant help and troubleshooting guidance
          </p>
        </div>

        <Separator className="mb-4" />

        {/* Messages */}
        <div className="flex-1 overflow-y-auto space-y-4 mb-4">
          {messages.length === 0 && !streamingMessage && (
            <div className="text-center py-12 text-muted-foreground">
              <Bot className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>Start a conversation with the AI assistant</p>
              <p className="text-sm mt-2">Ask questions about your issue or request troubleshooting steps</p>
            </div>
          )}

          {messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))}

          {streamingMessage && (
            <ChatMessage
              message={{
                id: 0,
                role: 'assistant',
                content: streamingMessage,
                created_at: new Date().toISOString(),
              }}
              isStreaming
            />
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="flex gap-2">
          <Input
            placeholder="Type your message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSendMessage()
              }
            }}
            disabled={isStreaming}
          />
          <Button
            onClick={handleSendMessage}
            disabled={!input.trim() || isStreaming}
            className="gap-2"
          >
            {isStreaming ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>
      </Card>
    </div>
  )
}

function ChatMessage({
  message,
  isStreaming = false
}: {
  message: Message
  isStreaming?: boolean
}) {
  // Skip rendering system messages
  if (message.role === 'system') {
    return null
  }

  const isUser = message.role === 'user'

  return (
    <div className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
          <Bot className="h-4 w-4 text-primary" />
        </div>
      )}

      <div className={`max-w-[80%] ${isUser ? 'order-first' : ''}`}>
        <div
          className={`rounded-lg p-3 ${
            isUser
              ? 'bg-primary text-primary-foreground'
              : 'bg-muted'
          }`}
        >
          {isUser ? (
            <p className="text-sm">{message.content}</p>
          ) : (
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <ReactMarkdown>{message.content}</ReactMarkdown>
              {isStreaming && (
                <span className="inline-block w-2 h-4 bg-current animate-pulse ml-1" />
              )}
            </div>
          )}
        </div>
        <p className="text-xs text-muted-foreground mt-1 px-1">
          {new Date(message.created_at).toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </p>
      </div>

      {isUser && (
        <div className="h-8 w-8 rounded-full bg-muted flex items-center justify-center flex-shrink-0">
          <UserIcon className="h-4 w-4" />
        </div>
      )}
    </div>
  )
}

function TicketSkeleton() {
  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <Skeleton className="h-96" />
      <Skeleton className="h-96 lg:col-span-2" />
    </div>
  )
}
