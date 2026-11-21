"use client";

import { AppShell } from "@/components/layout/AppShell";
import { EmptyState } from "@/components/ui/EmptyState";
import { FileDropzone } from "@/components/ui/FileDropzone";
import { ScanText } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";

export default function CheckerPage() {
  return (
    <AppShell>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-text-primary">Content Checker</h1>
          <p className="text-sm text-text-secondary mt-1">
            Probabilistic synthetic-pattern inspection with calibrated confidence intervals.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base font-semibold">Document or Text Ingestion</CardTitle>
                <CardDescription>
                  Upload a PDF, DOCX, or TXT file (up to 10 MB) or paste plain text. All content is processed
                  in memory and immediately cleared after scoring.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <FileDropzone onFileAccepted={() => {}} />

                <div className="relative">
                  <div className="absolute inset-0 flex items-center">
                    <span className="w-full border-t border-border-subtle" />
                  </div>
                  <div className="relative flex justify-center text-xs uppercase">
                    <span className="bg-surface-card px-2 text-text-muted">Or enter text</span>
                  </div>
                </div>

                <textarea
                  rows={6}
                  placeholder="Paste manuscript, essay, or technical draft for probabilistic evaluation..."
                  className="w-full rounded border border-border bg-surface-base p-3 text-sm text-text-primary placeholder:text-text-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent resize-y"
                  readOnly
                />

                <div className="flex justify-end">
                  <button
                    disabled
                    className="inline-flex items-center justify-center h-9 px-4 text-xs font-semibold rounded bg-accent text-white opacity-50 cursor-not-allowed"
                  >
                    Analyze Text (Phase 8 View Ready)
                  </button>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="space-y-4">
            <EmptyState
              icon={<ScanText className="h-6 w-6" />}
              title="Awaiting Input"
              description="Upload a document or paste text above to evaluate token perplexity, sentence burstiness, and stylometric indicators."
            />
          </div>
        </div>
      </div>
    </AppShell>
  );
}
