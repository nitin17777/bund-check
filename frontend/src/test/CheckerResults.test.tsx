import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { CheckerResults } from "@/components/checker/CheckerResults";
import { CheckResponse } from "@/lib/api-client";
import { ToastProvider } from "@/components/ui/Toast";

const mockResult: CheckResponse = {
  analysis_id: "ana_test_123",
  document_id: "doc_test_123",
  synthetic_pattern_confidence: 0.824,
  label: "likely AI-leaning",
  classification_band: "SYNTHETIC_INDICATIVE",
  uncertainty_interval: {
    lower: 0.74,
    upper: 0.89,
    confidence_level: 0.95,
  },
  abstain_band_thresholds: {
    lower: 0.4,
    upper: 0.6,
  },
  reliability_flag: "NORMAL",
  stats: {
    word_count: 320,
    paragraph_count: 2,
    sentence_count: 8,
  },
  top_contributing_signals: [
    {
      name: "perplexity",
      display_name: "Token Perplexity",
      measured_value: 14.2,
      direction: "synthetic_indicative",
      explanation: "Low perplexity indicating predictable token transitions.",
    },
  ],
  paragraphs: [
    {
      index: 0,
      id: "p0",
      synthetic_pattern_confidence: 0.82,
      classification_band: "SYNTHETIC_INDICATIVE",
      sentences: [
        {
          index: 0,
          id: "p0_s0",
          text: "Sentence test analysis text.",
          indicator_score: 0.82,
          status: "EVALUATED",
          is_elevated_homogeneity: true,
          attribution_disclaimer: "Local score only.",
        },
      ],
    },
  ],
  limitations: {
    disclaimer: "This analysis is statistical and does not prove authorship.",
    plain_language_limitations: [
      "Never Absolute Proof",
      "Adversarial Paraphrasing Vulnerability",
    ],
    model_version: "1.0.0",
    model_hash: "51a5e6e06236960b6c734b65f3d45a8c7ad37e90007b570dd1dd7ad0eabcadff",
  },
};

describe("CheckerResults component", () => {
  it("renders calibrated assessment label, confidence, limitations, and statistics", () => {
    const handleReset = vi.fn();
    render(
      <ToastProvider>
        <CheckerResults result={mockResult} onReset={handleReset} />
      </ToastProvider>
    );

    // Exact label wording
    expect(screen.getByText("Likely AI-leaning")).toBeInTheDocument();
    expect(screen.getByText("82.4%")).toBeInTheDocument();
    expect(screen.getByText(/SYNTHETIC_INDICATIVE/i)).toBeInTheDocument();

    // Limitations panel
    expect(screen.getByRole("region", { name: "Scientific Limitations Panel" })).toBeInTheDocument();
    expect(screen.getByText(/This analysis is statistical and does not prove authorship/i)).toBeInTheDocument();
    expect(screen.getByText("Never Absolute Proof")).toBeInTheDocument();

    // Stats
    expect(screen.getByText("320")).toBeInTheDocument();

    // Reset button
    const resetBtn = screen.getByRole("button", { name: /Inspect Another Document/i });
    fireEvent.click(resetBtn);
    expect(handleReset).toHaveBeenCalledTimes(1);
  });
});
