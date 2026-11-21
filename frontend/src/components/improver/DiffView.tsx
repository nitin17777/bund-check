"use client";

import React, { useMemo } from "react";
import { computeWordDiff, DiffToken } from "@/lib/diff";

export interface DiffViewProps {
  original: string;
  revised: string;
  viewMode?: "inline" | "side_by_side";
  className?: string;
}

export function DiffView({
  original,
  revised,
  viewMode = "inline",
  className = "",
}: DiffViewProps) {
  const diffTokens = useMemo(() => {
    return computeWordDiff(original, revised);
  }, [original, revised]);

  if (viewMode === "side_by_side") {
    return (
      <div className={`grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono leading-relaxed ${className}`}>
        {/* Left: Original with deletions highlighted */}
        <div className="rounded border border-border bg-surface-elevated/40 p-3 overflow-x-auto">
          <div className="text-[10px] font-sans font-semibold uppercase tracking-wider text-text-muted mb-2">
            Original Text
          </div>
          <p className="whitespace-pre-wrap text-text-secondary">
            {diffTokens.map((token, idx) => {
              if (token.type === "delete") {
                return (
                  <span
                    key={idx}
                    className="bg-red-500/20 text-red-300 line-through rounded px-0.5 py-0.2"
                  >
                    {token.value}
                  </span>
                );
              }
              if (token.type === "equal") {
                return <span key={idx}>{token.value}</span>;
              }
              return null; // hide inserts on the original side
            })}
          </p>
        </div>

        {/* Right: Revised with additions highlighted */}
        <div className="rounded border border-border bg-surface-elevated/40 p-3 overflow-x-auto">
          <div className="text-[10px] font-sans font-semibold uppercase tracking-wider text-text-muted mb-2">
            Proposed Revision
          </div>
          <p className="whitespace-pre-wrap text-text-primary">
            {diffTokens.map((token, idx) => {
              if (token.type === "insert") {
                return (
                  <span
                    key={idx}
                    className="bg-emerald-500/20 text-emerald-300 font-medium rounded px-0.5 py-0.2"
                  >
                    {token.value}
                  </span>
                );
              }
              if (token.type === "equal") {
                return <span key={idx}>{token.value}</span>;
              }
              return null; // hide deletes on the revised side
            })}
          </p>
        </div>
      </div>
    );
  }

  // Inline view
  return (
    <div className={`rounded border border-border/80 bg-surface-elevated/30 p-3 text-xs font-mono leading-relaxed overflow-x-auto ${className}`}>
      <p className="whitespace-pre-wrap">
        {diffTokens.map((token, idx) => {
          if (token.type === "equal") {
            return (
              <span key={idx} className="text-text-secondary">
                {token.value}
              </span>
            );
          }
          if (token.type === "delete") {
            return (
              <del
                key={idx}
                className="bg-red-500/20 text-red-300 line-through rounded px-1 py-0.5 mr-0.5 inline-block"
              >
                {token.value}
              </del>
            );
          }
          if (token.type === "insert") {
            return (
              <ins
                key={idx}
                className="bg-emerald-500/20 text-emerald-300 font-medium no-underline rounded px-1 py-0.5 mr-0.5 inline-block"
              >
                {token.value}
              </ins>
            );
          }
          return null;
        })}
      </p>
    </div>
  );
}
