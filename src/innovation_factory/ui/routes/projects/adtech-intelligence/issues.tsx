import { createFileRoute } from "@tanstack/react-router";
import { useCallback, useRef, useState } from "react";
import { QueryErrorResetBoundary } from "@tanstack/react-query";
import { ErrorBoundary } from "react-error-boundary";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import {
  AlertCircle,
  Bot,
  Loader2,
  Send,
  User,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";

export const Route = createFileRoute(
  "/projects/adtech-intelligence/issues",
)({
  component: () => <IssuesPage />,
});

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: Array<{ type: string; source: string }>;
}

function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Hello! I'm the Issue Resolution Assistant, powered by a Knowledge Base of operational runbooks, past incident reports, and SLA policies.\n\n" +
        "I can help you with:\n\n" +
        "- **Troubleshooting** ad delivery problems and DOOH screen outages\n" +
        "- **Resolving** click tracking issues and billing discrepancies\n" +
        "- **Looking up** SLA requirements and resolution procedures\n" +
        "- **Referencing** past incidents for known solutions\n\n" +
        "What issue can I help you resolve?",
      sources: [{ type: "knowledge_base", source: "Issue Resolution Knowledge Base" }],
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<number | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    setTimeout(() => {
      if (scrollRef.current) {
        scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
      }
    }, 50);
  }, []);

  const sendMessage = useCallback(async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setIsLoading(true);
    scrollToBottom();

    try {
      const response = await fetch("/api/projects/adtech-intelligence/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userMessage,
          session_id: sessionId,
        }),
      });

      const reader = response.body?.getReader();
      if (!reader) throw new Error("No reader");

      const decoder = new TextDecoder();
      let assistantContent = "";
      let sources: Array<{ type: string; source: string }> = [];

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const text = decoder.decode(value);
        const lines = text.split("\n");
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.session_id && !sessionId) {
                setSessionId(data.session_id);
              }
              if (data.content) {
                assistantContent += data.content;
              }
              if (data.sources) {
                sources = data.sources;
              }
            } catch {
              // ignore parse errors
            }
          }
        }
      }

      if (assistantContent) {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: assistantContent, sources },
        ]);
      }
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Sorry, I encountered an error. Please try again.",
        },
      ]);
    } finally {
      setIsLoading(false);
      scrollToBottom();
    }
  }, [input, isLoading, sessionId, scrollToBottom]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const suggestedQuestions = [
    "A DOOH screen is offline at Hamburg Hbf — what should I do?",
    "Click tracking is returning 404 errors for a campaign",
    "What are our SLA response times for premium advertisers?",
    "How do I handle a billing discrepancy?",
  ];

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      {/* Chat messages */}
      <ScrollArea className="flex-1 px-4" ref={scrollRef}>
        <div className="max-w-3xl mx-auto space-y-6 py-4">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={cn(
                "flex gap-3",
                msg.role === "user" ? "justify-end" : "justify-start",
              )}
            >
              {msg.role === "assistant" && (
                <div className="w-8 h-8 rounded-full bg-violet-500/10 flex items-center justify-center flex-shrink-0 mt-1">
                  <Bot className="h-4 w-4 text-violet-600" />
                </div>
              )}
              <div
                className={cn(
                  "rounded-2xl px-4 py-3 max-w-[80%]",
                  msg.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted",
                )}
              >
                <div className="prose prose-sm dark:prose-invert max-w-none whitespace-pre-wrap">
                  {msg.content}
                </div>
                {msg.sources && msg.sources.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2 pt-2 border-t border-border/50">
                    {msg.sources.map((src, j) => (
                      <Badge
                        key={j}
                        variant="secondary"
                        className="text-[10px] px-1.5 py-0"
                      >
                        {src.source}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
              {msg.role === "user" && (
                <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 mt-1">
                  <User className="h-4 w-4" />
                </div>
              )}
            </div>
          ))}

          {isLoading && (
            <div className="flex gap-3 justify-start">
              <div className="w-8 h-8 rounded-full bg-violet-500/10 flex items-center justify-center flex-shrink-0">
                <Bot className="h-4 w-4 text-violet-600" />
              </div>
              <div className="bg-muted rounded-2xl px-4 py-3">
                <Loader2 className="h-4 w-4 animate-spin" />
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Suggested questions (only when no user messages yet) */}
      {messages.length <= 1 && (
        <div className="px-4 pb-2">
          <div className="max-w-3xl mx-auto flex flex-wrap gap-2">
            {suggestedQuestions.map((q) => (
              <Button
                key={q}
                variant="outline"
                size="sm"
                className="text-xs"
                onClick={() => {
                  setInput(q);
                  setTimeout(() => sendMessage(), 0);
                }}
              >
                <Sparkles className="h-3 w-3 mr-1" />
                {q}
              </Button>
            ))}
          </div>
        </div>
      )}

      {/* Input area */}
      <div className="border-t bg-background p-4">
        <div className="max-w-3xl mx-auto flex gap-2">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about campaigns, anomalies, issues, inventory..."
            className="min-h-[44px] max-h-[120px] resize-none"
            rows={1}
          />
          <Button
            onClick={sendMessage}
            disabled={!input.trim() || isLoading}
            size="icon"
            className="h-[44px] w-[44px] flex-shrink-0"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}

function IssuesPage() {
  return (
    <QueryErrorResetBoundary>
      {({ reset }) => (
        <ErrorBoundary
          onReset={reset}
          fallbackRender={({ resetErrorBoundary }) => (
            <div className="p-6 flex items-center justify-center min-h-[50vh]">
              <Card className="border-destructive/50 max-w-lg">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-destructive">
                    <AlertCircle className="h-5 w-5" />
                    Agent Unavailable
                  </CardTitle>
                  <CardDescription>
                    Could not connect to the issue resolution agent.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Button variant="outline" onClick={resetErrorBoundary}>
                    Try Again
                  </Button>
                </CardContent>
              </Card>
            </div>
          )}
        >
          <div className="p-6 pb-0">
            <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
              <Bot className="h-6 w-6" />
              Issue Resolution Agent
            </h1>
            <p className="text-muted-foreground mt-1">
              AI-powered multi-agent system combining campaign data, incident knowledge, and customer relations.
            </p>
          </div>
          <ChatInterface />
        </ErrorBoundary>
      )}
    </QueryErrorResetBoundary>
  );
}
