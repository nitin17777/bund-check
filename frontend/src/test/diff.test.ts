import { describe, it, expect } from "vitest";
import { computeWordDiff, tokenizeWords } from "../lib/diff";

describe("Word-level Diff Engine", () => {
  it("handles identical texts cleanly", () => {
    const text = "The methodology was rigorous and fully documented.";
    const diff = computeWordDiff(text, text);
    expect(diff).toEqual([{ type: "equal", value: text }]);
  });

  it("handles empty original and empty revised", () => {
    expect(computeWordDiff("", "")).toEqual([]);
  });

  it("handles pure insertion", () => {
    const diff = computeWordDiff("", "New sentence added.");
    expect(diff).toEqual([{ type: "insert", value: "New sentence added." }]);
  });

  it("handles pure deletion", () => {
    const diff = computeWordDiff("Deleted sentence.", "");
    expect(diff).toEqual([{ type: "delete", value: "Deleted sentence." }]);
  });

  it("identifies single word replacement", () => {
    const diff = computeWordDiff("The quick brown fox jumps.", "The fast brown fox jumps.");
    expect(diff).toEqual([
      { type: "equal", value: "The " },
      { type: "delete", value: "quick" },
      { type: "insert", value: "fast" },
      { type: "equal", value: " brown fox jumps." },
    ]);
  });

  it("preserves punctuation, numbers, and citations exactly", () => {
    const orig = "Results in Area 51 (Smith et al., 2021) were 42.8% positive.";
    const rev = "Findings in Area 51 (Smith et al., 2021) were 42.8% positive.";
    const diff = computeWordDiff(orig, rev);
    
    // Protected values must be in equal tokens
    const equalValues = diff.filter((t) => t.type === "equal").map((t) => t.value).join("");
    expect(equalValues).toContain("Area 51");
    expect(equalValues).toContain("(Smith et al., 2021)");
    expect(equalValues).toContain("42.8%");
  });

  it("handles multi-line text with newlines", () => {
    const orig = "Paragraph one.\n\nParagraph two.";
    const rev = "Section one.\n\nParagraph two.";
    const diff = computeWordDiff(orig, rev);
    expect(diff.some((t) => t.type === "delete" && t.value === "Paragraph")).toBe(true);
    expect(diff.some((t) => t.type === "insert" && t.value === "Section")).toBe(true);
    expect(diff.some((t) => t.type === "equal" && t.value.includes("Paragraph two."))).toBe(true);
  });

  it("reconstructs original by taking equal + delete tokens", () => {
    const orig = "Dr. Grant did not find the specimens in sector 4.";
    const rev = "Dr. Grant failed to locate the specimens in sector 4.";
    const diff = computeWordDiff(orig, rev);

    const reconstructedOrig = diff
      .filter((t) => t.type === "equal" || t.type === "delete")
      .map((t) => t.value)
      .join("");
    expect(reconstructedOrig).toBe(orig);

    const reconstructedRev = diff
      .filter((t) => t.type === "equal" || t.type === "insert")
      .map((t) => t.value)
      .join("");
    expect(reconstructedRev).toBe(rev);
  });

  it("tokenizes whitespace and punctuation accurately", () => {
    const tokens = tokenizeWords("Hello, world!  How's it going?");
    expect(tokens.join("")).toBe("Hello, world!  How's it going?");
  });
});
