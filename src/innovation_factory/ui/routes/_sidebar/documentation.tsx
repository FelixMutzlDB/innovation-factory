import { createFileRoute } from "@tanstack/react-router";
import { Suspense, useState } from "react";
import { useSuspenseQuery } from "@tanstack/react-query";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { FileText } from "lucide-react";

export const Route = createFileRoute("/_sidebar/documentation")({
  component: () => <DocumentationPage />,
});

const PROJECT_LABELS: Record<string, string> = {
  "vi-home-one": "ViDistrictOne",
  "bsh-home-connect": "BSH Remote Assist",
  "adtech-intelligence": "AdTech Intelligence",
  "mol-asm-cockpit": "ASM Cockpit",
};

async function fetchDocList(): Promise<{ slugs: string[] }> {
  const res = await fetch("/api/docs/projects");
  if (!res.ok) throw new Error("Failed to load documentation list");
  return res.json();
}

async function fetchDoc(
  slug: string
): Promise<{ slug: string; title: string; content: string }> {
  const res = await fetch(`/api/docs/projects/${slug}`);
  if (!res.ok) throw new Error(`Failed to load docs for ${slug}`);
  return res.json();
}

function DocumentationPage() {
  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Documentation</h1>
        <p className="text-muted-foreground mt-1">
          Comprehensive guides for each project in the Innovation Factory
          platform.
        </p>
      </div>
      <Suspense fallback={<Skeleton className="h-96 w-full" />}>
        <DocumentationContent />
      </Suspense>
    </div>
  );
}

function DocumentationContent() {
  const { data: docList } = useSuspenseQuery({
    queryKey: ["docs", "projects"],
    queryFn: fetchDocList,
  });

  const [selectedSlug, setSelectedSlug] = useState<string>(
    docList.slugs[0] ?? ""
  );

  if (docList.slugs.length === 0) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center py-12 text-muted-foreground">
          <FileText size={48} className="mb-4 opacity-50" />
          <p>No project documentation available yet.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <Select value={selectedSlug} onValueChange={setSelectedSlug}>
        <SelectTrigger className="w-72">
          <SelectValue placeholder="Select a project" />
        </SelectTrigger>
        <SelectContent>
          {docList.slugs.map((slug) => (
            <SelectItem key={slug} value={slug}>
              {PROJECT_LABELS[slug] ?? slug}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Suspense
        key={selectedSlug}
        fallback={<Skeleton className="h-96 w-full" />}
      >
        <MarkdownViewer slug={selectedSlug} />
      </Suspense>
    </div>
  );
}

function MarkdownViewer({ slug }: { slug: string }) {
  const { data: doc } = useSuspenseQuery({
    queryKey: ["docs", "projects", slug],
    queryFn: () => fetchDoc(slug),
    staleTime: 5 * 60 * 1000,
  });

  return (
    <Card>
      <CardContent className="prose prose-sm dark:prose-invert max-w-none pt-6">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>
          {doc.content}
        </ReactMarkdown>
      </CardContent>
    </Card>
  );
}
