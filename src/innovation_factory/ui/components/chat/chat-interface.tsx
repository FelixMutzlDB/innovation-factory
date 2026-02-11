import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Send, Bot, User as UserIcon, AlertCircle, FileText } from "lucide-react";
import { toast } from "sonner";

interface ChatMessage {
  id: number;
  role: "user" | "assistant" | "system";
  content: string;
  sources?: string | null;
  created_at: string;
}

interface ChatInterfaceProps {
  ticketId: number;
  sessionType?: "customer_support" | "technician_assist";
}

export function ChatInterface({ ticketId, sessionType: _sessionType = "customer_support" }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load chat history (mock for now - real implementation coming later)
  useEffect(() => {
    // Mock: Start with empty history, no API call
    setMessages([]);
    setIsLoading(false);
  }, [ticketId]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingContent]);

  const handleSend = async () => {
    if (!input.trim() || isStreaming) return;

    const userMessage = input.trim();
    setInput("");
    setIsStreaming(true);
    setStreamingContent("");

    // Add user message immediately
    const tempUserMessage: ChatMessage = {
      id: Date.now(),
      role: "user",
      content: userMessage,
      sources: null,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMessage]);

    // Mock AI response (real implementation coming later)
    const mockResponse = "I'm sorry to hear that the manual fix was not successful. Would you like me to help you find a certified service partner in your area? They can provide professional assistance with your appliance repair.\n\nJust let me know your location or postal code, and I'll find the nearest BSH authorized service centers for you.";

    // Simulate streaming effect
    try {
      let currentContent = "";
      const words = mockResponse.split(" ");

      for (let i = 0; i < words.length; i++) {
        await new Promise(resolve => setTimeout(resolve, 30)); // Simulate typing
        currentContent += (i === 0 ? "" : " ") + words[i];
        setStreamingContent(currentContent);
      }

      // Add assistant message
      const assistantMessage: ChatMessage = {
        id: Date.now() + 1,
        role: "assistant",
        content: mockResponse,
        sources: null,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
      setStreamingContent("");
    } catch (error) {
      console.error("Failed to send message:", error);
      toast.error("Failed to send message. Please try again.");
    } finally {
      setIsStreaming(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto space-y-4 p-4">
        {isLoading ? (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex gap-3">
                <Skeleton className="h-8 w-8 rounded-full" />
                <Skeleton className="h-20 flex-1" />
              </div>
            ))}
          </div>
        ) : messages.length === 0 ? (
          <Card className="border-dashed border-primary/30 bg-primary/5">
            <CardContent className="pt-6 text-center">
              <div className="h-16 w-16 mx-auto mb-4 rounded-full bg-primary/10 flex items-center justify-center">
                <Bot className="h-8 w-8 text-primary" />
              </div>
              <h3 className="font-semibold text-lg mb-2">
                Home Connect Assistant
              </h3>
              <p className="text-sm text-muted-foreground max-w-sm mx-auto">
                Describe your issue and I'll help you troubleshoot your appliance or connect you with a certified service partner.
              </p>
            </CardContent>
          </Card>
        ) : (
          <>
            {messages.map((message) => (
              <ChatMessageComponent key={message.id} message={message} />
            ))}
          </>
        )}

        {/* Streaming Message */}
        {isStreaming && streamingContent && (
          <div className="flex gap-3">
            <div className="flex-shrink-0">
              <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center">
                <Bot className="h-4 w-4 text-primary-foreground" />
              </div>
            </div>
            <Card className="flex-1 bg-muted/50">
              <CardContent className="pt-4">
                <div className="prose prose-sm dark:prose-invert max-w-none">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {streamingContent}
                  </ReactMarkdown>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {isStreaming && !streamingContent && (
          <div className="flex gap-3">
            <Skeleton className="h-8 w-8 rounded-full" />
            <Card className="flex-1">
              <CardContent className="pt-4">
                <div className="flex gap-2">
                  <div className="h-2 w-2 rounded-full bg-primary animate-pulse" />
                  <div className="h-2 w-2 rounded-full bg-primary animate-pulse delay-75" />
                  <div className="h-2 w-2 rounded-full bg-primary animate-pulse delay-150" />
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t p-4">
        <div className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message..."
            disabled={isStreaming}
            className="flex-1"
          />
          <Button
            onClick={handleSend}
            disabled={!input.trim() || isStreaming}
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

function ChatMessageComponent({ message }: { message: ChatMessage }) {
  const sources = parseSources(message.sources ?? null);

  return (
    <div className="flex gap-3">
      <div className="flex-shrink-0">
        {message.role === "user" ? (
          <div className="h-8 w-8 rounded-full bg-secondary flex items-center justify-center">
            <UserIcon className="h-4 w-4" />
          </div>
        ) : message.role === "assistant" ? (
          <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center">
            <Bot className="h-4 w-4 text-primary-foreground" />
          </div>
        ) : (
          <div className="h-8 w-8 rounded-full bg-muted flex items-center justify-center">
            <AlertCircle className="h-4 w-4 text-muted-foreground" />
          </div>
        )}
      </div>

      <div className="flex-1 space-y-2">
        <Card className={message.role === "assistant" ? "bg-muted/50" : ""}>
          <CardContent className="pt-4">
            {message.role === "user" ? (
              <p className="text-sm whitespace-pre-wrap">{message.content}</p>
            ) : (
              <div className="prose prose-sm dark:prose-invert max-w-none">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    // Customize rendering
                    p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                    ul: ({ children }) => <ul className="mb-2 ml-4">{children}</ul>,
                    ol: ({ children }) => <ol className="mb-2 ml-4">{children}</ol>,
                    code: ({ children, node, ...props }) => {
                      const isInline = !props.className;
                      return isInline ? (
                        <code className="bg-muted px-1 py-0.5 rounded text-xs">
                          {children}
                        </code>
                      ) : (
                        <code {...props}>{children}</code>
                      );
                    },
                  }}
                >
                  {message.content}
                </ReactMarkdown>
              </div>
            )}

            {/* Sources */}
            {sources.length > 0 && (
              <div className="mt-4 pt-4 border-t space-y-2">
                <p className="text-xs font-medium text-muted-foreground flex items-center gap-1">
                  <FileText className="h-3 w-3" />
                  Sources:
                </p>
                <div className="flex flex-wrap gap-2">
                  {sources.map((source, idx) => (
                    <Badge key={idx} variant="outline" className="text-xs">
                      {source}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        <p className="text-xs text-muted-foreground">
          {new Date(message.created_at).toLocaleTimeString()}
        </p>
      </div>
    </div>
  );
}

function parseSources(sourcesStr: string | null): string[] {
  if (!sourcesStr) return [];
  try {
    const parsed = JSON.parse(sourcesStr);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}
