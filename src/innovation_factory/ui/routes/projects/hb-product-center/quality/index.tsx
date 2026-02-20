import { createFileRoute, Link } from "@tanstack/react-router";
import { Suspense, useState, useRef, useEffect, useCallback } from "react";
import { ErrorBoundary } from "react-error-boundary";
import { QueryErrorResetBoundary } from "@tanstack/react-query";
import {
  useHb_listInspectionsSuspense,
  useHb_getQualityStatsSuspense,
  useHb_getDatabricksResourcesSuspense,
} from "@/lib/api";
import { selector } from "@/lib/selector";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Clock,
  Eye,
  BarChart3,
  Sparkles,
  ExternalLink,
  Send,
  Loader2,
  Bot,
  User,
  BookOpen,
} from "lucide-react";

export const Route = createFileRoute(
  "/projects/hb-product-center/quality/",
)({
  component: () => <QualityPage />,
});

function QualityPage() {
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
          <ShieldCheck className="h-6 w-6" />
          Quality Control Studio
        </h1>
        <p className="text-muted-foreground mt-1">
          AI-powered defect detection, quality scoring, and approval workflows.
        </p>
      </div>

      <QueryErrorResetBoundary>
        {({ reset }) => (
          <ErrorBoundary
            onReset={reset}
            fallbackRender={({ resetErrorBoundary }) => (
              <Card>
                <CardContent className="p-6">
                  <p className="text-destructive">Failed to load quality data.</p>
                  <button onClick={resetErrorBoundary} className="mt-2 text-sm underline">Retry</button>
                </CardContent>
              </Card>
            )}
          >
            <Tabs defaultValue="assistant">
              <TabsList>
                <TabsTrigger value="assistant">
                  <BookOpen className="h-4 w-4 mr-2" />
                  Knowledge Assistant
                </TabsTrigger>
                <TabsTrigger value="dashboard">
                  <BarChart3 className="h-4 w-4 mr-2" />
                  AI/BI Dashboard
                </TabsTrigger>
                <TabsTrigger value="inspections">Inspections</TabsTrigger>
              </TabsList>

              <TabsContent value="assistant" className="space-y-4">
                <QualityAssistantChat />
              </TabsContent>

              <TabsContent value="dashboard" className="space-y-4">
                <Suspense
                  fallback={<Skeleton className="h-[70vh] w-full rounded-lg" />}
                >
                  <QualityDashboard />
                </Suspense>
              </TabsContent>

              <TabsContent value="inspections" className="space-y-6">
                <Suspense fallback={<QualitySkeleton />}>
                  <QualityStats />
                </Suspense>
                <Suspense fallback={<InspectionsSkeleton />}>
                  <InspectionsList />
                </Suspense>
              </TabsContent>
            </Tabs>
          </ErrorBoundary>
        )}
      </QueryErrorResetBoundary>
    </div>
  );
}

function QualityStats() {
  const { data: stats } = useHb_getQualityStatsSuspense(selector());

  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
      <Card>
        <CardContent className="p-4">
          <p className="text-xs text-muted-foreground font-medium">Total Inspections</p>
          <p className="text-2xl font-bold mt-1">{stats.total_inspections}</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-4">
          <p className="text-xs text-muted-foreground font-medium flex items-center gap-1">
            <CheckCircle2 className="h-3 w-3 text-green-500" /> Approved
          </p>
          <p className="text-2xl font-bold mt-1 text-green-600">{stats.approved}</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-4">
          <p className="text-xs text-muted-foreground font-medium flex items-center gap-1">
            <XCircle className="h-3 w-3 text-red-500" /> Rejected
          </p>
          <p className="text-2xl font-bold mt-1 text-red-600">{stats.rejected}</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-4">
          <p className="text-xs text-muted-foreground font-medium flex items-center gap-1">
            <Clock className="h-3 w-3 text-amber-500" /> Pending
          </p>
          <p className="text-2xl font-bold mt-1 text-amber-600">{stats.pending + stats.in_review}</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-4">
          <p className="text-xs text-muted-foreground font-medium flex items-center gap-1">
            <BarChart3 className="h-3 w-3 text-blue-500" /> Avg Score
          </p>
          <p className="text-2xl font-bold mt-1">{stats.avg_score}</p>
        </CardContent>
      </Card>
    </div>
  );
}

const statusVariant: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  approved: "default",
  rejected: "destructive",
  pending: "outline",
  in_review: "secondary",
};

const statusIcon: Record<string, React.ReactNode> = {
  approved: <CheckCircle2 className="h-3 w-3" />,
  rejected: <XCircle className="h-3 w-3" />,
  pending: <Clock className="h-3 w-3" />,
  in_review: <Eye className="h-3 w-3" />,
};

