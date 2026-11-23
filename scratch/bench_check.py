"""
Phase 9 Performance Benchmark: latency and memory for /api/v1/check
at 500, 5000, and 20000 word document sizes.

Usage:
    python scratch/bench_check.py

Requires the backend packages to be importable (run from d:/bund-check with venv active).
Calls the detection pipeline directly (not via HTTP) to avoid network overhead.
"""

import sys
import time
import tracemalloc
import statistics
import os

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Check VRAM availability
HAS_CUDA = False
try:
    import torch
    HAS_CUDA = torch.cuda.is_available()
except ImportError:
    pass

def _vram_mb() -> float:
    """Return current CUDA allocated VRAM in MB, or 0 if not available."""
    if not HAS_CUDA:
        return 0.0
    return torch.cuda.memory_allocated() / (1024 * 1024)

def _vram_reserved_mb() -> float:
    if not HAS_CUDA:
        return 0.0
    return torch.cuda.memory_reserved() / (1024 * 1024)

# Generate synthetic texts
WORD_SIZES = [500, 5_000, 20_000]
SENTENCE = (
    "The experimental results demonstrate that the proposed methodology "
    "significantly outperforms baseline approaches in terms of both accuracy "
    "and computational efficiency across all benchmark datasets evaluated."
)
WORDS_PER_SENTENCE = len(SENTENCE.split())


def make_text(word_count: int) -> str:
    words_needed = word_count
    sentences = []
    while words_needed > 0:
        sentences.append(SENTENCE)
        words_needed -= WORDS_PER_SENTENCE
    full = " ".join(sentences)
    # Trim to approximately word_count words
    words = full.split()[:word_count]
    return " ".join(words)


def run_benchmark():
    # Import the production pipeline
    from backend.app.services.detection.detector import run_detection_pipeline

    results = []

    print(f"\n{'='*70}")
    print(f"BundCheck Phase 9 — Performance Benchmark")
    print(f"Python {sys.version}")
    print(f"CUDA available: {HAS_CUDA}")
    if HAS_CUDA:
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        torch.cuda.reset_peak_memory_stats()
    print(f"{'='*70}\n")

    for word_count in WORD_SIZES:
        text = make_text(word_count)
        actual_words = len(text.split())
        print(f"Testing {actual_words:,} words...")

        # Warm-up run (not measured)
        try:
            run_detection_pipeline(text)
        except Exception as e:
            print(f"  Warm-up failed: {e}")
            results.append({
                "words": actual_words,
                "error": str(e),
            })
            continue

        # Measured runs
        RUNS = 3
        latencies = []
        peak_ram_mb_list = []
        vram_before = _vram_mb()

        for i in range(RUNS):
            tracemalloc.start()
            t0 = time.perf_counter()
            try:
                run_detection_pipeline(text)
            except Exception as e:
                print(f"  Run {i+1} failed: {e}")
                break
            t1 = time.perf_counter()
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            latencies.append((t1 - t0) * 1000)
            peak_ram_mb_list.append(peak / (1024 * 1024))

        vram_after = _vram_mb()
        vram_peak_reserved = _vram_reserved_mb()

        if latencies:
            avg_ms = statistics.mean(latencies)
            min_ms = min(latencies)
            max_ms = max(latencies)
            avg_ram = statistics.mean(peak_ram_mb_list)
            vram_delta = vram_after - vram_before

            results.append({
                "words": actual_words,
                "avg_ms": avg_ms,
                "min_ms": min_ms,
                "max_ms": max_ms,
                "peak_ram_mb": avg_ram,
                "vram_delta_mb": vram_delta,
                "vram_reserved_mb": vram_peak_reserved,
            })

            print(f"  Latency  : avg={avg_ms:.0f}ms  min={min_ms:.0f}ms  max={max_ms:.0f}ms")
            print(f"  Peak RAM : {avg_ram:.1f} MB (traced)")
            if HAS_CUDA:
                print(f"  VRAM delta: {vram_delta:.1f} MB  reserved: {vram_peak_reserved:.1f} MB")
            print()

    # Print markdown table
    print("\n## Benchmark Results Table (Markdown)\n")
    print("| Words | Avg Latency | Min Latency | Max Latency | Peak RAM | VRAM Delta |")
    print("|------:|------------:|------------:|------------:|---------:|-----------:|")
    for r in results:
        if "error" in r:
            print(f"| {r['words']:,} | ERROR | — | — | — | — |")
        else:
            vram_str = f"{r['vram_delta_mb']:.0f} MB" if HAS_CUDA else "N/A (CPU)"
            print(
                f"| {r['words']:,} "
                f"| {r['avg_ms']:.0f} ms "
                f"| {r['min_ms']:.0f} ms "
                f"| {r['max_ms']:.0f} ms "
                f"| {r['peak_ram_mb']:.1f} MB "
                f"| {vram_str} |"
            )

    if HAS_CUDA:
        peak_vram = torch.cuda.max_memory_allocated() / (1024 * 1024)
        print(f"\nPeak VRAM across all runs: {peak_vram:.1f} MB")
        limit_mb = 4096
        if peak_vram > limit_mb:
            print(f"WARNING: Peak VRAM {peak_vram:.1f} MB exceeds 4 GB limit!")
        else:
            print(f"OK: Peak VRAM {peak_vram:.1f} MB < 4096 MB limit.")
    else:
        print("\nRunning on CPU (no CUDA device detected).")

    return results


if __name__ == "__main__":
    run_benchmark()
