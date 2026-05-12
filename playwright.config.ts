import { defineConfig, devices } from "@playwright/test";

// Default to 9001 (the canonical apx dev port). Override with PW_PORT=NNNN
// when running against a sibling worktree on a different port (apx allocates
// 9000/9001/... based on first free port, so parallel checkouts collide).
const PORT = Number(process.env.PW_PORT) || 9001;
const BASE_URL = `http://localhost:${PORT}`;

export default defineConfig({
  testDir: "tests/visual",
  testMatch: /.*\.spec\.ts$/,
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  reporter: [["list"]],
  expect: {
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
      name: "chromium",
      use: { ...devices["Desktop Chrome"], viewport: { width: 1280, height: 800 } },
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
