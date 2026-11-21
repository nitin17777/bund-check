"use client";

import React, { useState } from "react";
import {
  Copy,
  Check,
  Download,
  RotateCcw,
  RotateCw,
  Edit3,
  CheckSquare,
  XSquare,
  Sparkles,
  Info,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Tooltip } from "@/components/ui/Tooltip";

export interface FinalTextEditorProps {
  finalText: string;
  onFinalTextChange: (text: string) => void;
  canUndo: boolean;
  canRedo: boolean;
  onUndo: () => void;
  onRedo: () => void;
  onAcceptAll: () => void;
  onRejectAll: () => void;
  totalEditsCount: number;
  acceptedEditsCount: number;
  providerUsed?: string;
  modelUsed?: string;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
    estimated_cost_usd: number;
  };
}

export function FinalTextEditor({
  finalText,
  onFinalTextChange,
  canUndo,
  canRedo,
  onUndo,
  onRedo,
  onAcceptAll,
  onRejectAll,
  totalEditsCount,
  acceptedEditsCount,
  providerUsed,
  modelUsed,
  usage,
}: FinalTextEditorProps) {
  const [isCopied, setIsCopied] = useState(false);
  const [isManualEdit, setIsManualEdit] = useState(false);

  const wordCount = finalText.trim() ? finalText.trim().split(/\s+/).length : 0;
  const charCount = finalText.length;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(finalText);
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    } catch {
      // Fallback if clipboard API is restricted
      const textarea = document.createElement("textarea");
      textarea.value = finalText;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    }
  };

  return (
    <Card className="border-border/80 bg-surface-base overflow-hidden">
      <CardHeader className="py-3.5 px-4 border-b border-border/50 bg-surface-elevated/30 flex flex-row items-center justify-between gap-3 flex-wrap">
        <div>
          <CardTitle className="text-sm font-semibold text-text-primary flex items-center gap-2">
            Final Polished Manuscript
            <Badge variant="outline" className="text-[10px] py-0 px-1.5 font-mono">
              {acceptedEditsCount} of {totalEditsCount} Edits Accepted
            </Badge>
          </CardTitle>
          <div className="text-[11px] text-text-muted mt-0.5">
            Source of truth for export • {wordCount} words • {charCount} characters
          </div>
        </div>

        {/* Global Action Toolbar */}
        <div className="flex items-center gap-1.5 flex-wrap">
          {/* Undo / Redo */}
          <div className="flex items-center border border-border/60 rounded-md bg-surface-base p-0.5 mr-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={onUndo}
              disabled={!canUndo}
              className="h-7 w-7 p-0 text-text-muted hover:text-text-primary disabled:opacity-30"
              title="Undo last change"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={onRedo}
              disabled={!canRedo}
              className="h-7 w-7 p-0 text-text-muted hover:text-text-primary disabled:opacity-30"
              title="Redo change"
            >
              <RotateCw className="w-3.5 h-3.5" />
            </Button>
          </div>

          {/* Accept All / Reject All */}
          <Button
            variant="outline"
            size="sm"
            onClick={onAcceptAll}
            className="h-7 text-xs border-border/70 hover:border-emerald-500/40 hover:text-emerald-400"
            title="Accept all sentence revisions"
          >
            <CheckSquare className="w-3 h-3 mr-1 text-emerald-400" />
            Accept All
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={onRejectAll}
            className="h-7 text-xs border-border/70 hover:border-border text-text-muted"
            title="Reject all sentence revisions and revert to original"
          >
            <XSquare className="w-3 h-3 mr-1" />
            Reject All
          </Button>

          {/* Toggle Manual Edit */}
          <Button
            variant={isManualEdit ? "primary" : "outline"}
            size="sm"
            onClick={() => setIsManualEdit(!isManualEdit)}
            className="h-7 text-xs border-border/70"
            title="Directly edit final text"
          >
            <Edit3 className="w-3 h-3 mr-1" />
            {isManualEdit ? "View Mode" : "Manual Edit"}
          </Button>
        </div>
      </CardHeader>

      <CardContent className="p-4 space-y-3">
        {/* Editor or Read-only Display */}
        {isManualEdit ? (
          <div className="space-y-1">
            <div className="text-[11px] text-accent font-medium flex items-center gap-1">
              <Edit3 className="w-3 h-3" /> Manual editing active. Changes made here directly dictate the export payload.
            </div>
            <textarea
              rows={12}
              value={finalText}
              onChange={(e) => onFinalTextChange(e.target.value)}
              className="w-full rounded-md border border-accent/40 bg-surface-elevated/40 p-3.5 text-xs font-mono text-text-primary leading-relaxed focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent resize-y"
            />
          </div>
        ) : (
          <div className="rounded-md border border-border/60 bg-surface-elevated/20 p-4 max-h-96 overflow-y-auto">
            <p className="whitespace-pre-wrap text-xs font-mono text-text-primary leading-relaxed">
              {finalText || <span className="text-text-muted italic">No text generated yet.</span>}
            </p>
          </div>
        )}

        {/* Telemetry info row if available */}
        {(providerUsed || usage) && (
          <div className="rounded border border-border/50 bg-surface-elevated/30 p-2.5 flex items-center justify-between text-[11px] text-text-muted flex-wrap gap-2">
            <div className="flex items-center gap-2">
              <Sparkles className="w-3.5 h-3.5 text-accent" />
              <span>
                Engine: <strong className="text-text-secondary">{providerUsed}</strong>
                {modelUsed && ` (${modelUsed})`}
              </span>
            </div>
            {usage && (
              <div className="flex items-center gap-3 font-mono text-[10px]">
                <span>Tokens: {usage.total_tokens.toLocaleString()}</span>
                <span>Prompt: {usage.prompt_tokens.toLocaleString()}</span>
                <span>Completion: {usage.completion_tokens.toLocaleString()}</span>
                {usage.estimated_cost_usd > 0 && (
                  <span className="text-emerald-400 font-bold">
                    Est. Cost: ${usage.estimated_cost_usd.toFixed(5)}
                  </span>
                )}
              </div>
            )}
          </div>
        )}

        {/* Export & Actions Row */}
        <div className="pt-2 border-t border-border/50 flex items-center justify-between gap-3">
          <div className="text-[11px] text-text-muted flex items-center gap-1">
            <Info className="w-3.5 h-3.5 text-text-muted shrink-0" />
            Final text state is preserved exactly upon copy or downstream export.
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleCopy}
              className="h-8 text-xs border-border/80 text-text-primary hover:border-accent"
            >
              {isCopied ? (
                <>
                  <Check className="w-3.5 h-3.5 mr-1.5 text-emerald-400" /> Copied!
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5 mr-1.5" /> Copy to Clipboard
                </>
              )}
            </Button>

            {/* Honest disabled download with tooltip per task requirements */}
            <Tooltip content="Document export (.docx / .pdf) will be enabled in a future release. Please use Copy to Clipboard for your final text.">
              <Button
                variant="secondary"
                size="sm"
                disabled
                className="h-8 text-xs opacity-50 cursor-not-allowed border border-border/50"
              >
                <Download className="w-3.5 h-3.5 mr-1.5" />
                Download
              </Button>
            </Tooltip>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
