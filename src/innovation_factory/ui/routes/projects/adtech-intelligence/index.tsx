import { createFileRoute, Link } from "@tanstack/react-router";
import { Suspense, useCallback, useRef, useState } from "react";
import { QueryErrorResetBoundary } from "@tanstack/react-query";
import { ErrorBoundary } from "react-error-boundary";
import { useAt_getDashboardSummarySuspense, useAt_getAnomalyCountsSuspense } from "@/lib/api";
import selector from "@/lib/selector";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  BarChart3,
  Bot,
  AlertTriangle,
  TrendingUp,
  Monitor,
  Radio,
  Activity,
  AlertCircle,
  ArrowRight,
  Send,
  Loader2,
  User,
  Sparkles,
} from "lucide-react";

export const Route = createFileRoute("/projects/adtech-intelligence/")({
  component: () => <AdTechHome />,
});

function KPICards() {
  const { data: summary } = useAt_getDashboardSummarySuspense(selector());

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Active Campaigns</CardTitle>
          <Radio className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{summary.active_campaigns}</div>
          <p className="text-xs text-muted-foreground">
            of {summary.total_campaigns} total campaigns
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Available Inventory</CardTitle>
          <Monitor className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{summary.available_inventory}</div>
          <p className="text-xs text-muted-foreground">
            of {summary.total_inventory} total slots
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Spend</CardTitle>
          <TrendingUp className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            €{(summary.total_spend / 1000).toFixed(0)}k
          </div>
          <p className="text-xs text-muted-foreground">
            Avg CTR: {summary.avg_ctr.toFixed(2)}%
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Active Anomalies</CardTitle>
          <Activity className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{summary.active_anomalies}</div>
          <p className="text-xs text-muted-foreground">
            {summary.critical_anomalies} critical
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

function ComponentCards() {
  const { data: anomalyCounts } = useAt_getAnomalyCountsSuspense(selector());

  const components = [
    {
      title: "Demand & Inventory Explorer",
      description:
        "Explore and analyze advertising demand and inventory across online and outdoor channels. Interactive AI/BI dashboard with ad-hoc questioning via Genie.",
      icon: <BarChart3 className="h-6 w-6" />,
      link: "/projects/adtech-intelligence/dashboard",
      color: "bg-blue-500",
      stats: "Multi-page dashboard with filters",
    },
    {
      title: "Issue Resolution Agent",
      description:
        "AI-powered multi-agent system that helps resolve advertising operations issues. Combines campaign data, past incident knowledge, and customer relations intelligence.",
      icon: <Bot className="h-6 w-6" />,
      link: "/projects/adtech-intelligence/issues",
      color: "bg-violet-500",
      stats: "3 specialized agents",
    },
    {
      title: "Anomaly Notification Center",
      description:
        "Real-time monitoring cockpit for campaign performance anomalies. Get alerted to performance drops, budget overruns, and unusual patterns with AI-suggested mitigations.",
      icon: <AlertTriangle className="h-6 w-6" />,
      link: "/projects/adtech-intelligence/anomalies",
      color: "bg-amber-500",
      badge: (anomalyCounts as { total?: number })?.total ? (anomalyCounts as { total: number }).total : undefined,
      stats: `${(anomalyCounts as { critical?: number })?.critical || 0} critical alerts`,
    },
  ];

  return (
    <div className="grid gap-6 md:grid-cols-3">
      {components.map((comp) => (
        <Link key={comp.link} to={comp.link as any} className="block group">
          <Card className="h-full transition-all hover:shadow-lg hover:border-primary/30 group-hover:scale-[1.01]">
            <CardHeader className="space-y-4">
              <div className="flex items-center justify-between">
                <div
                  className={`w-12 h-12 rounded-lg flex items-center justify-center text-white ${comp.color}`}
                >
                  {comp.icon}
                </div>
                {comp.badge && (
                  <Badge variant="destructive" className="text-xs">
                    {comp.badge} active
                  </Badge>
                )}
              </div>
              <div>
                <CardTitle className="text-xl flex items-center gap-2">
                  {comp.title}
                  <ArrowRight className="h-4 w-4 opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all" />
                </CardTitle>
                <p className="text-xs text-muted-foreground mt-1">{comp.stats}</p>
              </div>
            </CardHeader>
            <CardContent>
              <CardDescription className="text-sm leading-relaxed">
                {comp.description}
              </CardDescription>
            </CardContent>
          </Card>
        </Link>
      ))}
    </div>
  );
}

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  sources?: Array<{ type: string; source: string }>;
}

