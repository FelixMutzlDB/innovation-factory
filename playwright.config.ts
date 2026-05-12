/**
 * Playwright config — local browser smoke for the yard-pro demo gate.
 *
 * Scope: closes the open caveat on PR #14 (yard-pro P0). The plan §12
 * 6-step demo script is the acceptance gate. This config is local-only
 * and is NOT wired into CI runs.
 *
 * Prerequisites:
 *   - apx dev server already running on http://localhost:9001
 *     (`uv run apx dev start`). Do not start a second dev server.
 *
 * Run:
 *   uv run apx bun x playwright test tests/ui/e2e/yard_pro_demo.spec.ts
 */
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/ui/e2e",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  reporter: [["list"]],
  use: {
    baseURL: "http://localhost:9001",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
