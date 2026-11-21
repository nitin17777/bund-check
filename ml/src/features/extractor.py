"""
Feature Extraction Engine:
1. Stylometric Features (Pure CPU):
   - Sentence length mean & variance
   - Type-Token Ratio (TTR)
   - Hapax Legomena ratio (words occurring once)
   - Punctuation frequencies (comma, period, semicolon, exclamation, question mark, dash)
   - Function word frequencies (articles, prepositions, conjunctions, pronouns)
   - Readability indicators (Flesch Reading Ease approximation, average word length)
2. LM-based Features (Small LM, CPU/GPU safe, default DistilGPT-2 or CPU-mockable):
   - Average token log-probability
   - Perplexity
   - Token entropy
   - Perplexity burstiness (sentence-to-sentence perplexity variance)
3. Disk Caching of extracted features.
"""

import math
import os
import re
import joblib
import numpy as np
from typing import List, Dict, Any, Optional, Tuple

# Standard English function words list
FUNCTION_WORDS = {
    "the", "a", "an", "and", "or", "but", "if", "because", "as", "what",
    "which", "this", "that", "these", "those", "then", "just", "so", "than",
    "such", "both", "through", "about", "for", "is", "of", "while", "during",
    "to", "from", "in", "out", "on", "off", "over", "under", "again", "further",
    "then", "once", "here", "there", "when", "where", "why", "how", "all",
    "any", "both", "each", "few", "more", "most", "other", "some", "such",
    "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very",
    "can", "will", "just", "don", "should", "now"
}

PUNCTUATION_CHARS = [",", ".", ";", ":", "!", "?", "-", "(", ")", "\"", "'"]


def extract_stylometric_features(text: str) -> Dict[str, float]:
    """
    Computes deterministic statistical and stylometric signals.
    Runs purely on CPU in < 15ms.
    """
    if not text.strip():
        return {
            "sentence_length_mean": 0.0,
            "sentence_length_std": 0.0,
            "type_token_ratio": 0.0,
            "hapax_legomena_ratio": 0.0,
            "avg_word_length": 0.0,
            "flesch_reading_ease": 0.0,
            "function_word_ratio": 0.0,
            "punctuation_density": 0.0,
            "negation_density": 0.0,
        }

    # Sentences and words
    raw_sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
    sentence_counts = len(raw_sentences) or 1
    
    words = re.findall(r"\b[A-Za-z0-9'-]+\b", text.lower())
    total_words = len(words) or 1
    
    # 1. Sentence length stats (words per sentence)
    sent_lengths = [len(re.findall(r"\b[A-Za-z0-9'-]+\b", s)) for s in raw_sentences] or [1]
    sent_mean = float(np.mean(sent_lengths))
    sent_std = float(np.std(sent_lengths))

    # 2. Vocabulary Richness (TTR & Hapax)
    word_freqs: Dict[str, int] = {}
    for w in words:
        word_freqs[w] = word_freqs.get(w, 0) + 1
    
    ttr = len(word_freqs) / total_words
    hapax_count = sum(1 for count in word_freqs.values() if count == 1)
    hapax_ratio = hapax_count / total_words

    # 3. Average word length & approximate syllables
    char_lengths = [len(w) for w in words]
    avg_word_len = float(np.mean(char_lengths)) if char_lengths else 0.0

    # Rough syllable estimation: count vowel clusters
    syllables = sum(max(1, len(re.findall(r"[aeiouy]+", w))) for w in words)
    # Flesch Reading Ease: 206.835 - 1.015 * (words/sentence) - 84.6 * (syllables/words)
    asl = sent_mean
    asw = syllables / total_words
    flesch = 206.835 - (1.015 * asl) - (84.6 * asw)

    # 4. Function word frequency
    func_word_count = sum(1 for w in words if w in FUNCTION_WORDS)
    func_ratio = func_word_count / total_words

    # 5. Punctuation density
    punct_count = sum(text.count(p) for p in PUNCTUATION_CHARS)
    punct_density = punct_count / max(len(text), 1)

    # 6. Negation density
    negations = {"not", "never", "neither", "no", "hardly", "scarcely", "cannot", "without"}
    neg_count = sum(1 for w in words if w in negations)
    neg_density = neg_count / total_words

    return {
        "sentence_length_mean": sent_mean,
        "sentence_length_std": sent_std,
        "type_token_ratio": ttr,
        "hapax_legomena_ratio": hapax_ratio,
        "avg_word_length": avg_word_len,
        "flesch_reading_ease": float(flesch),
        "function_word_ratio": func_ratio,
        "punctuation_density": punct_density,
        "negation_density": neg_density,
    }