function MASChatWidget() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
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

  const sendMessage = useCallback(
    async (overrideMessage?: string) => {
      const msg = overrideMessage ?? input.trim();
      if (!msg || isLoading) return;

      if (!overrideMessage) setInput("");
      setMessages((prev) => [...prev, { role: "user", content: msg }]);
      setIsLoading(true);
      scrollToBottom();

      try {
        const response = await fetch(
          "/api/projects/adtech-intelligence/mas-chat",
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: msg, session_id: sessionId }),
          },
        );

        const reader = response.body?.getReader();
        if (!reader) throw new Error("No reader");

        const decoder = new TextDecoder();
        let assistantContent = "";
        let sources: Array<{ type: string; source: string }> = [];

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          const text = decoder.decode(value);
          for (const line of text.split("\n")) {
            if (line.startsWith("data: ")) {
              try {
                const data = JSON.parse(line.slice(6));
                if (data.session_id && !sessionId) setSessionId(data.session_id);
                if (data.content) assistantContent += data.content;
                if (data.sources) sources = data.sources;
              } catch {
                /* ignore parse errors */
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
      } catch {
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
    },
    [input, isLoading, sessionId, scrollToBottom],
  );

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const suggestions = [
    "How are our campaigns performing?",
    "Any anomalies I should be aware of?",
    "Show me inventory availability in Berlin",
    "Which advertiser has the largest contract?",
  ];

  return (
    <Card className="border-violet-500/20">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-violet-500 flex items-center justify-center text-white">
            <Bot className="h-4 w-4" />
          </div>
          <div>
            <CardTitle className="text-base">AdTech Intelligence Agent</CardTitle>
            <CardDescription className="text-xs">
              Multi-agent supervisor — ask about campaigns, issues, or customer data
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {messages.length > 0 && (
          <ScrollArea className="h-[250px] rounded-md border p-3" ref={scrollRef}>
            <div className="space-y-3">
              {messages.map((msg, i) => (
                <div
                  key={i}
                  className={`flex gap-2 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  {msg.role === "assistant" && (
                    <div className="w-6 h-6 rounded-full bg-violet-500/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <Bot className="h-3 w-3 text-violet-600" />
                    </div>
                  )}
                  <div
                    className={`rounded-xl px-3 py-2 text-sm max-w-[85%] ${
                      msg.role === "user"
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted"
                    }`}
                  >
                    <div className="whitespace-pre-wrap">{msg.content}</div>
                    {msg.sources && msg.sources.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-1.5 pt-1.5 border-t border-border/50">
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
                    <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <User className="h-3 w-3" />
                    </div>
                  )}
                </div>
              ))}
              {isLoading && (
                <div className="flex gap-2">
                  <div className="w-6 h-6 rounded-full bg-violet-500/10 flex items-center justify-center flex-shrink-0">
                    <Bot className="h-3 w-3 text-violet-600" />
                  </div>
                  <div className="bg-muted rounded-xl px-3 py-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                  </div>
                </div>
              )}
            </div>
          </ScrollArea>
        )}

        {messages.length === 0 && (
          <div className="flex flex-wrap gap-2">
            {suggestions.map((q) => (
              <Button
                key={q}
                variant="outline"
                size="sm"
                className="text-xs h-7"
                onClick={() => sendMessage(q)}
              >
                <Sparkles className="h-3 w-3 mr-1" />
                {q}
              </Button>
            ))}
          </div>
        )}

        <div className="flex gap-2">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about campaigns, anomalies, inventory, customers..."
            className="min-h-[40px] max-h-[80px] resize-none text-sm"
            rows={1}
          />
          <Button
            onClick={() => sendMessage()}
            disabled={!input.trim() || isLoading}
            size="icon"
            className="h-[40px] w-[40px] flex-shrink-0"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function HomeContent() {
  return (
    <div className="space-y-8 p-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">AdTech Intelligence</h1>
        <p className="text-muted-foreground mt-2">
          AI-powered advertising operations platform — explore demand, resolve issues, and
          monitor campaign anomalies across online and outdoor channels.
        </p>
      </div>

      <Suspense
        fallback={
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {[1, 2, 3, 4].map((i) => (
              <Card key={i}>
                <CardHeader className="pb-2">
                  <Skeleton className="h-4 w-24" />
                </CardHeader>
                <CardContent>
                  <Skeleton className="h-8 w-16" />
                  <Skeleton className="h-3 w-32 mt-2" />
                </CardContent>
              </Card>
            ))}
          </div>
        }
      >
        <KPICards />
      </Suspense>

      <MASChatWidget />

      <div>
        <h2 className="text-xl font-semibold mb-4">Components</h2>
        <Suspense
          fallback={
            <div className="grid gap-6 md:grid-cols-3">
              {[1, 2, 3].map((i) => (
                <Card key={i} className="h-full">
                  <CardHeader className="space-y-4">
                    <Skeleton className="w-12 h-12 rounded-lg" />
                    <Skeleton className="h-6 w-48" />
                  </CardHeader>
                  <CardContent>
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-full mt-2" />
                    <Skeleton className="h-4 w-3/4 mt-2" />
                  </CardContent>
                </Card>
              ))}
            </div>
          }
        >
          <ComponentCards />
        </Suspense>
      </div>
    </div>
  );
}

function AdTechHome() {
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
                    Failed to Load Dashboard
                  </CardTitle>
                  <CardDescription>
                    Could not load the AdTech Intelligence dashboard. Please
                    check that the backend is running.
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
          <HomeContent />
        </ErrorBoundary>
      )}
    </QueryErrorResetBoundary>
  );
}
