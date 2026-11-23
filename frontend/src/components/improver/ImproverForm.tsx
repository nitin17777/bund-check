"use client";

import React, { useState } from "react";
import { Sparkles, AlertCircle, X, ShieldCheck } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Progress } from "@/components/ui/Progress";
import { ImproverMode } from "@/lib/api-client";

export interface ImproverFormProps {
  sourceText: string;
  onSourceTextChange: (text: string) => void;
  selectedMode: ImproverMode;
  onModeChange: (mode: ImproverMode) => void;
  selectedProvider: string;
  onProviderChange: (provider: string) => void;
  runVerification: boolean;
  onToggleVerification: (enabled: boolean) => void;
  isLoading: boolean;
  progressPercent: number;
  currentStepMessage?: string;
  errorMessage?: string | null;
  onSubmit: () => void;
  onCancel: () => void;
}

export const IMPROVER_MODES: Array<{
  id: ImproverMode;
  label: string;
  description: string;
}> = [
  {
    id: "academic_clarity",
    label: "Academic Clarity",
    description: "Scholarly precision, syntactic cohesion, and objective academic tone.",
  },
  {
    id: "professional",
    label: "Professional & Executive",
    description: "Crisp workplace communication, direct active voice, and executive impact.",
  },
  {
    id: "natural_conversational",
    label: "Natural & Conversational",
    description: "Fluid, human-sounding rhythm, natural transitions, and engaging cadence.",
  },
  {
    id: "simple_readable",
    label: "Simple & Readable",
    description: "Maximum accessibility, plain English vocabulary, and digestible sentences.",
  },
  {
    id: "concise",
    label: "Concise & Tight",
    description: "High information density, trimming filler words and nominalizations.",
  },
  {
    id: "formal",
    label: "Formal & Polished",
    description: "Dignified, elevated syntactic structure for official documents and publications.",
  },
];

export function ImproverForm({
  sourceText,
  onSourceTextChange,
  selectedMode,
  onModeChange,
  selectedProvider,
  onProviderChange,
  runVerification,
  onToggleVerification,
  isLoading,
  progressPercent,
  currentStepMessage,
  errorMessage,
  onSubmit,
  onCancel,
}: ImproverFormProps) {
  const wordCount = sourceText.trim() ? sourceText.trim().split(/\s+/).length : 0;
  const charCount = sourceText.length;

  return (
    <Card className="border-border/80 bg-surface-base">
      <CardHeader className="py-4 px-5 border-b border-border/50">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-base font-semibold text-text-primary">Source Manuscript</CardTitle>
            <CardDescription className="text-xs text-text-secondary mt-0.5">
              Enter draft prose to polish. Protected spans (citations, numbers, formulas, dates) will be masked.
            </CardDescription>
          </div>
          <div className="text-right">
            <span className="text-xs font-mono font-medium text-text-primary">{wordCount} words</span>
            <span className="text-[11px] text-text-muted ml-2">({charCount} chars)</span>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-5 space-y-5">
        {/* Source Textarea */}
        <div className="space-y-1.5">
          <textarea
            rows={10}
            value={sourceText}
            onChange={(e) => onSourceTextChange(e.target.value)}
            disabled={isLoading}
            placeholder="Paste your manuscript paragraphs here (e.g. academic drafts, technical documentation, executive summaries)..."
            className="w-full rounded-md border border-border bg-surface-card p-3.5 text-xs font-mono text-text-primary placeholder:text-text-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent resize-y transition-colors leading-relaxed disabled:opacity-50"
          />
        </div>

        {/* Mode Selector */}
        <div className="space-y-2">
          <label className="text-xs font-semibold text-text-secondary">Editorial Mode</label>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {IMPROVER_MODES.map((mode) => {
              const isSelected = selectedMode === mode.id;
              return (
                <button
                  type="button"
                  key={mode.id}
                  onClick={() => onModeChange(mode.id)}
                  disabled={isLoading}
                  className={`text-left p-3 rounded-lg border transition-all ${
                    isSelected
                      ? "border-accent bg-accent/10 shadow-sm"
                      : "border-border/60 bg-surface-elevated/20 hover:border-border hover:bg-surface-elevated/40"
                  } disabled:opacity-50`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className={`text-xs font-semibold ${isSelected ? "text-accent" : "text-text-primary"}`}>
                      {mode.label}
                    </span>
                    {isSelected && <Badge variant="default" className="text-[9px] py-0 px-1 bg-accent">Active</Badge>}
                  </div>
                  <p className="text-[11px] text-text-muted leading-snug">{mode.description}</p>
                </button>
              );
            })}
          </div>
        </div>

        {/* Advanced Options Bar: Provider Override & Verification Toggle */}
        <div className="pt-2 border-t border-border/50 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-3 flex-wrap">
            <div className="flex items-center gap-1.5">
              <label htmlFor="provider-select" className="text-text-muted font-medium">Provider:</label>
              <select
                id="provider-select"
                value={selectedProvider}
                onChange={(e) => onProviderChange(e.target.value)}
                disabled={isLoading}
                className="rounded border border-border bg-surface-elevated text-text-primary text-xs px-2.5 py-1 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent"
              >
                <option value="">Server Default</option>
                <option value="groq">Groq (Llama-3.3-70B)</option>
                <option value="openrouter">OpenRouter (Llama-3.3-70B)</option>
                <option value="openai">OpenAI (GPT-4o mini)</option>
                <option value="local_small">Local Small (CPU/RTX 2050)</option>
              </select>
            </div>

            <label className="flex items-center gap-1.5 cursor-pointer text-text-secondary select-none">
              <input
                type="checkbox"
                checked={runVerification}
                onChange={(e) => onToggleVerification(e.target.checked)}
                disabled={isLoading}
                className="rounded border-border text-accent focus:ring-accent bg-surface-elevated"
              />
              <span className="flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5 text-accent" />
                Run Post-Rewrite Verification
              </span>
            </label>
          </div>
        </div>

        {/* Progress bar during generation */}
        {isLoading && (
          <div className="space-y-2 p-3 rounded-lg border border-border bg-surface-elevated/30">
            <div className="flex justify-between text-xs text-text-muted">
              <span>{currentStepMessage || "Improving prose with span protection..."}</span>
              <span className="font-mono">{Math.round(progressPercent)}%</span>
            </div>
            <Progress value={progressPercent} />
          </div>
        )}

        {/* Actionable Error Alert */}
        {errorMessage && (
          <div className="rounded-lg bg-red-500/10 border border-red-500/30 p-3 text-xs text-red-200 flex items-start gap-2.5">
            <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <div className="font-semibold text-red-300">Improvement Failed</div>
              <p className="text-[11px] leading-relaxed text-red-200/90">{errorMessage}</p>
            </div>
          </div>
        )}

        {/* Submission Controls */}
        <div className="flex items-center justify-between pt-1">
          <p className="text-[11px] text-text-muted">
            Directives forbid hallucinated facts, altered citations, or changed numbers.
          </p>

          <div className="flex items-center gap-2">
            {isLoading ? (
              <Button
                variant="outline"
                size="sm"
                onClick={onCancel}
                className="border-red-500/40 text-red-400 hover:bg-red-500/10"
              >
                <X className="w-4 h-4 mr-1.5" /> Cancel Request
              </Button>
            ) : (
              <Button
                variant="primary"
                size="md"
                onClick={onSubmit}
                disabled={!sourceText.trim() || wordCount < 3}
                className="px-5 font-semibold"
              >
                <Sparkles className="w-4 h-4 mr-1.5" />
                Improve Prose
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
