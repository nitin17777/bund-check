"""
Segmentation and Normalization Engine.
Handles:
- Paragraph segmentation.
- Sentence boundary splitting robust to abbreviations, citations ([1], (Smith, 2020)), decimals, bullet lists.
- Stable IDs for paragraphs (p0, p1) and sentences (p0_s0, p0_s1).
- Exact character offset tracking into the normalized text (both paragraph-relative and full-document relative).
- Language heuristic (identifying non-English text to warn).
"""

import re
import unicodedata
from typing import List, Tuple, Optional
from backend.app.models.document import Sentence, Paragraph

# Common typographic ligatures
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

HYPHEN_BREAK_PATTERN = re.compile(r"(\b[A-Za-z]+)-\s*[\r\n]+\s*([A-Za-z]+\b)")

# List of abbreviations that shouldn't end sentences
KNOWN_ABBREVIATIONS = {
    "dr.", "mr.", "mrs.", "ms.", "prof.", "sr.", "jr.",
    "e.g.", "i.e.", "vs.", "fig.", "eq.", "al.", "etc.",
    "no.", "vol.", "pp.", "ed.", "inc.", "ltd.", "co."
}

# Regex to detect potential sentence terminal (. ! ?) followed by whitespace and capital/quote/citation
CANDIDATE_SPLIT_REGEX = re.compile(r"([.!?]+)(\s+)(?=[A-Z0-9\"'(\[])")


def unfold_ligatures(text: str) -> str:
    for lig, replacement in LIGATURE_MAP.items():
        if lig in text:
            text = text.replace(lig, replacement)
    return text


def stitch_hyphenated_linebreaks(text: str) -> str:
    return HYPHEN_BREAK_PATTERN.sub(r"\1\2", text)


def normalize_paragraph_text(text: str) -> str:
    if not text:
        return ""

    cleaned = text.replace("\x00", "")
    cleaned = unfold_ligatures(cleaned)
    cleaned = unicodedata.normalize("NFC", cleaned)
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = stitch_hyphenated_linebreaks(cleaned)

    # Normalize whitespace inside lines
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in cleaned.split("\n")]
    cleaned = "\n".join(lines)
    cleaned = re.sub(r"\n{2,}", "\n", cleaned)
    return cleaned.strip()


def segment_sentences_with_offsets(paragraph_id: str, text: str) -> List[Sentence]:
    """
    Splits paragraph text into sentences and computes exact character offsets [start_char, end_char).
    Robust to abbreviations, citations, decimals (42.8%), and bullet lists.
    """
    if not text.strip():
        return []

    sentences: List[Sentence] = []
    
    # We find sentence boundaries using regex and abbreviation checking
    current_start = 0
    text_len = len(text)
    
    # Find all candidate punctuation matches
    matches = list(CANDIDATE_SPLIT_REGEX.finditer(text))
    
    if not matches:
        # Whole text is one sentence
        s_text = text.strip()
        return [
            Sentence(
                id=f"{paragraph_id}_s0",
                index=0,
                text=s_text,
                start_char=0,
                end_char=len(s_text),
                char_count=len(s_text),
                word_count=len(s_text.split()),
            )
        ]

    s_idx = 0
    for match in matches:
        punct_end = match.end(1)
        next_sentence_start = match.end()
        
        # Check text before punctuation
        candidate_segment = text[current_start:punct_end].strip()
        tokens = candidate_segment.split()
        last_word = tokens[-1].lower() if tokens else ""

        # Check if last word is a known abbreviation (e.g., 'Dr.', 'al.')
        if last_word in KNOWN_ABBREVIATIONS or last_word.endswith(tuple(KNOWN_ABBREVIATIONS)):
            continue  # Do not split here

        # Check for citation or parenthetical like (Smith et al., 2020)
        # If open paren/bracket is not closed yet
        open_parens = candidate_segment.count("(") - candidate_segment.count(")")
        open_brackets = candidate_segment.count("[") - candidate_segment.count("]")
        if open_parens > 0 or open_brackets > 0:
            continue  # Inside citation or parenthetical clause, do not split

        # Valid sentence split
        s_text = text[current_start:punct_end].strip()
        if s_text:
            # find actual start of non-whitespace
            actual_start = text.find(s_text, current_start)
            actual_end = actual_start + len(s_text)
            sentences.append(
                Sentence(
                    id=f"{paragraph_id}_s{s_idx}",
                    index=s_idx,
                    text=s_text,
                    start_char=actual_start,
                    end_char=actual_end,
                    char_count=len(s_text),
                    word_count=len(s_text.split()),
                )
            )
            s_idx += 1
            current_start = next_sentence_start

    # Trailing segment
    trailing_text = text[current_start:].strip()
    if trailing_text:
        actual_start = text.find(trailing_text, current_start)
        actual_end = actual_start + len(trailing_text)
        sentences.append(
            Sentence(
                id=f"{paragraph_id}_s{s_idx}",
                index=s_idx,
                text=trailing_text,
                start_char=actual_start,
                end_char=actual_end,
                char_count=len(trailing_text),
                word_count=len(trailing_text.split()),
            )
        )

    return sentences


def guess_language(text: str) -> Tuple[str, Optional[str]]:
    """
    Lightweight heuristic to detect language from common English stopwords vs foreign characters.
    Warns if non-English.
    """
    if not text:
        return "en", None

    common_english_words = {
        "the", "be", "to", "of", "and", "a", "in", "that", "have", "i",
        "it", "for", "not", "on", "with", "he", "as", "you", "do", "at",
        "this", "but", "his", "by", "from", "they", "we", "say", "her", "she",
        "or", "an", "will", "my", "one", "all", "would", "there", "their", "what"
    }

    words = re.findall(r"\b[A-Za-z]+\b", text.lower())
    
    # Check for non-Latin script dominance (Cyrillic, CJK, Arabic, etc.)
    non_ascii_chars = sum(1 for c in text if ord(c) > 127 and not unicodedata.category(c).startswith("P"))
    if non_ascii_chars / max(len(text), 1) > 0.20 or (len(words) > 10 and (sum(1 for w in words if w in common_english_words) / len(words)) < 0.05):
        return "unknown", "Text appears to be in a non-English language. Accuracy of models is optimized for English."

    return "en", None
