"use client";

import React, { useState } from "react";
import { Check, X, AlertTriangle, AlertCircle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Dialog } from "@/components/ui/Dialog";
import { DiffView } from "./DiffView";
import { VerificationFinding } from "@/lib/api-client";

export interface SentenceChangeCardProps {
  sentenceIndex: number;
  paragraphIndex: number;
  original: string;
  revised: string;
  accepted: boolean;
  viewMode: "inline" | "side_by_side";
  findings?: VerificationFinding[];
  onToggleAccept: (paragraphIndex: number, sentenceIndex: number, accepted: boolean) => void;
}

export function SentenceChangeCard({
  sentenceIndex,
  paragraphIndex,
  original,
  revised,
  accepted,
  viewMode,
  findings = [],
  onToggleAccept,
}: SentenceChangeCardProps) {
  const [showConfirmModal, setShowConfirmModal] = useState(false);

  const isUnchanged = original.trim() === revised.trim();
  const criticalFindings = findings.filter((f) => f.severity === "CRITICAL");
  const warnFindings = findings.filter((f) => f.severity === "WARN");
  const hasWarnings = criticalFindings.length > 0 || warnFindings.length > 0;

  const handleAcceptClick = () => {
    // If the sentence has critical or warning findings and is currently rejected,
    // require an explicit confirmation before accepting it!
    if (!accepted && hasWarnings) {
      setShowConfirmModal(true);
      return;
    }
    onToggleAccept(paragraphIndex, sentenceIndex, !accepted);
  };

  const handleConfirmAccept = () => {
    setShowConfirmModal(false);
    onToggleAccept(paragraphIndex, sentenceIndex, true);
  };

  return (
    <div
      className={`rounded-lg border transition-all ${
        accepted
          ? "border-border/80 bg-surface-base/80"
          : "border-border/40 bg-surface-base/30 opacity-75"
      } p-3.5 space-y-2.5`}
    >
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-text-secondary">
            Sentence {sentenceIndex + 1}
          </span>

          {isUnchanged && (
            <Badge variant="outline" className="text-[10px] py-0 px-1.5 border-border text-text-muted">
              Unchanged
            </Badge>
          )}

          {hasWarnings && (
            <Badge
              variant={criticalFindings.length > 0 ? "critical" : "warning"}
              className="text-[10px] py-0 px-1.5 flex items-center gap-1"
            >
              {criticalFindings.length > 0 ? (
                <AlertCircle className="w-3 h-3" />
              ) : (
                <AlertTriangle className="w-3 h-3" />
              )}
              {criticalFindings.length > 0
                ? `${criticalFindings.length} Critical Audit Flag`
                : `${warnFindings.length} Review Advisory`}
            </Badge>
          )}
        </div>

        <div className="flex items-center gap-2">
          {accepted ? (
            <Badge variant="success" className="text-[10px] py-0.5 px-2 font-medium">
              Accepted
            </Badge>
          ) : (
            <Badge variant="outline" className="text-[10px] py-0.5 px-2 text-text-muted border-border">
              Rejected (Original Kept)
            </Badge>
          )}

          {!isUnchanged && (
            <div className="flex items-center gap-1">
              <Button
                variant={accepted ? "outline" : "primary"}
                size="sm"
                className={`h-7 px-2.5 text-xs ${
                  accepted ? "border-emerald-500/40 text-emerald-400 hover:bg-emerald-500/10" : ""
                }`}
                onClick={handleAcceptClick}
                title={accepted ? "Reject this change" : "Accept this change"}
              >
                {accepted ? (
                  <>
                    <X className="w-3.5 h-3.5 mr-1" /> Reject
                  </>
                ) : (
                  <>
                    <Check className="w-3.5 h-3.5 mr-1" /> Accept
                  </>
                )}
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Diff or unchanged preview */}
      {isUnchanged ? (
        <p className="text-xs text-text-secondary font-mono leading-relaxed bg-surface-elevated/30 p-2.5 rounded border border-border/50">
          {original}
        </p>
      ) : (
        <DiffView original={original} revised={revised} viewMode={viewMode} />
      )}

      {/* Flagged warning notes if present */}
      {hasWarnings && (
        <div className="rounded bg-amber-500/10 border border-amber-500/30 p-2.5 space-y-1">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-amber-300">
            <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
            Verification Advisory on Paragraph {paragraphIndex + 1}:
          </div>
          <ul className="text-[11px] text-amber-200/90 list-disc list-inside space-y-0.5">
            {findings.map((finding, idx) => (
              <li key={idx}>
                <span className="font-mono text-amber-300">[{finding.code}]</span> {finding.message}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Explicit Confirmation Dialog when accepting a flagged change */}
      <Dialog
        isOpen={showConfirmModal}
        onClose={() => setShowConfirmModal(false)}
        title="Confirm Acceptance of Flagged Revision"
        description="This revision was flagged by the verification audit. Please review the advisory before proceeding."
      >
        <div className="space-y-4 text-xs">
          <div className="rounded bg-amber-500/10 border border-amber-500/30 p-3 space-y-2">
            <div className="font-semibold text-amber-300 flex items-center gap-1.5">
              <AlertTriangle className="w-4 h-4 shrink-0 text-amber-400" />
              Active Verification Findings:
            </div>
            <ul className="list-disc list-inside space-y-1 text-amber-200/90">
              {findings.map((f, i) => (
                <li key={i}>
                  <strong className="font-mono">{f.code}:</strong> {f.message}
                </li>
              ))}
            </ul>
          </div>

          <div className="space-y-2">
            <div className="text-text-secondary font-semibold">Proposed Change:</div>
            <div className="p-2 rounded bg-surface-elevated border border-border font-mono text-[11px]">
              <div className="text-red-400 line-through mb-1">Orig: {original}</div>
              <div className="text-emerald-400">Rev: {revised}</div>
            </div>
          </div>

          <p className="text-text-muted text-[11px]">
            Accepting this change will update the final manuscript with the revised sentence despite the advisory.
          </p>

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="ghost" size="sm" onClick={() => setShowConfirmModal(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              className="bg-amber-600 hover:bg-amber-500 text-white"
              onClick={handleConfirmAccept}
            >
              Confirm & Accept Change
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}
