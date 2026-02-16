import { Suspense, useMemo, useState, useRef, useEffect } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { ErrorBoundary } from "react-error-boundary";
import { motion } from "motion/react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  useMac_listStationsSuspense,
  useMac_listRegionsSuspense,
  useMac_listAnomalyAlertsSuspense,
  useMac_sendChatMessage,
  type MacChatMessageOut,
} from "@/lib/api";
import selector from "@/lib/selector";
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
import { BarChart3, AlertTriangle, Bot, Send, User as UserIcon } from "lucide-react";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/projects/mol-asm-cockpit/home")({
  component: () => <HomePage />,
});

const heroCards = [
  {
    title: "Demand & Inventory Explorer",
    icon: BarChart3,
    color: "#f59e0b",
    description:
      "Explore fuel, non-fuel, and pricing data across your station network. Drill down by region, station type, and time period.",
    to: "/projects/mol-asm-cockpit/explorer" as const,
  },
  {
    title: "Anomaly Notification Center",
    icon: AlertTriangle,
    color: "#ef4444",
    description:
      "Monitor and triage alerts across fuel volume, spoilage, stock-outs, workforce, pricing, and operations. Stay ahead of issues.",
    to: "/projects/mol-asm-cockpit/anomalies" as const,
    showBadge: true,
  },
];

function HomePage() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="pb-2">
        <h1 className="text-3xl font-bold tracking-tight">ASM Cockpit</h1>
        <p className="text-muted-foreground mt-2">
          Your intelligent retail station command center
        </p>
      </div>

      {/* KPI Summary Row */}
      <ErrorBoundary
        fallbackRender={() => (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {["Total Stations", "Active Alerts", "Regions", "Countries"].map(
              (label) => (
                <Card key={label} className="border-l-4 border-l-primary/50">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">
                      {label}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold text-muted-foreground">
                      —
                    </div>
                  </CardContent>
                </Card>
              ),
            )}
          </div>
        )}
      >
        <Suspense fallback={<KpiSkeleton />}>
          <KpiRow />
        </Suspense>
      </ErrorBoundary>

      {/* ASM Assistant Chat */}
      <AsmAssistantChat />

      {/* Hero Cards - these are static links, rendered immediately */}
      <ErrorBoundary
        fallbackRender={() => <HeroCardsStatic />}
      >
        <Suspense fallback={<HeroCardsStatic />}>
          <HeroCardsWithBadge />
        </Suspense>
      </ErrorBoundary>
    </div>
  );
}

