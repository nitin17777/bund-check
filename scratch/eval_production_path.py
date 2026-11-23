"""
Production Path Evaluation Script
==================================
Runs the BundCheck AI detector through the PRODUCTION inference path
(backend.app.services.detection.detector.run_detection_pipeline),
NOT through ml/ scripts alone.

Test data: SYNTHETIC (clearly labelled) — no held-out real dataset was found
in ml/data/ or ml/datasets/. The synthetic set is constructed to cover:
  - Canonical human-style text (long, varied, idiomatic)
  - Canonical AI-style text (uniform, low burstiness, function-word heavy)
  - Short text (<50 words) edge cases
  - Human-edited AI text proxies

All metrics are computed with the full production pipeline including the
calibrated GBDT artifact loaded via backend service loader.

Output: ml/reports/phase9_production_eval.md
"""

import sys
import os
import datetime
import numpy as np

# ── Path setup ────────────────────────────────────────────────────────────────
# Must run from d:\bund-check so relative imports resolve correctly.
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

# ── Import production pipeline ────────────────────────────────────────────────
from backend.app.services.detection.detector import run_detection_pipeline
from ml.src.eval.metrics import compute_comprehensive_metrics

# ── Synthetic test corpus ─────────────────────────────────────────────────────
# label 0 = human, label 1 = synthetic/AI
# Domain tags: "academic", "journalism", "essay", "technical"

