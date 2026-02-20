import { createFileRoute, Link } from "@tanstack/react-router";
import { Suspense } from "react";
import { QueryErrorResetBoundary } from "@tanstack/react-query";
import { ErrorBoundary } from "react-error-boundary";
import { useListProjectsSuspense } from "@/lib/api";
import selector from "@/lib/selector";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import Navbar from "@/components/apx/navbar";
import { motion } from "motion/react";
import {
  Plus,
  AlertCircle,
  Zap,
  Wrench,
  Home,
  Smartphone,
  Package,
  Settings,
  Database,
  Cloud,
  Cpu,
  Box,
  Layers,
  Grid,
  Radio,
  ScanSearch,
  type LucideIcon,
} from "lucide-react";

export const Route = createFileRoute("/")({
  component: () => <Index />,
});

// Map icon strings to lucide-react components
const iconMap: Record<string, LucideIcon> = {
  Zap,
  Wrench,
  Home,
  Smartphone,
  Package,
  Settings,
  Database,
  Cloud,
  Cpu,
  Box,
  Layers,
  Grid,
  Plus,
  Radio,
  ScanSearch,
};

function GalleryContent() {
  const { data: projects } = useListProjectsSuspense(selector());

  const getIconComponent = (iconName: string | null | undefined) => {
    if (!iconName) return Box;
    return iconMap[iconName] || Box;
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />

      <main className="flex-1 container mx-auto px-4 py-12">
        <div className="max-w-7xl mx-auto space-y-8">
          {/* Header */}
          <div className="text-center space-y-4">
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold">
              Innovation Factory
            </h1>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Explore our multi-project gallery and start building your next great idea
            </p>
          </div>

          {/* Project Grid */}
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {/* Build a New Idea Card */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: 0 }}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <Link to="/build-idea" className="block h-full">
                <Card className="h-full border-2 border-dashed border-primary/50 hover:border-primary transition-all hover:shadow-lg bg-gradient-to-br from-primary/5 to-primary/10">
                  <CardHeader className="space-y-4">
                    <div
                      className="w-12 h-12 rounded-lg flex items-center justify-center bg-primary text-primary-foreground"
                    >
                      <Plus className="h-6 w-6" />
                    </div>
                    <CardTitle className="text-2xl">Build a New Idea</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <CardDescription className="text-base">
                      Start a new innovation project and bring your ideas to life
                    </CardDescription>
                  </CardContent>
                </Card>
              </Link>
            </motion.div>

            {/* Project Cards */}
            {projects.map((project, index) => {
              const IconComponent = getIconComponent(project.icon);
              const colorStyle = project.color ? { backgroundColor: project.color } : {};

              return (
                <motion.div
                  key={project.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: (index + 1) * 0.1 }}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <Link to={`/projects/${project.slug}` as any} className="block h-full">
                    <Card className="h-full hover:shadow-lg transition-all border-primary/20">
                      <CardHeader className="space-y-4">
                        <div
                          className="w-12 h-12 rounded-lg flex items-center justify-center text-white"
                          style={colorStyle}
                        >
                          <IconComponent className="h-6 w-6" />
                        </div>
                        <div className="space-y-1">
                          <CardTitle className="text-2xl">{project.name}</CardTitle>
                          <p className="text-sm text-muted-foreground font-medium">
                            {project.company}
                          </p>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <CardDescription className="text-base line-clamp-3">
                          {project.description}
                        </CardDescription>
                      </CardContent>
                    </Card>
                  </Link>
                </motion.div>
              );
            })}
          </div>
        </div>
      </main>

      {/* APX Credit */}
      <footer className="container mx-auto px-4 py-8 flex justify-end">
        <a
          href="https://github.com/databricks-solutions/apx"
          target="_blank"
          rel="noopener noreferrer"
          className="group"
        >
          <div className="flex items-center gap-3 px-4 py-3 rounded-lg border bg-card hover:bg-accent transition-colors">
            <img
              src="https://raw.githubusercontent.com/databricks-solutions/apx/refs/heads/main/assets/logo.svg"
              className="h-8 w-8"
              alt="apx logo"
            />
            <div className="flex flex-col items-start">
              <span className="text-xs font-medium">Built with</span>
              <span className="text-sm font-semibold">apx</span>
            </div>
          </div>
        </a>
      </footer>
    </div>
  );
}

function GallerySkeleton() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />

      <main className="flex-1 container mx-auto px-4 py-12">
        <div className="max-w-7xl mx-auto space-y-8">
          <div className="text-center space-y-4">
            <Skeleton className="h-12 w-96 mx-auto" />
            <Skeleton className="h-6 w-[600px] mx-auto" />
          </div>

          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <Card key={i} className="h-full">
                <CardHeader className="space-y-4">
                  <Skeleton className="w-12 h-12 rounded-lg" />
                  <div className="space-y-2">
                    <Skeleton className="h-7 w-48" />
                    <Skeleton className="h-4 w-32" />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-3/4" />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}

function Index() {
  return (
    <QueryErrorResetBoundary>
      {({ reset }) => (
        <ErrorBoundary
          onReset={reset}
          fallbackRender={({ resetErrorBoundary }) => (
            <div className="min-h-screen flex flex-col">
              <Navbar />
              <main className="flex-1 container mx-auto px-4 py-12 flex items-center justify-center">
                <Card className="border-destructive/50 max-w-lg">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-destructive">
                      <AlertCircle className="h-5 w-5" />
                      Failed to Load Projects
                    </CardTitle>
                    <CardDescription>
                      There was an error loading the project gallery. Make sure
                      the backend is running and you're authenticated.
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="flex gap-2">
                    <Button variant="outline" onClick={resetErrorBoundary}>
                      Try Again
                    </Button>
                  </CardContent>
                </Card>
              </main>
            </div>
          )}
        >
          <Suspense fallback={<GallerySkeleton />}>
            <GalleryContent />
          </Suspense>
        </ErrorBoundary>
      )}
    </QueryErrorResetBoundary>
  );
}
