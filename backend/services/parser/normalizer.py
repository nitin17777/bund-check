"""
Text Normalization Engine.

Performs safe, deterministic text normalization while preserving original extracted text
separately. Ensures normalization does NOT alter technical terminology, equations, numbers,
citations, symbols, or polarity/meaning.
"""

import re
import unicodedata
from typing import List


# Standard Unicode ligatures map to exact equivalent character sequences
LIGATURE_MAP = {
    "\ufb00": "ff",
    "\ufb01": "fi",
    "\ufb02": "fl",
    "\ufb03": "ffi",
    "\ufb04": "ffl",
    "\ufb05": "ft",
    "\ufb06": "st",
    "\u0132": "IJ",
    "\u0133": "ij",
    "\u0152": "OE",
    "\u0153": "oe",
    "\u00e6": "ae",
    "\u00c6": "AE",
}

# Regex to find line-break hyphenation: e.g. "com- \n puter" or "multi-\nstage"
HYPHEN_BREAK_PATTERN = re.compile(r"(\b[A-Za-z]+)-\s*[\r\n]+\s*([A-Za-z]+\b)")

# Set of common abbreviations that end with a dot but should NOT split sentences
KNOWN_ABBREVIATIONS = {
    "dr.", "mr.", "mrs.", "ms.", "prof.", "sr.", "jr.",
    "e.g.", "i.e.", "vs.", "fig.", "eq.", "al.", "etc."
}

# General sentence boundary candidate splitter: punctuation followed by space and uppercase/number
CANDIDATE_SPLIT_PATTERN = re.compile(r"([.!?])\s+(?=[A-Z0-9\"'(\[])")


def unfold_ligatures(text: str) -> str:
    """Replace presentation form ligatures with constituent standard characters."""
    for lig, replacement in LIGATURE_MAP.items():
        if lig in text:
            text = text.replace(lig, replacement)
    return text


def stitch_hyphenated_linebreaks(text: str) -> str:
    """
    Stitches words split across line breaks by hyphens.
    Preserves hyphenated compound words that are not split across lines.
    """
    return HYPHEN_BREAK_PATTERN.sub(r"\1\2", text)


def normalize_text(text: str) -> str:
    """
    Normalizes extracted text safely:
    1. Replaces null bytes and non-printable control characters (except \\n, \\r, \\t).
    2. Unfolds presentation ligatures (fi, fl, ffi, etc.).
    3. Normalizes Unicode representations using NFC composition to preserve distinct
       mathematical superscripts, symbols, and accented characters.
    4. Stitches broken hyphenated words at line breaks.
    5. Normalizes carriage returns (\\r\\n and \\r) to standard newlines (\\n).
    6. Strips trailing whitespace per line and compresses multiple blank lines.

    Crucially, does not alter punctuation, citations, numbers, or technical terms.
    """
    if not text:
        return ""

    # 1. Strip null bytes
    cleaned = text.replace("\x00", "")

    # 2. Unfold ligatures
    cleaned = unfold_ligatures(cleaned)

    # 3. Unicode normalization: NFC maintains exact superscripts (e.g. mc²) and math symbols
    cleaned = unicodedata.normalize("NFC", cleaned)

    # 4. Normalize line breaks
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")

    # 5. Stitch hyphenated linebreaks
    cleaned = stitch_hyphenated_linebreaks(cleaned)

    # 6. Normalize trailing spaces on lines while preserving paragraph breaks
    lines = [line.rstrip() for line in cleaned.split("\n")]
    cleaned = "\n".join(lines)

    # 7. Collapse excessive blank lines (> 2 newlines into 2 newlines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    return cleaned.strip()


def segment_sentences(paragraph_text: str) -> List[str]:
    """
    Splits a paragraph into individual sentences while respecting abbreviations (Dr., et al.),
    numbers, and quotation marks without lookbehind limitations.
    """
    if not paragraph_text:
        return []

    stripped = paragraph_text.strip()
    if not stripped:
        return []

    # Tokenize and stitch spans if boundary followed a known abbreviation
    parts = CANDIDATE_SPLIT_PATTERN.split(stripped)
    # parts will be [sentence_head, punct, sentence_head, punct, ...]
    
    sentences: List[str] = []
    current_sentence = ""

    idx = 0
    while idx < len(parts):
        chunk = parts[idx]
        current_sentence += chunk

        if idx + 1 < len(parts):
            punct = parts[idx + 1]
            current_sentence += punct

            # Check the last word before the punctuation
            tokens = current_sentence.strip().split()
            last_word = (tokens[-1] if tokens else "").lower()

            # If last word is a known abbreviation (e.g. "dr.", "al."), do not split
            if last_word in KNOWN_ABBREVIATIONS or last_word.endswith(tuple(KNOWN_ABBREVIATIONS)):
                current_sentence += " "
            else:
                sentences.append(current_sentence.strip())
                current_sentence = ""
            idx += 2
        else:
            idx += 1

    if current_sentence.strip():
        sentences.append(current_sentence.strip())

    return [s for s in sentences if s]
