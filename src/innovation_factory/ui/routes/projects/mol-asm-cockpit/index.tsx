import { createFileRoute, Navigate } from "@tanstack/react-router";

export const Route = createFileRoute("/projects/mol-asm-cockpit/")({
  component: () => <Navigate to="/projects/mol-asm-cockpit/home" />,
});
