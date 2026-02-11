import SidebarLayout from "@/components/apx/sidebar-layout";
import { createFileRoute, Link, useLocation } from "@tanstack/react-router";
import { cn } from "@/lib/utils";
import { Home, MapPin, HeadphonesIcon, User } from "lucide-react";
import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuItem,
} from "@/components/ui/sidebar";

export const Route = createFileRoute("/projects/vi-home-one")({
  component: () => <Layout />,
});

function Layout() {
  const location = useLocation();

  const navItems = [
    {
      to: "/projects/vi-home-one",
      label: "Dashboard",
      icon: <Home size={16} />,
      match: (path: string) => path === "/projects/vi-home-one" || path === "/projects/vi-home-one/",
    },
    {
      to: "/projects/vi-home-one/households",
      label: "Households",
      icon: <Home size={16} />,
      match: (path: string) => path.startsWith("/projects/vi-home-one/households"),
    },
    {
      to: "/projects/vi-home-one/neighborhood",
      label: "Neighborhood",
      icon: <MapPin size={16} />,
      match: (path: string) => path.startsWith("/projects/vi-home-one/neighborhood"),
    },
    {
      to: "/projects/vi-home-one/support",
      label: "Support",
      icon: <HeadphonesIcon size={16} />,
      match: (path: string) => path.startsWith("/projects/vi-home-one/support"),
    },
    {
      to: "/projects/vi-home-one/profile",
      label: "Profile",
      icon: <User size={16} />,
      match: (path: string) => path.startsWith("/projects/vi-home-one/profile"),
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
