# AI Model Design & Machine Learning Architecture

## 1. Module A: Probabilistic Content Detection Methodology

### 1.1 Critical Operating Principle
The detection engine **never claims to prove authorship or authenticity**. Statistical detectors evaluate probability distributions and surface statistical anomalies indicative of machine-generated text. All outputs are probabilistic estimates accompanied by confidence intervals, calibration bands, and explicit notice that false positives and false negatives naturally occur.

Under no circumstances will the system use an "Ask an LLM if this text is AI" approach. Such approaches produce hallucinated rationales and completely uncalibrated probabilities.

---

### 1.2 Multi-Signal Feature Comparison & Architecture

To achieve robustness against model updates and paraphrasing, the detection pipeline synthesizes four complementary signal categories:

```
                  ┌────────────────────────────────────────┐
                  │          Input Normalized Text         │
                  └──────────────────┬─────────────────────┘
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         ▼                           ▼                           ▼
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│  Signal A: LM    │       │  Signal B:       │       │  Signal C:       │
│  Perplexity &    │       │  Stylometric &   │       │  Fine-Tuned      │
│  Entropy Engine  │       │  Statistical POS │       │  Transformer     │
└────────┬─────────┘       └────────┬─────────┘       └────────┬─────────┘
         │                          │                          │
         │ (Perplexity, Var,        │ (TTR, Hapax,             │ (Pooled Logits,
         │  Burstiness, Cross-Ent)  │  POS Frequencies,        │  Cross-Entropy)
         │                          │  Readability Scores)     │
         └──────────────────────────┼──────────────────────────┘
                                    │
                                    ▼
                     ┌─────────────────────────────┐
                     │    Feature Concatenation    │
                     └──────────────┬──────────────┘
                                    ▼
                     ┌─────────────────────────────┐
                     │   Ensemble Meta-Learner     │
                     │  (Gradient Boosting / LogR) │
                     └──────────────┬──────────────┘
                                    ▼
                     ┌─────────────────────────────┐
                     │    Isotonic / Platt         │
                     │       Calibrator            │
                     └──────────────┬──────────────┘
                                    ▼
         ┌─────────────────────────────────────────────────────┐
         │ Final Output: P(Synthetic), Band, Attribution Map   │
         └─────────────────────────────────────────────────────┘
```

#### Comparison of Methodologies:

| Methodology | Strengths | Weaknesses | Local Suitability (RTX 2050 / 4GB) |
|---|---|---|---|
| **(a) Perplexity, Entropy & Burstiness (Small LM)** | Grounded in language modeling mechanics. Synthetic text tends to follow lower perplexity paths with uniform token distributions. | Can yield false positives on predictable technical, legal, or repetitive human writing. | Excellent. A quantized small model (e.g. `distilgpt2` or `EleutherAI/pythia-160m`) runs in < 1 GB VRAM or CPU. |
| **(b) Stylometric & Statistical Features + GBDT** | Extremely fast, zero VRAM usage, highly interpretable (e.g. vocabulary richness, hapax legomena, sentence length variance). | Easily defeated by style matching; weak on very short inputs (< 100 words). | Excellent. Uses CPU with `scikit-learn` and `spaCy/NLTK`. |
| **(c) Fine-tuned Transformer Classifier** | Captures deep contextual patterns and semantic coherence. High accuracy on in-domain test sets. | Prone to overfitting to specific generator models (e.g. GPT-4); high VRAM footprint if unoptimized. | Feasible locally using distilled classifiers (e.g., `distilroberta-base` fine-tuned) in FP16 (< 1.5 GB VRAM). Training must be offloaded to Colab/Kaggle. |
| **(d) Calibrated Ensemble** (Selected Approach) | Combines the generalization of perplexity, the interpretability of stylometry, and the contextual discrimination of transformers. | Higher engineering complexity; requires rigorous cross-validation to prevent leakage. | Ideal. Small inference footprint while maximizing robustness against evasion. |

---

### 1.3 Statistical Signals & Mathematical Formulations

1. **Perplexity (PPL)**:
   $$\text{PPL}(W) = \exp \left( -\frac{1}{N} \sum_{i=1}^{N} \log P(w_i \mid w_1, \dots, w_{i-1}) \right)$$
   Synthetic text generated via nucleus or top-$k$ sampling typically clusters in a lower, narrower perplexity envelope than human prose.

