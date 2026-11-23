"use client";

import * as React from "react";
import { AppShell } from "@/components/layout/AppShell";
import { EmptyState } from "@/components/ui/EmptyState";
import { CheckerResults } from "@/components/checker/CheckerResults";
import { localStore } from "@/lib/local-store";
import { CheckResponse } from "@/lib/api-client";
import { FileText, ArrowLeft, Info, ExternalLink } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/Button";
import { Card, CardContent } from "@/components/ui/Card";

export default function ReportDetailPage({
  params,
}: {
  params: { id: string };
}) {
  const [result, setResult] = React.useState<CheckResponse | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);

  React.useEffect(() => {
    // Look up opted-in record from local store
    const record = localStore.getRecordById(params.id);
    if (record && record.checkData) {
      setResult(record.checkData);
    }
    setIsLoading(false);
  }, [params.id]);

  return (
    <AppShell>
      <div className="space-y-6">
        {/* Breadcrumb Header */}
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <div className="flex items-center gap-3">
            <Link
              href="/history"
              className="rounded p-1.5 text-text-secondary hover:text-text-primary hover:bg-surface-card transition-colors"
              aria-label="Back to history"
            >
              <ArrowLeft className="h-4 w-4" />
            </Link>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-text-primary">
                Inspection Report
              </h1>
              <p className="text-xs font-mono text-text-muted mt-0.5">
                Report Identifier: {params.id}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Link href="/checker">
              <Button variant="outline" size="sm" className="text-xs">
                New Inspection
              </Button>
            </Link>
          </div>
        </div>

        {/* If populated with real check data from local store, reuse CheckerResults */}
        {result ? (
          <div className="space-y-4">
            <Card className="border-border/80 bg-surface-card/60">
              <CardContent className="p-3 text-xs text-text-secondary flex items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <Info className="h-4 w-4 text-accent shrink-0" />
                  <span>
                    Viewing saved report record. Scientific limitations, calibrated band, and full sentence heatmap are preserved exactly as evaluated.
                  </span>
                </div>
              </CardContent>
            </Card>

            <CheckerResults
              result={result}
              onReset={() => {
                window.location.href = "/checker";
              }}
            />
          </div>
        ) : !isLoading ? (
          <EmptyState
            icon={<FileText className="h-8 w-8 text-text-muted" />}
            title="Report Record Unpopulated"
            description={`No persisted audit record was found in your browser storage for identifier "${params.id}". Documents evaluated in strict zero-retention mode are not stored and do not generate permanent cloud links.`}
            action={
              <div className="flex items-center gap-2">
                <Link href="/checker">
                  <Button variant="primary" size="sm">
                    Inspect New Document
                  </Button>
                </Link>
                <Link href="/history">
                  <Button variant="outline" size="sm">
                    Back to History
                  </Button>
                </Link>
              </div>
            }
          />
        ) : null}
      </div>
    </AppShell>
  );
}
