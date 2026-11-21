"use client";

import React from "react";
import {
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Info,
  Hash,
  Bookmark,
  Building,
  Layers,
  ArrowRight,
  RefreshCw,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { VerificationReport, VerificationFinding } from "@/lib/api-client";

export interface VerificationPanelProps {
  report: VerificationReport | null;
  isVerifying?: boolean;
  onReverify?: () => void;
  onJumpToParagraph?: (paragraphIndex: number) => void;
}

export function VerificationPanel({
  report,
  isVerifying = false,
  onReverify,
  onJumpToParagraph,
}: VerificationPanelProps) {
  if (!report) {
    return (
      <Card className="border-border/60 bg-surface-base">
        <CardHeader className="py-3 px-4 border-b border-border/50">
          <CardTitle className="text-sm font-semibold flex items-center gap-2 text-text-primary">
            <ShieldAlert className="w-4 h-4 text-text-muted" />
            Verification Audit
          </CardTitle>
        </CardHeader>
        <CardContent className="p-4 text-xs text-text-muted">
          Verification has not been executed yet. Enable verification during improvement or click Re-verify.
        </CardContent>
      </Card>
    );
  }

  const { status, overall_similarity_score, similarity_note, findings, needs_review } = report;

  // Breakdown findings by category
  const numbersFindings = findings.filter((f) => f.category === "numbers");
  const citationsFindings = findings.filter((f) => f.category === "citations");
  const entitiesFindings = findings.filter((f) => f.category === "entities");
  const structureFindings = findings.filter((f) => f.category === "structure");
  const semanticFindings = findings.filter((f) => f.category === "semantics" || f.category === "negations");

  const criticalCount = findings.filter((f) => f.severity === "CRITICAL").length;
  const warnCount = findings.filter((f) => f.severity === "WARN").length;
  const infoCount = findings.filter((f) => f.severity === "INFO").length;

  return (
    <Card className="border-border/80 bg-surface-base overflow-hidden">
      <CardHeader className="py-3.5 px-4 border-b border-border/50 bg-surface-elevated/20 flex flex-row items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          {status === "PASSED" ? (
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
          ) : status === "NEEDS_REVIEW" ? (
            <AlertTriangle className="w-5 h-5 text-amber-400" />
          ) : (
            <ShieldAlert className="w-5 h-5 text-red-400" />
          )}
          <div>
            <div className="text-sm font-semibold text-text-primary flex items-center gap-2">
              Verification Audit
              <Badge
                variant={
                  status === "PASSED"
                    ? "success"
                    : status === "NEEDS_REVIEW"
                    ? "warning"
                    : "critical"
                }
                className="text-[10px] uppercase font-bold tracking-wider py-0 px-2"
              >
                {status.replace("_", " ")}
              </Badge>
            </div>
            <div className="text-[11px] text-text-muted">
              Semantic similarity: {(overall_similarity_score * 100).toFixed(1)}%
            </div>
          </div>
        </div>

        {onReverify && (
          <Button
            variant="outline"
            size="sm"
            onClick={onReverify}
            disabled={isVerifying}
            className="h-7 text-xs border-border"
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${isVerifying ? "animate-spin" : ""}`} />
            Re-verify
          </Button>
        )}
      </CardHeader>

      <CardContent className="p-4 space-y-4 text-xs">
        {/* Severity summary counters */}
        <div className="grid grid-cols-3 gap-2 text-center">
          <div className="rounded border border-red-500/30 bg-red-500/10 p-2">
            <div className="text-base font-bold text-red-400 font-mono">{criticalCount}</div>
            <div className="text-[10px] text-red-300/80 uppercase tracking-wider font-semibold">Critical</div>
          </div>
          <div className="rounded border border-amber-500/30 bg-amber-500/10 p-2">
            <div className="text-base font-bold text-amber-400 font-mono">{warnCount}</div>
            <div className="text-[10px] text-amber-300/80 uppercase tracking-wider font-semibold">Review Advised</div>
          </div>
          <div className="rounded border border-sky-500/30 bg-sky-500/10 p-2">
            <div className="text-base font-bold text-sky-400 font-mono">{infoCount}</div>
            <div className="text-[10px] text-sky-300/80 uppercase tracking-wider font-semibold">Info</div>
          </div>
        </div>

        {/* Category breakdown pills */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <Badge variant="outline" className="text-[11px] py-0.5 px-2 border-border/80 flex items-center gap-1">
            <Hash className="w-3 h-3 text-text-muted" /> Numbers:{" "}
            <span className={numbersFindings.length > 0 ? "text-amber-400 font-bold" : "text-emerald-400"}>
              {numbersFindings.length === 0 ? "Preserved" : `${numbersFindings.length} flagged`}
            </span>
          </Badge>
          <Badge variant="outline" className="text-[11px] py-0.5 px-2 border-border/80 flex items-center gap-1">
            <Bookmark className="w-3 h-3 text-text-muted" /> Citations:{" "}
            <span className={citationsFindings.length > 0 ? "text-amber-400 font-bold" : "text-emerald-400"}>
              {citationsFindings.length === 0 ? "Preserved" : `${citationsFindings.length} flagged`}
            </span>
          </Badge>
          <Badge variant="outline" className="text-[11px] py-0.5 px-2 border-border/80 flex items-center gap-1">
            <Building className="w-3 h-3 text-text-muted" /> Entities:{" "}
            <span className={entitiesFindings.length > 0 ? "text-amber-400 font-bold" : "text-emerald-400"}>
              {entitiesFindings.length === 0 ? "Preserved" : `${entitiesFindings.length} flagged`}
            </span>
          </Badge>
          <Badge variant="outline" className="text-[11px] py-0.5 px-2 border-border/80 flex items-center gap-1">
            <Layers className="w-3 h-3 text-text-muted" /> Structure:{" "}
            <span className={structureFindings.length > 0 ? "text-amber-400 font-bold" : "text-emerald-400"}>
              {structureFindings.length === 0 ? "Aligned" : "Mismatch"}
            </span>
          </Badge>
        </div>

        {/* List of findings with jump-to buttons */}
        {findings.length > 0 ? (
          <div className="space-y-2">
            <div className="text-[11px] font-semibold text-text-muted uppercase tracking-wider">
              Findings Details & Locations
            </div>
            <div className="space-y-1.5 max-h-56 overflow-y-auto pr-1">
              {findings.map((f, idx) => (
                <div
                  key={idx}
                  className={`rounded p-2.5 border text-[11px] flex items-start justify-between gap-2 ${
                    f.severity === "CRITICAL"
                      ? "bg-red-500/10 border-red-500/30 text-red-200"
                      : f.severity === "WARN"
                      ? "bg-amber-500/10 border-amber-500/30 text-amber-200"
                      : "bg-surface-elevated border-border text-text-secondary"
                  }`}
                >
                  <div className="space-y-0.5">
                    <div className="font-semibold flex items-center gap-1.5">
                      <span className="font-mono text-[10px] uppercase opacity-90">[{f.code}]</span>
                      {f.paragraph_index !== undefined && (
                        <span className="text-[10px] opacity-75">
                          Paragraph {f.paragraph_index + 1}
                        </span>
                      )}
                    </div>
                    <p className="text-[11px] opacity-90 leading-tight">{f.message}</p>
                  </div>

                  {f.paragraph_index !== undefined && onJumpToParagraph && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onJumpToParagraph(f.paragraph_index!)}
                      className="h-6 px-1.5 text-[10px] text-text-muted hover:text-text-primary shrink-0"
                      title={`Jump to paragraph ${f.paragraph_index + 1}`}
                    >
                      Jump <ArrowRight className="w-2.5 h-2.5 ml-0.5" />
                    </Button>
                  )}
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="rounded bg-emerald-500/10 border border-emerald-500/20 p-2.5 text-emerald-300 text-[11px] flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 shrink-0 text-emerald-400" />
            <span>All verification integrity checks passed: numbers, citations, entities, and polarity preserved.</span>
          </div>
        )}

        {/* Honest heuristic disclosure */}
        <div className="rounded bg-surface-elevated/40 border border-border/40 p-2.5 text-[11px] text-text-muted space-y-1">
          <div className="font-semibold text-text-secondary flex items-center gap-1">
            <Info className="w-3.5 h-3.5 text-text-muted" />
            Verification Scope & Limitations
          </div>
          <p className="leading-relaxed">
            {similarity_note ||
              "Embedding cosine similarity evaluates proximity in latent space; it does not guarantee logical equivalence."}{" "}
            Authors must verify that all technical nuances, citations, and specific claims accurately reflect their intended meaning.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
