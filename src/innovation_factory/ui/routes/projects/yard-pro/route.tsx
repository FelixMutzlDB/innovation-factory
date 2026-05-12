import SidebarLayout from "@/components/apx/sidebar-layout";
import { ProjectThemeScope } from "@/components/apx/project-theme-scope";
import { createFileRoute, Link, useLocation } from "@tanstack/react-router";
import { cn } from "@/lib/utils";
import { Sprout, MessageCircle } from "lucide-react";
import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuItem,
} from "@/components/ui/sidebar";

export const Route = createFileRoute("/projects/yard-pro")({
  component: () => <Layout />,
});

function Layout() {
  const location = useLocation();

  const navItems = [
    {
      to: "/projects/yard-pro",
      label: "Cockpit",
      icon: <Sprout size={16} />,
      match: (path: string) =>
        path === "/projects/yard-pro" ||
        path === "/projects/yard-pro/",
    },
    {
      to: "/projects/yard-pro/coach",
      label: "Coach",
      icon: <MessageCircle size={16} />,
      match: (path: string) => path.startsWith("/projects/yard-pro/coach"),
    },
  ];

  return (
    <ProjectThemeScope slug="yard-pro">
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
    </ProjectThemeScope>
  );
}
