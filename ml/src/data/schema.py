"""
Unified Data Schema, Deduplication, and Prompt-Grouped Splitting Engine.

Enforces:
- Unified schema: {text, label, source, domain, generator, prompt_id}
- Label: 0 = human, 1 = machine/synthetic
- MinHash LSH deduplication across texts
- GroupKFold / Prompt-Disjoint Splitting: guarantees prompt_id never crosses train/val/test splits.
- Automated leakage verification assertions.
"""

import re
from typing import List, Dict, Any, Tuple, Optional
from pydantic import BaseModel, Field
from datasketch import MinHash, MinHashLSH
from sklearn.model_selection import GroupShuffleSplit


class DataRecord(BaseModel):
    text: str
    label: int = Field(description="0 for human, 1 for machine/synthetic")
    source: str = Field(description="Dataset origin, e.g. 'hc3', 'mimu', 'ghostbuster'")
    domain: str = Field(description="Domain category, e.g. 'medicine', 'finance', 'essays'")
    generator: str = Field(description="'human', 'chatgpt', 'gpt-3.5', 'llama-2', 'human_edited'")
    prompt_id: str = Field(description="Unique identifier of the question or prompt")


def tokenize_shingles(text: str, n: int = 3) -> List[str]:
    words = re.findall(r"\b[A-Za-z0-9]+\b", text.lower())
    if len(words) < n:
        return [" ".join(words)]
    return [" ".join(words[i : i + n]) for i in range(len(words) - n + 1)]


def deduplicate_records(records: List[DataRecord], threshold: float = 0.85, num_perm: int = 64) -> List[DataRecord]:
    """
    Near-duplicate removal using MinHash LSH.
    Eliminates documents with Jaccard 3-shingle similarity >= threshold.
    """
    lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)
    unique_records: List[DataRecord] = []

    for idx, rec in enumerate(records):
        shingles = tokenize_shingles(rec.text)
        if not shingles:
            continue
        m = MinHash(num_perm=num_perm)
        for s in shingles:
            m.update(s.encode("utf-8"))

        # Query if near-duplicate exists in LSH index
        duplicates = lsh.query(m)
        if not duplicates:
            lsh.insert(f"rec_{idx}", m)
            unique_records.append(rec)

    return unique_records


def split_grouped_dataset(
    records: List[DataRecord],
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    random_state: int = 42,
) -> Tuple[List[DataRecord], List[DataRecord], List[DataRecord]]:
    """
    Grouped split by prompt_id so the same question/prompt never leaks
    across train, val, and test.
    """
    assert abs((train_ratio + val_ratio + test_ratio) - 1.0) < 1e-5, "Ratios must sum to 1.0"

    prompt_groups = [r.prompt_id for r in records]

    # Split train vs temp (val + test)
    gss1 = GroupShuffleSplit(n_splits=1, train_size=train_ratio, random_state=random_state)
    train_idx, temp_idx = next(gss1.split(records, groups=prompt_groups))

    train_records = [records[i] for i in train_idx]
    temp_records = [records[i] for i in temp_idx]
    temp_groups = [r.prompt_id for r in temp_records]

    # Split temp into val and test
    relative_val_ratio = val_ratio / (val_ratio + test_ratio)
    gss2 = GroupShuffleSplit(n_splits=1, train_size=relative_val_ratio, random_state=random_state)
    val_rel_idx, test_rel_idx = next(gss2.split(temp_records, groups=temp_groups))

    val_records = [temp_records[i] for i in val_rel_idx]
    test_records = [temp_records[i] for i in test_rel_idx]

    # Run automated leakage assertion
    assert_no_split_leakage(train_records, val_records, test_records)

    return train_records, val_records, test_records


def assert_no_split_leakage(
    train: List[DataRecord], val: List[DataRecord], test: List[DataRecord]
) -> None:
    train_prompts = set(r.prompt_id for r in train)
    val_prompts = set(r.prompt_id for r in val)
    test_prompts = set(r.prompt_id for r in test)

    train_val_leak = train_prompts.intersection(val_prompts)
    train_test_leak = train_prompts.intersection(test_prompts)
    val_test_leak = val_prompts.intersection(test_prompts)

    if train_val_leak:
        raise ValueError(f"Leakage detected between train and val! Leaked prompts: {train_val_leak}")
    if train_test_leak:
        raise ValueError(f"Leakage detected between train and test! Leaked prompts: {train_test_leak}")
    if val_test_leak:
        raise ValueError(f"Leakage detected between val and test! Leaked prompts: {val_test_leak}")
