import SidebarLayout from "@/components/apx/sidebar-layout";
import { createFileRoute, Link, useLocation } from "@tanstack/react-router";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  BarChart3,
  Bot,
  AlertTriangle,
  User,
} from "lucide-react";
import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuItem,
} from "@/components/ui/sidebar";

export const Route = createFileRoute("/projects/adtech-intelligence")({
  component: () => <Layout />,
});

function Layout() {
  const location = useLocation();

  const navItems = [
    {
      to: "/projects/adtech-intelligence",
      label: "Overview",
      icon: <LayoutDashboard size={16} />,
      match: (path: string) =>
        path === "/projects/adtech-intelligence" ||
        path === "/projects/adtech-intelligence/",
    },
    {
      to: "/projects/adtech-intelligence/dashboard",
      label: "Demand & Inventory",
      icon: <BarChart3 size={16} />,
      match: (path: string) =>
        path.startsWith("/projects/adtech-intelligence/dashboard"),
    },
    {
      to: "/projects/adtech-intelligence/issues",
      label: "Issue Resolution",
      icon: <Bot size={16} />,
      match: (path: string) =>
        path.startsWith("/projects/adtech-intelligence/issues"),
    },
    {
      to: "/projects/adtech-intelligence/anomalies",
      label: "Anomaly Center",
      icon: <AlertTriangle size={16} />,
      match: (path: string) =>
        path.startsWith("/projects/adtech-intelligence/anomalies"),
    },
    {
      to: "/projects/adtech-intelligence/profile",
      label: "Profile",
      icon: <User size={16} />,
      match: (path: string) =>
        path.startsWith("/projects/adtech-intelligence/profile"),
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
