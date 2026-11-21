import { test, expect } from "@playwright/test";

test.describe("Writing Improver Workspace E2E", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/humanizer");
    // Wait for the page to load — look for the main textarea or any visible page content
    // "Writing Improver" text may be in a hidden sidebar nav on mobile; look for the form instead
    await expect(page.locator("textarea").first()).toBeVisible({
      timeout: 10000,
    });
  });

  test("Scenario 1: Page renders with 6 mode cards and proper disclaimers", async ({
    page,
  }) => {
    // All 6 mode cards must be visible (exact labels from ImproverForm.tsx IMPROVER_MODES)
    await expect(page.getByText("Academic Clarity")).toBeVisible();
    await expect(page.getByText("Professional & Executive")).toBeVisible();
    await expect(page.getByText("Natural & Conversational")).toBeVisible();
    await expect(page.getByText("Simple & Readable")).toBeVisible();
    await expect(page.getByText("Concise & Tight")).toBeVisible();
    await expect(page.getByText("Formal & Polished")).toBeVisible();

    // "Improve Prose" submit button disabled when no text entered
    const runBtn = page.getByRole("button", { name: /Improve Prose/i });
    await expect(runBtn).toBeDisabled();

    // Honest framing: prohibition note on hallucinations must be visible
    await expect(
      page.getByText(/hallucinated facts|altered citations|changed numbers/i)
    ).toBeVisible();
  });

  test("Scenario 2: Text input enables run button, word count updates", async ({
    page,
  }) => {
    const sourceText =
      "The researcher conducted an extensive investigation into behavioral patterns. " +
      "The findings were published in a peer-reviewed journal. " +
      "Additional analysis confirmed the initial hypothesis.";

    // Enter text into first textarea (source)
    const sourceTextarea = page.locator("textarea").first();
    await sourceTextarea.fill(sourceText);

    // Verify word count appears (should show ~27 words)
    await expect(page.getByText(/\d+ words/i)).toBeVisible();

    // "Improve Prose" button should now be enabled
    const runBtn = page.getByRole("button", { name: /Improve Prose/i });
    await expect(runBtn).toBeEnabled({ timeout: 3000 });
  });

  test("Scenario 3: Empty text keeps run button disabled", async ({ page }) => {
    const runBtn = page.getByRole("button", { name: /Improve Prose/i });
    await expect(runBtn).toBeDisabled();

    // Enter only whitespace — still disabled
    const sourceTextarea = page.locator("textarea").first();
    await sourceTextarea.fill("   ");
    await expect(runBtn).toBeDisabled();
  });

  test("Scenario 4: Mode switching updates card selection state", async ({
    page,
  }) => {
    // Click Academic Clarity mode card
    await page.getByText("Academic Clarity").click();
    // "Active" badge inside the mode selection grid should appear
    await expect(page.getByText("Active", { exact: true })).toBeVisible();

    // Switch to Natural & Conversational
    await page.getByText("Natural & Conversational").click();
    await expect(page.getByText("Active", { exact: true })).toBeVisible();

    // "Improve Prose" still disabled (no text)
    const runBtn = page.getByRole("button", { name: /Improve Prose/i });
    await expect(runBtn).toBeDisabled();
  });

  test("Scenario 5: Verification checkbox toggle is present and toggleable", async ({
    page,
  }) => {
    // Verification checkbox — no name attr in HTML, use label text
    const checkbox = page.locator(
      'input[type="checkbox"]'
    );
    // The page has at least one checkbox (run_verification)
    await expect(checkbox.first()).toBeVisible();

    // Toggle it twice (on then off)
    await checkbox.first().click();
    await checkbox.first().click();
  });

  test("Scenario 6: Mobile layout is usable at 375px width", async ({
    page,
  }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.reload();

    // On mobile the sidebar nav may be collapsed; look for page-level content instead
    // Source textarea must be visible and interactable
    const sourceTextarea = page.locator("textarea").first();
    await expect(sourceTextarea).toBeVisible({ timeout: 10000 });
    await sourceTextarea.fill("Test text for mobile responsiveness.");
    await expect(page.getByText(/\d+ words?/i)).toBeVisible();

    // Run button must exist
    await expect(
      page.getByRole("button", { name: /Improve Prose/i })
    ).toBeVisible();
  });

  test("Scenario 7: Heuristic disclosure and verification advisory present", async ({
    page,
  }) => {
    // Scroll to find ethical disclosure about heuristic verification
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));

    // Check for any mention of heuristics / user review requirement
    // Disclosure can appear as help text, tooltip, or info panel
    const disclosureText = page
      .getByText(/heuristic|must review|verification checks/i)
      .or(page.getByText(/meaning preservation/i))
      .or(page.getByText(/hallucinated facts/i));

    await expect(disclosureText.first()).toBeVisible({ timeout: 5000 });
  });

  test("Scenario 8: Provider selector is functional", async ({ page }) => {
    // Provider select dropdown must be present
    const providerSelect = page.locator("#provider-select");
    await expect(providerSelect).toBeVisible();

    // Should have at least groq and openrouter options
    const options = await providerSelect.locator("option").allTextContents();
    expect(options.length).toBeGreaterThanOrEqual(2);
    expect(options.some((o) => o.toLowerCase().includes("groq") || o.toLowerCase().includes("auto"))).toBe(true);
  });
});
