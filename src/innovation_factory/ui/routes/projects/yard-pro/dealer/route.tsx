import SidebarLayout from "@/components/apx/sidebar-layout";
import { ProjectThemeScope } from "@/components/apx/project-theme-scope";
import { createFileRoute, Link, useLocation } from "@tanstack/react-router";
import { cn } from "@/lib/utils";
import { Store, Sprout, MessageCircle } from "lucide-react";
import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import { Badge } from "@/components/ui/badge";

/**
 * Dealer panel layout (UC6, P5).
 *
 * Same theme scope as the consumer cockpit (`<ProjectThemeScope slug="yard-pro">`)
 * so brand-adjacency is consistent. The "Dealer view" badge in the sidebar is
 * the visual reminder that this subtree is the B2B2C dealer surface, not
 * Martin's cockpit — even though the URL also lives under /projects/yard-pro/*.
 *
 * Plan §12 Q6: "same deployment, sub-route `/dealer/*`, separate
 * service-principal UC grants for Klaus". The grants live at the Databricks
 * workspace layer; the route layer just renders the panel.
 */
export const Route = createFileRoute("/projects/yard-pro/dealer")({
  component: () => <DealerLayout />,
});

function DealerLayout() {
  const location = useLocation();

  const navItems = [
    {
      to: "/projects/yard-pro",
      label: "Cockpit",
      icon: <Sprout size={16} />,
      match: (path: string) =>
        path === "/projects/yard-pro" || path === "/projects/yard-pro/",
    },
    {
      to: "/projects/yard-pro/coach",
      label: "Coach",
      icon: <MessageCircle size={16} />,
      match: (path: string) => path.startsWith("/projects/yard-pro/coach"),
    },
    {
      to: "/projects/yard-pro/dealer",
      label: "Dealer panel",
      icon: <Store size={16} />,
      match: (path: string) => path.startsWith("/projects/yard-pro/dealer"),
    },
  ];

  return (
    <ProjectThemeScope slug="yard-pro">
      <SidebarLayout projectSlug="yard-pro">
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {navItems.map((item) => (
                <SidebarMenuItem key={item.to}>
                  <Link
                    to={item.to}
                    className={cn(
                      "flex items-center gap-2 p-2 rounded-lg",
                      item.match(location.pathname)
                        ? "bg-sidebar-accent text-sidebar-accent-foreground"
                        : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
                    )}
                  >
                    {item.icon}
                    <span>{item.label}</span>
                  </Link>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup>
          <SidebarGroupContent>
            <div className="px-2 py-2">
              <Badge variant="outline" className="gap-1">
                <Store size={12} />
                Dealer view
              </Badge>
              <p className="text-xs text-muted-foreground mt-2 leading-snug">
                You are seeing the OEM-side B2B2C dealer surface. Customer
                data here is anonymized via HMAC at ingest; no raw yard_id
                is reachable.
              </p>
            </div>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarLayout>
    </ProjectThemeScope>
  );
}
