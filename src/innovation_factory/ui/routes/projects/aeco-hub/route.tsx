import SidebarLayout from "@/components/apx/sidebar-layout";
import { createFileRoute, Link, useLocation } from "@tanstack/react-router";
import { cn } from "@/lib/utils";
import { LayoutDashboard, Wrench, Store, Bot } from "lucide-react";
import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuItem,
} from "@/components/ui/sidebar";

export const Route = createFileRoute("/projects/aeco-hub")({
  component: () => <Layout />,
});

function Layout() {
  const location = useLocation();

  const navItems = [
    {
      to: "/projects/aeco-hub",
      label: "Overview",
      icon: <LayoutDashboard size={16} />,
      match: (path: string) =>
        path === "/projects/aeco-hub" ||
        path === "/projects/aeco-hub/" ||
        path.startsWith("/projects/aeco-hub/projects/"),
    },
    {
      to: "/projects/aeco-hub/tools",
      label: "Tool Navigator",
      icon: <Wrench size={16} />,
      match: (path: string) => path.startsWith("/projects/aeco-hub/tools"),
    },
    {
      to: "/projects/aeco-hub/marketplace",
      label: "Marketplace",
      icon: <Store size={16} />,
      match: (path: string) => path.startsWith("/projects/aeco-hub/marketplace"),
    },
    {
      to: "/projects/aeco-hub/agent",
      label: "AI Agent",
      icon: <Bot size={16} />,
      match: (path: string) => path.startsWith("/projects/aeco-hub/agent"),
    },
  ];

  return (
    <SidebarLayout>
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
    </SidebarLayout>
  );
}
