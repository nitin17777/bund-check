import { AppShell } from "@/components/layout/AppShell";
import { EmptyState } from "@/components/ui/EmptyState";
import { History, ArrowRight } from "lucide-react";
import Link from "next/link";

export default function HistoryPage() {
  return (
    <AppShell>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-text-primary">Audit History</h1>
          <p className="text-sm text-text-secondary mt-1">
            Historical inspection records and revision logs.
          </p>
        </div>

        <EmptyState
          icon={<History className="h-8 w-8" />}
          title="No Stored Audits"
          description="BundCheck operates in ephemeral zero-retention mode by default. Opt-in local session storage will be configured in user preferences."
          action={
            <Link
              href="/checker"
              className="inline-flex items-center gap-2 h-9 px-4 text-xs font-semibold rounded bg-accent text-white hover:bg-accent-hover transition-colors"
            >
              <span>Run New Check</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          }
        />
      </div>
    </AppShell>
  );
}
