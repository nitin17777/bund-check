# Dataset Provenance, Licensing & Benchmark Audit

This document audits candidate human vs. machine text detection datasets in accordance with academic standards and licensing requirements.

---

## 1. Candidate Datasets Audit

| Dataset Name | Source / Repository | Verified License | Domains Covered | Generator Models | Size / Samples | Known Issues & Biases | Usability Status |
|---|---|---|---|---|---|---|---|
| **HC3 (Human ChatGPT Comparison Corpus)** | `Hello-SimpleAI/HC3` (HuggingFace) | **CC-BY-SA 4.0** (Open research & commercial with attribution) | Medicine, Finance, Reddit (ELI5), Open Q&A, Computer Science, Law | ChatGPT (early `gpt-3.5-turbo` & `text-davinci-003`) | ~24,000 Q&A pairs (human vs ChatGPT answers) | 1. Prompt overlap between pairs (must split by prompt_id to prevent leakage).<br>2. Early ChatGPT outputs show predictable phrase patterns ("In conclusion", "It is important to note"). | **VERIFIED & SELECTED** (Primary in-distribution corpus) |
| **MIMU-Text** | `mimu-text` / Zenodo & HuggingFace (`tum-nlp/mimu-text`) | **CC-BY 4.0** | Wikipedia, News, ArXiv abstracts, Student essays | GPT-3.5, Llama-2-70B, Mistral-7B, Falcon-40B | ~15,000 documents | Multi-generator open weights. Useful for cross-model evaluation. | **VERIFIED & SELECTED** (Out-of-distribution generator corpus) |
| **Ghostbuster Benchmark Dataset** | `vashistha/ghostbuster-data` | **Apache 2.0 / MIT** | Student essays, Creative writing, News journalism | GPT-3, ChatGPT, Claude-instant | ~10,000 articles | Multi-domain human vs machine. Includes some heavily prompted articles. | **VERIFIED & SELECTED** (Domain robustness evaluation) |
| **TuringBench** | Zenodo / GitHub | **Research Only (Non-commercial)** | News articles | GPT-2, GROVER, RoBERTa generation, CTRL | ~200,000 short articles | Older generator architectures (pre-2021). Restricted license prevents commercial downstream packaging. | **VERIFIED BUT EXCLUDED** (License restriction & obsolete generators) |
| **ArguGPT** | HuggingFace (`argugpt`) | **CC0 (Public Domain)** | Argumentative student essays | GPT-3.5, GPT-4, Human argumentative essays | ~4,000 essays | Domain limited strictly to academic argumentation. | **VERIFIED & SELECTED** (Academic domain evaluation) |
| **Syn-Detect-Paraphrase (Internal / Kaggle-ready)** | Generated via Colab/Kaggle scripts | **MIT** | Multi-domain (HC3 + Ghostbuster samples) | Human-edited / paraphrased machine text | Curated benchmark set | Explicitly created to test detector degradation under human editing. | **VERIFIED & SELECTED** (Human-edited AI evaluation category) |

---

## 2. Unverified or Prohibited Datasets Recorded
- **Unverified Proprietary Corpora**: Commercial closed-source benchmark dumps lacking verifiable licenses or originating from scraped unconsented personal emails were excluded.
- **Leaked / Poisoned Datasets**: Datasets with pre-split sets where prompts are leaked across train/test were rejected from direct loading without custom prompt-grouped splitting.

---

## 3. Data Integrity & Leakage Prevention Rules
1. **Unified Schema**:
   All dataset loaders normalize inputs into the exact schema:
   ```json
   {
     "text": "Normalized body text...",
     "label": 0, // 0 = human, 1 = machine/synthetic
     "source": "hc3",
     "domain": "finance",
     "generator": "human", // "human", "gpt-3.5", "llama-2", "human_edited_gpt35"
     "prompt_id": "prompt_10492"
   }
   ```
2. **MinHash Near-Deduplication**:
   Jaccard similarity threshold $J \ge 0.85$ over 3-shingles eliminates near-identical prompts and copied responses.
3. **Prompt-Disjoint Grouping**:
   Splits are **strictly grouped by `prompt_id`**. If prompt $P$ is assigned to `train`, all human answers and all machine answers to prompt $P$ are quarantined from `val` and `test`.
