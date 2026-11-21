"use client";

import * as React from "react";
import { AppShell } from "@/components/layout/AppShell";
import { CheckerForm } from "@/components/checker/CheckerForm";
import { CheckerResults } from "@/components/checker/CheckerResults";
import { CheckResponse } from "@/lib/api-client";

export default function CheckerPage() {
  const [analysisResult, setAnalysisResult] = React.useState<CheckResponse | null>(null);

  return (
    <AppShell>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-text-primary">
            Content Checker Workspace
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            Probabilistic synthetic-pattern inspection with multi-signal calibration, sentence-level attribution, and zero-retention memory execution.
          </p>
        </div>

        {analysisResult ? (
          <CheckerResults
            result={analysisResult}
            onReset={() => setAnalysisResult(null)}
          />
        ) : (
          <CheckerForm onSuccess={(result) => setAnalysisResult(result)} />
        )}
      </div>
    </AppShell>
  );
}