function KpiRow() {
  const { data: stations } = useMac_listStationsSuspense(selector());
  const { data: regions } = useMac_listRegionsSuspense(selector());
  const { data: alerts } = useMac_listAnomalyAlertsSuspense({
    params: { status: "active", limit: 500 },
    ...selector(),
  });

  const stationList = Array.isArray(stations) ? stations : [];
  const regionList = Array.isArray(regions) ? regions : [];
  const alertList = Array.isArray(alerts) ? alerts : [];

  const countries = useMemo(() => {
    const set = new Set(regionList.map((r: { country: string }) => r.country));
    return set.size;
  }, [regionList]);

  const kpiStats = [
    { label: "Total Stations", value: stationList.length },
    { label: "Active Alerts", value: alertList.length },
    { label: "Regions Covered", value: regionList.length },
    { label: "Countries", value: countries },
  ];

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {kpiStats.map((stat) => (
        <Card key={stat.label} className="border-l-4 border-l-primary/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{stat.label}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stat.value}</div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

interface ChatMessage {
  id: number;
  role: "user" | "assistant";
  content: string;
  createdAt: Date;
}

function AsmAssistantChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<number | undefined>(undefined);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const sendMessage = useMac_sendChatMessage();

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput("");
    setIsLoading(true);

    const userMsg: ChatMessage = {
      id: Date.now(),
      role: "user",
      content: userMessage,
      createdAt: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);

    try {
      const result = await sendMessage.mutateAsync({
        params: { session_id: sessionId },
        data: { message: userMessage, session_type: "issue_resolution" },
      });
      const responseData = (result as { data: MacChatMessageOut }).data;
      if (responseData.session_id && !sessionId) {
        setSessionId(responseData.session_id);
      }
      const assistantMsg: ChatMessage = {
        id: responseData.id ?? Date.now() + 1,
        role: "assistant",
        content: responseData.content,
        createdAt: new Date(responseData.created_at),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Unknown error";
      setMessages((prev) => [
        ...prev,
        { id: Date.now() + 1, role: "assistant", content: `Error: ${errorMessage}`, createdAt: new Date() },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const suggestions = [
    "Why is Station HU-BP-001 underperforming?",
    "Which stations have the biggest margin upside?",
    "Show me Fresh Corner spoilage trends",
  ];

  return (
    <Card className="border-l-4 border-l-blue-500">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-lg bg-blue-500 flex items-center justify-center">
            <Bot className="h-5 w-5 text-white" />
          </div>
          <div>
            <CardTitle className="text-lg">Area Sales Manager Assistant</CardTitle>
            <CardDescription>
              Ask about performance, pricing, operations, or customer relations
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Messages area */}
        {messages.length > 0 && (
          <div className="max-h-80 overflow-y-auto space-y-3 border rounded-lg p-3 bg-muted/30">
            {messages.map((msg) => (
              <div key={msg.id} className="flex gap-2">
                <div className="flex-shrink-0 mt-0.5">
                  {msg.role === "user" ? (
                    <div className="h-6 w-6 rounded-full bg-secondary flex items-center justify-center">
                      <UserIcon className="h-3 w-3" />
                    </div>
                  ) : (
                    <div className="h-6 w-6 rounded-full bg-blue-500 flex items-center justify-center">
                      <Bot className="h-3 w-3 text-white" />
                    </div>
                  )}
                </div>
                <div className={cn("flex-1 text-sm", msg.role === "user" && "font-medium")}>
                  {msg.role === "user" ? (
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                  ) : (
                    <div className="prose prose-sm dark:prose-invert max-w-none">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                          p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                          ul: ({ children }) => <ul className="mb-2 ml-4 list-disc">{children}</ul>,
                          ol: ({ children }) => <ol className="mb-2 ml-4 list-decimal">{children}</ol>,
                          table: ({ children }) => (
                            <div className="overflow-x-auto my-2">
                              <table className="min-w-full text-sm border-collapse">{children}</table>
                            </div>
                          ),
                          th: ({ children }) => <th className="border px-2 py-1 text-left font-medium">{children}</th>,
                          td: ({ children }) => <td className="border px-2 py-1">{children}</td>,
                          code: ({ children, className }) =>
                            className ? (
                              <code className={cn("block bg-muted p-2 rounded text-xs overflow-x-auto", className)}>{children}</code>
                            ) : (
                              <code className="bg-muted px-1 py-0.5 rounded text-xs">{children}</code>
                            ),
                        }}
                      >
                        {msg.content}
                      </ReactMarkdown>
                    </div>
                  )}
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex gap-2">
                <div className="h-6 w-6 rounded-full bg-blue-500 flex items-center justify-center flex-shrink-0">
                  <Bot className="h-3 w-3 text-white" />
                </div>
                <div className="flex gap-1.5 items-center pt-1">
                  <div className="h-1.5 w-1.5 rounded-full bg-blue-500 animate-pulse" />
                  <div className="h-1.5 w-1.5 rounded-full bg-blue-500 animate-pulse" style={{ animationDelay: "150ms" }} />
                  <div className="h-1.5 w-1.5 rounded-full bg-blue-500 animate-pulse" style={{ animationDelay: "300ms" }} />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}

        {/* Quick suggestions when no messages */}
        {messages.length === 0 && (
          <div className="flex flex-wrap gap-2">
            {suggestions.map((s) => (
              <button
                key={s}
                onClick={() => { setInput(s); }}
                className="text-xs px-3 py-1.5 rounded-full border bg-background hover:bg-accent transition-colors text-muted-foreground hover:text-foreground"
              >
                {s}
              </button>
            ))}
          </div>
        )}

        {/* Input */}
        <div className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about performance, pricing, or operations..."
            disabled={isLoading}
            className="flex-1"
          />
          <Button onClick={handleSend} disabled={!input.trim() || isLoading} size="icon">
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function HeroCardsWithBadge() {
  const { data: alerts } = useMac_listAnomalyAlertsSuspense({
    params: { status: "active", limit: 500 },
    ...selector(),
  });
  const alertCount = Array.isArray(alerts) ? alerts.length : 0;

  return (
    <div className="grid gap-6 md:grid-cols-2">
      {heroCards.map((card) => (
        <motion.div
          key={card.to}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          transition={{ type: "spring", stiffness: 400, damping: 17 }}
        >
          <Link to={card.to} className="block h-full">
            <Card
              className="h-full transition-all hover:shadow-lg hover:border-primary/30"
              style={{
                borderLeftWidth: "4px",
                borderLeftColor: card.color,
              }}
            >
              <CardHeader className="flex flex-row items-start justify-between space-y-0">
                <div
                  className="h-12 w-12 rounded-lg flex items-center justify-center text-white"
                  style={{ backgroundColor: card.color }}
                >
                  <card.icon className="h-6 w-6" />
                </div>
                {card.showBadge && alertCount > 0 && (
                  <span
                    className="rounded-full px-2.5 py-0.5 text-xs font-medium text-white"
                    style={{ backgroundColor: card.color }}
                  >
                    {alertCount} active
                  </span>
                )}
              </CardHeader>
              <CardContent>
                <CardTitle className="text-xl">{card.title}</CardTitle>
                <CardDescription className="mt-2 text-base">
                  {card.description}
                </CardDescription>
              </CardContent>
            </Card>
          </Link>
        </motion.div>
      ))}
    </div>
  );
}

function HeroCardsStatic() {
  return (
    <div className="grid gap-6 md:grid-cols-2">
      {heroCards.map((card) => (
        <motion.div
          key={card.to}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          transition={{ type: "spring", stiffness: 400, damping: 17 }}
        >
          <Link to={card.to} className="block h-full">
            <Card
              className="h-full transition-all hover:shadow-lg hover:border-primary/30"
              style={{
                borderLeftWidth: "4px",
                borderLeftColor: card.color,
              }}
            >
              <CardHeader className="flex flex-row items-start justify-between space-y-0">
                <div
                  className="h-12 w-12 rounded-lg flex items-center justify-center text-white"
                  style={{ backgroundColor: card.color }}
                >
                  <card.icon className="h-6 w-6" />
                </div>
              </CardHeader>
              <CardContent>
                <CardTitle className="text-xl">{card.title}</CardTitle>
                <CardDescription className="mt-2 text-base">
                  {card.description}
                </CardDescription>
              </CardContent>
            </Card>
          </Link>
        </motion.div>
      ))}
    </div>
  );
}

function KpiSkeleton() {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {[1, 2, 3, 4].map((i) => (
        <Skeleton key={i} className="h-[90px]" />
      ))}
    </div>
  );
}
