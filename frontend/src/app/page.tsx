import Link from "next/link";
import {
  ShieldCheck,
  FileCheck2,
  AlertTriangle,
  ArrowRight,
  SlidersHorizontal,
  Lock,
  Cpu,
  Layers,
  FileText,
} from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background text-text-primary selection:bg-accent/30 selection:text-text-primary">
      {/* Top Navigation */}
      <header className="sticky top-0 z-40 border-b border-border-subtle bg-surface-base/90 backdrop-blur-md">
        <div className="max-w-7xl mx-auto flex items-center justify-between h-16 px-4 sm:px-6 md:px-8">
          <Link
            href="/"
            className="flex items-center gap-2.5 font-bold tracking-tight text-text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent rounded"
          >
            <div className="rounded bg-accent p-1.5 text-white">
              <ShieldCheck className="h-4 w-4" />
            </div>
            <span className="text-lg">BundCheck</span>
          </Link>

          <nav className="hidden md:flex items-center gap-6 text-sm" aria-label="Main navigation">
            <Link
              href="/checker"
              className="text-text-secondary hover:text-text-primary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent rounded px-1"
            >
              Checker
            </Link>
            <Link
              href="/humanizer"
              className="text-text-secondary hover:text-text-primary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent rounded px-1"
            >
              Writing Improver
            </Link>
            <Link
              href="/dashboard"
              className="text-text-secondary hover:text-text-primary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent rounded px-1"
            >
              Dashboard
            </Link>
            <a
              href="#methodology"
              className="text-text-secondary hover:text-text-primary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent rounded px-1"
            >
              Methodology
            </a>
          </nav>

          <div className="flex items-center gap-3">
            <Link
              href="/checker"
              className="inline-flex items-center justify-center h-9 px-4 text-xs font-semibold rounded bg-accent text-white hover:bg-accent-hover transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            >
              Launch App
            </Link>
          </div>
        </div>
      </header>

      <main id="main-content" className="max-w-7xl mx-auto px-4 sm:px-6 md:px-8 py-12 md:py-20 space-y-20">
        {/* Hero Section */}
        <section className="text-center space-y-6 max-w-3xl mx-auto pt-4 md:pt-8" aria-labelledby="hero-heading">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-border-subtle bg-surface-card text-xs text-text-secondary">
            <Badge variant="outline" className="text-[10px] tracking-wider uppercase font-mono px-1.5 py-0">
              Honest Architecture
            </Badge>
            <span>Probabilistic inspection with deterministic verification</span>
          </div>

          <h1
            id="hero-heading"
            className="text-3xl sm:text-4xl md:text-5xl font-bold tracking-tight text-text-primary leading-tight"
          >
            Probabilistic content inspection and precision writing quality.
          </h1>

          <p className="text-base sm:text-lg text-text-secondary leading-relaxed max-w-2xl mx-auto">
            Engineered for researchers, editors, and educators who require principled statistical methodology over
            exaggerated claims. Understand distributional patterns and improve prose clarity without compromising
            factual integrity.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
            <Link
              href="/checker"
              className="w-full sm:w-auto inline-flex items-center justify-center h-11 px-6 text-sm font-semibold rounded bg-accent text-white hover:bg-accent-hover transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent shadow-sm gap-2"
            >
              <span>Inspect Content</span>
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="/humanizer"
              className="w-full sm:w-auto inline-flex items-center justify-center h-11 px-6 text-sm font-medium rounded border border-border bg-surface-card text-text-primary hover:bg-surface-overlay transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            >
              Improve Writing Quality
            </Link>
          </div>
        </section>

        {/* Mandatory Honest Scientific Disclosure */}
        <section aria-label="Scientific Limitations Disclosure">
          <div className="rounded-lg border border-semantic-warning/30 bg-semantic-warning-subtle/40 p-6 md:p-8 space-y-3">
            <div className="flex items-center gap-2.5 text-semantic-warning font-semibold text-sm sm:text-base">
              <AlertTriangle className="h-5 w-5 flex-shrink-0" />
              <h2>Scientific Premise & Limitations Statement</h2>
            </div>
            <p className="text-sm text-text-secondary leading-relaxed">
              Detection of synthetic text is inherently probabilistic and does not constitute proof of authorship.
              Language models and human writers share overlapping statistical traits across domains and technical
              terminologies. BundCheck provides calibrated distributional signals to assist human evaluation; it
              deliberately abstains on ambiguous inputs and must never be employed as unilateral proof or automated
              disciplinary evidence.
            </p>
            <p className="text-xs text-text-muted leading-relaxed">
              Similarly, the writing improvement pipeline is constructed to optimize readability, tone, and
              structure. It is not designed to deceive detection systems or produce synthetic artifacts.
            </p>
          </div>
        </section>

        {/* Core Pillars Grid */}
        <section className="space-y-8" aria-labelledby="pillars-heading" id="methodology">
          <div className="text-center space-y-2 max-w-2xl mx-auto">
            <h2 id="pillars-heading" className="text-2xl sm:text-3xl font-bold tracking-tight text-text-primary">
              Core Architectural Pillars
            </h2>
            <p className="text-sm text-text-secondary">
              A transparent engineering separation between statistical evaluation and deterministic semantic safeguards.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Pillar 1 */}
            <Card className="flex flex-col justify-between">
              <CardHeader>
                <div className="rounded bg-surface-overlay p-2.5 w-fit border border-border-subtle mb-3 text-accent">
                  <SlidersHorizontal className="h-5 w-5" />
                </div>
                <CardTitle>Multi-Signal Calibration</CardTitle>
                <CardDescription>
                  Replaces brittle single-model classifiers with ensemble evaluation: token-level perplexity,
                  sentence-level burstiness, and stylometric features with explicit abstain thresholds.
                </CardDescription>
              </CardHeader>
              <CardContent className="text-xs text-text-muted border-t border-border-subtle pt-4">
                Calibration prevents overconfidence; ambiguous inputs return an inconclusive status rather than an
                unreliable verdict.
              </CardContent>
            </Card>

            {/* Pillar 2 */}
            <Card className="flex flex-col justify-between">
              <CardHeader>
                <div className="rounded bg-surface-overlay p-2.5 w-fit border border-border-subtle mb-3 text-semantic-info">
                  <FileCheck2 className="h-5 w-5" />
                </div>
                <CardTitle>Deterministic Verification</CardTitle>
                <CardDescription>
                  Every editorial revision undergoes automated audits: numerical preservation, citation set diffing,
                  named entity stability, paragraph alignment, and negation polarity checks.
                </CardDescription>
              </CardHeader>
              <CardContent className="text-xs text-text-muted border-t border-border-subtle pt-4">
                Guarantees that numbers, citations, and critical technical terminology are never dropped or silently
                mutated during rewriting.
              </CardContent>
            </Card>

            {/* Pillar 3 */}
            <Card className="flex flex-col justify-between">
              <CardHeader>
                <div className="rounded bg-surface-overlay p-2.5 w-fit border border-border-subtle mb-3 text-semantic-success">
                  <Lock className="h-5 w-5" />
                </div>
                <CardTitle>Zero-Retention Privacy</CardTitle>
                <CardDescription>
                  Documents are parsed strictly in memory or transient sandboxes and removed immediately after
                  processing. No user text is persisted to disk or databases without opt-in archival.
                </CardDescription>
              </CardHeader>
              <CardContent className="text-xs text-text-muted border-t border-border-subtle pt-4">
                Suitable for confidential manuscripts, proprietary research drafts, and student submissions.
              </CardContent>
            </Card>
          </div>
        </section>

        {/* Technical Implementation Specifications */}
        <section className="space-y-6 rounded-lg border border-border-subtle bg-surface-card/60 p-6 sm:p-8" aria-labelledby="specs-heading">
          <div className="space-y-1">
            <h2 id="specs-heading" className="text-xl font-bold text-text-primary">
              System Specifications & Operational Boundaries
            </h2>
            <p className="text-xs text-text-secondary">
              Strict resource bounding and reproducible scientific architecture.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-2">
            <div className="rounded border border-border-subtle bg-surface-base p-4 space-y-2">
              <div className="flex items-center gap-2 text-text-primary text-xs font-semibold">
                <Cpu className="h-4 w-4 text-accent" />
                <span>Bounded Hardware</span>
              </div>
              <p className="text-xs text-text-muted leading-relaxed">
                Local feature extractors and sentence transformers operate strictly within consumer hardware ceilings.
              </p>
            </div>

            <div className="rounded border border-border-subtle bg-surface-base p-4 space-y-2">
              <div className="flex items-center gap-2 text-text-primary text-xs font-semibold">
                <FileText className="h-4 w-4 text-semantic-info" />
                <span>Format Support</span>
              </div>
              <p className="text-xs text-text-muted leading-relaxed">
                Safe ingestion for PDF, DOCX, and plain text with zip-bomb guards, signature checks, and encoding detection.
              </p>
            </div>

            <div className="rounded border border-border-subtle bg-surface-base p-4 space-y-2">
              <div className="flex items-center gap-2 text-text-primary text-xs font-semibold">
                <Layers className="h-4 w-4 text-semantic-warning" />
                <span>Editorial Modes</span>
              </div>
              <p className="text-xs text-text-muted leading-relaxed">
                Six dedicated clarity styles: academic clarity, natural, professional, simple readable, concise, and formal.
              </p>
            </div>

            <div className="rounded border border-border-subtle bg-surface-base p-4 space-y-2">
              <div className="flex items-center gap-2 text-text-primary text-xs font-semibold">
                <ShieldCheck className="h-4 w-4 text-semantic-success" />
                <span>Audit Reporting</span>
              </div>
              <p className="text-xs text-text-muted leading-relaxed">
                Downloadable reports containing full methodology disclosures, confidence intervals, and model version stamps.
              </p>
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="border-t border-border-subtle pt-8 text-xs text-text-muted flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-accent" />
            <span className="font-semibold text-text-secondary">BundCheck</span>
            <span>— Open-Standard Content Verification</span>
          </div>

          <div className="flex items-center gap-6">
            <Link href="/checker" className="hover:text-text-primary transition-colors">
              Checker
            </Link>
            <Link href="/humanizer" className="hover:text-text-primary transition-colors">
              Improver
            </Link>
            <Link href="/settings" className="hover:text-text-primary transition-colors">
              Settings
            </Link>
          </div>
        </footer>
      </main>
    </div>
  );
}