2. **Perplexity Burstiness (Variance over Sentences)**:
   $$\text{Burstiness} = \frac{\sigma(\text{PPL}_{s})}{\mu(\text{PPL}_{s})}$$
   Human writing displays high variance in sentence-level perplexity (bursts of complexity interspersed with simple sentences), whereas LLM text exhibits homogeneous perplexity across sentences.

3. **Stylometric Indicators**:
   - **Type-Token Ratio (TTR)**: Vocabulary richness $V / N$.
   - **Hapax Legomena Ratio**: Proportion of words occurring exactly once $V_1 / N$.
   - **Part-of-Speech (POS) Distributional Entropy**: Shannon entropy over the distribution of POS tags (nouns, verbs, adjectives, function words).
   - **Sentence Length Variation**: Standard deviation of token counts per sentence.

---

### 1.4 Calibration, Uncertainty & The Abstain Band

Uncalibrated classifier outputs frequently produce overconfident probabilities near $0.0$ or $1.0$.

#### 1. Calibration Method
We apply **Isotonic Regression** (or Platt Scaling for smaller validation sets) on held-out validation data to ensure that a reported probability of $0.80$ corresponds to an empirical 80% synthetic prevalence.

$$\min_{m} \sum_{i=1}^{n} (y_i - m(z_i))^2 \quad \text{subject to } m(z_a) \le m(z_b) \text{ whenever } z_a \le z_b$$

#### 2. Three-Band Decision Architecture (Including Abstain Band)
Rather than a binary cut at $0.50$, the system enforces three calibrated regions:

| Probability Range | Classification State | Meaning & User Guidance |
|---|---|---|
| **$0.00 \le P < 0.40$** | **Low Statistical Machine Presence** | Characteristics strongly align with typical human stylistic variance. |
| **$0.40 \le P \le 0.60$** | **Inconclusive (Abstain Band)** | **The system abstains from classification.** Text features fall within overlapping statistical distributions. Human editorial review is required. |
| **$0.60 < P \le 1.00$** | **Elevated Statistical Machine Presence** | Characteristics show statistical homogeneity, low burstiness, or patterns typical of generated text. |

#### 3. Sentence-Level Attribution
Sentence scores $s_j \in [0, 1]$ are computed by projecting the sentence's local perplexity, burstiness deviation, and transformer attention/attribution weights against the calibrated model. Sentences falling above the 75th percentile of synthetic indicator thresholds are highlighted in the UI with detailed explanatory signal breakdowns.

---

### 1.5 Datasets, Splitting Strategy & Bias Evaluation

#### Candidate Datasets:
1. **HC3 (Human ChatGPT Comparison Corpus)**: Questions and human/ChatGPT answers across medicine, finance, open-domain questions.
2. **MIMU-Text**: Multi-generator benchmark including open-weight LLMs (Llama-2, Mistral).
3. **Ghostbuster Benchmark Dataset**: Multi-domain human vs. machine articles across student essays, creative writing, and journalism.

#### Data Integrity Requirements:
- **License Audit**: Must be verified permissive for research and platform benchmarking (CC-BY, MIT, or Apache 2.0).
- **Exact & Near Deduplication**: MinHash LSH deduplication across inputs to eliminate duplicate prompts and responses.
- **Source/Prompt-Disjoint Splitting**: Splits **must never leak prompts or topics** between train, validation, and test. If prompt $P_k$ is in the training split, all human and machine responses to $P_k$ are excluded from validation and test splits.

#### Evaluation Metrics:
- **Precision, Recall, F1-Score, ROC-AUC, PR-AUC**.
- **False Positive Rate (FPR)** and **False Negative Rate (FNR)** at fixed classification operating points.
- **Expected Calibration Error (ECE)**:
  $$\text{ECE} = \sum_{m=1}^{M} \frac{|B_m|}{N} |\text{acc}(B_m) - \text{conf}(B_m)|$$
