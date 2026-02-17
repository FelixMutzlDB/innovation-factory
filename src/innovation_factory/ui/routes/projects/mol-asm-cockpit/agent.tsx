import { useState, useRef, useEffect } from "react";
import { createFileRoute } from "@tanstack/react-router";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  useMac_sendChatMessage,
  type MacChatMessageOut,
} from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Bot, Send, User as UserIcon } from "lucide-react";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/projects/mol-asm-cockpit/agent")({
  component: () => <AgentPage />,
});

interface ChatMessage {
  id: number;
  role: "user" | "assistant";
  content: string;
  createdAt: Date;
  sessionId?: number;
}

function AgentPage() {
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
        data: {
          message: userMessage,
          session_type: "issue_resolution",
        },
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
        sessionId: responseData.session_id,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Unknown error";
      const errorMsg: ChatMessage = {
        id: Date.now() + 1,
        role: "assistant",
        content: `I encountered an error: ${errorMessage}. Please try again.`,
        createdAt: new Date(),
      };
      setMessages((prev) => [...prev, errorMsg]);
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

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] min-h-[500px]">
      {/* Header */}
      <div className="flex items-center gap-3 pb-4 border-b mb-4">
        <div className="h-10 w-10 rounded-lg bg-primary flex items-center justify-center">
          <Bot className="h-5 w-5 text-primary-foreground" />
        </div>
        <div>
          <h2 className="font-semibold text-lg">ASM Assistant</h2>
          <p className="text-sm text-muted-foreground">
            Multi-agent supervisor for retail analytics, operations &amp; customer relations
          </p>
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto space-y-4">
        {messages.length === 0 ? (
          <Card className="border-dashed border-primary/30 bg-primary/5">
            <CardContent className="pt-6 text-center">
              <div className="h-16 w-16 mx-auto mb-4 rounded-full bg-primary/10 flex items-center justify-center">
                <Bot className="h-8 w-8 text-primary" />
              </div>
              <h3 className="font-semibold text-lg mb-2">
                ASM Assistant
              </h3>
              <p className="text-sm text-muted-foreground max-w-md mx-auto">
                I route your questions to specialized agents: retail data
                analytics, operational issue resolution, and customer
                relations. Ask about station performance, troubleshooting, or
                fleet contracts.
              </p>
            </CardContent>
          </Card>
        ) : (
          messages.map((msg) => (
            <div key={msg.id} className="flex gap-3">
              <div className="flex-shrink-0">
                {msg.role === "user" ? (
                  <div className="h-8 w-8 rounded-full bg-secondary flex items-center justify-center">
                    <UserIcon className="h-4 w-4" />
                  </div>
                ) : (
                  <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center">
                    <Bot className="h-4 w-4 text-primary-foreground" />
                  </div>
                )}
              </div>
              <Card
                className={cn(
                  "flex-1",
                  msg.role === "assistant" && "bg-muted/50",
                )}
              >
                <CardContent className="pt-4">
                  {msg.role === "user" ? (
                    <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                  ) : (
                    <div className="prose prose-sm dark:prose-invert max-w-none">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                          p: ({ children }) => (
                            <p className="mb-2 last:mb-0">{children}</p>
                          ),
                          ul: ({ children }) => (
                            <ul className="mb-2 ml-4 list-disc">{children}</ul>
                          ),
                          ol: ({ children }) => (
                            <ol className="mb-2 ml-4 list-decimal">
                              {children}
                            </ol>
                          ),
                          table: ({ children }) => (
                            <div className="overflow-x-auto my-4">
                              <table className="min-w-full text-sm border-collapse">
                                {children}
                              </table>
                            </div>
                          ),
                          th: ({ children }) => (
                            <th className="border px-3 py-2 text-left font-medium">
                              {children}
                            </th>
                          ),
                          td: ({ children }) => (
                            <td className="border px-3 py-2">{children}</td>
                          ),
                          code: ({ children, className }) =>
                            className ? (
                              <code
                                className={cn(
                                  "block bg-muted p-2 rounded text-xs overflow-x-auto",
                                  className,
                                )}
                              >
                                {children}
                              </code>
                            ) : (
                              <code className="bg-muted px-1 py-0.5 rounded text-xs">
                                {children}
                              </code>
                            ),
                        }}
                      >
                        {msg.content}
                      </ReactMarkdown>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          ))
        )}

        {isLoading && (
          <div className="flex gap-3">
            <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center flex-shrink-0">
              <Bot className="h-4 w-4 text-primary-foreground" />
            </div>
            <Card className="flex-1 bg-muted/50">
              <CardContent className="pt-4">
                <div className="flex gap-2">
                  <div className="h-2 w-2 rounded-full bg-primary animate-pulse" />
                  <div
                    className="h-2 w-2 rounded-full bg-primary animate-pulse"
                    style={{ animationDelay: "150ms" }}
                  />
                  <div
                    className="h-2 w-2 rounded-full bg-primary animate-pulse"
                    style={{ animationDelay: "300ms" }}
                  />
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t pt-4 mt-4">
        <div className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about performance, pricing, or operations..."
            disabled={isLoading}
            className="flex-1"
          />
          <Button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            size="icon"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
        <p className="text-xs text-muted-foreground mt-2">
          Press Enter to send, Shift+Enter for new line
        </p>
      </div>
    </div>
  );
}