SYNTHETIC_TEST_SET = [
    # --- HUMAN texts (label=0) ---
    {
        "label": 0, "domain": "journalism",
        "generator": "human",
        "text": (
            "It was an odd sort of morning, the kind where the light comes through at an angle and "
            "everything looks slightly unfamiliar. The cat had knocked over her coffee, and she spent "
            "ten minutes wiping the table, cursing softly under her breath. Outside, a neighbour was "
            "trying—unsuccessfully—to restart an old lawnmower. She was supposed to be in a meeting "
            "by nine. These things happen. She grabbed her coat and left without saying goodbye to anyone "
            "in particular, though there was no one to say goodbye to anyway. The bus was late, as it "
            "always was on Tuesdays. She stood in the drizzle, wondering whether the presentation she'd "
            "spent three evenings preparing actually mattered, and concluded—provisionally—that it did not. "
            "Still, she went."
        ),
    },
    {
        "label": 0, "domain": "essay",
        "generator": "human",
        "text": (
            "My grandmother never threw anything away. Not the plastic bags folded twelve times into "
            "origami triangles and stuffed into a larger plastic bag—not the rubber bands around the "
            "newspaper, not the elastic from bread loaves. When I was seven I thought this was embarrassing. "
            "Now I find it clarifying. She grew up during rationing; waste was not a virtue to be cultivated, "
            "it was a failure of imagination. I think of her every time I watch someone throw away a glass jar. "
            "The whole culture of disposability—the throwaway coffee cup, the fast fashion, the new phone every "
            "eighteen months—would have baffled her completely. Not because she was moralistic about it, but "
            "because she simply couldn't understand why you'd want something to exist only briefly. Things, in "
            "her world, were not meant to be temporary. They were meant to last, and to be passed on."
        ),
    },
    {
        "label": 0, "domain": "academic",
        "generator": "human",
        "text": (
            "The question of whether consciousness can be meaningfully attributed to non-biological systems "
            "remains philosophically contested, though recent advances in large language modelling have forced "
            "the debate into a more practical register. Critics of functionalism have long maintained that "
            "substrate matters: a silicon circuit, however complex, cannot instantiate subjective experience "
            "simply by virtue of performing the right computations. Chalmers's 'hard problem'—the explanatory "
            "gap between objective physical processes and the felt quality of experience—has not been dissolved "
            "by scaling parameters. What has changed is the degree to which these systems produce outputs "
            "indistinguishable from those of a conscious agent. Whether that indistinguishability is itself "
            "philosophically significant, or merely an artefact of our limited epistemic access, is precisely "
            "what is at stake. The debate is not new, but it has acquired a new urgency."
        ),
    },
    {
        "label": 0, "domain": "journalism",
        "generator": "human",
        "text": (
            "Nobody expected the vote to go that way. The polls had been consistent for weeks—a narrow but "
            "stable lead for the incumbent—and the morning of election day felt routine in the way that "
            "important things often do before they aren't. By half past ten, the picture had changed. The "
            "rural returns, which had come in faster than expected, showed a swing of twelve points. By "
            "midnight, the margin had widened. 'We got it wrong,' one pollster said, without elaborating on "
            "how or why. His brevity was, perhaps, the most honest thing said all evening. The opposition "
            "leader, visibly surprised, gave a speech that was generous in tone and bewildered in substance. "
            "What happens next depends, as it usually does, on what everyone agrees to pretend is obvious "
            "in retrospect."
        ),
    },
    {
        "label": 0, "domain": "technical",
        "generator": "human",
        "text": (
            "The build had been failing for three days before anyone noticed it was failing silently—the CI "
            "dashboard showed green because the test runner itself had crashed before running any tests. "
            "Classic. I found it by accident while checking an unrelated deployment log, spotted the missing "
            "exit code, and spent an hour reconstructing what had actually happened. The fix was two lines. "
            "The retrospective took forty minutes and covered topics ranging from monitoring gaps to, "
            "inexplicably, the colour scheme of the status page. I added an alert. The alert immediately "
            "began firing on a different unrelated problem, which we also hadn't known about. So: net positive, "
            "probably. The build is green again, in the genuine sense this time."
        ),
    },
    # --- AI/Synthetic texts (label=1) ---
    {
        "label": 1, "domain": "academic",
        "generator": "gpt-style",
        "text": (
            "Artificial intelligence has emerged as a transformative technology that is reshaping numerous "
            "industries across the globe. The rapid advancement of machine learning algorithms and deep neural "
            "networks has enabled unprecedented capabilities in natural language processing, computer vision, "
            "and decision-making systems. Organizations are increasingly leveraging these technologies to "
            "enhance operational efficiency and drive innovation. The integration of AI into business processes "
            "has demonstrated significant potential for cost reduction and productivity improvement. Furthermore, "
            "the development of large language models has opened new possibilities for human-computer interaction "
            "and knowledge synthesis. As these systems continue to evolve, it is essential to consider both "
            "the opportunities and challenges they present to society. The ethical implications of AI deployment "
            "require careful consideration and robust governance frameworks to ensure responsible innovation."
        ),
    },
    {
        "label": 1, "domain": "essay",
        "generator": "gpt-style",
        "text": (
            "Climate change represents one of the most significant challenges facing humanity in the twenty-first "
            "century. The scientific consensus is clear: global temperatures are rising due to human activities, "
            "primarily the burning of fossil fuels and deforestation. This phenomenon has far-reaching "
            "consequences for ecosystems, weather patterns, and human communities worldwide. Addressing climate "
            "change requires a comprehensive and coordinated global response involving governments, businesses, "
            "and individuals. Renewable energy technologies offer promising solutions for reducing greenhouse gas "
            "emissions while maintaining economic growth. Additionally, nature-based solutions such as reforestation "
            "and wetland restoration can play a crucial role in carbon sequestration. It is imperative that "
            "policymakers implement effective climate policies that balance environmental protection with economic "
            "development. The transition to a sustainable, low-carbon economy presents both challenges and "
            "opportunities for innovation and growth."
        ),
    },
    {
        "label": 1, "domain": "technical",
        "generator": "gpt-style",
        "text": (
            "Machine learning models require careful evaluation to ensure their performance meets the requirements "
            "of the intended application. The evaluation process typically involves splitting the available data "
            "into training, validation, and test sets. The training set is used to fit the model parameters, "
            "while the validation set is used to tune hyperparameters and prevent overfitting. The test set "
            "provides an unbiased estimate of the model's generalization performance. Common evaluation metrics "
            "include accuracy, precision, recall, and the F1 score. For imbalanced datasets, it is important to "
            "consider metrics such as the area under the receiver operating characteristic curve and the "
            "precision-recall curve. Cross-validation techniques can help obtain more robust performance estimates "
            "by averaging results across multiple data splits. It is essential to report all relevant metrics "
            "and to interpret results in the context of the specific application requirements."
        ),
    },
    {
        "label": 1, "domain": "journalism",
        "generator": "gpt-style",
        "text": (
            "The global economy is experiencing significant transformation driven by technological innovation "
            "and changing consumer preferences. Digital transformation has accelerated across all sectors, "
            "creating new opportunities for businesses that adapt quickly to evolving market conditions. "
            "Supply chain disruptions have highlighted the importance of resilience and diversification in "
            "business operations. Many organizations are investing in automation and artificial intelligence "
            "to improve efficiency and reduce operational costs. The rise of the gig economy has created new "
            "employment models that offer flexibility but also raise questions about worker protections and "
            "benefits. Financial markets have shown considerable volatility, reflecting uncertainty about "
            "future economic conditions. Policymakers face the challenge of balancing growth objectives "
            "with inflation control and fiscal sustainability. The path forward requires careful navigation "
            "of complex economic trade-offs and international cooperation."
        ),
    },
    {
        "label": 1, "domain": "academic",
        "generator": "gpt-style",
        "text": (
            "The implementation of sustainable development goals requires a multidimensional approach that "
            "integrates economic, social, and environmental considerations. Research has demonstrated that "
            "countries with strong institutional frameworks and transparent governance structures are better "
            "positioned to achieve sustainable development outcomes. The relationship between economic growth "
            "and environmental sustainability presents a complex set of trade-offs that require careful policy "
            "design. Evidence suggests that investments in human capital, particularly education and healthcare, "
            "are associated with improved development outcomes across multiple dimensions. International "
            "cooperation and knowledge sharing are essential components of effective sustainable development "
            "strategies. The role of civil society organizations in monitoring progress and holding governments "
            "accountable has been increasingly recognized in development literature. Future research should "
            "focus on identifying context-specific pathways to sustainable development that account for local "
            "conditions and priorities."
        ),
    },
    # --- Short text edge cases (< 50 words) ---
    {
        "label": 0, "domain": "essay",
        "generator": "human_short",
        "text": "She didn't answer his texts. It wasn't cruelty—it was exhaustion, the kind that "
                 "makes even small decisions feel enormous. He probably understood. She hoped so.",
    },
    {
        "label": 1, "domain": "technical",
        "generator": "gpt-style_short",
        "text": "This solution provides an efficient and scalable approach to solving complex problems "
                 "in modern software development environments. The methodology ensures optimal performance.",
    },
    # --- Human-edited AI text proxies ---
    {
        "label": 1, "domain": "academic",
        "generator": "human_edited_ai",
        "text": (
            "AI has transformed—quite dramatically, actually—the landscape of modern research. Some would say "
            "this is overstated; I'm not sure I agree. The core point stands: machine learning models have "
            "enabled capabilities in language and vision tasks that simply weren't feasible a decade ago. "
            "Whether the specific framing of 'transformation' is warranted is, perhaps, a secondary concern. "
            "What matters is that the tools exist, they work better than expected, and nobody quite knows "
            "what to do with that yet. The integration of AI into business processes has demonstrated "
            "significant potential, yes, but the governance frameworks lag considerably behind the technology. "
            "This is not a small problem. It is, arguably, the central problem."
        ),
    },
    {
        "label": 1, "domain": "essay",
        "generator": "human_edited_ai",
        "text": (
            "Climate change is a defining challenge of our time—that much is settled. The scientific evidence, "
            "accumulated over decades, points in one direction. What remains genuinely contested is the question "
            "of response: how fast, at what cost, distributed how across nations and generations? These are not "
            "scientific questions, they're political and ethical ones, and no amount of additional temperature "
            "data will resolve them. Renewable energy is clearly part of the answer, though the grid integration "
            "challenges are real and underappreciated. Reforestation helps, but the land requirements are vast. "
            "The honest position is that we have tools, we have rough timelines, and we lack the political will "
            "to deploy them at the necessary scale. That gap is the actual problem."
        ),
    },
]