function InspectionsList() {
  const { data: inspections } = useHb_listInspectionsSuspense(selector());

  return (
    <Card>
      <CardHeader>
        <CardTitle>Quality Inspections</CardTitle>
        <CardDescription>{inspections.length} inspections found</CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>Batch</TableHead>
              <TableHead>Inspector</TableHead>
              <TableHead>Partner</TableHead>
              <TableHead>Score</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Date</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {inspections.map((insp) => (
              <TableRow key={insp.id}>
                <TableCell>
                  <Link
                    to="/projects/hb-product-center/quality/$inspectionId"
                    params={{ inspectionId: String(insp.id) }}
                    className="text-primary hover:underline font-mono text-sm"
                  >
                    #{insp.id}
                  </Link>
                </TableCell>
                <TableCell className="font-mono text-xs">{insp.batch_number}</TableCell>
                <TableCell className="text-sm">{insp.inspector}</TableCell>
                <TableCell className="text-sm">{insp.manufacturing_partner}</TableCell>
                <TableCell>
                  <span
                    className={
                      insp.overall_score >= 85
                        ? "text-green-600 font-semibold"
                        : insp.overall_score >= 70
                          ? "text-amber-600 font-semibold"
                          : "text-red-600 font-semibold"
                    }
                  >
                    {insp.overall_score}
                  </span>
                </TableCell>
                <TableCell>
                  <Badge variant={statusVariant[insp.status] ?? "outline"} className="gap-1">
                    {statusIcon[insp.status]}
                    {insp.status.replace("_", " ")}
                  </Badge>
                </TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {new Date(insp.created_at).toLocaleDateString()}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

function QualityAssistantChat() {
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
      const res = await fetch(
        "/api/projects/hb-product-center/quality/assistant-chat",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ content: text, session_id: sessionId }),
        },
      );

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

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
                  return [
                    ...prev.slice(0, -1),
                    { role: "assistant", content: chunk.content },
                  ];
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
        {
          role: "assistant",
          content:
            "Sorry, I couldn't reach the quality assistant. Please try again.",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-lg flex items-center gap-2">
          <BookOpen className="h-5 w-5 text-primary" />
          Quality Knowledge Assistant
        </CardTitle>
        <CardDescription>
          Describe a quality issue to get mitigation recommendations based on
          Hugo Boss quality documentation
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div
          ref={scrollRef}
          className="h-96 overflow-y-auto space-y-3 mb-3 rounded-lg border bg-muted/30 p-3"
        >
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-muted-foreground text-sm gap-2">
              <Bot className="h-8 w-8" />
              <p>
                Describe a quality issue and I'll propose mitigations based on
                our quality documentation.
              </p>
              <div className="flex flex-wrap gap-2 mt-2 justify-center">
                {[
                  "Fabric pilling on BOSS knitwear after 3 washes",
                  "Color shade variation in suit jacket lot",
                  "Button detachment on shirts batch HB-2026-0412",
                  "Seam puckering on lightweight summer trousers",
                ].map((q) => (
                  <button
                    key={q}
                    className="px-3 py-1.5 rounded-full border text-xs hover:bg-muted transition-colors"
                    onClick={() => setInput(q)}
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
                className={`max-w-[85%] rounded-lg px-3 py-2 text-sm whitespace-pre-wrap ${
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
            placeholder="Describe a quality issue for mitigation recommendations..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isLoading}
          />
          <Button
            type="submit"
            size="sm"
            disabled={isLoading || !input.trim()}
          >
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

function QualityDashboard() {
  const { data: resources } = useHb_getDatabricksResourcesSuspense(selector());
  const dashboardUrl = `https://${resources.workspace_url}/sql/dashboardsv3/${resources.aq_dashboard_id}`;
  const genieUrl = `https://${resources.workspace_url}/genie/rooms/${resources.aq_genie_space_id}`;

  return (
    <div className="space-y-4">
      <div className="flex gap-3 flex-wrap">
        <a href={dashboardUrl} target="_blank" rel="noopener noreferrer">
          <Button variant="outline" size="sm">
            <BarChart3 className="h-4 w-4 mr-2" />
            Open in Databricks
            <ExternalLink className="h-3 w-3 ml-2" />
          </Button>
        </a>
        <a href={genieUrl} target="_blank" rel="noopener noreferrer">
          <Button variant="outline" size="sm">
            <Sparkles className="h-4 w-4 mr-2" />
            Ask Genie
            <ExternalLink className="h-3 w-3 ml-2" />
          </Button>
        </a>
      </div>
      <div
        className="rounded-lg border overflow-hidden bg-white"
        style={{ height: "70vh" }}
      >
        <iframe
          src={resources.aq_dashboard_embed_url}
          className="w-full h-full border-0"
          title="Quality Control AI/BI Dashboard"
          allow="fullscreen"
        />
      </div>
    </div>
  );
}

function QualitySkeleton() {
  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
      {Array.from({ length: 5 }).map((_, i) => (
        <Card key={i}>
          <CardContent className="p-4 space-y-2">
            <Skeleton className="h-3 w-20" />
            <Skeleton className="h-8 w-12" />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function InspectionsSkeleton() {
  return (
    <Card>
      <CardHeader><Skeleton className="h-6 w-48" /></CardHeader>
      <CardContent className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full" />
        ))}
      </CardContent>
    </Card>
  );
}
