"use client";

import React, { useState, useRef, useCallback } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { ImproverForm } from "@/components/improver/ImproverForm";
import { SentenceChangeCard } from "@/components/improver/SentenceChangeCard";
import { VerificationPanel } from "@/components/improver/VerificationPanel";
import { FinalTextEditor } from "@/components/improver/FinalTextEditor";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import {
  FileEdit,
  Sparkles,
  Columns,
  AlignLeft,
  ArrowUpDown,
  RotateCcw,
  ShieldCheck,
} from "lucide-react";
import {
  apiClient,
  ApiException,
  ImproverMode,
  ImproveResponse,
  ParagraphImprovement,
  VerificationReport,
} from "@/lib/api-client";

function computeFinalTextFromParagraphs(paragraphs: ParagraphImprovement[]): string {
  return paragraphs
    .map((p) => {
      if (p.is_heading || p.status === "SKIPPED_HEADING") {
        return p.original_text;
      }
      if (!p.changes || p.changes.length === 0) {
        return p.revised_text || p.original_text;
      }
      return p.changes.map((c) => (c.accepted ? c.revised : c.original)).join(" ");
    })
    .join("\n\n");
}

export default function HumanizerPage() {
  const [sourceText, setSourceText] = useState("");
  const [selectedMode, setSelectedMode] = useState<ImproverMode>("academic_clarity");
  const [selectedProvider, setSelectedProvider] = useState("");
  const [runVerification, setRunVerification] = useState(true);

  // Loading & Execution State
  const [isLoading, setIsLoading] = useState(false);
  const [progressPercent, setProgressPercent] = useState(0);
  const [stepMessage, setStepMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Response & Working Manuscript State
  const [response, setResponse] = useState<ImproveResponse | null>(null);
  const [paragraphs, setParagraphs] = useState<ParagraphImprovement[]>([]);
  const [finalText, setFinalText] = useState("");

  // History stack for undo / redo
  const [undoStack, setUndoStack] = useState<string[]>([]);
  const [redoStack, setRedoStack] = useState<string[]>([]);

  // Verification Report & Re-verification State
  const [verificationReport, setVerificationReport] = useState<VerificationReport | null>(null);
  const [isVerifying, setIsVerifying] = useState(false);

  // View Mode: "inline" vs "side_by_side"
  const [comparisonViewMode, setComparisonViewMode] = useState<"inline" | "side_by_side">("inline");

  // In-flight cancellation
  const abortControllerRef = useRef<AbortController | null>(null);

  // Counts
  const totalEditsCount = paragraphs.reduce((acc, p) => acc + (p.changes?.length || 0), 0);
  const acceptedEditsCount = paragraphs.reduce(
    (acc, p) => acc + (p.changes?.filter((c) => c.accepted).length || 0),
    0
  );

  const pushToHistory = (newText: string) => {
    setUndoStack((prev) => [...prev, finalText]);
    setRedoStack([]);
    setFinalText(newText);
  };

  const handleUndo = () => {
    if (undoStack.length === 0) return;
    const prevText = undoStack[undoStack.length - 1];
    setUndoStack((prev) => prev.slice(0, prev.length - 1));
    setRedoStack((prev) => [...prev, finalText]);
    setFinalText(prevText);
  };

  const handleRedo = () => {
    if (redoStack.length === 0) return;
    const nextText = redoStack[redoStack.length - 1];
    setRedoStack((prev) => prev.slice(0, prev.length - 1));
    setUndoStack((prev) => [...prev, finalText]);
    setFinalText(nextText);
  };

  // Run Improvement Pipeline
  const handleSubmit = async () => {
    if (!sourceText.trim()) return;

    setIsLoading(true);
    setErrorMessage(null);
    setProgressPercent(15);
    setStepMessage("Masking protected spans and citations...");

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      setProgressPercent(40);
      setStepMessage(`Generating ${selectedMode.replace("_", " ")} revision via LLM...`);

      const resp = await apiClient.improveContent(
        {
          text: sourceText,
          mode: selectedMode,
          provider: selectedProvider || undefined,
          run_verification: runVerification,
          enable_nli: false,
        },
        { signal: controller.signal }
      );

      setProgressPercent(85);
      setStepMessage("Aligning sentences and compiling verification audit...");

      setResponse(resp);
      const initialParagraphs = resp.paragraphs || [];
      setParagraphs(initialParagraphs);

      const computedFinal = computeFinalTextFromParagraphs(initialParagraphs);
      setFinalText(computedFinal);
      setUndoStack([]);
      setRedoStack([]);

      // Aggregate paragraph verification reports if present
      if (initialParagraphs.length > 0 && initialParagraphs[0].verification_report) {
        setVerificationReport(initialParagraphs[0].verification_report);
      } else if (runVerification) {
        // Run standalone verification on the generated revision
        try {
          const vReport = await apiClient.verifyRevision({
            source_text: sourceText,
            target_text: computedFinal,
            enable_nli: false,
          });
          setVerificationReport(vReport);
        } catch {
          // Non-blocking: improver result already available
        }
      } else {
        setVerificationReport(null);
      }

      setProgressPercent(100);
    } catch (err: unknown) {
      if (err instanceof Error && err.name === "AbortError") {
        setErrorMessage("Improvement operation was cancelled by the user.");
      } else if (err instanceof ApiException) {
        setErrorMessage(`[${err.code}] ${err.message}`);
      } else if (err instanceof Error) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage("An unexpected error occurred while communicating with the improver API.");
      }
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  };

  const handleCancel = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  };

  // Toggle individual sentence change
  const handleToggleAccept = (paragraphIndex: number, sentenceIndex: number, accepted: boolean) => {
    setParagraphs((prev) => {
      const updated = prev.map((p, pIdx) => {
        if (pIdx !== paragraphIndex) return p;
        const updatedChanges = p.changes.map((c, cIdx) => {
          if (cIdx !== sentenceIndex) return c;
          return { ...c, accepted };
        });
        return { ...p, changes: updatedChanges };
      });
      const newFinal = computeFinalTextFromParagraphs(updated);
      pushToHistory(newFinal);
      return updated;
    });
  };

  // Accept all changes
  const handleAcceptAll = () => {
    setParagraphs((prev) => {
      const updated = prev.map((p) => ({
        ...p,
        changes: p.changes.map((c) => ({ ...c, accepted: true })),
      }));
      const newFinal = computeFinalTextFromParagraphs(updated);
      pushToHistory(newFinal);
      return updated;
    });
  };

  // Reject all changes
  const handleRejectAll = () => {
    setParagraphs((prev) => {
      const updated = prev.map((p) => ({
        ...p,
        changes: p.changes.map((c) => ({ ...c, accepted: false })),
      }));
      const newFinal = computeFinalTextFromParagraphs(updated);
      pushToHistory(newFinal);
      return updated;
    });
  };

  // Standalone re-verification against currently edited final text
  const handleReverify = async () => {
    if (!sourceText || !finalText) return;
    setIsVerifying(true);
    try {
      const report = await apiClient.verifyRevision({
        source_text: sourceText,
        target_text: finalText,
        enable_nli: false,
      });
      setVerificationReport(report);
    } catch (err: unknown) {
      if (err instanceof ApiException) {
        setErrorMessage(`Verification audit failed: [${err.code}] ${err.message}`);
      }
    } finally {
      setIsVerifying(false);
    }
  };

  // Jump to specific paragraph card
  const handleJumpToParagraph = (paragraphIndex: number) => {
    const el = document.getElementById(`para-block-${paragraphIndex}`);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "center" });
      el.classList.add("ring-2", "ring-accent");
      setTimeout(() => el.classList.remove("ring-2", "ring-accent"), 2000);
    }
  };

  return (
    <AppShell>
      <div className="space-y-6 max-w-7xl mx-auto">
        {/* Header with methodology disclosure */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-border/60 pb-5">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-text-primary flex items-center gap-2">
              <Sparkles className="w-6 h-6 text-accent" />
              Writing Improver
            </h1>
            <p className="text-sm text-text-secondary mt-1">
              Stylistic clarity, flow, and readability with verified span protection. Not for detector evasion.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-xs py-1 px-2.5 font-mono border-border">
              Protected Spans: Citations, Numbers, Dates, Code
            </Badge>
          </div>
        </div>

        {/* Top Split: Source Form on Left, Final Manuscript Editor on Right */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
          {/* Source Input Column */}
          <ImproverForm
            sourceText={sourceText}
            onSourceTextChange={setSourceText}
            selectedMode={selectedMode}
            onModeChange={setSelectedMode}
            selectedProvider={selectedProvider}
            onProviderChange={setSelectedProvider}
            runVerification={runVerification}
            onToggleVerification={setRunVerification}
            isLoading={isLoading}
            progressPercent={progressPercent}
            currentStepMessage={stepMessage}
            errorMessage={errorMessage}
            onSubmit={handleSubmit}
            onCancel={handleCancel}
          />

          {/* Final Output / Export Column */}
          {response ? (
            <FinalTextEditor
              finalText={finalText}
              onFinalTextChange={(newText) => {
                setUndoStack((prev) => [...prev, finalText]);
                setRedoStack([]);
                setFinalText(newText);
              }}
              canUndo={undoStack.length > 0}
              canRedo={redoStack.length > 0}
              onUndo={handleUndo}
              onRedo={handleRedo}
              onAcceptAll={handleAcceptAll}
              onRejectAll={handleRejectAll}
              totalEditsCount={totalEditsCount}
              acceptedEditsCount={acceptedEditsCount}
              providerUsed={response.provider_used}
              modelUsed={response.model_used}
              usage={response.usage}
            />
          ) : (
            <Card className="border-border/80 bg-surface-base">
              <CardHeader className="py-4 px-5 border-b border-border/50">
                <CardTitle className="text-base font-semibold text-text-primary">
                  Final Polished Manuscript
                </CardTitle>
              </CardHeader>
              <CardContent className="p-8">
                <EmptyState
                  icon={<FileEdit className="h-8 w-8 text-text-muted" />}
                  title="No Active Revision"
                  description="Submit source text on the left to generate improvements with sentence-level accept/reject staging."
                />
              </CardContent>
            </Card>
          )}
        </div>

        {/* Lower Section: Active Revision Diff Staging & Verification Audit */}
        {response && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start pt-2">
            {/* Left 2 Columns: Sentence-by-Sentence Comparison View */}
            <div className="lg:col-span-2 space-y-4">
              <div className="flex items-center justify-between border-b border-border/60 pb-3 flex-wrap gap-2">
                <div className="flex items-center gap-2">
                  <h2 className="text-base font-semibold text-text-primary">
                    Interactive Staging & Sentence Diffs
                  </h2>
                  <Badge variant="outline" className="text-xs font-mono">
                    {paragraphs.length} Paragraphs
                  </Badge>
                </div>

                {/* Diff View Mode Switcher */}
                <div className="flex items-center border border-border/80 rounded-md bg-surface-elevated p-0.5 text-xs">
                  <button
                    type="button"
                    onClick={() => setComparisonViewMode("inline")}
                    className={`px-2.5 py-1 rounded flex items-center gap-1.5 transition-all ${
                      comparisonViewMode === "inline"
                        ? "bg-accent text-white font-medium shadow-sm"
                        : "text-text-muted hover:text-text-primary"
                    }`}
                  >
                    <AlignLeft className="w-3.5 h-3.5" /> Inline Diff
                  </button>
                  <button
                    type="button"
                    onClick={() => setComparisonViewMode("side_by_side")}
                    className={`px-2.5 py-1 rounded flex items-center gap-1.5 transition-all ${
                      comparisonViewMode === "side_by_side"
                        ? "bg-accent text-white font-medium shadow-sm"
                        : "text-text-muted hover:text-text-primary"
                    }`}
                  >
                    <Columns className="w-3.5 h-3.5" /> Side-by-Side
                  </button>
                </div>
              </div>

              {/* Paragraphs and Sentence Change Cards */}
              <div className="space-y-6">
                {paragraphs.map((p, pIdx) => {
                  const paraFindings =
                    verificationReport?.findings.filter((f) => f.paragraph_index === pIdx) || [];
                  const needsReview =
                    paraFindings.some((f) => f.severity === "CRITICAL" || f.severity === "WARN") ||
                    p.verification_report?.needs_review;

                  return (
                    <div
                      key={pIdx}
                      id={`para-block-${pIdx}`}
                      className="rounded-xl border border-border bg-surface-elevated/20 p-4 space-y-3 transition-all"
                    >
                      <div className="flex items-center justify-between border-b border-border/50 pb-2 flex-wrap gap-2">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold uppercase tracking-wider text-text-secondary font-mono">
                            Paragraph {pIdx + 1}
                          </span>
                          {p.is_heading && (
                            <Badge variant="outline" className="text-[10px] py-0 px-1.5 border-border">
                              Heading (Preserved)
                            </Badge>
                          )}
                          {needsReview && (
                            <Badge variant="warning" className="text-[10px] py-0 px-1.5 font-semibold">
                              Needs Review
                            </Badge>
                          )}
                        </div>

                        <span className="text-[11px] text-text-muted font-mono">
                          {p.changes?.length || 0} sentences
                        </span>
                      </div>

                      {/* Heading or non-editable block */}
                      {p.is_heading ? (
                        <p className="font-semibold text-text-primary text-sm font-mono p-2 rounded bg-surface-elevated/40">
                          {p.original_text}
                        </p>
                      ) : (
                        <div className="space-y-3">
                          {p.changes?.map((change, cIdx) => (
                            <SentenceChangeCard
                              key={cIdx}
                              sentenceIndex={cIdx}
                              paragraphIndex={pIdx}
                              original={change.original}
                              revised={change.revised}
                              accepted={change.accepted}
                              viewMode={comparisonViewMode}
                              findings={paraFindings}
                              onToggleAccept={handleToggleAccept}
                            />
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Right Column: Verification Audit Panel */}
            <div className="space-y-4">
              <VerificationPanel
                report={verificationReport}
                isVerifying={isVerifying}
                onReverify={handleReverify}
                onJumpToParagraph={handleJumpToParagraph}
              />
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
