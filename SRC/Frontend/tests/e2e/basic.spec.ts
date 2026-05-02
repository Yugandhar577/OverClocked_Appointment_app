import { expect, test } from "@playwright/test"

test("home renders appointment booking shell", async ({ page }) => {
  await page.goto("/")
  await expect(page.getByRole("heading", { name: "Book an appointment" })).toBeVisible()
})
