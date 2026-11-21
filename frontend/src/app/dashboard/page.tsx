import { AppShell } from "@/components/layout/AppShell";
import { EmptyState } from "@/components/ui/EmptyState";
import { LayoutDashboard, ArrowRight } from "lucide-react";
import Link from "next/link";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";

export default function DashboardPage() {
  return (
    <AppShell>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-text-primary">Dashboard Overview</h1>
          <p className="text-sm text-text-secondary mt-1">
            Centralized overview of document inspections and writing revisions.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium text-text-secondary">Recent Analyses</CardTitle>
              <div className="text-2xl font-bold text-text-primary font-mono mt-2">0</div>
              <CardDescription className="text-xs text-text-muted mt-1">
                Zero-storage active. No stored past sessions.
              </CardDescription>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium text-text-secondary">Calibrated Abstain Band</CardTitle>
              <div className="text-sm font-medium text-text-primary mt-2">Active [0.40 - 0.60]</div>
              <CardDescription className="text-xs text-text-muted mt-1">
                Ambiguous inputs are flagged inconclusive.
              </CardDescription>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium text-text-secondary">Verification Engine</CardTitle>
              <div className="text-sm font-medium text-semantic-success mt-2">Ready</div>
              <CardDescription className="text-xs text-text-muted mt-1">
                Audits numbers, citations, and entities.
              </CardDescription>
            </CardHeader>
          </Card>
        </div>

        <EmptyState
          icon={<LayoutDashboard className="h-8 w-8" />}
          title="No Inspection Activity Recorded"
          description="You are currently running in zero-retention mode. Begin by analyzing a document or submitting text for writing improvement."
          action={
            <Link
              href="/checker"
              className="inline-flex items-center gap-2 h-9 px-4 text-xs font-semibold rounded bg-accent text-white hover:bg-accent-hover transition-colors"
            >
              <span>Start Content Check</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          }
        />
      </div>
    </AppShell>
  );
}
