"use client";

import * as React from "react";
import { AppShell } from "@/components/layout/AppShell";
import { EmptyState } from "@/components/ui/EmptyState";
import {
  History,
  ArrowRight,
  Search,
  Trash2,
  ExternalLink,
  ShieldAlert,
  Sparkles,
  Info,
  Calendar,
  Filter,
} from "lucide-react";
import Link from "next/link";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import { localStore, AuditRecord } from "@/lib/local-store";

export default function HistoryPage() {
  const [history, setHistory] = React.useState<AuditRecord[]>([]);
  const [isStoreOptIn, setIsStoreOptIn] = React.useState(false);
  const [searchQuery, setSearchQuery] = React.useState("");
  const [selectedFilter, setSelectedFilter] = React.useState<"all" | "check" | "improver">("all");
  const [deleteTarget, setDeleteTarget] = React.useState<AuditRecord | null>(null);

  React.useEffect(() => {
    const settings = localStore.getSettings();
    setIsStoreOptIn(settings.storeOptIn);
    setHistory(localStore.getHistory());
  }, []);

  const handleDeleteConfirm = () => {
    if (!deleteTarget) return;
    localStore.deleteRecord(deleteTarget.id);
    setHistory(localStore.getHistory());
    setDeleteTarget(null);
  };

  const filteredRecords = history.filter((record) => {
    const matchesFilter = selectedFilter === "all" || record.type === selectedFilter;
    const matchesQuery =
      record.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      record.summary.toLowerCase().includes(searchQuery.toLowerCase()) ||
      record.labelOrMode.toLowerCase().includes(searchQuery.toLowerCase()) ||
      record.id.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesFilter && matchesQuery;
  });

  return (
    <AppShell>
      <div className="space-y-6 max-w-6xl">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-text-primary">
              Audit History
            </h1>
            <p className="text-sm text-text-secondary mt-1">
              Historical inspection records, revision logs, and retention management.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Link href="/checker">
              <Button variant="outline" size="sm" className="gap-1.5 text-xs">
                <ShieldAlert className="h-3.5 w-3.5 text-accent" />
                <span>New Check</span>
              </Button>
            </Link>
            <Link href="/humanizer">
              <Button variant="outline" size="sm" className="gap-1.5 text-xs">
                <Sparkles className="h-3.5 w-3.5 text-accent" />
                <span>New Revision</span>
              </Button>
            </Link>
          </div>
        </div>

        {/* Retention / Zero-Storage Advisory Card */}
        <Card className="border-border/80 bg-surface-card/60">
          <CardContent className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
            <div className="flex items-start sm:items-center gap-2.5">
              <Info className="h-4 w-4 text-accent shrink-0 mt-0.5 sm:mt-0" />
              <div className="text-text-secondary">
                <strong className="text-text-primary">Retention Policy: </strong>
                {isStoreOptIn
                  ? "Audit records are stored locally in your browser per your explicit opt-in preference. Remote servers retain zero copies."
                  : "Strict zero-storage mode is active. Historical records are not saved to disk or browser storage unless opted in via Settings."}
              </div>
            </div>
            <Link href="/settings" className="shrink-0 text-accent font-semibold hover:underline">
              Configure Retention &rarr;
            </Link>
          </CardContent>
        </Card>

        {/* Search, Filter, and Controls Bar */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
          {/* Search box */}
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-text-muted" />
            <input
              type="text"
              placeholder="Search by title, snippet, or identifier..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-2 text-xs rounded border border-border bg-surface-base text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent"
            />
          </div>

          {/* Filter tabs */}
          <div className="flex items-center gap-1.5 rounded border border-border p-1 bg-surface-base text-xs">
            <button
              onClick={() => setSelectedFilter("all")}
              className={`px-3 py-1 rounded transition-colors ${
                selectedFilter === "all"
                  ? "bg-accent text-white font-medium shadow-sm"
                  : "text-text-secondary hover:text-text-primary"
              }`}
            >
              All Records
            </button>
            <button
              onClick={() => setSelectedFilter("check")}
              className={`px-3 py-1 rounded transition-colors ${
                selectedFilter === "check"
                  ? "bg-accent text-white font-medium shadow-sm"
                  : "text-text-secondary hover:text-text-primary"
              }`}
            >
              Content Checks
            </button>
            <button
              onClick={() => setSelectedFilter("improver")}
              className={`px-3 py-1 rounded transition-colors ${
                selectedFilter === "improver"
                  ? "bg-accent text-white font-medium shadow-sm"
                  : "text-text-secondary hover:text-text-primary"
              }`}
            >
              Writing Revisions
            </button>
          </div>
        </div>

        {/* Records List or Proper Empty State */}
        {filteredRecords.length > 0 ? (
          <div className="divide-y divide-border border border-border rounded-lg bg-surface-card overflow-hidden">
            {filteredRecords.map((record) => (
              <div
                key={record.id}
                className="p-4 flex flex-col md:flex-row md:items-center md:justify-between gap-3 hover:bg-surface-elevated/40 transition-colors"
              >
                <div className="space-y-1.5 max-w-2xl">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-semibold text-sm text-text-primary">
                      {record.title}
                    </span>
                    <Badge
                      variant={record.type === "check" ? "default" : "info"}
                      className="text-[10px] py-0 px-2"
                    >
                      {record.type === "check" ? "Check Analysis" : "Prose Revision"}
                    </Badge>
                    <Badge variant="outline" className="text-[10px] py-0 px-2 text-text-muted">
                      {record.labelOrMode}
                    </Badge>
                    <span className="text-[11px] font-mono text-text-muted">
                      {record.wordCount} words
                    </span>
                  </div>
                  <p className="text-xs text-text-muted leading-relaxed">
                    {record.summary}
                  </p>
                  <div className="flex items-center gap-3 text-[11px] text-text-muted">
                    <span className="flex items-center gap-1 font-mono">
                      <Calendar className="h-3 w-3" />
                      {new Date(record.timestamp).toLocaleDateString()} at{" "}
                      {new Date(record.timestamp).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                    <span className="font-mono text-text-muted">ID: {record.id.slice(0, 16)}</span>
                  </div>
                </div>

                <div className="flex items-center gap-2 self-end md:self-center shrink-0">
                  <Link
                    href={record.type === "check" ? `/reports/${record.id}` : "/humanizer"}
                  >
                    <Button variant="outline" size="sm" className="h-8 text-xs gap-1.5">
                      <ExternalLink className="h-3.5 w-3.5" />
                      <span>Open Record</span>
                    </Button>
                  </Link>

                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setDeleteTarget(record)}
                    className="h-8 px-2 text-text-muted hover:text-semantic-critical"
                    title="Delete record"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState
            icon={<History className="h-8 w-8 text-text-muted" />}
            title={
              searchQuery || selectedFilter !== "all"
                ? "No Matching Audits Found"
                : "No Stored Audits"
            }
            description={
              searchQuery || selectedFilter !== "all"
                ? "No audit records matched your current query and filter. Try resetting search parameters."
                : isStoreOptIn
                ? "You have local audit retention enabled, but have not generated any records yet. Completed checks and revisions will appear here."
                : "BundCheck operates in strict zero-retention mode by default. Documents and analysis transcripts are discarded immediately upon request completion."
            }
            action={
              <div className="flex items-center gap-2">
                {searchQuery || selectedFilter !== "all" ? (
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => {
                      setSearchQuery("");
                      setSelectedFilter("all");
                    }}
                  >
                    Reset Filters
                  </Button>
                ) : (
                  <>
                    <Link href="/checker">
                      <Button variant="primary" size="sm" className="gap-1.5">
                        <span>Run New Check</span>
                        <ArrowRight className="h-3 w-3" />
                      </Button>
                    </Link>
                    <Link href="/settings">
                      <Button variant="outline" size="sm">
                        Configure Opt-In
                      </Button>
                    </Link>
                  </>
                )}
              </div>
            }
          />
        )}

        {/* Delete Confirmation Modal */}
        <Dialog
          isOpen={!!deleteTarget}
          onClose={() => setDeleteTarget(null)}
          title="Confirm Record Deletion"
          description="Are you sure you want to delete this audit record from local storage? This action cannot be undone."
        >
          {deleteTarget && (
            <div className="space-y-4 text-xs">
              <div className="rounded border border-border p-3 bg-surface-elevated/40 space-y-1">
                <div className="font-semibold text-text-primary">{deleteTarget.title}</div>
                <p className="text-text-muted">{deleteTarget.summary}</p>
                <div className="font-mono text-[11px] text-text-muted mt-2">
                  ID: {deleteTarget.id}
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <Button variant="ghost" size="sm" onClick={() => setDeleteTarget(null)}>
                  Cancel
                </Button>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={handleDeleteConfirm}
                  className="gap-1.5"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                  <span>Confirm Delete</span>
                </Button>
              </div>
            </div>
          )}
        </Dialog>
      </div>
    </AppShell>
  );
}
