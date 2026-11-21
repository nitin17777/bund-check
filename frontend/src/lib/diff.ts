/**
 * Word-level and character-level diff computation using Longest Common Subsequence (LCS).
 * Deterministic, pure TypeScript, zero external dependencies.
 */

export interface DiffToken {
  type: "equal" | "delete" | "insert";
  value: string;
}

/**
 * Tokenize string into word and whitespace/punctuation chunks.
 * Preserves every character including spaces and newlines so concatenation
 * exactly reconstructs the input text.
 */
export function tokenizeWords(text: string): string[] {
  if (!text) return [];
  const matches = text.match(/\s+|\w+|[^\s\w]+/g);
  return matches || [text];
}

/**
 * Computes word-level diff between original and revised text.
 * Returns an array of DiffToken objects where:
 * - "equal": text present in both original and revised
 * - "delete": text removed from original
 * - "insert": text added to revised
 */
export function computeWordDiff(original: string, revised: string): DiffToken[] {
  if (original === revised) {
    return original ? [{ type: "equal", value: original }] : [];
  }

  if (!original) {
    return revised ? [{ type: "insert", value: revised }] : [];
  }

  if (!revised) {
    return original ? [{ type: "delete", value: original }] : [];
  }

  const tokensA = tokenizeWords(original);
  const tokensB = tokenizeWords(revised);
  const n = tokensA.length;
  const m = tokensB.length;

  // Standard LCS DP Table
  // dp[i][j] stores length of LCS of tokensA[0..i-1] and tokensB[0..j-1]
  const dp: number[][] = Array.from({ length: n + 1 }, () => new Array(m + 1).fill(0));

  for (let i = 1; i <= n; i++) {
    for (let j = 1; j <= m; j++) {
      if (tokensA[i - 1] === tokensB[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1] + 1;
      } else {
        dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
      }
    }
  }

  // Backtrack to build raw token diff
  const rawDiff: DiffToken[] = [];
  let i = n;
  let j = m;

  while (i > 0 || j > 0) {
    if (i > 0 && j > 0 && tokensA[i - 1] === tokensB[j - 1]) {
      rawDiff.push({ type: "equal", value: tokensA[i - 1] });
      i--;
      j--;
    } else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
      rawDiff.push({ type: "insert", value: tokensB[j - 1] });
      j--;
    } else if (i > 0 && (j === 0 || dp[i][j - 1] < dp[i - 1][j])) {
      rawDiff.push({ type: "delete", value: tokensA[i - 1] });
      i--;
    }
  }

  rawDiff.reverse();

  // Merge consecutive tokens of the same type for cleaner rendering
  const merged: DiffToken[] = [];
  for (const token of rawDiff) {
    if (merged.length > 0 && merged[merged.length - 1].type === token.type) {
      merged[merged.length - 1].value += token.value;
    } else {
      merged.push({ ...token });
    }
  }

  return merged;
}
