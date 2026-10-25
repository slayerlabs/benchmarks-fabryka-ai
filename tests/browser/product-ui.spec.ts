import { test, expect } from "@playwright/test";
test.beforeEach(async ({ page }) => {
 await page.route("**/*", route => {
   const url = new URL(route.request().url());
   if (url.hostname !== "127.0.0.1") throw new Error("External request forbidden: " + url.origin);
   return route.continue();
 });
 await page.goto("/models");
 await expect(page.getByRole("table")).toBeVisible();
});
test("primary metric follows identity and secondary metrics remain opt-in", async ({ page }) => {
 const headers = page.getByRole("columnheader");
 await expect(headers.nth(1)).toHaveText("Model");
 await expect(headers.nth(2)).toContainText("eff");
 await expect(page.getByRole("columnheader", { name: /ARC-Easy/ })).toHaveCount(0);
 await page.getByLabel("Show secondary metrics").check();
 await expect(page.getByRole("columnheader", { name: /ARC-Easy/ })).toBeVisible();
 await page.getByRole("button", { name: "PL", exact: true }).click();
 await expect(headers.nth(2)).toContainText("eff-PL");
 await page.getByRole("button", { name: "PL+EN", exact: true }).click();
 await expect(headers.nth(2)).toContainText("PL+EN");
 await expect(page.getByText(/Protocol compatibility is unverified/)).toBeVisible();
});
test("details distinguish unavailable provenance and legacy trust from verification", async ({ page }) => {
 await page.getByText("Details", { exact: true }).first().click();
 const details = page.getByRole("region", { name: /^Evaluation details for/ }).first();
 await expect(details).toContainText("fabryka.provenance-ui/1");
 await expect(details.locator("div").filter({ has: page.locator("dt", { hasText: /^Execution status$/ }) })).toContainText("Unavailable");
 await expect(details.locator("div").filter({ has: page.locator("dt", { hasText: /^Verification status$/ }) })).toContainText("Unavailable");
 await expect(details).toContainText("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa");
 await details.getByText("Logs and reproduction", { exact: true }).click();
 await expect(details.getByText("Logs: Unavailable", { exact: true })).toBeVisible();
});
test("navigation, direct routes, methodology and mobile layout", async ({ page }) => {
 const nav = page.getByRole("navigation", { name: "Main navigation" });
 await nav.getByRole("link", { name: "Benchmarks", exact: true }).click();
 await expect(page.getByRole("heading", { name: "Benchmarks", exact: true })).toBeVisible();
 await expect(page.getByText("en · legacy-display-v1", { exact: true })).toBeVisible();
 await nav.getByRole("link", { name: "About / Methodology" }).click();
 await expect(page.getByRole("heading", { name: "About / Methodology" })).toBeVisible();
 await expect(page.getByText(/fabryka.scoring\/1.0 is a draft contract proposal/)).toBeVisible();
 await page.reload();
 await expect(page.getByRole("heading", { name: "About / Methodology" })).toBeVisible();
 await page.goBack();
 await page.goto("/");
 await expect(page).toHaveURL(/\/models$/);
 await page.setViewportSize({ width: 390, height: 844 });
 await expect(nav).toBeVisible();
 await expect(page.getByRole("region", { name: "EN model results" })).toBeVisible();
 expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});
test("AutoEval is explicitly disconnected and status examples never create results", async ({ page }) => {
 await page.getByRole("navigation").getByRole("link", { name: "AutoEval" }).click();
 await expect(page.getByRole("heading", { name: "AutoEval", exact: true })).toBeVisible();
 await page.getByLabel("Hugging Face repository").fill("example/test-model");
 await page.getByLabel("Pinned model revision").fill("a".repeat(40));
 await page.getByLabel("Checkpoint selection").fill("model.safetensors");
 await expect(page.getByRole("button", { name: "Run evaluation — not connected" })).toBeDisabled();
 await expect(page.getByText(/Execution unavailable:/)).toBeVisible();
 for (const state of ["Validating","Loading model","Evaluating","Completed","Failed","Pending"]) {
   await page.getByLabel("Inspect an example state").selectOption(state);
   await expect(page.getByRole("status")).toContainText("Illustrative execution status: " + state);
   await expect(page.getByText(/Results and provenance: unavailable/)).toBeVisible();
 }
 await page.reload();
 await expect(page.getByRole("status")).toContainText("Pending");
});