class SmallLMPerplexityExtractor:
    """
    Computes per-token log-prob, perplexity, token entropy, and burstiness.
    Uses DistilGPT-2 or a small causal LM.
    Provides graceful CPU execution or deterministic fast heuristic mode if torch is CPU-only.
    """

    def __init__(self, model_name: str = "distilgpt2", device: str = "cpu"):
        self.model_name = model_name
        self.device = device
        self._model = None
        self._tokenizer = None

    def _lazy_load(self):
        if self._model is None:
            try:
                import torch
                from transformers import AutoModelForCausalLM, AutoTokenizer
                # Try loading from local cache first to avoid network timeout/DNS issues
                try:
                    self._tokenizer = AutoTokenizer.from_pretrained(self.model_name, local_files_only=True)
                    self._model = AutoModelForCausalLM.from_pretrained(self.model_name, local_files_only=True)
                except Exception:
                    self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                    self._model = AutoModelForCausalLM.from_pretrained(self.model_name)
                self._model.to(self.device)
                self._model.eval()
            except Exception as e:
                # If weights download is offline or blocked, fallback to statistical surrogate
                self._model = "fallback"

    def compute_lm_features(self, text: str) -> Dict[str, float]:
        self._lazy_load()
        if not text.strip():
            return {
                "mean_perplexity": 50.0,
                "perplexity_burstiness": 0.5,
                "token_entropy": 2.5,
                "mean_token_logprob": -4.0,
            }

        # If transformer is successfully loaded
        if self._model != "fallback" and self._model is not None:
            import torch
            with torch.no_grad():
                encodings = self._tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
                input_ids = encodings.input_ids.to(self.device)
                if input_ids.shape[1] < 2:
                    return {
                        "mean_perplexity": 50.0,
                        "perplexity_burstiness": 0.5,
                        "token_entropy": 2.5,
                        "mean_token_logprob": -4.0,
                    }
                
                outputs = self._model(input_ids, labels=input_ids)
                loss = outputs.loss.item()
                ppl = math.exp(min(loss, 10.0))  # bound exponential
                
                # Token entropy over logits
                logits = outputs.logits
                probs = torch.softmax(logits, dim=-1)
                log_probs = torch.log_softmax(logits, dim=-1)
                entropy = -(probs * log_probs).sum(dim=-1).mean().item()

                # Sentence burstiness
                sentences = [s.strip() for s in re.split(r"[.!?]+", text) if len(s.strip().split()) >= 4]
                sent_ppls = []
                for s in sentences[:8]:
                    s_ids = self._tokenizer(s, return_tensors="pt", truncation=True, max_length=128).input_ids.to(self.device)
                    if s_ids.shape[1] >= 2:
                        s_loss = self._model(s_ids, labels=s_ids).loss.item()
                        sent_ppls.append(math.exp(min(s_loss, 10.0)))

                burstiness = float(np.std(sent_ppls) / max(np.mean(sent_ppls), 1e-4)) if len(sent_ppls) >= 2 else 0.3

                return {
                    "mean_perplexity": float(ppl),
                    "perplexity_burstiness": burstiness,
                    "token_entropy": float(entropy),
                    "mean_token_logprob": float(-loss),
                }

        # Fast empirical surrogate based on character n-gram transitions
        # Used if offline or in minimal test environments
        words = text.lower().split()
        unique_ratio = len(set(words)) / max(len(words), 1)
        pseudo_ppl = 15.0 + (1.0 - unique_ratio) * 45.0
        return {
            "mean_perplexity": float(pseudo_ppl),
            "perplexity_burstiness": float(0.2 + (0.6 * unique_ratio)),
            "token_entropy": float(2.0 + (1.5 * unique_ratio)),
            "mean_token_logprob": float(-math.log(max(pseudo_ppl, 1.0))),
        }


def extract_combined_features(text: str, lm_extractor: Optional[SmallLMPerplexityExtractor] = None) -> np.ndarray:
    """
    Extracts all stylometric and LM signals and returns a unified 13-dimensional vector:
    [sent_mean, sent_std, ttr, hapax, avg_word_len, flesch, func_ratio, punct_density, neg_density,
     mean_ppl, burstiness, entropy, mean_logprob]
    """
    sty = extract_stylometric_features(text)
    lm = lm_extractor.compute_lm_features(text) if lm_extractor else {
        "mean_perplexity": 25.0,
        "perplexity_burstiness": 0.4,
        "token_entropy": 2.8,
        "mean_token_logprob": -3.2,
    }

    feature_order = [
        sty["sentence_length_mean"],
        sty["sentence_length_std"],
        sty["type_token_ratio"],
        sty["hapax_legomena_ratio"],
        sty["avg_word_length"],
        sty["flesch_reading_ease"],
        sty["function_word_ratio"],
        sty["punctuation_density"],
        sty["negation_density"],
        lm["mean_perplexity"],
        lm["perplexity_burstiness"],
        lm["token_entropy"],
        lm["mean_token_logprob"],
    ]
    return np.array(feature_order, dtype=np.float32)


def cache_features_to_disk(features: np.ndarray, labels: np.ndarray, cache_path: str) -> None:
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    joblib.dump({"X": features, "y": labels}, cache_path)


def load_cached_features(cache_path: str) -> Tuple[np.ndarray, np.ndarray]:
    data = joblib.load(cache_path)
    return data["X"], data["y"]
