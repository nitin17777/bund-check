/**
 * Local opt-in session store for history, dashboard activity, and settings.
 * Complies with strict privacy guidelines:
 * - Default: "store_opt_in" = false (strict zero-storage).
 * - Documents are stored locally in browser session/local storage ONLY when the user explicitly opts in.
 * - Clear functions for deleting individual records, exporting data, or purging all data.
 */

import { CheckResponse, ImproveResponse } from "./api-client";

export interface AuditRecord {
  id: string; // analysis_id or revision_id
  type: "check" | "improver";
  timestamp: string; // ISO string
  title: string;
  summary: string;
  wordCount: number;
  labelOrMode: string;
  checkData?: CheckResponse;
  improverData?: ImproveResponse;
}

export interface UserSettings {
  storeOptIn: boolean; // default false
  defaultImprovementMode: string; // default "academic_clarity"
  dataRetentionDays: number; // default 30 (0 = session only)
  selectedProvider: string; // default "groq"
}

const SETTINGS_KEY = "bundcheck_user_settings";
const HISTORY_KEY = "bundcheck_audit_history";

export const DEFAULT_SETTINGS: UserSettings = {
  storeOptIn: false,
  defaultImprovementMode: "academic_clarity",
  dataRetentionDays: 30,
  selectedProvider: "groq",
};

export const localStore = {
  getSettings(): UserSettings {
    if (typeof window === "undefined") return DEFAULT_SETTINGS;
    try {
      const stored = localStorage.getItem(SETTINGS_KEY);
      if (!stored) return DEFAULT_SETTINGS;
      return { ...DEFAULT_SETTINGS, ...JSON.parse(stored) };
    } catch {
      return DEFAULT_SETTINGS;
    }
  },

  saveSettings(settings: Partial<UserSettings>): UserSettings {
    if (typeof window === "undefined") return DEFAULT_SETTINGS;
    try {
      const current = this.getSettings();
      const updated = { ...current, ...settings };
      localStorage.setItem(SETTINGS_KEY, JSON.stringify(updated));
      // If user disabled storeOptIn, purge history
      if (!updated.storeOptIn) {
        localStorage.removeItem(HISTORY_KEY);
      }
      return updated;
    } catch {
      return DEFAULT_SETTINGS;
    }
  },

  getHistory(): AuditRecord[] {
    if (typeof window === "undefined") return [];
    try {
      const settings = this.getSettings();
      if (!settings.storeOptIn) return [];
      const stored = localStorage.getItem(HISTORY_KEY);
      if (!stored) return [];
      const records: AuditRecord[] = JSON.parse(stored);
      // Auto-prune expired records based on retention
      if (settings.dataRetentionDays > 0) {
        const cutoff = Date.now() - settings.dataRetentionDays * 24 * 60 * 60 * 1000;
        return records.filter((r) => new Date(r.timestamp).getTime() > cutoff);
      }
      return records;
    } catch {
      return [];
    }
  },

  saveCheckRecord(result: CheckResponse, snippet?: string): void {
    if (typeof window === "undefined") return;
    const settings = this.getSettings();
    if (!settings.storeOptIn) return; // Strict zero-storage default

    const record: AuditRecord = {
      id: result.analysis_id,
      type: "check",
      timestamp: new Date().toISOString(),
      title: result.document_id ? `Document ${result.document_id.slice(0, 8)}` : `Inspection ${result.analysis_id.slice(0, 8)}`,
      summary: snippet ? snippet.slice(0, 120) + (snippet.length > 120 ? "..." : "") : `Analyzed with synthetic pattern score ${result.synthetic_pattern_confidence.toFixed(2)}`,
      wordCount: result.stats?.word_count ?? (snippet ? snippet.trim().split(/\s+/).length : 0),
      labelOrMode: result.label,
      checkData: result,
    };

    const records = this.getHistory();
    const updated = [record, ...records.filter((r) => r.id !== record.id)].slice(0, 50);
    try {
      localStorage.setItem(HISTORY_KEY, JSON.stringify(updated));
    } catch {
      // quota exceeded or storage unavailable
    }
  },

  saveImproverRecord(result: ImproveResponse, originalSnippet?: string): void {
    if (typeof window === "undefined") return;
    const settings = this.getSettings();
    if (!settings.storeOptIn) return;

    const record: AuditRecord = {
      id: result.revision_id,
      type: "improver",
      timestamp: new Date().toISOString(),
      title: `Revision ${result.revision_id.slice(0, 8)} (${result.mode})`,
      summary: originalSnippet ? originalSnippet.slice(0, 120) + "..." : `Mode: ${result.mode}`,
      wordCount: result.stats?.original_word_count ?? 0,
      labelOrMode: result.mode,
      improverData: result,
    };

    const records = this.getHistory();
    const updated = [record, ...records.filter((r) => r.id !== record.id)].slice(0, 50);
    try {
      localStorage.setItem(HISTORY_KEY, JSON.stringify(updated));
    } catch {
      // quota exceeded
    }
  },

  getRecordById(id: string): AuditRecord | null {
    const records = this.getHistory();
    return records.find((r) => r.id === id) || null;
  },

  deleteRecord(id: string): void {
    if (typeof window === "undefined") return;
    try {
      const records = this.getHistory();
      const updated = records.filter((r) => r.id !== id);
      localStorage.setItem(HISTORY_KEY, JSON.stringify(updated));
    } catch {
      // ignore
    }
  },

  clearAllData(): void {
    if (typeof window === "undefined") return;
    try {
      localStorage.removeItem(HISTORY_KEY);
      localStorage.removeItem(SETTINGS_KEY);
    } catch {
      // ignore
    }
  },

  exportAllData(): string {
    const settings = this.getSettings();
    const history = this.getHistory();
    return JSON.stringify(
      {
        exported_at: new Date().toISOString(),
        settings,
        history,
      },
      null,
      2
    );
  },
};
