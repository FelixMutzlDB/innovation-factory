import { createFileRoute } from "@tanstack/react-router";
import { Suspense, useState } from "react";
import { ErrorBoundary } from "react-error-boundary";
import { QueryErrorResetBoundary } from "@tanstack/react-query";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export const Route = createFileRoute("/projects/yard-pro/coach")({
  component: () => <CoachPage />,
});

function CoachPage() {
  const [sessions] = useState<Array<{ id: number; title: string; date: string }>>([
    { id: 1, title: "Weekend plans", date: "May 10, 2026" },
    { id: 2, title: "Plant care calendar", date: "May 8, 2026" },
  ]);
  const [activeSessionId, setActiveSessionId] = useState(1);

  return (
    <div className="flex h-[calc(100vh-4rem)] gap-4 p-6">
      {/* Session List */}
      <div className="w-64 flex flex-col">
        <Card className="flex-1 flex flex-col">
          <CardHeader>
            <CardTitle>Sessions</CardTitle>
            <CardDescription>Chat history</CardDescription>
          </CardHeader>
          <CardContent className="flex-1 overflow-hidden">
            <QueryErrorResetBoundary>
              {({ reset }) => (
                <ErrorBoundary
                  onReset={reset}
                  fallbackRender={({ resetErrorBoundary }) => (
                    <div className="text-destructive text-sm p-2">
                      <p>Failed to load sessions</p>
                      <Button
                        size="sm"
                        onClick={resetErrorBoundary}
                        className="mt-2"
                      >
                        Retry
                      </Button>
                    </div>
                  )}
                >
                  <Suspense
                    fallback={
                      <div className="space-y-2">
                        {[...Array(3)].map((_, i) => (
                          <Skeleton key={i} className="h-12 w-full" />
                        ))}
                      </div>
                    }
                  >
                    <div className="h-full overflow-auto">
                      <div className="space-y-2">
                        {sessions.map((session) => (
                          <button
                            key={session.id}
                            onClick={() => setActiveSessionId(session.id)}
                            className={`w-full text-left p-2 rounded-lg text-sm ${
                              activeSessionId === session.id
                                ? "bg-primary text-primary-foreground"
                                : "bg-muted hover:bg-muted"
                            }`}
                          >
                            <div className="font-medium truncate">
                              {session.title}
                            </div>
                            <div className="text-xs opacity-70">
                              {session.date}
                            </div>
                          </button>
                        ))}
                      </div>
                    </div>
                  </Suspense>
                </ErrorBoundary>
              )}
            </QueryErrorResetBoundary>
          </CardContent>
        </Card>
        <Button className="mt-4 w-full" variant="outline">
          New Session
        </Button>
      </div>

      {/* Chat Panel */}
      <div className="flex-1 flex flex-col">
        <Card className="flex-1 flex flex-col">
          <CardHeader>
            <CardTitle>Seasonal Coach</CardTitle>
            <CardDescription>
              Personalized care recommendations based on your yard
            </CardDescription>
          </CardHeader>
          <CardContent className="flex-1 overflow-hidden flex flex-col">
            <QueryErrorResetBoundary>
              {({ reset }) => (
                <ErrorBoundary
                  onReset={reset}
                  fallbackRender={({ resetErrorBoundary }) => (
                    <div className="text-destructive text-sm p-2">
                      <p>Failed to load chat</p>
                      <Button
                        size="sm"
                        onClick={resetErrorBoundary}
                        className="mt-2"
                      >
                        Retry
                      </Button>
                    </div>
                  )}
                >
                  <Suspense
                    fallback={
                      <div className="space-y-4 flex-1">
                        {[...Array(3)].map((_, i) => (
                          <Skeleton key={i} className="h-12 w-2/3" />
                        ))}
                      </div>
                    }
                  >
                    <ChatMessages sessionId={activeSessionId} />
                  </Suspense>
                </ErrorBoundary>
              )}
            </QueryErrorResetBoundary>

            {/* Input Area */}
            <div className="mt-4 pt-4 border-t flex gap-2">
              <Input placeholder="Ask the coach..." />
              <Button>Send</Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function ChatMessages(_: { sessionId: number }) {
  const messages = [
    {
      role: "user",
      content: "What should I do this weekend?",
    },
    {
      role: "assistant",
      content:
        "Based on your yard and the local weather forecast, I recommend: (1) Prune the apple tree before the fruit sets — the window closes May 25th. (2) Apply fungicide for the leaf-spot issue if you haven't already. (3) Check the robotic mower's battery level. AI-generated, advisory only",
    },
  ];

  return (
    <div className="flex-1 overflow-auto">
      <div className="space-y-4">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${
              msg.role === "user" ? "justify-end" : "justify-start"
            }`}
          >
            <div
              className={`max-w-xs p-3 rounded-lg text-sm ${
                msg.role === "user"
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-muted-foreground"
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