- **Cross-Domain Evaluation**: Benchmark degradation across academic prose, creative fiction, technical documentation, and journalism.
- **Non-Native English Writer False Positive Audit**: Explicit evaluation on non-native English corpora (e.g., TOEFL essays). Detectors have a documented bias of misclassifying non-native English writing as machine-generated due to lower lexical entropy. The pipeline will track this specific subgroup FPR and tune calibration to suppress false positives on low-entropy human prose.

---

## 2. Module B: Writing Improver Architecture

### 2.1 Design & Ethical Boundaries
The Writing Improver is designed strictly for **clarity, conciseness, tone alignment, and readability**. It is explicitly **not** an "AI bypasser" or "stealth rewriter" designed to evade detection. The system enforces this by:
1. Rejecting adversarial prompts that instruct the engine to "bypass AI detectors" or "insert human mistakes."
2. Prioritizing clarity, syntactic coherence, and flow over perturbation.
3. Providing full transparency through an interactive change-diff interface.

---

### 2.2 Protected-Span Extraction Engine

Before passing text to the LLM, sensitive spans are extracted using deterministic regex and named-entity recognition (`spaCy`), replacing them with typed placeholder tokens:

```
Raw Text:
"In 2023, Dr. Alan Grant published report NASA-TR-409 stating that 42.8% of specimens in Area 51..."

Masked Text:
"In {{NUM_1}}, {{PERSON_1}} published report {{CODE_1}} stating that {{NUM_2}} of specimens in {{LOC_1}}..."
```

#### Protected Entity Categories:
- **Citations**: Standard formats (e.g., `(Smith et al., 2021)`, `[12]`, `doi:10.1038/...`).
- **Numbers & Percentages**: Integers, decimals, currency values (`$45.50`), ratios (`3:1`).
- **Equations & Math**: Inline and block LaTeX (`$E=mc^2$`).
- **URLs & Emails**: Web addresses, URIs, email handles.
- **Code & Identifiers**: Markdown backticks, programming syntax, standard reference codes.
- **Named Entities (Strict Mode)**: Organizations, people, locations.

---

### 2.3 Rewriting Modes & Prompt Engineering

The system supports six distinct operational modes:

| Mode | Objective | System Guidance Summary |
|---|---|---|
| **Natural / Conversational** | Fluidity, relaxed phrasing, accessible cadence | Soften overly dense clauses; adopt modern conversational rhythm without slang. |
| **Academic Clarity** | Rigor, logical cohesion, passive/active balance | Eliminate colloquialisms; enforce precise academic phrasing; maintain formal hedging. |
| **Professional** | Executive communication, action orientation | Clear business syntax; eliminate filler words; emphasize impact and actionability. |
| **Simple / Readable** | Maximum accessibility (Flesch-Kincaid ~ Grade 6-8) | Shorten sentences; replace complex jargon with clear everyday terminology. |
| **Concise** | Maximum information density | Eliminate redundancy, passive voice, and pleonasms; cut length by 20-35%. |
| **Formal** | Traditional dignity, diplomatic tone | Use elevated vocabulary, formal sentence constructions, and strict grammatical elegance. |

---

### 2.4 Hosted vs. Open-Weight Models for RTX 2050 Hardware

| Model Strategy | Feasibility on RTX 2050 (4GB VRAM) | Latency | Quality / Coherence | Cost Profile |
|---|---|---|---|---|
| **Local 7B / 8B (e.g., Llama-3-8B 4-bit)** | Marginal/Unstable. Fits in ~3.8 GB VRAM at 4-bit quant, but leaves zero headroom for context windows > 1024 tokens or sentence embeddings. | High (~10-15 tokens/sec). Prone to OOM on long documents. | Moderate to Good. | Free compute, but high risk of GPU crashes. |
| **Local 1B-3B (e.g., Llama-3.2-3B, Qwen2.5-3B)** | Runs smoothly in 4GB VRAM with 4-bit or 8-bit quantization. | Fast (~30 tokens/sec). | Weak on nuanced academic rewriting and strict placeholder adherence. | Free compute. |
| **Hosted API (Groq / OpenRouter / Anthropic)** (Selected) | Offloaded. Zero VRAM consumed. | Extremely Fast (Groq: 150-300 tps). | Superior. Full 70B+ parameter coherence and strict placeholder preservation. | Fraction of a cent per rewrite (e.g., $0.0005 per document on Groq/DeepSeek/Llama-3). |

