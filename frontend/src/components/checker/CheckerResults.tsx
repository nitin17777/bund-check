"use client";

import * as React from "react";
import {
  CheckResponse,
  apiClient,
} from "@/lib/api-client";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { SentenceHeatmap } from "@/components/checker/SentenceHeatmap";
import {
  AlertTriangle,
  Download,
  RotateCcw,
  ShieldAlert,
  Info,
  CheckCircle2,
  Sliders,
  FileCode,
  FileText,
} from "lucide-react";
import { useToast } from "@/components/ui/Toast";

interface CheckerResultsProps {
  result: CheckResponse;
  onReset: () => void;
}

export function CheckerResults({ result, onReset }: CheckerResultsProps) {
  const { toast } = useToast();
  const [downloadingFormat, setDownloadingFormat] = React.useState<string | null>(null);

  // Label badge styling matching API wording exactly
  const getLabelBadge = () => {
    const label = result.label;
    if (label === "likely AI-leaning") {
      return (
        <Badge variant="critical" className="text-xs px-3 py-1 font-semibold tracking-wide">
          Likely AI-leaning
        </Badge>
      );
    }
    if (label === "inconclusive") {
      return (
        <Badge variant="warning" className="text-xs px-3 py-1 font-semibold tracking-wide">
          Inconclusive (Abstain Band)
        </Badge>
      );
    }
    return (
      <Badge variant="success" className="text-xs px-3 py-1 font-semibold tracking-wide">
        Likely human-leaning
      </Badge>
    );
  };

  const handleDownloadReport = async (format: "json" | "html" | "pdf") => {
    try {
      setDownloadingFormat(format);
      const { blob, filename } = await apiClient.exportReport({
        check_response: result,
        format,
        title: "BundCheck Content Analysis Report",
      });

      // Browser download trigger
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast({
        type: "success",
        title: "Report Downloaded",
        description: `Exported ${filename} successfully.`,
      });
    } catch (err: unknown) {
      toast({
        type: "critical",
        title: "Export Failed",
        description: err instanceof Error ? err.message : "Could not export report.",
      });
    } finally {
      setDownloadingFormat(null);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in-0 duration-200">
      {/* Top Banner: Score, Uncertainty & Actions */}
      <Card className="border-border">
        <CardContent className="p-6">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
            <div className="space-y-2">
              <div className="flex flex-wrap items-center gap-2.5">
                {getLabelBadge()}
                <Badge variant="outline" className="font-mono text-xs">
                  Band: {result.classification_band}
                </Badge>
                {result.reliability_flag !== "NORMAL" && (
                  <Badge variant="warning" className="text-xs">
                    {result.reliability_flag}
                  </Badge>
                )}
              </div>

              <div className="flex items-baseline gap-3 pt-1">
                <span className="text-4xl font-extrabold font-mono tracking-tight text-text-primary">
                  {(result.synthetic_pattern_confidence * 100).toFixed(1)}%
                </span>
                <span className="text-xs text-text-muted">
                  Synthetic Pattern Confidence
                </span>
              </div>

              <div className="flex flex-wrap items-center gap-4 text-xs text-text-secondary pt-1">
                <span>
                  95% Confidence Interval:{" "}
                  <strong className="text-text-primary font-mono font-medium">
                    [{(result.uncertainty_interval.lower * 100).toFixed(1)}% –{" "}
                    {(result.uncertainty_interval.upper * 100).toFixed(1)}%]
                  </strong>
                </span>
                <span>•</span>
                <span>
                  Abstain Thresholds:{" "}
                  <span className="font-mono">
                    [{(result.abstain_band_thresholds.lower * 100).toFixed(0)}% –{" "}
                    {(result.abstain_band_thresholds.upper * 100).toFixed(0)}%]
                  </span>
                </span>
              </div>

              {result.length_warning && (
                <div className="mt-2 text-xs text-semantic-warning flex items-center gap-1.5 bg-semantic-warning-subtle/50 p-2 rounded border border-semantic-warning/20">
                  <AlertTriangle className="h-4 w-4 flex-shrink-0" />
                  <span>{result.length_warning}</span>
                </div>
              )}
            </div>

            {/* Action Buttons */}
            <div className="flex flex-wrap items-center gap-2.5 self-start lg:self-center">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleDownloadReport("html")}
                isLoading={downloadingFormat === "html"}
                className="gap-1.5"
              >
                <FileText className="h-3.5 w-3.5" />
                <span>HTML Report</span>
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleDownloadReport("json")}
                isLoading={downloadingFormat === "json"}
                className="gap-1.5"
              >
                <FileCode className="h-3.5 w-3.5" />
                <span>JSON</span>
              </Button>
              <Button
                variant="secondary"
                size="sm"
                onClick={onReset}
                className="gap-1.5"
              >
                <RotateCcw className="h-3.5 w-3.5" />
                <span>Inspect Another Document</span>
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Prominent Scientific Limitations Panel */}
      <div
        role="region"
        aria-label="Scientific Limitations Panel"
        className="rounded-lg border border-semantic-warning/30 bg-semantic-warning-subtle/30 p-5 space-y-3"
      >
        <div className="flex items-center gap-2 text-semantic-warning font-semibold text-sm">
          <ShieldAlert className="h-4 w-4 flex-shrink-0" />
          <span>Scientific Limitations & Methodological Disclaimers</span>
        </div>
        <p className="text-xs text-text-secondary leading-relaxed">
          {result.limitations.disclaimer}
        </p>
        <ul className="text-xs text-text-secondary space-y-1.5 pl-4 list-disc leading-relaxed">
          {result.limitations.plain_language_limitations.map((lim, idx) => (
            <li key={idx}>{lim}</li>
          ))}
        </ul>
        <div className="flex items-center gap-3 text-[11px] font-mono text-text-muted pt-1 border-t border-semantic-warning/20">
          <span>Model Version: {result.limitations.model_version}</span>
          <span>•</span>
          <span className="truncate">Hash: {result.limitations.model_hash.slice(0, 16)}...</span>
        </div>
      </div>

      {/* Document Statistics Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 space-y-1">
            <span className="text-xs text-text-muted">Total Words</span>
            <p className="text-xl font-bold font-mono text-text-primary">
              {result.stats.word_count ?? 0}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 space-y-1">
            <span className="text-xs text-text-muted">Paragraphs</span>
            <p className="text-xl font-bold font-mono text-text-primary">
              {result.stats.paragraph_count ?? result.paragraphs.length}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 space-y-1">
            <span className="text-xs text-text-muted">Sentences</span>
            <p className="text-xl font-bold font-mono text-text-primary">
              {result.stats.sentence_count ?? result.paragraphs.reduce((acc, p) => acc + p.sentences.length, 0)}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 space-y-1">
            <span className="text-xs text-text-muted">Reliability Status</span>
            <p className="text-sm font-semibold text-text-primary pt-1">
              {result.reliability_flag === "NORMAL" ? "Optimal Length" : "Short Text Alert"}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Top Contributing Signals */}
      {result.top_contributing_signals && result.top_contributing_signals.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base font-semibold">Signal Attribution & Feature Contribution</CardTitle>
            <CardDescription>
              Linguistic features extracted from the input and their statistical directionality relative to calibrated human baseline distributions.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {result.top_contributing_signals.map((sig) => (
                <div
                  key={sig.name}
                  className="rounded border border-border-subtle bg-surface-base p-3.5 space-y-1.5"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-text-primary">
                      {sig.display_name}
                    </span>
                    <Badge
                      variant={
                        sig.direction === "synthetic_indicative"
                          ? "critical"
                          : "info"
                      }
                      className="text-[10px]"
                    >
                      {sig.direction === "synthetic_indicative"
                        ? "Synthetic Pattern"
                        : "Human Pattern"}
                    </Badge>
                  </div>
                  <div className="text-xs font-mono text-text-muted">
                    Measured: {sig.measured_value.toFixed(4)}
                  </div>
                  <p className="text-xs text-text-secondary leading-relaxed">
                    {sig.explanation}
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Sentence Heatmap & Offsets View */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-semibold">
            Sentence-Level Heatmap & Attribution Offsets
          </CardTitle>
          <CardDescription>
            Sentence blocks reconstructed using exact normalized character offsets. Click any sentence to review local lexical homogeneity and disclaimers.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <SentenceHeatmap paragraphs={result.paragraphs} />
        </CardContent>
      </Card>
    </div>
  );
}
