import { createFileRoute, Navigate } from "@tanstack/react-router";

export const Route = createFileRoute("/projects/vi-home-one/")({
  component: () => <Navigate to="/projects/vi-home-one/households" />,
});
