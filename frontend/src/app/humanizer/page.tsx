import { AppShell } from "@/components/layout/AppShell";
import { EmptyState } from "@/components/ui/EmptyState";
import { FileEdit } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";

export default function HumanizerPage() {
  return (
    <AppShell>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-text-primary">Writing Quality Improver</h1>
          <p className="text-sm text-text-secondary mt-1">
            Provider-agnostic stylistic clarity, tone refinement, and sentence-level change review with protected span preservation.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base font-semibold">Source Text</CardTitle>
              <CardDescription>
                Input text to refine. Numbers, citations, URLs, and code blocks will be masked and preserved.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <textarea
                rows={10}
                placeholder="Enter text to improve for academic clarity, conciseness, or professional readability..."
                className="w-full rounded border border-border bg-surface-base p-3 text-sm text-text-primary placeholder:text-text-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent resize-y"
                readOnly
              />
              <div className="flex justify-between items-center text-xs text-text-muted">
                <span>Mode: Academic Clarity</span>
                <button
                  disabled
                  className="inline-flex items-center justify-center h-8 px-3 text-xs font-semibold rounded bg-accent text-white opacity-50 cursor-not-allowed"
                >
                  Improve (Phase 8 View Ready)
                </button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base font-semibold">Revised Output & Verification</CardTitle>
              <CardDescription>
                Sentence-aligned revisions and deterministic audit results will appear here.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <EmptyState
                icon={<FileEdit className="h-6 w-6" />}
                title="No Active Revision"
                description="Submit source text on the left to generate improvements with sentence-level accept/reject staging."
              />
            </CardContent>
          </Card>
        </div>
      </div>
    </AppShell>
  );
}
