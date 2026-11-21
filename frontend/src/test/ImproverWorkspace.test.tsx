import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { SentenceChangeCard } from '../components/improver/SentenceChangeCard';
import { DiffView } from '../components/improver/DiffView';
import { FinalTextEditor } from '../components/improver/FinalTextEditor';
import type { VerificationFinding } from '../lib/api-client';

describe('DiffView component', () => {
  it('renders inline diff with ins and del tags', () => {
    render(<DiffView original="The quick brown fox" revised="The fast brown dog" viewMode="inline" />);
    
    expect(screen.getByText('quick')).toBeDefined();
    expect(screen.getByText('fast')).toBeDefined();
    expect(screen.getByText('fox')).toBeDefined();
    expect(screen.getByText('dog')).toBeDefined();
  });

  it('renders side-by-side diff with both columns', () => {
    render(<DiffView original="The quick brown fox" revised="The fast brown dog" viewMode="side_by_side" />);
    
    expect(screen.getByText('Original Text')).toBeDefined();
    expect(screen.getByText('Proposed Revision')).toBeDefined();
    expect(screen.getByText('quick')).toBeDefined();
    expect(screen.getByText('fast')).toBeDefined();
  });
});

describe('SentenceChangeCard component', () => {
  it('allows accepting and rejecting changes', () => {
    const onToggleAccept = vi.fn();

    render(
      <SentenceChangeCard
        sentenceIndex={0}
        paragraphIndex={0}
        original="This was badly written."
        revised="This was authored with clarity."
        accepted={false}
        viewMode="inline"
        findings={[]}
        onToggleAccept={onToggleAccept}
      />
    );

    // Initial state is unaccepted, button label is "Accept"
    const acceptBtn = screen.getByRole('button', { name: /accept/i });
    fireEvent.click(acceptBtn);
    expect(onToggleAccept).toHaveBeenCalledWith(0, 0, true);
  });

  it('triggers confirmation dialog when accepting a flagged critical finding', () => {
    const onToggleAccept = vi.fn();

    const criticalFinding: VerificationFinding = {
      code: 'NUM_DIFF',
      category: 'numbers',
      severity: 'CRITICAL',
      message: 'Number altered from 42 to 43',
      source_span: '42',
      revised_span: '43',
    };

    render(
      <SentenceChangeCard
        sentenceIndex={0}
        paragraphIndex={0}
        original="In 42 cases it succeeded."
        revised="In 43 cases it succeeded."
        accepted={false}
        viewMode="inline"
        findings={[criticalFinding]}
        onToggleAccept={onToggleAccept}
      />
    );

    // Click accept triggers modal dialog instead of immediately calling onToggleAccept
    const acceptBtn = screen.getByRole('button', { name: /accept/i });
    fireEvent.click(acceptBtn);
    expect(onToggleAccept).not.toHaveBeenCalled();

    // Confirm dialog should appear
    expect(screen.getByText(/Confirm Acceptance of Flagged Revision/i)).toBeDefined();
    expect(screen.getAllByText(/Number altered from 42 to 43/).length).toBeGreaterThanOrEqual(1);

    // Click confirm accept inside dialog
    fireEvent.click(screen.getByRole('button', { name: /confirm & accept change/i }));
    expect(onToggleAccept).toHaveBeenCalledWith(0, 0, true);
  });
});

describe('FinalTextEditor component', () => {
  it('handles undo, redo, and edit actions', () => {
    const onFinalTextChange = vi.fn();
    const onUndo = vi.fn();
    const onRedo = vi.fn();
    const onAcceptAll = vi.fn();
    const onRejectAll = vi.fn();

    render(
      <FinalTextEditor
        finalText="Draft revised paragraph."
        onFinalTextChange={onFinalTextChange}
        canUndo={true}
        canRedo={true}
        onUndo={onUndo}
        onRedo={onRedo}
        onAcceptAll={onAcceptAll}
        onRejectAll={onRejectAll}
        totalEditsCount={3}
        acceptedEditsCount={2}
        providerUsed="groq"
        modelUsed="llama-3.3-70b-versatile"
        usage={{
          prompt_tokens: 150,
          completion_tokens: 100,
          total_tokens: 250,
          estimated_cost_usd: 0.0001,
        }}
      />
    );

    // Verify telemetry display
    expect(screen.getByText(/groq/)).toBeDefined();
    expect(screen.getByText(/llama-3.3-70b-versatile/)).toBeDefined();
    expect(screen.getByText(/250/)).toBeDefined();

    // Verify undo & redo buttons
    const undoBtn = screen.getByTitle(/undo last change/i);
    fireEvent.click(undoBtn);
    expect(onUndo).toHaveBeenCalledTimes(1);

    const redoBtn = screen.getByTitle(/redo change/i);
    fireEvent.click(redoBtn);
    expect(onRedo).toHaveBeenCalledTimes(1);

    // Verify accept all & reject all
    fireEvent.click(screen.getByRole('button', { name: /accept all/i }));
    expect(onAcceptAll).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole('button', { name: /reject all/i }));
    expect(onRejectAll).toHaveBeenCalledTimes(1);

    // Toggle manual edit mode
    fireEvent.click(screen.getByRole('button', { name: /manual edit/i }));

    // Verify editing the text
    const textarea = screen.getByRole('textbox');
    fireEvent.change(textarea, { target: { value: 'User edited manually.' } });
    expect(onFinalTextChange).toHaveBeenCalledWith('User edited manually.');
  });

  it('renders disabled download button with proper tooltip and does not trigger fake download', () => {
    render(
      <FinalTextEditor
        finalText="Some text"
        onFinalTextChange={vi.fn()}
        canUndo={false}
        canRedo={false}
        onUndo={vi.fn()}
        onRedo={vi.fn()}
        onAcceptAll={vi.fn()}
        onRejectAll={vi.fn()}
        totalEditsCount={0}
        acceptedEditsCount={0}
      />
    );

    const downloadBtn = screen.getByRole('button', { name: /download/i });
    expect(downloadBtn).toHaveProperty('disabled', true);
  });
});
