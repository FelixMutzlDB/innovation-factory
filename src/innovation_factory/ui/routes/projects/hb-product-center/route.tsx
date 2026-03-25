import SidebarLayout from "@/components/apx/sidebar-layout";
import { createFileRoute, Link, useLocation } from "@tanstack/react-router";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  ScanSearch,
  ShieldCheck,
  Fingerprint,
  Truck,
  User,
} from "lucide-react";
import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuItem,
} from "@/components/ui/sidebar";

export const Route = createFileRoute("/projects/hb-product-center")({
  component: () => <Layout />,
});

function Layout() {
  const location = useLocation();

  const navItems = [
    {
      to: "/projects/hb-product-center",
      label: "Overview",
      icon: <LayoutDashboard size={16} />,
      match: (path: string) =>
        path === "/projects/hb-product-center" ||
        path === "/projects/hb-product-center/",
    },
    {
      to: "/projects/hb-product-center/recognition",
      label: "Visual Recognition",
      icon: <ScanSearch size={16} />,
      match: (path: string) =>
        path.startsWith("/projects/hb-product-center/recognition"),
    },
    {
      to: "/projects/hb-product-center/quality",
      label: "Quality Control",
      icon: <ShieldCheck size={16} />,
      match: (path: string) =>
        path.startsWith("/projects/hb-product-center/quality"),
    },
    {
      to: "/projects/hb-product-center/authenticity",
      label: "Authenticity",
      icon: <Fingerprint size={16} />,
      match: (path: string) =>
        path.startsWith("/projects/hb-product-center/authenticity"),
    },
    {
      to: "/projects/hb-product-center/supply-chain",
      label: "Supply Chain",
      icon: <Truck size={16} />,
      match: (path: string) =>
        path.startsWith("/projects/hb-product-center/supply-chain"),
    },
    {
      to: "/projects/hb-product-center/profile",
      label: "Profile",
      icon: <User size={16} />,
      match: (path: string) =>
        path.startsWith("/projects/hb-product-center/profile"),
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
