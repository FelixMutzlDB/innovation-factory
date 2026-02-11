import { createFileRoute, Navigate } from "@tanstack/react-router";

export const Route = createFileRoute("/projects/bsh-home-connect/")({
  component: () => <Navigate to="/projects/bsh-home-connect/dashboard" />,
});
