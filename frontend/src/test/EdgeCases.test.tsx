import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { computeWordDiff } from '../lib/diff';
import { SentenceChangeCard } from '../components/improver/SentenceChangeCard';
import { DiffView } from '../components/improver/DiffView';
import type { VerificationFinding } from '../lib/api-client';

describe('Diff and Edge Cases Unit Tests', () => {
  it('handles empty paragraphs seamlessly in computeWordDiff', () => {
    const diff = computeWordDiff('', '');
    expect(diff).toEqual([]);

    const diffEmptyOrig = computeWordDiff('', 'New paragraph introduced.');
    expect(diffEmptyOrig).toEqual([{ type: 'insert', value: 'New paragraph introduced.' }]);

    const diffEmptyRev = computeWordDiff('Original paragraph deleted.', '');
    expect(diffEmptyRev).toEqual([{ type: 'delete', value: 'Original paragraph deleted.' }]);
  });

  it('handles consecutive whitespace and overlapping word boundaries', () => {
    const orig = 'word1    word2\n\nword3';
    const rev = 'word1  word2\n\nword4';
    const diff = computeWordDiff(orig, rev);

    // Verify reconstruction matches
    const reconstructedOrig = diff
      .filter((t) => t.type === 'equal' || t.type === 'delete')
      .map((t) => t.value)
      .join('');
    expect(reconstructedOrig).toBe(orig);

    const reconstructedRev = diff
      .filter((t) => t.type === 'equal' || t.type === 'insert')
      .map((t) => t.value)
      .join('');
    expect(reconstructedRev).toBe(rev);
  });

  it('handles multiple overlapping edits within the same sentence', () => {
    const orig = 'The old protocol failed due to an old error in the old routine.';
    const rev = 'The new protocol failed due to an updated error in the revised routine.';
    const diff = computeWordDiff(orig, rev);

    const deletions = diff.filter((t) => t.type === 'delete').map((t) => t.value);
    const insertions = diff.filter((t) => t.type === 'insert').map((t) => t.value);

    expect(deletions).toContain('old');
    expect(insertions).toContain('new');
    expect(insertions).toContain('updated');
    expect(insertions).toContain('revised');
  });

  it('SentenceChangeCard properly renders with empty findings and toggles accept', () => {
    const onToggle = vi.fn();
    render(
      <SentenceChangeCard
        sentenceIndex={1}
        paragraphIndex={2}
        original="Original edge sentence."
        revised="Revised edge sentence."
        accepted={true}
        viewMode="inline"
        findings={[]}
        onToggleAccept={onToggle}
      />
    );

    // When already accepted, clicking Reject should call onToggle with false
    const rejectBtn = screen.getByRole('button', { name: /reject/i });
    fireEvent.click(rejectBtn);
    expect(onToggle).toHaveBeenCalledWith(2, 1, false);
  });

  it('SentenceChangeCard with WARNING finding allows accept directly without blocking modal', () => {
    const onToggle = vi.fn();
    const warningFinding: VerificationFinding = {
      code: 'STYLE_SHIFT',
      category: 'style',
      severity: 'WARNING',
      message: 'Slight formality change detected.',
      source_span: 'edge',
      revised_span: 'frontier',
    };

    render(
      <SentenceChangeCard
        sentenceIndex={0}
        paragraphIndex={0}
        original="At the cutting edge."
        revised="At the cutting frontier."
        accepted={false}
        viewMode="inline"
        findings={[warningFinding]}
        onToggleAccept={onToggle}
      />
    );

    const acceptBtn = screen.getByRole('button', { name: /accept/i });
    fireEvent.click(acceptBtn);
    // Non-critical warning should accept directly without modal
    expect(onToggle).toHaveBeenCalledWith(0, 0, true);
  });
});
