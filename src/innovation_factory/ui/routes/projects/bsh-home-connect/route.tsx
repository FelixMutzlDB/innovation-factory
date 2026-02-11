import SidebarLayout from "@/components/apx/sidebar-layout";
import { createFileRoute, Link, useLocation } from "@tanstack/react-router";
import { cn } from "@/lib/utils";
import { LayoutDashboard, Smartphone, Ticket, HeadphonesIcon, User } from "lucide-react";
import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuItem,
} from "@/components/ui/sidebar";

export const Route = createFileRoute("/projects/bsh-home-connect")({
  component: () => <Layout />,
});

function Layout() {
  const location = useLocation();

  const navItems = [
    {
      to: "/projects/bsh-home-connect",
      label: "Dashboard",
      icon: <LayoutDashboard size={16} />,
      match: (path: string) => path === "/projects/bsh-home-connect" || path === "/projects/bsh-home-connect/",
    },
    {
      to: "/projects/bsh-home-connect/devices",
      label: "Devices",
      icon: <Smartphone size={16} />,
      match: (path: string) => path.startsWith("/projects/bsh-home-connect/devices"),
    },
    {
      to: "/projects/bsh-home-connect/tickets",
      label: "Tickets",
      icon: <Ticket size={16} />,
      match: (path: string) => path.startsWith("/projects/bsh-home-connect/tickets"),
    },
    {
      to: "/projects/bsh-home-connect/support",
      label: "Support",
      icon: <HeadphonesIcon size={16} />,
      match: (path: string) => path.startsWith("/projects/bsh-home-connect/support"),
    },
    {
      to: "/projects/bsh-home-connect/profile",
      label: "Profile",
      icon: <User size={16} />,
      match: (path: string) => path.startsWith("/projects/bsh-home-connect/profile"),
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
