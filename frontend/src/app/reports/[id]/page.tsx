import { AppShell } from "@/components/layout/AppShell";
import { EmptyState } from "@/components/ui/EmptyState";
import { FileText, ArrowLeft } from "lucide-react";
import Link from "next/link";

export default function ReportDetailPage({
  params,
}: {
  params: { id: string };
}) {
  return (
    <AppShell>
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <Link
            href="/dashboard"
            className="rounded p-1.5 text-text-secondary hover:text-text-primary hover:bg-surface-card transition-colors"
            aria-label="Back to dashboard"
          >
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-text-primary">
              Inspection Report
            </h1>
            <p className="text-xs font-mono text-text-muted mt-0.5">
              Report ID: {params.id}
            </p>
          </div>
        </div>

        <EmptyState
          icon={<FileText className="h-8 w-8" />}
          title="Report Record Unpopulated"
          description={`No persisted audit found for identifier "${params.id}". Documents evaluated in ephemeral mode do not generate permanent cloud links.`}
          action={
            <Link
              href="/checker"
              className="inline-flex items-center gap-2 h-9 px-4 text-xs font-semibold rounded bg-accent text-white hover:bg-accent-hover transition-colors"
            >
              <span>Inspect New Document</span>
            </Link>
          }
        />
      </div>
    </AppShell>
  );
}
