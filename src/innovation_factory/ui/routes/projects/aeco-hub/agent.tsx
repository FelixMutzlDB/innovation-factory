import { createFileRoute } from "@tanstack/react-router";
import { Suspense, useState, useRef, useEffect } from "react";
import { ErrorBoundary } from "react-error-boundary";
import { QueryErrorResetBoundary } from "@tanstack/react-query";
import { useAeco_getDatabricksResourcesSuspense } from "@/lib/api";
import { selector } from "@/lib/selector";
import SafeMarkdown from "@/components/safe-markdown";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Send, Bot, User as UserIcon, Loader2, Info } from "lucide-react";

export const Route = createFileRoute("/projects/aeco-hub/agent")({
  component: () => <AgentPage />,
});

interface ChatMessage {
  id: number;
  role: "user" | "assistant";
  content: string;
}

const SAMPLE_PROMPTS = [
  "Which projects are behind schedule?",
  "What's the average energy consumption per building?",
  "List overdue maintenance orders by priority",
  "What does COBie require for the operate phase hand-off?",
  "Compare cost overruns across projects",
];

function AgentPage() {
  return (
    <div className="p-6 h-[calc(100vh-2rem)] flex flex-col gap-4">
      <div>
        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
          <Bot className="text-amber-500" size={28} />
          AECO Hub Supervisor
        </h1>
        <p className="text-muted-foreground mt-1 max-w-3xl">
          Ask anything about the portfolio. The supervisor routes to the
          Project Analytics Genie, the Operations Intelligence Genie, or the
          Standards & Compliance Knowledge Assistant depending on the question.
        </p>
      </div>

      <QueryErrorResetBoundary>
        {({ reset }) => (
          <ErrorBoundary
            onReset={reset}
            fallbackRender={() => (
              <Card>
                <CardContent className="p-6 text-destructive">Failed to load.</CardContent>
              </Card>
            )}
          >
            <Suspense fallback={<Skeleton className="flex-1 w-full" />}>
              <AgentChat />
            </Suspense>
          </ErrorBoundary>
        )}
      </QueryErrorResetBoundary>
    </div>
  );
}

function AgentChat() {
  const { data: resources } = useAeco_getDatabricksResourcesSuspense(selector());
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async (prompt?: string) => {
    const text = (prompt ?? input).trim();
    if (!text || isStreaming) return;
    setInput("");
    setIsStreaming(true);

    const userMsg: ChatMessage = { id: Date.now(), role: "user", content: text };
    setMessages((m) => [...m, userMsg]);

    try {
      const r = await fetch("/api/projects/aeco-hub/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, session_id: sessionId }),
      });
      if (!r.ok || !r.body) throw new Error(`status ${r.status}`);

      const reader = r.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let assistantContent = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";
        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const payload = line.slice(6).trim();
          if (!payload || payload === "[DONE]") continue;
          try {
            const parsed = JSON.parse(payload);
            if (parsed.session_id && sessionId === null) setSessionId(parsed.session_id);
            if (parsed.content) assistantContent = parsed.content;
            if (parsed.done) break;
          } catch {
            // ignore malformed chunks
          }
        }
      }

      const assistantMsg: ChatMessage = {
        id: Date.now() + 1,
        role: "assistant",
        content: assistantContent || "(no response)",
      };
      setMessages((m) => [...m, assistantMsg]);
    } catch (e) {
      setMessages((m) => [
        ...m,
        {
          id: Date.now() + 1,
          role: "assistant",
          content:
            "Sorry — the supervisor is unreachable. The MAS endpoint may be warming up; please try again in a minute.",
        },
      ]);
    } finally {
      setIsStreaming(false);
    }
  };

  return (
    <Card className="flex-1 flex flex-col overflow-hidden">
      <CardContent className="flex-1 flex flex-col p-0">
        {!resources.mas_configured && (
          <div className="px-4 py-3 bg-amber-500/10 border-b text-xs text-amber-700 dark:text-amber-400 flex items-center gap-2">
            <Info size={14} />
            MAS endpoint not configured. Set <code className="mx-1">AECO_MAS_ENDPOINT_NAME</code>
            in app.yml after running the bootstrap.
          </div>
        )}

        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 ? (
            <EmptyState onPick={(p) => send(p)} />
          ) : (
            messages.map((m) => <MessageBubble key={m.id} message={m} />)
          )}
          {isStreaming && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 size={14} className="animate-spin" />
              Thinking…
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="border-t p-3 flex gap-2">
          <Input
            placeholder="Ask the AECO Hub Supervisor…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send()}
            disabled={isStreaming}
          />
          <Button onClick={() => send()} disabled={!input.trim() || isStreaming}>
            <Send size={16} />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function EmptyState({ onPick }: { onPick: (prompt: string) => void }) {
  return (
    <div className="text-center text-sm text-muted-foreground py-8 space-y-4">
      <p>Try one of these:</p>
      <div className="flex flex-wrap gap-2 justify-center max-w-2xl mx-auto">
        {SAMPLE_PROMPTS.map((p) => (
          <button
            key={p}
            onClick={() => onPick(p)}
            className="px-3 py-1.5 text-xs rounded-full border bg-card hover:bg-muted/50 hover:border-amber-500/50 transition-colors"
          >
            {p}
          </button>
        ))}
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  return (
    <div className={`flex gap-2 ${isUser ? "justify-end" : "justify-start"}`}>
      {!isUser && (
        <div className="flex-shrink-0 w-7 h-7 rounded-full bg-amber-500/15 flex items-center justify-center">
          <Bot size={14} className="text-amber-600" />
        </div>
      )}
      <div
        className={`max-w-[80%] rounded-lg px-3 py-2 text-sm ${
          isUser
            ? "bg-amber-500/15 text-foreground"
            : "bg-muted/50 text-foreground"
        }`}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap">{message.content}</p>
        ) : (
          <SafeMarkdown>{message.content}</SafeMarkdown>
        )}
      </div>
      {isUser && (
        <div className="flex-shrink-0 w-7 h-7 rounded-full bg-muted flex items-center justify-center">
          <UserIcon size={14} />
        </div>
      )}
    </div>
  );
}
