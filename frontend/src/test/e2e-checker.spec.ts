import { test, expect } from "@playwright/test";
import path from "path";

const FIXTURES_DIR = path.resolve(__dirname, "../../../tests/fixtures");

test.describe("AI Content Checker Workspace E2E", () => {
  test("Scenario 1: Paste multi-paragraph text with Unicode & verify heatmap offsets and popover", async ({
    page,
  }) => {
    await page.goto("/checker");

    // Multi-paragraph test text with Unicode (café, naïve, em-dash, smart quotes, mathematical symbols)
    const unicodeText = `The study examined several cafés and naïve participants during the experimental phase — observing behavioral traits across diverse conditions. Overall performance was evaluated using standard metrics, and results showed significant variance across groups.

A secondary analysis evaluated the mathematical α-helix and β-sheet formations in synthetic protein sequences. "The findings indicate strong alignment with prior literature," stated the principal investigator. Additional trials confirmed that numerical stability was preserved under all test temperatures.`;

    // Paste text into textarea
    const textarea = page.locator("#content-textarea");
    await textarea.fill(unicodeText);

    // Verify word count live feedback
    await expect(page.getByText("71 words")).toBeVisible();

    // Click "Inspect Content"
    const inspectBtn = page.getByRole("button", { name: /Inspect Content/i });
    await inspectBtn.click();

    // Verify results view renders
    await expect(page.locator("text=Synthetic Pattern Confidence")).toBeVisible({ timeout: 25000 });
    await expect(page.getByRole("region", { name: "Scientific Limitations Panel" })).toBeVisible();

    // Verify calibrated label badge wording is from API
    const labelBadge = page.locator("text=/Likely human-leaning|Inconclusive|Likely AI-leaning/i");
    await expect(labelBadge.first()).toBeVisible();

    // Verify document statistics
    await expect(page.locator("text=Total Words")).toBeVisible();
    await expect(page.locator("text=Paragraphs")).toBeVisible();
    await expect(page.getByText("Sentences", { exact: true })).toBeVisible();

    // Verify heatmap rendered both paragraphs and preserved Unicode characters
    await expect(page.getByText(/cafés and naïve participants/i)).toBeVisible();
    await expect(page.getByText(/mathematical α-helix/i)).toBeVisible();

    // Click first sentence to trigger popover
    const firstSentence = page.getByText(/The study examined several cafés/i);
    await firstSentence.click();

    // Verify popover drawer appears with local indicator and attribution disclaimer
    const popover = page.getByRole("region", { name: "Sentence Analysis Inspector" });
    await expect(popover).toBeVisible();
    await expect(popover.getByText(/Local Synthetic Indicator:/i)).toBeVisible();
    await expect(popover.getByText(/Attribution Disclaimer:/i)).toBeVisible();

    // Close popover
    await page.getByRole("button", { name: "Close sentence detail" }).click({ force: true });
    await expect(popover).not.toBeVisible();

    // Verify sentence filter tabs work
    const allTab = page.getByRole("tab", { name: /All Sentences/i });
    await expect(allTab).toHaveAttribute("aria-selected", "true");

    const humanTab = page.getByRole("tab", { name: /Human-Typical/i });
    await humanTab.click();
    await expect(humanTab).toHaveAttribute("aria-selected", "true");
  });

  test("Scenario 2: Download analysis report in HTML and JSON format", async ({ page }) => {
    await page.goto("/checker");

    const sampleText = `This is a comprehensive research evaluation document written to verify report export capabilities. The experiment ran over several weeks and collected metrics across thirty distinct participant cohorts. Statistical tests confirmed all baseline assumptions and demonstrated robust calibration.`;
    await page.locator("#content-textarea").fill(sampleText);
    await page.getByRole("button", { name: /Inspect Content/i }).click();

    await expect(page.locator("text=Synthetic Pattern Confidence")).toBeVisible({ timeout: 25000 });

    // Download HTML report
    const [htmlDownload] = await Promise.all([
      page.waitForEvent("download"),
      page.getByRole("button", { name: /HTML Report/i }).click(),
    ]);
    expect(htmlDownload.suggestedFilename()).toMatch(/\.html$/i);

    // Download JSON report
    const [jsonDownload] = await Promise.all([
      page.waitForEvent("download"),
      page.getByRole("button", { name: /JSON/i }).click(),
    ]);
    expect(jsonDownload.suggestedFilename()).toMatch(/\.json$/i);
  });

  test("Scenario 3: Upload real TXT document fixture", async ({ page }) => {
    await page.goto("/checker");

    // Switch to Upload File tab
    await page.getByRole("tab", { name: "Upload File" }).click();

    // Upload sample_document.txt
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(path.join(FIXTURES_DIR, "sample_document.txt"));

    await expect(page.getByText("sample_document.txt")).toBeVisible();

    // Click inspect
    await page.getByRole("button", { name: /Inspect Content/i }).click();

    await expect(page.locator("text=Synthetic Pattern Confidence")).toBeVisible({ timeout: 25000 });
  });

  test("Scenario 4: Upload real DOCX document fixture", async ({ page }) => {
    await page.goto("/checker");
    await page.getByRole("tab", { name: "Upload File" }).click();

    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(path.join(FIXTURES_DIR, "sample_report.docx"));

    await expect(page.getByText("sample_report.docx")).toBeVisible();
    await page.getByRole("button", { name: /Inspect Content/i }).click();

    await expect(page.locator("text=Synthetic Pattern Confidence")).toBeVisible({ timeout: 25000 });
  });

  test("Scenario 5: Upload real PDF document fixture", async ({ page }) => {
    await page.goto("/checker");
    await page.getByRole("tab", { name: "Upload File" }).click();

    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(path.join(FIXTURES_DIR, "valid_research.pdf"));

    await expect(page.getByText("valid_research.pdf")).toBeVisible();
    await page.getByRole("button", { name: /Inspect Content/i }).click();

    await expect(page.locator("text=Synthetic Pattern Confidence")).toBeVisible({ timeout: 25000 });
  });

  test("Scenario 6: Trigger Scanned PDF error state", async ({ page }) => {
    await page.goto("/checker");
    await page.getByRole("tab", { name: "Upload File" }).click();

    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(path.join(FIXTURES_DIR, "scanned_image_only.pdf"));

    await page.getByRole("button", { name: /Inspect Content/i }).click();

    // Should display actionable message
    await expect(
      page.getByText(/Scanned PDF \(OCR Not Supported\)/i)
    ).toBeVisible({ timeout: 15000 });
    await expect(
      page.getByText(/The uploaded PDF appears to be scanned or image-only/i)
    ).toBeVisible();
  });

  test("Scenario 7: Trigger empty and short text error states", async ({ page }) => {
    await page.goto("/checker");

    // Empty text
    await page.locator("#content-textarea").fill("   ");
    // Button is disabled when text is empty
    const inspectBtn = page.getByRole("button", { name: /Inspect Content/i });
    await expect(inspectBtn).toBeDisabled();

    // Short text (< 10 words)
    await page.locator("#content-textarea").fill("Too short.");
    await inspectBtn.click();
    await expect(page.getByText(/Text Too Short/i)).toBeVisible();
    await expect(page.getByText(/fewer than 10 words/i)).toBeVisible();
  });
});
