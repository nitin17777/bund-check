import React from 'react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { localStore, DEFAULT_SETTINGS } from '../lib/local-store';
import DashboardPage from '../app/dashboard/page';
import HistoryPage from '../app/history/page';
import SettingsPage from '../app/settings/page';
import ReportDetailPage from '../app/reports/[id]/page';
import { ToastProvider } from '../components/ui/Toast';
import type { CheckResponse } from '../lib/api-client';

// Mock matchMedia for AppShell
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

describe('localStore unit tests', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('returns default settings when storage is empty', () => {
    const settings = localStore.getSettings();
    expect(settings.storeOptIn).toBe(false);
    expect(settings.defaultImprovementMode).toBe('academic_clarity');
    expect(settings.dataRetentionDays).toBe(30);
  });

  it('saves and loads custom settings', () => {
    localStore.saveSettings({ storeOptIn: true, dataRetentionDays: 7 });
    const settings = localStore.getSettings();
    expect(settings.storeOptIn).toBe(true);
    expect(settings.dataRetentionDays).toBe(7);
  });

  it('strict zero-storage: does not save check record if storeOptIn is false', () => {
    const mockCheck: CheckResponse = {
      analysis_id: 'chk_123',
      synthetic_pattern_confidence: 0.15,
      label: 'likely human-leaning',
      abstain_margin: { lower: 0.4, upper: 0.6 },
      top_contributing_signals: [],
      paragraphs: [],
      limitations: {
        disclaimer: 'Probabilistic',
        plain_language_limitations: [],
        model_version: '1.0.0',
        model_hash: 'abc',
      },
    };

    localStore.saveCheckRecord(mockCheck, 'Test snippet');
    expect(localStore.getHistory()).toHaveLength(0);
  });

  it('saves and retrieves check record when storeOptIn is true', () => {
    localStore.saveSettings({ storeOptIn: true });

    const mockCheck: CheckResponse = {
      analysis_id: 'chk_456',
      synthetic_pattern_confidence: 0.85,
      label: 'likely AI-leaning',
      abstain_margin: { lower: 0.4, upper: 0.6 },
      top_contributing_signals: [],
      paragraphs: [],
      limitations: {
        disclaimer: 'Probabilistic',
        plain_language_limitations: [],
        model_version: '1.0.0',
        model_hash: 'abc',
      },
    };

    localStore.saveCheckRecord(mockCheck, 'Sample essay snippet');
    const history = localStore.getHistory();
    expect(history).toHaveLength(1);
    expect(history[0].id).toBe('chk_456');
    expect(history[0].labelOrMode).toBe('likely AI-leaning');

    const record = localStore.getRecordById('chk_456');
    expect(record).not.toBeNull();
    expect(record?.checkData?.analysis_id).toBe('chk_456');
  });

  it('purges data on clearAllData', () => {
    localStore.saveSettings({ storeOptIn: true });
    localStore.clearAllData();
    expect(localStore.getHistory()).toHaveLength(0);
    expect(localStore.getSettings()).toEqual(DEFAULT_SETTINGS);
  });
});

describe('Dashboard Page Component', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('renders dashboard overview with proper zero-retention empty state for new users', async () => {
    render(<DashboardPage />);

    expect(screen.getByText('Dashboard Overview')).toBeDefined();
    expect(screen.getByText('Abstain Band')).toBeDefined();
    expect(screen.getByText('[0.40 - 0.60]')).toBeDefined();
    expect(screen.getByText('No Inspection Activity Recorded')).toBeDefined();
    expect(screen.getAllByText('Zero-Storage').length).toBeGreaterThanOrEqual(1);
  });
});

describe('History Page Component', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('renders history page with retention policy advisory and empty state', () => {
    render(<HistoryPage />);

    expect(screen.getAllByText('Audit History').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/Retention Policy:/i)).toBeDefined();
    expect(screen.getByText('No Stored Audits')).toBeDefined();
  });

  it('renders records when opt-in store has items and supports deletion dialog', () => {
    localStore.saveSettings({ storeOptIn: true });
    const mockCheck: CheckResponse = {
      analysis_id: 'chk_test_del',
      synthetic_pattern_confidence: 0.5,
      label: 'inconclusive',
      abstain_margin: { lower: 0.4, upper: 0.6 },
      top_contributing_signals: [],
      paragraphs: [],
      limitations: {
        disclaimer: 'Probabilistic',
        plain_language_limitations: [],
        model_version: '1.0.0',
        model_hash: 'abc',
      },
    };
    localStore.saveCheckRecord(mockCheck, 'Test delete snippet');

    render(
      <ToastProvider>
        <HistoryPage />
      </ToastProvider>
    );

    expect(screen.getByText(/Inspection chk_test/i)).toBeDefined();
    const deleteBtn = screen.getByTitle('Delete record');
    fireEvent.click(deleteBtn);

    expect(screen.getByText('Confirm Record Deletion')).toBeDefined();
    const confirmBtn = screen.getByRole('button', { name: /Confirm Delete/i });
    fireEvent.click(confirmBtn);

    expect(localStore.getHistory()).toHaveLength(0);
  });
});

describe('Settings Page Component', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('renders settings sections, opt-in toggle, default mode selection, and honest Phase 8 notice', () => {
    render(
      <ToastProvider>
        <SettingsPage />
      </ToastProvider>
    );

    expect(screen.getByText('System & Privacy Settings')).toBeDefined();
    expect(screen.getByText('Data Privacy & Document Retention')).toBeDefined();
    expect(screen.getByText(/Opt into storing my past analyses/i)).toBeDefined();
    expect(screen.getByText('Default Writing Improver Mode')).toBeDefined();
    expect(screen.getByText(/Honest API Status: Multi-user authentication & remote settings sync are not built yet/i)).toBeDefined();
  });
});

describe('Report Detail Page Component', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('renders unpopulated state for unknown ID without fabricating data', () => {
    render(<ReportDetailPage params={{ id: 'non_existent_123' }} />);

    expect(screen.getByText('Inspection Report')).toBeDefined();
    expect(screen.getByText('Report Record Unpopulated')).toBeDefined();
    expect(screen.getByText(/No persisted audit record was found in your browser storage/i)).toBeDefined();
  });

  it('renders report with limitations and model version when found in local store', () => {
    localStore.saveSettings({ storeOptIn: true });
    const mockCheck: CheckResponse = {
      analysis_id: 'report_found_456',
      synthetic_pattern_confidence: 0.12,
      label: 'likely human-leaning',
      classification_band: 'HUMAN_TYPICAL',
      abstain_margin: { lower: 0.4, upper: 0.6 },
      abstain_band_thresholds: { lower: 0.4, upper: 0.6 },
      uncertainty_interval: { lower: 0.08, upper: 0.18, confidence_level: 0.95 },
      stats: { word_count: 140, paragraph_count: 1, sentence_count: 5 },
      top_contributing_signals: [],
      paragraphs: [],
      limitations: {
        disclaimer: 'Scientific Limitations Note',
        plain_language_limitations: ['Statistical indicators only'],
        model_version: '1.0.0',
        model_hash: 'sha256_mock_hash',
      },
    };
    localStore.saveCheckRecord(mockCheck, 'Saved report text');

    render(
      <ToastProvider>
        <ReportDetailPage params={{ id: 'report_found_456' }} />
      </ToastProvider>
    );

    expect(screen.getByText(/Viewing saved report record/i)).toBeDefined();
    expect(screen.getByText('Likely human-leaning')).toBeDefined();
    expect(screen.getByText(/Model Version: 1\.0\.0/i)).toBeDefined();
  });
});
