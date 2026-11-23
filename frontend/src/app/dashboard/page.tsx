"use client";

import * as React from "react";
import { AppShell } from "@/components/layout/AppShell";
import { EmptyState } from "@/components/ui/EmptyState";
import {
  LayoutDashboard,
  ArrowRight,
  ShieldAlert,
  Sparkles,
  Activity,
  History,
  FileText,
  Clock,
  Layers,
} from "lucide-react";
import Link from "next/link";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { apiClient, HealthResponse } from "@/lib/api-client";
import { localStore, AuditRecord } from "@/lib/local-store";

export default function DashboardPage() {
  const [health, setHealth] = React.useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = React.useState<string | null>(null);
  const [history, setHistory] = React.useState<AuditRecord[]>([]);
  const [isStoreOptIn, setIsStoreOptIn] = React.useState(false);

  React.useEffect(() => {
    // 1. Fetch real health status from the API
    let isMounted = true;
    apiClient
      .getHealth()
      .then((data) => {
        if (isMounted) setHealth(data);
      })
      .catch((err) => {
        if (isMounted) setHealthError(err.message || "Failed to query backend health.");
      });

    // 2. Load opt-in history from localStore
    const settings = localStore.getSettings();
    setIsStoreOptIn(settings.storeOptIn);
    setHistory(localStore.getHistory());

    return () => {
      isMounted = false;
    };
  }, []);

  const totalChecks = history.filter((r) => r.type === "check").length;
  const totalImproves = history.filter((r) => r.type === "improver").length;

  return (
    <AppShell>
      <div className="space-y-6 max-w-6xl">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-text-primary">
              Dashboard Overview
            </h1>
            <p className="text-sm text-text-secondary mt-1">
              Real-time operational status, quick actions, and recent activity metrics.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Link href="/checker">
              <Button variant="primary" size="sm" className="gap-1.5">
                <ShieldAlert className="h-4 w-4" />
                <span>New Content Check</span>
              </Button>
            </Link>
            <Link href="/humanizer">
              <Button variant="secondary" size="sm" className="gap-1.5">
                <Sparkles className="h-4 w-4" />
                <span>Writing Improver</span>
              </Button>
            </Link>
          </div>
        </div>

        {/* Real Status & Counts Row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Health status */}
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-xs font-semibold uppercase tracking-wider text-text-muted">
                  Service Engine
                </CardTitle>
                <Activity className="h-4 w-4 text-accent" />
              </div>
              <div className="text-xl font-bold font-mono mt-1">
                {health ? (
                  <span className="text-semantic-success flex items-center gap-1.5">
                    <span className="h-2 w-2 rounded-full bg-semantic-success animate-pulse" />
                    Online
                  </span>
                ) : healthError ? (
                  <span className="text-semantic-critical text-sm">Offline</span>
                ) : (
                  <span className="text-text-muted text-sm">Checking...</span>
                )}
              </div>
              <CardDescription className="text-xs text-text-muted mt-1">
                {health ? `v${health.version} (${health.environment})` : "Backend status check"}
              </CardDescription>
            </CardHeader>
          </Card>

          {/* Calibrated Abstain Band */}
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-xs font-semibold uppercase tracking-wider text-text-muted">
                  Abstain Band
                </CardTitle>
                <Layers className="h-4 w-4 text-semantic-warning" />
              </div>
              <div className="text-xl font-bold font-mono text-text-primary mt-1">
                [0.40 - 0.60]
              </div>
              <CardDescription className="text-xs text-text-muted mt-1">
                Calibrated inconclusive margin
              </CardDescription>
            </CardHeader>
          </Card>

          {/* Stored Checks */}
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-xs font-semibold uppercase tracking-wider text-text-muted">
                  Analyses Stored
                </CardTitle>
                <FileText className="h-4 w-4 text-text-muted" />
              </div>
              <div className="text-xl font-bold font-mono text-text-primary mt-1">
                {isStoreOptIn ? totalChecks : 0}
              </div>
              <CardDescription className="text-xs text-text-muted mt-1">
                {isStoreOptIn ? "Opted-in local records" : "Zero-storage active"}
              </CardDescription>
            </CardHeader>
          </Card>

          {/* Stored Revisions */}
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-xs font-semibold uppercase tracking-wider text-text-muted">
                  Revisions Stored
                </CardTitle>
                <Sparkles className="h-4 w-4 text-text-muted" />
              </div>
              <div className="text-xl font-bold font-mono text-text-primary mt-1">
                {isStoreOptIn ? totalImproves : 0}
              </div>
              <CardDescription className="text-xs text-text-muted mt-1">
                {isStoreOptIn ? "Opted-in local records" : "Zero-storage active"}
              </CardDescription>
            </CardHeader>
          </Card>
        </div>

        {/* Quick Actions & Privacy Notice */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="md:col-span-2">
            <CardHeader>
              <CardTitle className="text-base font-semibold">Quick Actions</CardTitle>
              <CardDescription>
                Direct access to core AI detection, document enhancement, and audit workflows.
              </CardDescription>
            </CardHeader>
            <CardContent className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-0">
              <Link
                href="/checker"
                className="group flex flex-col justify-between p-4 rounded-lg border border-border/70 bg-surface-base hover:bg-surface-card hover:border-accent transition-all"
              >
                <div>
                  <div className="flex items-center gap-2 font-semibold text-sm text-text-primary group-hover:text-accent">
                    <ShieldAlert className="h-4 w-4 text-accent" />
                    AI Content Checker
                  </div>
                  <p className="text-xs text-text-muted mt-1.5 leading-relaxed">
                    Inspect PDF, DOCX, or text manuscripts with calibrated multi-signal detection and character-aligned sentence heatmaps.
                  </p>
                </div>
                <div className="flex items-center gap-1 text-xs font-medium text-accent mt-3">
                  <span>Open workspace</span>
                  <ArrowRight className="h-3 w-3 group-hover:translate-x-0.5 transition-transform" />
                </div>
              </Link>

              <Link
                href="/humanizer"
                className="group flex flex-col justify-between p-4 rounded-lg border border-border/70 bg-surface-base hover:bg-surface-card hover:border-accent transition-all"
              >
                <div>
                  <div className="flex items-center gap-2 font-semibold text-sm text-text-primary group-hover:text-accent">
                    <Sparkles className="h-4 w-4 text-accent" />
                    Writing Improver
                  </div>
                  <p className="text-xs text-text-muted mt-1.5 leading-relaxed">
                    Enhance prose across 6 editorial styles with protected span preservation, sentence diffs, and verification audits.
                  </p>
                </div>
                <div className="flex items-center gap-1 text-xs font-medium text-accent mt-3">
                  <span>Open workspace</span>
                  <ArrowRight className="h-3 w-3 group-hover:translate-x-0.5 transition-transform" />
                </div>
              </Link>
            </CardContent>
          </Card>

          {/* Privacy posture card */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-base font-semibold">Storage Policy</CardTitle>
                <Badge variant={isStoreOptIn ? "info" : "success"}>
                  {isStoreOptIn ? "Opt-in Local" : "Zero-Storage"}
                </Badge>
              </div>
              <CardDescription>
                Client privacy and document retention configuration.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-xs text-text-secondary pt-0">
              <p className="leading-relaxed">
                {isStoreOptIn
                  ? "Audit records and report links are retained locally in this browser only. Cloud storage is never used without explicit authorization."
                  : "All uploaded documents and text submissions are analyzed in ephemeral memory and discarded immediately upon response completion."}
              </p>
              <Link
                href="/settings"
                className="inline-flex items-center gap-1.5 text-accent hover:underline font-medium"
              >
                <span>Manage privacy in Settings</span>
                <ArrowRight className="h-3 w-3" />
              </Link>
            </CardContent>
          </Card>
        </div>

        {/* Recent Activity Section */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold tracking-tight text-text-primary">
              Recent Activity
            </h2>
            {history.length > 0 && (
              <Link
                href="/history"
                className="text-xs font-medium text-accent hover:underline flex items-center gap-1"
              >
                <span>View all ({history.length})</span>
                <ArrowRight className="h-3 w-3" />
              </Link>
            )}
          </div>

          {history.length > 0 ? (
            <div className="divide-y divide-border border border-border rounded-lg bg-surface-card overflow-hidden">
              {history.slice(0, 5).map((record) => (
                <div
                  key={record.id}
                  className="p-3.5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 hover:bg-surface-elevated/40 transition-colors"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-xs text-text-primary">
                        {record.title}
                      </span>
                      <Badge
                        variant={record.type === "check" ? "default" : "info"}
                        className="text-[10px] py-0 px-1.5"
                      >
                        {record.type === "check" ? "Check" : "Improver"}
                      </Badge>
                      <Badge variant="outline" className="text-[10px] py-0 px-1.5 text-text-muted">
                        {record.labelOrMode}
                      </Badge>
                    </div>
                    <p className="text-xs text-text-muted line-clamp-1">
                      {record.summary}
                    </p>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-text-muted shrink-0">
                    <span className="flex items-center gap-1 font-mono">
                      <Clock className="h-3 w-3" />
                      {new Date(record.timestamp).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                    <Link
                      href={record.type === "check" ? `/reports/${record.id}` : "/humanizer"}
                      className="text-accent hover:underline font-medium text-xs"
                    >
                      Open
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              icon={<LayoutDashboard className="h-8 w-8 text-text-muted" />}
              title="No Inspection Activity Recorded"
              description={
                isStoreOptIn
                  ? "You have opted into local audit retention, but have not performed any inspections or text improvements yet."
                  : "You are currently running in strict zero-retention mode. No inspection transcripts or document records are stored."
              }
              action={
                <div className="flex items-center gap-2">
                  <Link
                    href="/checker"
                    className="inline-flex items-center gap-2 h-8 px-3.5 text-xs font-semibold rounded bg-accent text-white hover:bg-accent-hover transition-colors"
                  >
                    <span>Inspect Document</span>
                    <ArrowRight className="h-3 w-3" />
                  </Link>
                  <Link
                    href="/history"
                    className="inline-flex items-center gap-2 h-8 px-3.5 text-xs font-semibold rounded border border-border text-text-primary hover:bg-surface-card transition-colors"
                  >
                    <History className="h-3 w-3" />
                    <span>History Guide</span>
                  </Link>
                </div>
              }
            />
          )}
        </div>
      </div>
    </AppShell>
  );
}