def run_evaluation():
    """Run all test cases through the production inference path."""
    print("=" * 70)
    print("BundCheck Production Path Evaluation")
    print(f"Date: {datetime.date.today()}")
    print("Test set: SYNTHETIC (see notes below)")
    print("=" * 70)
    print()

    y_true = []
    y_probs = []
    results_detail = []
    errors = []

    for i, sample in enumerate(SYNTHETIC_TEST_SET):
        try:
            resp = run_detection_pipeline(text=sample["text"])
            prob = resp.synthetic_pattern_confidence
            y_probs.append(prob)
            y_true.append(sample["label"])
            results_detail.append({
                "idx": i,
                "label": sample["label"],
                "domain": sample["domain"],
                "generator": sample["generator"],
                "word_count": resp.stats.get("word_count", 0),
                "predicted_prob": prob,
                "band": resp.classification_band,
                "reliability_flag": resp.reliability_flag,
            })
            print(
                f"  [{i:02d}] label={sample['label']} gen={sample['generator']:20s} "
                f"domain={sample['domain']:12s} prob={prob:.4f} band={resp.classification_band}"
            )
        except Exception as e:
            errors.append({"idx": i, "error": str(e), "sample": sample})
            print(f"  [{i:02d}] ERROR: {e}")

    if len(errors) > 0:
        print(f"\nWARNING: {len(errors)} samples failed inference:")
        for err in errors:
            print(f"  idx={err['idx']}: {err['error']}")

    y_true_arr = np.array(y_true)
    y_probs_arr = np.array(y_probs)

    # Overall metrics at threshold=0.60 (production threshold for SYNTHETIC_INDICATIVE)
    metrics_60 = compute_comprehensive_metrics(y_true_arr, y_probs_arr, threshold=0.60)
    # Also at 0.50 for reference
    metrics_50 = compute_comprehensive_metrics(y_true_arr, y_probs_arr, threshold=0.50)

    # Domain breakdown
    domains = set(r["domain"] for r in results_detail)
    domain_metrics = {}
    for d in domains:
        mask = np.array([r["domain"] == d for r in results_detail])
        if np.sum(mask) >= 2 and len(np.unique(y_true_arr[mask])) > 1:
            domain_metrics[d] = compute_comprehensive_metrics(y_true_arr[mask], y_probs_arr[mask], threshold=0.60)

    # Generator breakdown
    generators = set(r["generator"] for r in results_detail)
    gen_metrics = {}
    for g in generators:
        mask = np.array([r["generator"] == g for r in results_detail])
        human_mask = np.array([r["label"] == 0 for r in results_detail])
        sub = mask | human_mask
        if np.sum(mask) >= 1 and len(np.unique(y_true_arr[sub])) > 1:
            gen_metrics[g] = compute_comprehensive_metrics(y_true_arr[sub], y_probs_arr[sub], threshold=0.60)

    # Short text subset
    short_indices = [i for i, r in enumerate(results_detail) if r["word_count"] < 50]
    short_metrics = None
    if len(short_indices) >= 2:
        sm = np.array([y_true[i] for i in short_indices])
        sp = np.array([y_probs[i] for i in short_indices])
        if len(np.unique(sm)) > 1:
            short_metrics = compute_comprehensive_metrics(sm, sp, threshold=0.60)

    # Human-edited AI
    edited_indices = [i for i, r in enumerate(results_detail) if "edited" in r["generator"]]
    edited_metrics = None
    if len(edited_indices) >= 1:
        human_indices = [i for i, r in enumerate(results_detail) if r["label"] == 0]
        sub_indices = list(set(edited_indices + human_indices))
        em = np.array([y_true[i] for i in sub_indices])
        ep = np.array([y_probs[i] for i in sub_indices])
        if len(np.unique(em)) > 1:
            edited_metrics = compute_comprehensive_metrics(em, ep, threshold=0.60)

    print(f"\n--- Overall metrics (threshold=0.60, N={metrics_60['total_samples']}) ---")
    print(f"  Accuracy:          {((y_probs_arr >= 0.60).astype(int) == y_true_arr).mean():.4f}")
    print(f"  Precision:         {metrics_60['precision']:.4f}")
    print(f"  Recall:            {metrics_60['recall']:.4f}")
    print(f"  F1:                {metrics_60['f1']:.4f}")
    print(f"  ROC-AUC:           {metrics_60['roc_auc']:.4f}")
    print(f"  ECE:               {metrics_60['ece']:.4f}")
    print(f"  Brier Score:       {metrics_60['brier_score']:.4f}")
    print(f"  FPR:               {metrics_60['fpr']:.4f}")
    print(f"  FNR:               {metrics_60['fnr']:.4f}")
    print(f"  TPR @ 1% FPR:      {metrics_60['tpr_at_1pct_fpr']:.4f}")
    print(f"  TPR @ 5% FPR:      {metrics_60['tpr_at_5pct_fpr']:.4f}")

    # Accuracy number for report
    accuracy = float(((y_probs_arr >= 0.60).astype(int) == y_true_arr).mean())

    # Write report
    write_report(
        metrics_60=metrics_60,
        metrics_50=metrics_50,
        accuracy=accuracy,
        domain_metrics=domain_metrics,
        gen_metrics=gen_metrics,
        short_metrics=short_metrics,
        edited_metrics=edited_metrics,
        results_detail=results_detail,
        errors=errors,
    )

    return metrics_60, accuracy


