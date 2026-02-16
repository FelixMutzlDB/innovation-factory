import SidebarLayout from "@/components/apx/sidebar-layout";
import { createFileRoute, Link, useLocation } from "@tanstack/react-router";
import { cn } from "@/lib/utils";
import {
  Home,
  BarChart3,
  Bot,
  AlertTriangle,
  MapPin,
} from "lucide-react";
import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuItem,
} from "@/components/ui/sidebar";

export const Route = createFileRoute("/projects/mol-asm-cockpit")({
  component: () => <Layout />,
});

function Layout() {
  const location = useLocation();

  const navItems = [
    {
      to: "/projects/mol-asm-cockpit/home",
      label: "Home",
      icon: <Home size={16} />,
      match: (path: string) =>
        path === "/projects/mol-asm-cockpit/home" ||
        path === "/projects/mol-asm-cockpit/home/",
    },
    {
      to: "/projects/mol-asm-cockpit/explorer",
      label: "Explorer",
      icon: <BarChart3 size={16} />,
      match: (path: string) => path.startsWith("/projects/mol-asm-cockpit/explorer"),
    },
    {
      to: "/projects/mol-asm-cockpit/agent",
      label: "ASM Assistant",
      icon: <Bot size={16} />,
      match: (path: string) => path.startsWith("/projects/mol-asm-cockpit/agent"),
    },
    {
      to: "/projects/mol-asm-cockpit/anomalies",
      label: "Anomalies",
      icon: <AlertTriangle size={16} />,
      match: (path: string) =>
        path.startsWith("/projects/mol-asm-cockpit/anomalies"),
    },
    {
      to: "/projects/mol-asm-cockpit/stations",
      label: "Stations",
      icon: <MapPin size={16} />,
      match: (path: string) =>
        path.startsWith("/projects/mol-asm-cockpit/stations"),
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
