import { defineConfig, devices } from "@playwright/test";

// Default to 9001 (the canonical apx dev port). Override with PW_PORT=NNNN
// when running against a sibling worktree on a different port (apx allocates
// 9000/9001/... based on first free port, so parallel checkouts collide).
const PORT = Number(process.env.PW_PORT) || 9001;
const BASE_URL = `http://localhost:${PORT}`;

export default defineConfig({
  // Each project below sets its own testDir. The top-level testMatch
  // applies to both: any .spec.ts under the project's testDir.
  testMatch: /.*\.spec\.ts$/,
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  reporter: [["list"]],
  expect: {
    // Visual regression tolerance for the brand-themes spec (master).
    // The yard-pro smoke spec uses raw assertions, not toHaveScreenshot,
    // so this knob doesn't affect it.
    toHaveScreenshot: {
      maxDiffPixelRatio: 0.001,
      animations: "disabled",
      caret: "hide",
      scale: "css",
    },
  },
  use: {
    baseURL: BASE_URL,
    viewport: { width: 1280, height: 800 },
    screenshot: "only-on-failure",
    trace: "off",
    video: "off",
  },
  projects: [
    {
      // Brand-theme visual regression (master) — pixelmatch baselines
      // under tests/visual/baselines/<slug>/<light|dark>.png.
      name: "visual",
      testDir: "tests/visual",
      use: {
        ...devices["Desktop Chrome"],
        viewport: { width: 1280, height: 800 },
      },
    },
    {
      // yard-pro functional browser smoke (PR #14 demo gate) — opens
      // the cockpit + coach, asserts the load-bearing strings, checks
      // the runtime obfuscation guard, and probes RT-016 cross-tenant.
      // See tests/ui/e2e/yard_pro_demo.spec.ts.
      name: "yard-pro-smoke",
      testDir: "tests/ui/e2e",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: {
    command: "uv run apx dev start",
    url: BASE_URL,
    reuseExistingServer: true,
    timeout: 120_000,
    stdout: "pipe",
    stderr: "pipe",
  },
});