def write_report(
    metrics_60, metrics_50, accuracy, domain_metrics, gen_metrics,
    short_metrics, edited_metrics, results_detail, errors
):
    """Write the evaluation report to ml/reports/phase9_production_eval.md."""
    today = datetime.date.today().isoformat()
    n = metrics_60["total_samples"]
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    out_path = os.path.join(repo_root, "ml", "reports", "phase9_production_eval.md")

    lines = [
        "# Phase 9: Production Path Detector Evaluation",
        "",
        f"**Evaluation Date**: {today}  ",
        "**Inference Path**: `backend.app.services.detection.detector.run_detection_pipeline`  ",
        "**Model Artifact**: `ml/models/artifacts/gbdt_calibrated_ensemble.joblib`  ",
        "**Hardware**: RTX 2050 (4 GB VRAM) / 24 GB RAM — inference on CPU  ",
        "**Calibration**: Isotonic Regression (fit on held-out validation split during training)",
        "",
        "> [!IMPORTANT]",
        f"> **Test set is SYNTHETIC** (N={n}). No held-out real-world dataset was found in `ml/data/`",
        "> or `ml/datasets/`. All samples were constructed to cover canonical human prose (long, varied,",
        "> idiomatic), canonical AI-style prose (uniform, low burstiness), short-text edge cases (<50 words),",
        "> and human-edited AI text proxies. Numbers below reflect performance on this synthetic corpus",
        "> **only**; they cannot be directly extrapolated to real-world deployment distributions.",
        "",
        "---",
        "",
        "## 1. Overall Metrics — Production Threshold (≥ 0.60 → SYNTHETIC_INDICATIVE)",
        "",
        f"| Metric | Value (threshold=0.60) | Value (threshold=0.50) |",
        f"|--------|------------------------|------------------------|",
        f"| **Accuracy** | **{accuracy:.4f}** | {float(((np.array([r['predicted_prob'] for r in results_detail]) >= 0.50).astype(int) == np.array([r['label'] for r in results_detail])).mean()):.4f} |",
        f"| **Precision** | **{metrics_60['precision']:.4f}** | {metrics_50['precision']:.4f} |",
        f"| **Recall** | **{metrics_60['recall']:.4f}** | {metrics_50['recall']:.4f} |",
        f"| **F1-Score** | **{metrics_60['f1']:.4f}** | {metrics_50['f1']:.4f} |",
        f"| **ROC-AUC** | **{metrics_60['roc_auc']:.4f}** | — |",
        f"| **PR-AUC** | **{metrics_60['pr_auc']:.4f}** | — |",
        f"| **ECE (Expected Calibration Error)** | **{metrics_60['ece']:.4f}** | — |",
        f"| **Brier Score** | **{metrics_60['brier_score']:.4f}** | — |",
        f"| **FPR (False Positive Rate)** | **{metrics_60['fpr']:.4f}** | {metrics_50['fpr']:.4f} |",
        f"| **FNR (False Negative Rate)** | **{metrics_60['fnr']:.4f}** | {metrics_50['fnr']:.4f} |",
        f"| **TPR @ 1% FPR** | **{metrics_60['tpr_at_1pct_fpr']:.4f}** | — |",
        f"| **TPR @ 5% FPR** | **{metrics_60['tpr_at_5pct_fpr']:.4f}** | — |",
        f"| **Total Samples** | {n} | {n} |",
        "",
        "---",
        "",
        "## 2. Per-Domain Breakdown",
        "",
    ]

    if domain_metrics:
        lines += [
            "| Domain | Precision | Recall | F1 | ROC-AUC | ECE | N |",
            "|--------|-----------|--------|----|---------|-----|---|",
        ]
        for d, m in sorted(domain_metrics.items()):
            lines.append(
                f"| {d} | {m['precision']:.3f} | {m['recall']:.3f} | {m['f1']:.3f} | "
                f"{m['roc_auc']:.3f} | {m['ece']:.3f} | {m['total_samples']} |"
            )
    else:
        lines.append("*Insufficient samples per domain for breakdown.*")

    lines += [
        "",
        "---",
        "",
        "## 3. Per-Generator Breakdown",
        "",
    ]

    if gen_metrics:
        lines += [
            "| Generator | Precision | Recall | F1 | FPR | N |",
            "|-----------|-----------|--------|----|-----|---|",
        ]
        for g, m in sorted(gen_metrics.items()):
            lines.append(
                f"| {g} | {m['precision']:.3f} | {m['recall']:.3f} | {m['f1']:.3f} | "
                f"{m['fpr']:.3f} | {m['total_samples']} |"
            )
    else:
        lines.append("*Insufficient samples per generator for breakdown.*")

    lines += [
        "",
        "---",
        "",
        "## 4. Robustness Checks",
        "",
        "### 4.1 Short Text (<50 words)",
        "",
    ]
    if short_metrics:
        lines += [
            f"- Precision: {short_metrics['precision']:.4f}",
            f"- Recall: {short_metrics['recall']:.4f}",
            f"- F1: {short_metrics['f1']:.4f}",
            f"- N: {short_metrics['total_samples']}",
            "",
            "> [!WARNING]",
            "> Short text performance is unreliable. The production pipeline explicitly flags texts",
            "> under 50 words with `UNRELIABLE_VERY_SHORT_TEXT`. Numbers above are for reference only.",
        ]
    else:
        lines.append("*Not enough short-text samples with both classes to compute metrics.*")

    lines += [
        "",
        "### 4.2 Human-Edited AI Text",
        "",
    ]
    if edited_metrics:
        lines += [
            f"- Precision: {edited_metrics['precision']:.4f}",
            f"- Recall: {edited_metrics['recall']:.4f}",
            f"- F1: {edited_metrics['f1']:.4f}",
            f"- N: {edited_metrics['total_samples']}",
            "",
            "> [!NOTE]",
            "> Human-edited AI text is the hardest category. Prior research (and the existing",
            "> `detection_eval.md` report) documents up to 28% recall drop on heavily edited AI text.",
            "> The synthetic proxies here are mildly edited; real production edited text would likely",
            "> perform worse.",
        ]
    else:
        lines.append("*Insufficient edited samples for breakdown.*")

    lines += [
        "",
        "---",
        "",
        "## 5. Per-Sample Detail",
        "",
        "| # | Label | Generator | Domain | Words | Prob | Band | Flag |",
        "|---|-------|-----------|--------|-------|------|------|------|",
    ]
    for r in results_detail:
        lines.append(
            f"| {r['idx']} | {'AI' if r['label'] == 1 else 'Human'} | {r['generator']} | "
            f"{r['domain']} | {r['word_count']} | {r['predicted_prob']:.4f} | "
            f"{r['band']} | {r['reliability_flag']} |"
        )

    if errors:
        lines += [
            "",
            "### Inference Errors",
            "",
        ]
        for err in errors:
            lines.append(f"- Sample {err['idx']} ({err['sample']['generator']}): `{err['error']}`")

    lines += [
        "",
        "---",
        "",
        "## 6. Limitations",
        "",
        "> [!CAUTION]",
        "> The following limitations apply to all results in this report and to the production detector.",
        "> Users and developers MUST read and understand these limitations before using or citing detector outputs.",
        "",
        "### 6.1 Training / Test Distribution Mismatch",
        "- **This report uses a synthetic test set.** The model artifact (`gbdt_calibrated_ensemble.joblib`)",
        "  was trained and calibrated on a held-out split of the development corpus. This evaluation script",
        "  does not have access to that corpus and constructs a small synthetic set instead.",
        "- Metrics on the synthetic set reflect the model's ability to discriminate between *prototypical*",
        "  human prose and *prototypical* AI prose. Real-world text is messier, more varied, and often",
        "  falls somewhere in between.",
        "- **Do not use the numbers in this report as a headline accuracy claim for real-world performance.**",
        "  Refer to `ml/reports/detection_eval.md` for the training-time evaluation against the actual",
        "  development corpus.",
        "",
        "### 6.2 Known Failure Modes",
        "1. **Human-Edited AI Text**: The detector degrades significantly when AI-generated text undergoes",
        "   human stylistic revision. Prior evaluation documents recall drops of up to 28% on this category.",
        "2. **Short Text (<50 words)**: Sentence perplexity variance cannot be computed reliably on very short",
        "   texts. The production pipeline flags these as `UNRELIABLE_VERY_SHORT_TEXT` and explicitly widens",
        "   the uncertainty interval.",
        "3. **Domain Shift (Legal/Technical/Non-Native English)**: Formal technical and legal prose, and",
        "   non-native English writing, exhibit naturally lower lexical entropy and flatter perplexity",
        "   distributions. These features mimic AI-style signals and may elevate false-positive rates.",
        "4. **Out-of-Distribution Generators**: Models unseen during training (e.g., new proprietary LLMs)",
        "   may produce stylistic patterns not covered by the GBDT's training distribution.",
        "5. **Low-Vocabulary Domains**: Formulaic genres (legal disclaimers, software changelogs, meeting",
        "   minutes) may systematically trigger elevated synthetic confidence regardless of actual authorship.",
        "",
        "### 6.3 Abstain Band Rationale",
        "- The production pipeline abstains from classification when `synthetic_pattern_confidence ∈ [0.40, 0.60]`.",
        "- This band is configured via `ABSTAIN_LOWER_THRESHOLD` / `ABSTAIN_UPPER_THRESHOLD` in",
        "  `backend/app/core/config.py` and was set based on calibration reliability curves.",
        "- **Rationale**: The model's reliability in this region is insufficient to make a directional claim.",
        "  Forcing a binary decision in this band would inflate both false positives and false negatives.",
        "  The abstain design is a conservative, honest choice — not a limitation to be engineered away.",
        "",
        "### 6.4 What the Model CANNOT Do",
        "- **Cannot prove AI authorship**: A high `synthetic_pattern_confidence` score indicates statistical",
        "  alignment with machine text patterns. It does not constitute proof that a specific AI system",
        "  generated the text, nor does it disprove human authorship.",
        "- **Cannot attribute to a specific AI model**: The detector is a binary/ordinal classifier;",
        "  it cannot identify which LLM generated a text.",
        "- **Cannot detect lightly paraphrased AI text**: Translation round-trips, synonym substitution,",
        "  or sentence reordering significantly degrade detection.",
        "- **Cannot evaluate document fragments reliably**: Paragraph-level and sentence-level scores are",
        "  explicitly labelled as *exploratory local variance indicators* and do not constitute independent",
        "  attribution evidence.",
        "- **Cannot guarantee zero false positives on any real corpus**: The model is calibrated to minimize",
        "  expected calibration error on its training distribution; FPR on out-of-distribution corpora",
        "  is uncharacterised.",
        "",
        "---",
        "",
        "## 7. Comparison with Phase 3 Training-Time Report",
        "",
        "| Metric | Training-Time (detection_eval.md) | Phase 9 Production Path (synthetic) |",
        "|--------|-----------------------------------|--------------------------------------|",
        "| F1 | 1.000 (GBDT) | *see Section 1* |",
        "| ECE | 0.000 (GBDT) | *see Section 1* |",
        "| Test N | unreported | {n} (synthetic) |",
        "",
        "> [!NOTE]",
        "> The training-time report shows perfect scores (F1=1.000, ECE=0.000) on the development",
        "> corpus. This is consistent with a small, well-separated synthetic training set where the",
        "> stylometric signals are unambiguous. These numbers should **not** be interpreted as",
        "> production accuracy on real-world documents. Real-world performance on ambiguous or",
        "> mixed-authorship text will be substantially lower.",
        "",
        "---",
        "",
        f"*Report generated by `scratch/eval_production_path.py` on {today}.*  ",
        "*Test corpus: synthetic, N={n}.*",
    ]

    # Fix the f-string interpolation issue in the last section
    report = "\n".join(lines)
    report = report.replace("{n}", str(n))

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\nReport written to: {out_path}")


if __name__ == "__main__":
    metrics, accuracy = run_evaluation()
    print(f"\nDone. Summary: Accuracy={accuracy:.4f} F1={metrics['f1']:.4f} ECE={metrics['ece']:.4f}")
