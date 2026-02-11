import { createFileRoute, Link } from "@tanstack/react-router";
import { Suspense, useEffect, useRef, useState } from "react";
import { QueryErrorResetBoundary, useQueryClient } from "@tanstack/react-query";
import { ErrorBoundary } from "react-error-boundary";
import {
  useCreateIdeaSession,
  useSendIdeaMessage,
  useGetIdeaSessionSuspense,
  useGetIdeaMessagesSuspense,
  IdeaSessionStatus,
} from "@/lib/api";
import selector from "@/lib/selector";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";
import Navbar from "@/components/apx/navbar";
import { motion, AnimatePresence } from "motion/react";
import {
  ArrowLeft,
  Sparkles,
  User,
  Send,
  AlertCircle,
  Copy,
  Check,
  Loader2,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { toast } from "sonner";

export const Route = createFileRoute("/build-idea/")({
  component: () => <BuildIdea />,
});

function ChatContent({ sessionId }: { sessionId: number }) {
  const queryClient = useQueryClient();
  const [inputValue, setInputValue] = useState("");
  const [copiedPrompt, setCopiedPrompt] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const { data: session } = useGetIdeaSessionSuspense({
    params: { session_id: sessionId },
    ...selector(),
  });

  const { data: messages } = useGetIdeaMessagesSuspense({
    params: { session_id: sessionId },
    ...selector(),
  });

  const sendMessage = useSendIdeaMessage({
    mutation: {
      onSuccess: () => {
        // Invalidate queries to fetch new messages
        queryClient.invalidateQueries({
          queryKey: ["get", "/api/ideas/sessions", { params: { path: { session_id: sessionId } } }],
        });
        queryClient.invalidateQueries({
          queryKey: ["get", "/api/ideas/messages", { params: { path: { session_id: sessionId } } }],
        });
      },
      onError: (error) => {
        toast.error("Failed to send message. Please try again.");
        console.error("Error sending message:", error);
      },
    },
  });

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Focus input when component mounts
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || sendMessage.isPending) return;

    const messageContent = inputValue.trim();
    setInputValue("");

    await sendMessage.mutateAsync({
      params: { session_id: sessionId },
      data: { content: messageContent },
    });
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleCopyPrompt = async () => {
    if (!session.generated_prompt) return;

    try {
      await navigator.clipboard.writeText(session.generated_prompt);
      setCopiedPrompt(true);
      toast.success("Prompt copied to clipboard!");
      setTimeout(() => setCopiedPrompt(false), 2000);
    } catch (err) {
      toast.error("Failed to copy to clipboard");
      console.error("Copy error:", err);
    }
  };

  const getStatusText = () => {
    switch (session.status) {
      case IdeaSessionStatus.collecting_name:
        return "Collecting company name...";
      case IdeaSessionStatus.collecting_description:
        return "Collecting description...";
      case IdeaSessionStatus.generating:
        return "Generating prompt...";
      case IdeaSessionStatus.completed:
        return "Completed";
      default:
        return "";
    }
  };

  const isCompleted = session.status === IdeaSessionStatus.completed;

  return (
    <div className="h-screen flex flex-col">
      {/* Navbar */}
      <Navbar
        leftContent={
          <div className="flex items-center gap-4">
            <Link to="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
              <ArrowLeft className="h-5 w-5" />
              <span className="font-medium">Back to Gallery</span>
            </Link>
            <Separator orientation="vertical" className="h-6" />
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-primary" />
              <span className="font-semibold">Build a New Idea</span>
            </div>
          </div>
        }
      />

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-4xl mx-auto space-y-6">
          {/* Status Badge */}
          {!isCompleted && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex justify-center"
            >
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary text-sm font-medium">
                <Loader2 className="h-4 w-4 animate-spin" />
                {getStatusText()}
              </div>
            </motion.div>
          )}

          {/* Messages */}
          <AnimatePresence mode="popLayout">
            {messages.map((message, index) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3, delay: index * 0.05 }}
              >
                {message.role === "assistant" ? (
                  <div className="flex gap-4 items-start">
                    <Avatar className="h-10 w-10 shrink-0">
                      <AvatarFallback className="bg-primary text-primary-foreground">
                        <Sparkles className="h-5 w-5" />
                      </AvatarFallback>
                    </Avatar>
                    <Card className="flex-1 border-primary/20">
                      <CardContent className="pt-4">
                        <div className="prose prose-sm dark:prose-invert max-w-none">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {message.content}
                          </ReactMarkdown>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                ) : (
                  <div className="flex gap-4 items-start justify-end">
                    <Card className="flex-1 max-w-2xl bg-primary/5 border-primary/30">
                      <CardContent className="pt-4">
                        <p className="text-foreground">{message.content}</p>
                      </CardContent>
                    </Card>
                    <Avatar className="h-10 w-10 shrink-0">
                      <AvatarFallback className="bg-muted">
                        <User className="h-5 w-5" />
                      </AvatarFallback>
                    </Avatar>
                  </div>
                )}
              </motion.div>
            ))}
          </AnimatePresence>

          {/* Generated Prompt Card */}
          {isCompleted && session.generated_prompt && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.4 }}
            >
              <Card className="border-2 border-primary/50 bg-gradient-to-br from-primary/5 to-primary/10">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="space-y-1">
                      <CardTitle className="text-2xl flex items-center gap-2">
                        <Sparkles className="h-6 w-6 text-primary" />
                        Generated Coding Agent Prompt
                      </CardTitle>
                      <CardDescription>
                        Your custom prompt is ready! Copy it and use it with your coding agent.
                      </CardDescription>
                    </div>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={handleCopyPrompt}
                      className="shrink-0"
                    >
                      {copiedPrompt ? (
                        <>
                          <Check className="h-4 w-4 mr-2" />
                          Copied!
                        </>
                      ) : (
                        <>
                          <Copy className="h-4 w-4 mr-2" />
                          Copy
                        </>
                      )}
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="bg-background/80 rounded-lg p-4 border">
                    <pre className="whitespace-pre-wrap text-sm font-mono overflow-x-auto">
                      {session.generated_prompt}
                    </pre>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* Loading indicator when sending message */}
          {sendMessage.isPending && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex gap-4 items-start"
            >
              <Avatar className="h-10 w-10 shrink-0">
                <AvatarFallback className="bg-primary text-primary-foreground">
                  <Sparkles className="h-5 w-5" />
                </AvatarFallback>
              </Avatar>
              <Card className="flex-1 border-primary/20">
                <CardContent className="pt-4">
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>Thinking...</span>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      {!isCompleted && (
        <div className="border-t bg-background/80 backdrop-blur-sm">
          <div className="max-w-4xl mx-auto px-4 py-4">
            <div className="flex gap-3">
              <Input
                ref={inputRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Type your message..."
                disabled={sendMessage.isPending}
                className="flex-1"
              />
              <Button
                onClick={handleSendMessage}
                disabled={!inputValue.trim() || sendMessage.isPending}
                size="icon"
                className="shrink-0"
              >
                {sendMessage.isPending ? (
                  <Loader2 className="h-5 w-5 animate-spin" />
                ) : (
                  <Send className="h-5 w-5" />
                )}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function ChatSkeleton() {
  return (
    <div className="h-screen flex flex-col">
      <Navbar
        leftContent={
          <div className="flex items-center gap-4">
            <Link to="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
              <ArrowLeft className="h-5 w-5" />
              <span className="font-medium">Back to Gallery</span>
            </Link>
            <Separator orientation="vertical" className="h-6" />
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-primary" />
              <span className="font-semibold">Build a New Idea</span>
            </div>
          </div>
        }
      />

      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-4xl mx-auto space-y-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex gap-4 items-start">
              <Skeleton className="h-10 w-10 rounded-full shrink-0" />
              <Card className="flex-1">
                <CardContent className="pt-4 space-y-2">
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-3/4" />
                </CardContent>
              </Card>
            </div>
          ))}
        </div>
      </div>

      <div className="border-t bg-background/80 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex gap-3">
            <Skeleton className="h-10 flex-1" />
            <Skeleton className="h-10 w-10" />
          </div>
        </div>
      </div>
    </div>
  );
}

function BuildIdeaContent() {
  const [sessionId, setSessionId] = useState<number | null>(null);
  const createSession = useCreateIdeaSession({
    mutation: {
      onSuccess: (response) => {
        setSessionId(response.data.id);
      },
      onError: (error) => {
        toast.error("Failed to create session. Please try again.");
        console.error("Session creation error:", error);
      },
    },
  });

  useEffect(() => {
    if (!sessionId && !createSession.isPending && !createSession.isSuccess) {
      createSession.mutate();
    }
  }, [sessionId, createSession]);

  if (createSession.isError) {
    return (
      <div className="h-screen flex flex-col">
        <Navbar
          leftContent={
            <div className="flex items-center gap-4">
              <Link to="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
                <ArrowLeft className="h-5 w-5" />
                <span className="font-medium">Back to Gallery</span>
              </Link>
            </div>
          }
        />
        <div className="flex-1 flex items-center justify-center px-4">
          <Card className="border-destructive/50 max-w-lg">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-destructive">
                <AlertCircle className="h-5 w-5" />
                Failed to Create Session
              </CardTitle>
              <CardDescription>
                There was an error creating your idea session. Please try again.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex gap-2">
              <Button
                variant="outline"
                onClick={() => {
                  createSession.reset();
                  createSession.mutate();
                }}
              >
                Try Again
              </Button>
              <Link to="/">
                <Button variant="ghost">Go Back</Button>
              </Link>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  if (!sessionId) {
    return <ChatSkeleton />;
  }

  return (
    <Suspense fallback={<ChatSkeleton />}>
      <ChatContent sessionId={sessionId} />
    </Suspense>
  );
}

function BuildIdea() {
  return (
    <QueryErrorResetBoundary>
      {({ reset }) => (
        <ErrorBoundary
          onReset={reset}
          fallbackRender={({ resetErrorBoundary }) => (
            <div className="h-screen flex flex-col">
              <Navbar
                leftContent={
                  <div className="flex items-center gap-4">
                    <Link to="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
                      <ArrowLeft className="h-5 w-5" />
                      <span className="font-medium">Back to Gallery</span>
                    </Link>
                  </div>
                }
              />
              <div className="flex-1 flex items-center justify-center px-4">
                <Card className="border-destructive/50 max-w-lg">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-destructive">
                      <AlertCircle className="h-5 w-5" />
                      Something Went Wrong
                    </CardTitle>
                    <CardDescription>
                      There was an unexpected error. Please try again or go back to the gallery.
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="flex gap-2">
                    <Button variant="outline" onClick={resetErrorBoundary}>
                      Try Again
                    </Button>
                    <Link to="/">
                      <Button variant="ghost">Go Back</Button>
                    </Link>
                  </CardContent>
                </Card>
              </div>
            </div>
          )}
        >
          <Suspense fallback={<ChatSkeleton />}>
            <BuildIdeaContent />
          </Suspense>
        </ErrorBoundary>
      )}
    </QueryErrorResetBoundary>
  );
}