---

## 3. Post-Rewrite Verification Layer

### 3.1 Verification Architecture
Meaning preservation cannot be mathematically guaranteed by any generative model. Therefore, BundCheck implements an automated **Verification Audit Engine** that evaluates the output prior to presenting it to the user.

```
                    ┌───────────────────────────────────┐
                    │  Original Text vs. Rewritten Text │
                    └─────────────────┬─────────────────┘
                                      │
         ┌────────────────────────────┼────────────────────────────┐
         ▼                            ▼                            ▼
┌───────────────────┐       ┌───────────────────┐       ┌───────────────────┐
│ Numeric Integrity │       │ Citation & Entity │       │ Structural &      │
│ Audit (Regex Diff)│       │ Audit (NER Diff)  │       │ Paragraph Check   │
└────────┬──────────┘       └────────┬──────────┘       └────────┬──────────┘
         │                           │                           │
         └───────────────────────────┼───────────────────────────┘
                                     │
         ┌───────────────────────────┴───────────────────────────┐
         ▼                                                       ▼
┌───────────────────────────────┐       ┌───────────────────────────────┐
│ Paragraph Semantic Similarity │       │ Natural Language Inference    │
│ (Sentence-Transformers cosine)│       │ Contradiction Check (NLI)     │
└──────────────┬────────────────┘       └──────────────┬────────────────┘
               │                                       │
               └───────────────────────┬───────────────┘
                                       ▼
                    ┌─────────────────────────────────────┐
                    │    Verification Report Evaluator    │
                    │   (Severity Classification)         │
                    └──────────────────┬──────────────────┘
                                       ▼
                    ┌─────────────────────────────────────┐
                    │   Passed / Needs Review / Warning   │
                    └─────────────────────────────────────┘
```

### 3.2 Audit Subsystems & Failure Thresholds

1. **Numeric Integrity Audit**:
   - Compares the multiset of numbers in the source vs. rewritten text.
   - Any missing, altered, or hallucinated numerical value triggers a `CRITICAL` severity warning.
2. **Citation & Reference Audit**:
   - Ensures all extracted citations from the source exist verbatim in the output.
   - Any dropped citation triggers a `CRITICAL` severity warning.
3. **Named Entity Audit**:
   - Runs `spaCy` NER over both texts. Evaluates precision and recall of original entities (people, organizations, locations). Missing entities trigger a `WARNING`.
4. **Structural / Paragraph Alignment**:
   - Compares original paragraph count to rewritten paragraph count. Mismatches trigger an `INFO` or `WARNING` flag.
5. **Semantic Embedding Similarity**:
   - Computes cosine similarity between source and target paragraphs using `all-MiniLM-L6-v2` or `bge-small-en-v1.5`.
   - Score $\ge 0.88$: Normal pass.
   - Score $0.75 - 0.88$: Flagged for `Needs Review`.
   - Score $< 0.75$: Marked `POTENTIAL_SEMANTIC_DRIFT` warning.
6. **Contradiction Detection via NLI (Optional/High-Sensitivity Mode)**:
   - Evaluates sentence pairs via a small local NLI model (e.g., `cross-encoder/nli-deberta-v3-small`).
   - If $P(\text{Contradiction}) > 0.25$, flags specific sentence pair with `CONTRADICTION_DETECTED`.

### 3.3 Verification Severity Output

Every rewrite response includes a `VerificationReport`:
```json
{
  "status": "NEEDS_REVIEW",
  "similarity_score": 0.84,
  "checks": {
    "numeric_integrity": {"passed": true, "missing_numbers": []},
    "citation_integrity": {"passed": true, "missing_citations": []},
    "entity_integrity": {"passed": false, "missing_entities": ["Dr. Alan Grant"]},
    "paragraph_alignment": {"passed": true, "source_count": 3, "target_count": 3},
    "contradiction_check": {"passed": true, "contradiction_probability": 0.04}
  },
  "flags": [
    {
      "severity": "WARNING",
      "code": "MISSING_ENTITY",
      "message": "Named entity 'Dr. Alan Grant' appears in the original text but was omitted or altered in the rewrite."
    }
  ]
}
```
