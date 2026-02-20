import { createFileRoute, Link } from "@tanstack/react-router";
import { Suspense, useState, useRef, useEffect, useCallback } from "react";
import { ErrorBoundary } from "react-error-boundary";
import { QueryErrorResetBoundary } from "@tanstack/react-query";
import { useHb_getDashboardSummarySuspense } from "@/lib/api";
import { selector } from "@/lib/selector";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Package,
  ScanSearch,
  ShieldCheck,
  Fingerprint,
  Truck,
  Leaf,
  TrendingUp,
  MessageSquare,
  Send,
  Loader2,
  Bot,
  User,
} from "lucide-react";

export const Route = createFileRoute("/projects/hb-product-center/")({
  component: () => <OverviewPage />,
});

function OverviewPage() {
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">
          Hugo Boss Intelligent Product Center
        </h1>
        <p className="text-muted-foreground mt-1">
          One-stop shop for product recognition, quality control, authenticity
          verification, and supply chain intelligence.
        </p>
      </div>

      <QueryErrorResetBoundary>
        {({ reset }) => (
          <ErrorBoundary
            onReset={reset}
            fallbackRender={({ resetErrorBoundary }) => (
              <Card>
                <CardContent className="p-6">
                  <p className="text-destructive">Failed to load dashboard.</p>
                  <button
                    onClick={resetErrorBoundary}
                    className="mt-2 text-sm underline"
                  >
                    Retry
                  </button>
                </CardContent>
              </Card>
            )}
          >
            <Suspense fallback={<DashboardSkeleton />}>
              <DashboardContent />
            </Suspense>
          </ErrorBoundary>
        )}
      </QueryErrorResetBoundary>

      <ProductCenterChat />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Link to="/projects/hb-product-center/recognition">
          <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900/30">
                  <ScanSearch className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                </div>
                <div>
                  <CardTitle className="text-lg">
                    Visual Recognition Hub
                  </CardTitle>
                  <CardDescription>
                    Upload images to identify products instantly
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
          </Card>
        </Link>

        <Link to="/projects/hb-product-center/quality">
          <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-green-100 dark:bg-green-900/30">
                  <ShieldCheck className="h-5 w-5 text-green-600 dark:text-green-400" />
                </div>
                <div>
                  <CardTitle className="text-lg">
                    Quality Control Studio
                  </CardTitle>
                  <CardDescription>
                    AI-powered defect detection and quality scoring
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
          </Card>
        </Link>

        <Link to="/projects/hb-product-center/authenticity">
          <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-purple-100 dark:bg-purple-900/30">
                  <Fingerprint className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                </div>
                <div>
                  <CardTitle className="text-lg">
                    Authenticity Verification
                  </CardTitle>
                  <CardDescription>
                    Brand protection and counterfeit detection
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
          </Card>
        </Link>

        <Link to="/projects/hb-product-center/supply-chain">
          <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-amber-100 dark:bg-amber-900/30">
                  <Truck className="h-5 w-5 text-amber-600 dark:text-amber-400" />
                </div>
                <div>
                  <CardTitle className="text-lg">
                    Supply Chain Intelligence
                  </CardTitle>
                  <CardDescription>
                    Track products and sustainability metrics
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
          </Card>
        </Link>
      </div>
    </div>
  );
}

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

function ProductCenterChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<number | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || isLoading) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setIsLoading(true);

    try {
      const res = await fetch("/api/projects/hb-product-center/chat/mas-chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: text, session_id: sessionId }),
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const reader = res.body?.getReader();
      if (!reader) throw new Error("No response body");

      const decoder = new TextDecoder();
      let accumulated = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        accumulated += decoder.decode(value, { stream: true });

        const lines = accumulated.split("\n");
        accumulated = lines.pop() ?? "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          try {
            const chunk = JSON.parse(line.slice(6));
            if (chunk.session_id) setSessionId(chunk.session_id);
            if (chunk.content && !chunk.done) {
              setMessages((prev) => {
                const last = prev[prev.length - 1];
                if (last?.role === "assistant") {
                  return [...prev.slice(0, -1), { role: "assistant", content: chunk.content }];
                }
                return [...prev, { role: "assistant", content: chunk.content }];
              });
            }
          } catch {
            // skip malformed lines
          }
        }
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Sorry, I couldn't reach the agent. Please try again." },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-lg flex items-center gap-2">
          <MessageSquare className="h-5 w-5 text-primary" />
          Product Center Intelligence Agent
        </CardTitle>
        <CardDescription>
          Ask questions about supply chain, quality, authenticity, or product identification
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div
          ref={scrollRef}
          className="h-64 overflow-y-auto space-y-3 mb-3 rounded-lg border bg-muted/30 p-3"
        >
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-muted-foreground text-sm gap-2">
              <Bot className="h-8 w-8" />
              <p>Ask me anything about your product center.</p>
              <div className="flex flex-wrap gap-2 mt-2 justify-center">
                {[
                  "What's the current supply chain status?",
                  "Show quality inspection trends",
                  "Identify a black wool blazer",
                ].map((q) => (
                  <button
                    key={q}
                    className="px-3 py-1.5 rounded-full border text-xs hover:bg-muted transition-colors"
                    onClick={() => {
                      setInput(q);
                    }}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex gap-2 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              {msg.role === "assistant" && (
                <div className="flex-shrink-0 h-7 w-7 rounded-full bg-primary/10 flex items-center justify-center">
                  <Bot className="h-4 w-4 text-primary" />
                </div>
              )}
              <div
                className={`max-w-[80%] rounded-lg px-3 py-2 text-sm ${
                  msg.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : "bg-background border"
                }`}
              >
                {msg.content}
              </div>
              {msg.role === "user" && (
                <div className="flex-shrink-0 h-7 w-7 rounded-full bg-muted flex items-center justify-center">
                  <User className="h-4 w-4" />
                </div>
              )}
            </div>
          ))}
          {isLoading && messages[messages.length - 1]?.role === "user" && (
            <div className="flex gap-2">
              <div className="flex-shrink-0 h-7 w-7 rounded-full bg-primary/10 flex items-center justify-center">
                <Bot className="h-4 w-4 text-primary" />
              </div>
              <div className="bg-background border rounded-lg px-3 py-2">
                <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
              </div>
            </div>
          )}
        </div>
        <form
          className="flex gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
        >
          <input
            type="text"
            className="flex-1 rounded-md border px-3 py-2 text-sm"
            placeholder="Ask about products, supply chain, quality..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isLoading}
          />
          <Button type="submit" size="sm" disabled={isLoading || !input.trim()}>
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

function DashboardContent() {
  const { data: summary } = useHb_getDashboardSummarySuspense(selector());

  const kpis = [
    {
      label: "Total Products",
      value: summary.total_products.toLocaleString(),
      sub: `${summary.active_products} active`,
      icon: <Package className="h-4 w-4" />,
      color: "text-blue-600",
    },
    {
      label: "Recognition Jobs",
      value: summary.recognition_jobs_total.toLocaleString(),
      sub: `${summary.recognition_jobs_today} today`,
      icon: <ScanSearch className="h-4 w-4" />,
      color: "text-indigo-600",
    },
    {
      label: "Avg Quality Score",
      value: `${summary.avg_quality_score}`,
      sub: `${summary.inspections_pending} pending`,
      icon: <TrendingUp className="h-4 w-4" />,
      color: "text-green-600",
    },
    {
      label: "Auth Success Rate",
      value: `${summary.auth_success_rate}%`,
      sub: `${summary.auth_alerts_open} open alerts`,
      icon: <Fingerprint className="h-4 w-4" />,
      color: "text-purple-600",
    },
    {
      label: "Supply Chain Events",
      value: summary.supply_chain_events_total.toLocaleString(),
      sub: "across value chain",
      icon: <Truck className="h-4 w-4" />,
      color: "text-amber-600",
    },
    {
      label: "Avg Recycled Content",
      value: `${summary.avg_sustainability_score}%`,
      sub: "sustainability metric",
      icon: <Leaf className="h-4 w-4" />,
      color: "text-emerald-600",
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {kpis.map((kpi) => (
        <Card key={kpi.label}>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <span className={kpi.color}>{kpi.icon}</span>
              <span className="text-xs text-muted-foreground font-medium">
                {kpi.label}
              </span>
            </div>
            <p className="text-2xl font-bold">{kpi.value}</p>
            <p className="text-xs text-muted-foreground mt-1">{kpi.sub}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {Array.from({ length: 6 }).map((_, i) => (
        <Card key={i}>
          <CardContent className="p-4 space-y-2">
            <Skeleton className="h-4 w-20" />
            <Skeleton className="h-8 w-16" />
            <Skeleton className="h-3 w-24" />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
