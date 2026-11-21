import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { SentenceHeatmap } from "@/components/checker/SentenceHeatmap";
import { ParagraphDetectionResult } from "@/lib/api-client";

const mockParagraphs: ParagraphDetectionResult[] = [
  {
    index: 0,
    id: "p0",
    synthetic_pattern_confidence: 0.85,
    classification_band: "SYNTHETIC_INDICATIVE",
    sentences: [
      {
        index: 0,
        id: "p0_s0",
        text: "The model demonstrates high uniformity.",
        indicator_score: 0.88,
        status: "EVALUATED",
        is_elevated_homogeneity: true,
        attribution_disclaimer: "Local indicator only.",
      },
      {
        index: 1,
        id: "p0_s1",
        text: "In contrast, human writing exhibits substantial variance.",
        indicator_score: 0.15,
        status: "EVALUATED",
        is_elevated_homogeneity: false,
        attribution_disclaimer: "Local indicator only.",
      },
    ],
  },
];

describe("SentenceHeatmap component", () => {
  it("renders sentences and opens sentence detail popover on click", () => {
    render(<SentenceHeatmap paragraphs={mockParagraphs} />);

    expect(screen.getByText(/The model demonstrates high uniformity/i)).toBeInTheDocument();
    expect(screen.getByText(/In contrast, human writing exhibits substantial variance/i)).toBeInTheDocument();

    // Click first sentence
    fireEvent.click(screen.getByText(/The model demonstrates high uniformity/i));

    // Popover drawer should appear
    expect(screen.getByRole("region", { name: "Sentence Analysis Inspector" })).toBeInTheDocument();
    expect(screen.getByText("88.0%")).toBeInTheDocument();
    expect(screen.getByText("Elevated Homogeneity")).toBeInTheDocument();
  });

  it("filters sentences by category", () => {
    render(<SentenceHeatmap paragraphs={mockParagraphs} />);

    const elevatedTab = screen.getByRole("tab", { name: /Elevated Synthetic/i });
    fireEvent.click(elevatedTab);

    expect(elevatedTab).toHaveAttribute("aria-selected", "true");
  });
});
