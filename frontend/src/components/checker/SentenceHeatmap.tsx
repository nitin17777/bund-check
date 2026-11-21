"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import {
  ParagraphDetectionResult,
  SentenceIndicator,
} from "@/lib/api-client";
import { Badge } from "@/components/ui/Badge";
import { AlertCircle, HelpCircle, X, Sliders } from "lucide-react";

interface SentenceHeatmapProps {
  paragraphs: ParagraphDetectionResult[];
  className?: string;
}

type FilterCategory = "all" | "elevated" | "inconclusive" | "human";

export function SentenceHeatmap({ paragraphs, className }: SentenceHeatmapProps) {
  const [selectedSentence, setSelectedSentence] = React.useState<SentenceIndicator | null>(null);
  const [activeFilter, setActiveFilter] = React.useState<FilterCategory>("all");

  const getSentenceCategory = (s: SentenceIndicator): FilterCategory => {
    if (s.is_elevated_homogeneity || (s.indicator_score !== null && s.indicator_score !== undefined && s.indicator_score > 0.6)) {
      return "elevated";
    }
    if (s.indicator_score !== null && s.indicator_score !== undefined && s.indicator_score >= 0.4) {
      return "inconclusive";
    }
    return "human";
  };

  const getSentenceStyle = (s: SentenceIndicator) => {
    const category = getSentenceCategory(s);
    const matchesFilter = activeFilter === "all" || activeFilter === category;

    let baseStyle = "transition-all duration-150 inline rounded px-0.5 py-0.5 mx-0.5 cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent";

    if (!matchesFilter) {
      return cn(baseStyle, "opacity-30 hover:opacity-90");
    }

    if (category === "elevated") {
      return cn(
        baseStyle,
        "bg-semantic-critical-subtle text-text-primary border-b-2 border-semantic-critical font-medium hover:bg-semantic-critical/20"
      );
    }
    if (category === "inconclusive") {
      return cn(
        baseStyle,
        "bg-semantic-warning-subtle text-text-primary border-b-2 border-semantic-warning hover:bg-semantic-warning/20"
      );
    }
    if (s.status === "INSUFFICIENT_LENGTH" || s.status === "BELOW_LOCAL_RELIABILITY_THRESHOLD") {
      return cn(baseStyle, "border-b border-dashed border-border-strong text-text-secondary hover:bg-surface-overlay");
    }

    // Human-typical
    return cn(baseStyle, "hover:bg-surface-overlay text-text-primary");
  };

  // Count sentences by category
  const allSentences = paragraphs.flatMap((p) => p.sentences);
  const counts = {
    all: allSentences.length,
    elevated: allSentences.filter((s) => getSentenceCategory(s) === "elevated").length,
    inconclusive: allSentences.filter((s) => getSentenceCategory(s) === "inconclusive").length,
    human: allSentences.filter((s) => getSentenceCategory(s) === "human").length,
  };

  return (
    <div className={cn("space-y-4", className)}>
      {/* Filter and Legend Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-lg border border-border-subtle bg-surface-card">
        <div className="flex items-center gap-1.5" role="tablist" aria-label="Sentence highlight filter">
          <button
            type="button"
            role="tab"
            aria-selected={activeFilter === "all"}
            onClick={() => setActiveFilter("all")}
            className={cn(
              "px-2.5 py-1 text-xs font-medium rounded transition-colors",
              activeFilter === "all"
                ? "bg-surface-active text-text-primary border border-border"
                : "text-text-secondary hover:text-text-primary"
            )}
          >
            All Sentences ({counts.all})
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={activeFilter === "elevated"}
            onClick={() => setActiveFilter("elevated")}
            className={cn(
              "px-2.5 py-1 text-xs font-medium rounded transition-colors flex items-center gap-1.5",
              activeFilter === "elevated"
                ? "bg-semantic-critical-subtle text-semantic-critical border border-semantic-critical/40"
                : "text-text-secondary hover:text-semantic-critical"
            )}
          >
            <span className="h-2 w-2 rounded-full bg-semantic-critical" />
            Elevated Synthetic ({counts.elevated})
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={activeFilter === "inconclusive"}
            onClick={() => setActiveFilter("inconclusive")}
            className={cn(
              "px-2.5 py-1 text-xs font-medium rounded transition-colors flex items-center gap-1.5",
              activeFilter === "inconclusive"
                ? "bg-semantic-warning-subtle text-semantic-warning border border-semantic-warning/40"
                : "text-text-secondary hover:text-semantic-warning"
            )}
          >
            <span className="h-2 w-2 rounded-full bg-semantic-warning" />
            Inconclusive ({counts.inconclusive})
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={activeFilter === "human"}
            onClick={() => setActiveFilter("human")}
            className={cn(
              "px-2.5 py-1 text-xs font-medium rounded transition-colors flex items-center gap-1.5",
              activeFilter === "human"
                ? "bg-surface-active text-text-primary border border-border"
                : "text-text-secondary hover:text-text-primary"
            )}
          >
            Human-Typical ({counts.human})
          </button>
        </div>

        <div className="flex items-center gap-3 text-xs text-text-muted">
          <span className="flex items-center gap-1">
            <HelpCircle className="h-3.5 w-3.5" />
            Click any sentence to inspect why it was flagged
          </span>
        </div>
      </div>

      {/* Document Heatmap Content */}
      <div className="rounded-lg border border-border-subtle bg-surface-card p-6 space-y-4 max-h-[550px] overflow-y-auto leading-relaxed text-sm">
        {paragraphs.map((p) => (
          <p key={`p-${p.index}`} className="text-text-primary leading-relaxed">
            {p.sentences.map((s) => (
              <span
                key={s.id || `p${p.index}-s${s.index}`}
                role="button"
                tabIndex={0}
                onClick={() => setSelectedSentence(s)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    setSelectedSentence(s);
                  }
                }}
                className={getSentenceStyle(s)}
                aria-label={`Sentence: ${s.text.slice(0, 30)}...`}
              >
                {s.text}{" "}
              </span>
            ))}
          </p>
        ))}
      </div>

      {/* Sentence Detail Popover Drawer */}
      {selectedSentence && (
        <div
          role="region"
          aria-label="Sentence Analysis Inspector"
          className="rounded-lg border border-border-strong bg-surface-overlay p-4 text-sm space-y-3 animate-in fade-in-0 slide-in-from-top-2"
        >
          <div className="flex items-start justify-between gap-3 border-b border-border-subtle pb-3">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono text-text-muted">
                  Sentence {selectedSentence.id || `#${selectedSentence.index}`}
                </span>
                <Badge
                  variant={
                    getSentenceCategory(selectedSentence) === "elevated"
                      ? "critical"
                      : getSentenceCategory(selectedSentence) === "inconclusive"
                      ? "warning"
                      : "secondary"
                  }
                >
                  {selectedSentence.status}
                </Badge>
                {selectedSentence.is_elevated_homogeneity && (
                  <Badge variant="critical">Elevated Homogeneity</Badge>
                )}
              </div>
              <p className="font-serif italic text-text-primary bg-surface-base/80 p-2.5 rounded border border-border-subtle">
                &ldquo;{selectedSentence.text}&rdquo;
              </p>
            </div>
            <button
              type="button"
              onClick={() => setSelectedSentence(null)}
              aria-label="Close sentence detail"
              className="text-text-muted hover:text-text-primary rounded p-1 transition-colors relative z-10 shrink-0"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div className="space-y-1">
              <span className="text-text-muted block">Local Synthetic Indicator:</span>
              <span className="text-sm font-semibold font-mono text-text-primary">
                {selectedSentence.indicator_score !== null && selectedSentence.indicator_score !== undefined
                  ? `${(selectedSentence.indicator_score * 100).toFixed(1)}%`
                  : "Insufficient length for scoring"}
              </span>
            </div>
            <div className="space-y-1">
              <span className="text-text-muted block">Attribution Disclaimer:</span>
              <span className="text-text-secondary leading-normal block">
                {selectedSentence.attribution_disclaimer}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
