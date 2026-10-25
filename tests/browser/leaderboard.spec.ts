import { test, expect } from "@playwright/test";

test.beforeEach(async ({ page }) => {
 // Fail any nonlocal request, including accidental production integrations.
 await page.route("**/*", route => {
   const url = new URL(route.request().url());
   if (url.hostname !== "127.0.0.1") throw new Error("External request forbidden: " + url.origin);
   return route.continue();
 });
 await page.goto("/models");
 await expect(page.getByRole("table")).toBeVisible();
});

test("fixture labels, trust presentation and provenance", async ({ page }) => {
 await expect(page.getByRole("note")).toContainText("synthetic test data");
 for (const label of ["verified ✓", "measured by Fabryka", "self-reported"]) {
   await expect(page.getByText(label, { exact: true }).first()).toBeVisible();
 }
 await page.getByText("Details", { exact: true }).first().click();
 await expect(page.getByText(/ckpt aaaaaaaa/)).toBeVisible();
 await page.getByRole("group", { name: "Language" }).getByRole("button", { name: "PL", exact: true }).click();
 await expect(page.getByText("measured by track", { exact: true })).toBeVisible();
 const external = page.getByRole("row").filter({ hasText: "External tie" });
 await expect(external).toContainText("65.00†");
 const reported = page.getByRole("row").filter({ hasText: "Self-reported 64M" });
 await expect(reported).not.toContainText("†");
 await page.getByLabel("Hide self-reported").check();
 await expect(reported).toHaveCount(0);
 await expect(page.getByText("measured by track", { exact: true })).toBeVisible();
});

test("category, filter, rank and sort controls preserve semantics", async ({ page }) => {
 const rows = page.locator("tbody tr");
 await expect(rows).toHaveCount(4);
 await expect(rows.nth(0).locator("td").first()).toHaveText("1");
 await expect(rows.nth(1).locator("td").first()).toHaveText("1");
 await expect(rows.nth(2).locator("td").first()).toHaveText("3");
 await page.getByRole("columnheader", { name: /^eff / }).getByRole("button").click();
 await expect(rows.first()).toContainText("EN only");
 await expect(rows.first().locator("td").first()).toHaveText("4");
 await page.getByRole("group", { name: "Ranking", exact: true }).getByRole("button", { name: "Overall" }).click();
 await expect(page.getByRole("columnheader", { name: /Overall/ })).toHaveAttribute("aria-sort", "descending");
 await page.getByRole("button", { name: /^≤16M/ }).click();
 await expect(rows).toHaveCount(1);
 await page.getByRole("button", { name: /^All sizes/ }).click();
 await page.getByRole("button", { name: /^PL\+EN/ }).click();
 await expect(rows).toHaveCount(3);
 await page.getByRole("group", { name: "Language" }).getByRole("button", { name: "PL", exact: true }).click();
 await expect(rows).toHaveCount(5);
 await expect(rows.nth(3).locator("td").first()).toHaveText("—");
 await expect(rows.nth(3)).toContainText("Track PL only");
 await page.setViewportSize({ width: 390, height: 844 });
 await expect(page.getByRole("region", { name: "PL model results" })).toBeVisible();
});
