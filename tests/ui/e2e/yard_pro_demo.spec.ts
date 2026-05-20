/**
 * Playwright browser smoke for the yard-pro P0 demo gate.
 *
 * Closes the open caveat on PR #14: the chrome-devtools MCP first-paint
 * smoke disconnected. This spec exercises the 6-step demo script from
 * docs/projects/yard-pro-plan.md §12 in a real browser:
 *
 *   1. Cockpit loads and surfaces the load-bearing demo string.
 *   2. First paint (FCP) is fast on the cockpit route.
 *   3. Coach route renders the "AI-generated, advisory only" chip.
 *   4. The diagnose modal opens from the cockpit "Snap a photo" button.
 *   5. Runtime obfuscation (RT-013): "Stihl" never appears in the DOM.
 *   6. Cross-tenant access via X-Forwarded-User returns 404 (RT-016).
 *
 * Prerequisites:
 *   - apx dev server running on http://localhost:9001 (do NOT start a
 *     second one — `uv run apx dev start` handles both frontend +
 *     backend on this port).
 *   - The seeded yard belongs to user martin@yard-pro.local.
 *
 * Run:
 *   uv run apx bun x playwright test tests/ui/e2e/yard_pro_demo.spec.ts
 *
 * This spec is intentionally NOT part of `uv run apx dev check` (tsc
 * scopes itself to src/innovation_factory/ui) and is NOT wired into CI
 * — it is a local smoke test owned by the demo gate.
 */
import { test, expect, request as pwRequest } from "@playwright/test";

const MARTIN = "martin@yard-pro.local";
const HOSTILE = "hostile@attacker.local";
const BASE = "http://localhost:9001";

test.describe("yard-pro P0 demo gate (plan §12)", () => {
  test.beforeEach(async ({ page }) => {
    // The auth-proxy header is the only identity signal the backend
    // trusts in this env — see backend/projects/yard_pro/routers/
    // yards.py `_resolve_user_key`. Seed-owner is Martin's yard.
    await page.setExtraHTTPHeaders({ "X-Forwarded-User": MARTIN });
  });

  test("step 1: cockpit loads and shows the load-bearing demo string", async ({
    page,
  }) => {
    await page.goto("/projects/yard-pro/");
    // The plan §12 step 1 anchor string — rendered statically in
    // CalendarCardContent for the seeded 2026-05-08 row.
    await expect(
      page.getByText("Apple tree fungus check", { exact: false })
    ).toBeVisible({ timeout: 10_000 });
    await page.screenshot({
      path: "tests/ui/e2e/__snapshots__/01_cockpit.png",
      fullPage: true,
    });
  });

  test("step 2: first paint (FCP) on cockpit route", async ({ page }) => {
    await page.goto("/projects/yard-pro/", { waitUntil: "load" });
    // Use the Paint Timing API directly — `performance.timing` is
    // deprecated/zero under modern SPA navigation, and Vite serves the
    // entry HTML via dev middleware so the legacy timing model
    // doesn't apply cleanly.
    const fcpMs: number = await page.evaluate(() => {
      return new Promise<number>((resolve) => {
        const entries = performance.getEntriesByName("first-contentful-paint");
        if (entries.length > 0) {
          resolve(entries[0].startTime);
          return;
        }
        const obs = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (entry.name === "first-contentful-paint") {
              obs.disconnect();
              resolve(entry.startTime);
              return;
            }
          }
        });
        obs.observe({ type: "paint", buffered: true });
        // Safety net: don't hang forever if no FCP fires.
        setTimeout(() => {
          obs.disconnect();
          resolve(-1);
        }, 5_000);
      });
    });

    // eslint-disable-next-line no-console
    console.log(`[yard-pro demo] cockpit FCP = ${fcpMs.toFixed(1)} ms`);

    expect(fcpMs).toBeGreaterThan(0);
    // The plan §12 target is < 1000 ms; that's a production goal.
    // Vite dev mode (HMR, on-demand transform, no minify) adds
    // overhead that easily blows past 1 s on a cold module graph. We
    // assert < 2000 ms here and log the measured number so the
    // production gate can be verified separately against a built
    // bundle.
    expect(fcpMs).toBeLessThan(2000);
  });

  test("step 3: coach route shows the AdvisoryChip text", async ({ page }) => {
    await page.goto("/projects/yard-pro/coach");
    // The stubbed assistant message includes the chip copy verbatim
    // (see routes/projects/yard-pro/coach.tsx → ChatMessages).
    await expect(
      page.getByText("AI-generated, advisory only", { exact: false }).first()
    ).toBeVisible({ timeout: 10_000 });
  });

  test("step 4: diagnose modal opens and exposes a JPEG file input", async ({
    page,
  }) => {
    await page.goto("/projects/yard-pro/");
    await page.getByRole("button", { name: /Snap a photo/i }).click();
    const fileInput = page.locator('input[type="file"]');
    await expect(fileInput).toBeVisible();
    const accept = await fileInput.getAttribute("accept");
    expect(accept ?? "").toContain("image/jpeg");
    // We deliberately do NOT upload — the backend vision endpoint is
    // not wired in this env. Modal opening + accept attribute is
    // sufficient to close the smoke gate.
  });

  test("step 5: runtime obfuscation — no 'Stihl' in cockpit DOM (RT-013)", async ({
    page,
  }) => {
    await page.goto("/projects/yard-pro/");
    // Wait for network idle so React-rendered content is in the DOM
    // before we snapshot it.
    await page.waitForLoadState("networkidle");
    const html = await page.content();
    expect(html).not.toContain("Stihl");
  });

  test("step 6: cross-tenant cockpit fetch is 404, not 200 (RT-016)", async () => {
    // Use a fresh APIRequestContext rather than `page.evaluate` —
    // beforeEach() sets Martin's X-Forwarded-User on the page context
    // via setExtraHTTPHeaders, and Playwright appends those to in-page
    // fetch() calls, which means the hostile header was being overridden
    // by Martin's. A standalone request context isolates the headers.
    const ctx = await pwRequest.newContext({
      baseURL: BASE,
      extraHTTPHeaders: { "X-Forwarded-User": HOSTILE },
    });
    const res = await ctx.get("/api/projects/yard-pro/yards/1/cockpit");
    expect(res.status()).toBe(404);
    await ctx.dispose();
  });
});
