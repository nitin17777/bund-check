"use client";

import * as React from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import { useToast } from "@/components/ui/Toast";
import {
  ShieldCheck,
  Cpu,
  HardDrive,
  Trash2,
  Download,
  AlertTriangle,
  Info,
  CheckCircle2,
  Save,
  Server,
} from "lucide-react";
import { localStore, UserSettings, DEFAULT_SETTINGS } from "@/lib/local-store";

const IMPROVER_MODES = [
  { id: "academic_clarity", label: "Academic Clarity", desc: "Scholarly precision and objective syntactic cohesion" },
  { id: "professional", label: "Professional & Executive", desc: "Crisp workplace communication and direct voice" },
  { id: "natural_conversational", label: "Natural & Conversational", desc: "Fluid rhythm and engaging cadence" },
  { id: "simple_readable", label: "Simple & Readable", desc: "Accessible vocabulary and digestible syntax" },
  { id: "concise", label: "Concise & Tight", desc: "High information density and minimal filler words" },
  { id: "formal", label: "Formal & Polished", desc: "Dignified syntactic structure for official documents" },
];

export default function SettingsPage() {
  const { toast } = useToast();
  const [settings, setSettings] = React.useState<UserSettings>(DEFAULT_SETTINGS);
  const [isSaved, setIsSaved] = React.useState(false);
  const [showDeleteModal, setShowDeleteModal] = React.useState(false);

  React.useEffect(() => {
    setSettings(localStore.getSettings());
  }, []);

  const handleSave = () => {
    localStore.saveSettings(settings);
    setIsSaved(true);
    toast({
      type: "success",
      title: "Settings Saved",
      description: "Preferences updated successfully in local storage.",
    });
    setTimeout(() => setIsSaved(false), 2000);
  };

  const handleDeleteAll = () => {
    localStore.clearAllData();
    setSettings(DEFAULT_SETTINGS);
    setShowDeleteModal(false);
    toast({
      type: "critical",
      title: "Data Purged",
      description: "All audit history and local preferences have been permanently cleared.",
    });
  };

  const handleExportData = () => {
    const jsonStr = localStore.exportAllData();
    const blob = new Blob([jsonStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `bundcheck_user_data_${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast({
      type: "info",
      title: "Data Exported",
      description: "Downloaded your settings and audit history JSON archive.",
    });
  };

  return (
    <AppShell>
      <div className="space-y-6 max-w-4xl">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-text-primary">
            System & Privacy Settings
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            Configure default improvement modes, document retention policies, and export or purge data.
          </p>
        </div>

        <div className="space-y-6">
          {/* Privacy & Retention Section */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <ShieldCheck className="h-5 w-5 text-semantic-success" />
                  <CardTitle className="text-base font-semibold">
                    Data Privacy & Document Retention
                  </CardTitle>
                </div>
                <Badge variant={settings.storeOptIn ? "info" : "success"}>
                  {settings.storeOptIn ? "Opt-in Local Storage" : "Strict Zero-Storage"}
                </Badge>
              </div>
              <CardDescription>
                Determine whether your document submissions and inspection summaries are retained in local browser storage.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-5 text-xs text-text-secondary">
              {/* Store Opt-in Checkbox */}
              <div className="rounded-lg border border-border p-3.5 bg-surface-base space-y-3">
                <label className="flex items-start gap-3 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={settings.storeOptIn}
                    onChange={(e) =>
                      setSettings({ ...settings, storeOptIn: e.target.checked })
                    }
                    className="mt-0.5 rounded border-border text-accent focus:ring-accent bg-surface-elevated"
                  />
                  <div className="space-y-1">
                    <span className="font-semibold text-text-primary text-xs">
                      Opt into storing my past analyses and revisions locally
                    </span>
                    <p className="text-text-muted leading-relaxed">
                      Default is OFF (strict zero-storage). When enabled, audit metadata and evaluation reports are stored only in this browser&apos;s localStorage so you can review them in History. Remote servers never persist manuscripts or logs.
                    </p>
                  </div>
                </label>
              </div>

              {/* Data Retention Period */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-text-primary block">
                  Local Retention Window
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                  {[
                    { days: 7, label: "7 Days" },
                    { days: 30, label: "30 Days (Recommended)" },
                    { days: 90, label: "90 Days" },
                  ].map((item) => (
                    <button
                      key={item.days}
                      type="button"
                      disabled={!settings.storeOptIn}
                      onClick={() => setSettings({ ...settings, dataRetentionDays: item.days })}
                      className={`p-2.5 rounded border text-left transition-all ${
                        settings.dataRetentionDays === item.days && settings.storeOptIn
                          ? "border-accent bg-accent/10 text-text-primary font-medium"
                          : "border-border/70 bg-surface-base text-text-muted hover:border-border"
                      } disabled:opacity-40 disabled:cursor-not-allowed`}
                    >
                      <div className="font-semibold text-xs">{item.label}</div>
                      <div className="text-[10px] text-text-muted mt-0.5">
                        Prune records older than {item.days} days
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Default Improvement Mode */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2.5">
                <Cpu className="h-5 w-5 text-accent" />
                <CardTitle className="text-base font-semibold">
                  Default Writing Improver Mode
                </CardTitle>
              </div>
              <CardDescription>
                Select the preselected editorial style preset for text improvements.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-xs">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {IMPROVER_MODES.map((mode) => {
                  const isSelected = settings.defaultImprovementMode === mode.id;
                  return (
                    <button
                      key={mode.id}
                      type="button"
                      onClick={() =>
                        setSettings({ ...settings, defaultImprovementMode: mode.id })
                      }
                      className={`p-3 rounded-lg border text-left transition-all ${
                        isSelected
                          ? "border-accent bg-accent/10 shadow-sm"
                          : "border-border/70 bg-surface-base hover:border-border hover:bg-surface-elevated/40"
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span
                          className={`font-semibold text-xs ${
                            isSelected ? "text-accent" : "text-text-primary"
                          }`}
                        >
                          {mode.label}
                        </span>
                        {isSelected && (
                          <Badge variant="default" className="text-[9px] py-0 px-1 bg-accent">
                            Default
                          </Badge>
                        )}
                      </div>
                      <p className="text-[11px] text-text-muted leading-snug">{mode.desc}</p>
                    </button>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* Cloud Sync & Phase 8 API Contract Information */}
          <Card className="border-border/60 bg-surface-base/40">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <Server className="h-5 w-5 text-text-muted" />
                  <CardTitle className="text-base font-semibold text-text-secondary">
                    Remote Account & Cloud Sync
                  </CardTitle>
                </div>
                <Badge variant="outline" className="text-[10px]">
                  Phase 8 Roadmap
                </Badge>
              </div>
              <CardDescription>
                Documented in docs/API_SPEC.md § 3.10 (/api/v1/settings, /api/v1/delete).
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-xs text-text-muted">
              <div className="flex items-start gap-2.5 rounded border border-border/60 bg-surface-card p-3">
                <Info className="h-4 w-4 text-accent shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <p className="text-text-secondary font-medium">
                    Honest API Status: Multi-user authentication & remote settings sync are not built yet.
                  </p>
                  <p className="text-[11px] leading-relaxed">
                    Endpoints <code className="font-mono text-accent">GET /api/v1/settings</code> and <code className="font-mono text-accent">DELETE /api/v1/delete</code> will be integrated in Phase 8 cloud deployment. In the current release, all settings are stored and enforced locally on this client with zero telemetry sent to servers.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Data Export & Purge Actions */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2.5">
                <HardDrive className="h-5 w-5 text-semantic-info" />
                <CardTitle className="text-base font-semibold">
                  Data Portability & Deletion
                </CardTitle>
              </div>
              <CardDescription>
                Export your configured preferences and audit records, or permanently purge all stored data.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-xs">
              <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 p-3.5 rounded-lg border border-border bg-surface-base">
                <div>
                  <div className="font-semibold text-text-primary text-xs">
                    Export My Data
                  </div>
                  <div className="text-text-muted text-[11px] mt-0.5">
                    Download all local settings and audit history records in structured JSON format.
                  </div>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleExportData}
                  className="gap-1.5 text-xs h-8 shrink-0"
                >
                  <Download className="h-3.5 w-3.5 text-accent" />
                  <span>Export JSON</span>
                </Button>
              </div>

              <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 p-3.5 rounded-lg border border-semantic-critical/30 bg-semantic-critical/5">
                <div>
                  <div className="font-semibold text-semantic-critical text-xs">
                    Delete All Data
                  </div>
                  <div className="text-text-muted text-[11px] mt-0.5">
                    Immediately and permanently erase all saved audit transcripts and reset settings.
                  </div>
                </div>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => setShowDeleteModal(true)}
                  className="gap-1.5 text-xs h-8 shrink-0"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                  <span>Delete All Data</span>
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Sticky Bottom Save Bar */}
          <div className="flex items-center justify-end gap-3 pt-2">
            <Button
              variant="primary"
              size="md"
              onClick={handleSave}
              className="gap-2 px-5 font-semibold"
            >
              <Save className="h-4 w-4" />
              <span>{isSaved ? "Preferences Saved!" : "Save Preferences"}</span>
            </Button>
          </div>
        </div>

        {/* Delete All Confirmation Dialog */}
        <Dialog
          isOpen={showDeleteModal}
          onClose={() => setShowDeleteModal(false)}
          title="Permanently Purge All Data?"
          description="This action will permanently erase your local audit records, inspection summaries, and restore settings to defaults. This cannot be undone."
        >
          <div className="space-y-4 text-xs">
            <div className="rounded border border-semantic-critical/40 bg-semantic-critical/10 p-3 space-y-1 text-semantic-critical">
              <div className="font-semibold flex items-center gap-1.5">
                <AlertTriangle className="h-4 w-4" />
                Irreversible Action
              </div>
              <p className="text-[11px] text-text-secondary">
                All records in browser localStorage will be purged immediately.
              </p>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button variant="ghost" size="sm" onClick={() => setShowDeleteModal(false)}>
                Cancel
              </Button>
              <Button
                variant="destructive"
                size="sm"
                onClick={handleDeleteAll}
                className="gap-1.5"
              >
                <Trash2 className="h-3.5 w-3.5" />
                <span>Confirm & Purge All</span>
              </Button>
            </div>
          </div>
        </Dialog>
      </div>
    </AppShell>
  );
}
