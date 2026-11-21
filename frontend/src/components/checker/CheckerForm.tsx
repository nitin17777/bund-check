"use client";

import * as React from "react";
import {
  apiClient,
  CheckResponse,
  ApiException,
  Document,
} from "@/lib/api-client";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { FileDropzone } from "@/components/ui/FileDropzone";
import { Progress } from "@/components/ui/Progress";
import {
  AlertCircle,
  FileText,
  UploadCloud,
  FileCheck2,
  XCircle,
  AlertTriangle,
} from "lucide-react";

interface CheckerFormProps {
  onSuccess: (result: CheckResponse) => void;
}

export type ProcessingStage = "idle" | "uploading" | "extracting" | "analyzing";

export function CheckerForm({ onSuccess }: CheckerFormProps) {
  const [activeTab, setActiveTab] = React.useState<"paste" | "upload">("paste");
  const [pastedText, setPastedText] = React.useState("");
  const [selectedFile, setSelectedFile] = React.useState<File | null>(null);
  const [processingStage, setProcessingStage] = React.useState<ProcessingStage>("idle");
  const [errorMessage, setErrorMessage] = React.useState<{ title: string; message: string } | null>(null);
  const abortControllerRef = React.useRef<AbortController | null>(null);

  // Live word counter
  const wordCount = React.useMemo(() => {
    const trimmed = pastedText.trim();
    return trimmed ? trimmed.split(/\s+/).length : 0;
  }, [pastedText]);

  const handleCancel = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setProcessingStage("idle");
    setErrorMessage({
      title: "Inspection Cancelled",
      message: "The document analysis request was cancelled by the user.",
    });
  };

  const handleAnalyze = async () => {
    setErrorMessage(null);
    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      let extractedDoc: Document | undefined = undefined;

      if (activeTab === "upload") {
        if (!selectedFile) {
          setErrorMessage({
            title: "No File Selected",
            message: "Please choose or drop a PDF, DOCX, or TXT file to inspect.",
          });
          return;
        }

        // Step 1: Upload & Extract
        setProcessingStage("uploading");
        const formData = new FormData();
        formData.append("file", selectedFile);

        setProcessingStage("extracting");
        extractedDoc = await apiClient.extractDocument(formData, { signal: controller.signal });
      } else {
        // Paste mode
        const text = pastedText.trim();
        if (!text) {
          setErrorMessage({
            title: "Empty Input Text",
            message: "Please paste text into the editor before initiating inspection.",
          });
          return;
        }

        if (wordCount < 10) {
          setErrorMessage({
            title: "Text Too Short",
            message: "Input contains fewer than 10 words. A minimum of 50 words is recommended for statistical reliability.",
          });
          return;
        }

        // Extract normalized structure for pasted text
        setProcessingStage("extracting");
        extractedDoc = await apiClient.extractDocument(
          { text, filename: "pasted_text.txt" },
          { signal: controller.signal }
        );
      }

      // Step 2: Multi-Signal Inspection
      setProcessingStage("analyzing");
      const checkResult = await apiClient.checkContent(
        { document: extractedDoc },
        { signal: controller.signal }
      );

      setProcessingStage("idle");
      onSuccess(checkResult);
    } catch (err: unknown) {
      if (err instanceof DOMException && err.name === "AbortError") {
        return; // Handled by cancel
      }

      setProcessingStage("idle");
      if (err instanceof ApiException) {
        let title = "Analysis Failed";
        let message = err.message;

        if (
          err.code === "SCANNED_PDF_NOT_SUPPORTED" ||
          err.code === "SCANNED_PDF_OCR_NOT_SUPPORTED" ||
          err.code === "SCANNED_PAGE_DETECTED" ||
          err.message?.toLowerCase().includes("scanned") ||
          err.message?.toLowerCase().includes("ocr")
        ) {
          title = "Scanned PDF (OCR Not Supported)";
          message =
            "The uploaded PDF appears to be scanned or image-only with no extractable text layer. Please provide a searchable PDF, DOCX, or text file.";
        } else if (err.code === "PAYLOAD_TOO_LARGE" || err.code === "FILE_TOO_LARGE") {
          title = "Document Exceeds Size Limit";
          message = "The document exceeds the maximum permitted limit of 10 MB or 50,000 words.";
        } else if (err.code === "EMPTY_DOCUMENT_TEXT") {
          title = "Document Empty";
          message = "No readable text was found in the document archive.";
        } else if (err.code === "ENCRYPTED_PDF_NOT_SUPPORTED") {
          title = "Encrypted Document";
          message = "Password-protected or encrypted PDF files are not supported.";
        } else if (err.code === "UNSUPPORTED_MEDIA_TYPE") {
          title = "Unsupported Format";
          message = "Only PDF, DOCX, and TXT files are accepted.";
        }

        setErrorMessage({ title, message });
      } else {
        setErrorMessage({
          title: "Request Error",
          message: err instanceof Error ? err.message : "An unexpected communication error occurred.",
        });
      }
    } finally {
      abortControllerRef.current = null;
    }
  };

  const isBusy = processingStage !== "idle";

  return (
    <div className="space-y-6">
      <Card className="border-border">
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <CardTitle className="text-lg font-semibold">Document & Text Input</CardTitle>
              <CardDescription className="mt-1">
                Upload a document or paste manuscript text. Ephemeral in-memory execution guarantees zero disk persistence.
              </CardDescription>
            </div>

            {/* Input Type Toggle */}
            <div
              className="inline-flex h-9 items-center rounded-md bg-surface-base p-1 border border-border-subtle self-start"
              role="tablist"
              aria-label="Input mode selector"
            >
              <button
                type="button"
                role="tab"
                aria-selected={activeTab === "paste"}
                disabled={isBusy}
                onClick={() => setActiveTab("paste")}
                className={`px-3 py-1 text-xs font-medium rounded transition-colors ${
                  activeTab === "paste"
                    ? "bg-surface-card text-text-primary font-semibold shadow-sm border border-border-subtle"
                    : "text-text-secondary hover:text-text-primary"
                }`}
              >
                Paste Text
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={activeTab === "upload"}
                disabled={isBusy}
                onClick={() => setActiveTab("upload")}
                className={`px-3 py-1 text-xs font-medium rounded transition-colors ${
                  activeTab === "upload"
                    ? "bg-surface-card text-text-primary font-semibold shadow-sm border border-border-subtle"
                    : "text-text-secondary hover:text-text-primary"
                }`}
              >
                Upload File
              </button>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          {activeTab === "paste" ? (
            <div className="space-y-2">
              <label htmlFor="content-textarea" className="sr-only">
                Paste manuscript or text content
              </label>
              <textarea
                id="content-textarea"
                rows={9}
                value={pastedText}
                onChange={(e) => setPastedText(e.target.value)}
                disabled={isBusy}
                placeholder="Paste technical paper, essay, manuscript, or prose draft for probabilistic inspection..."
                className="w-full rounded border border-border bg-surface-base p-3.5 text-sm text-text-primary placeholder:text-text-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent resize-y font-sans leading-relaxed disabled:opacity-50"
              />

              <div className="flex items-center justify-between text-xs text-text-muted px-1">
                <span className="font-mono">
                  {wordCount} {wordCount === 1 ? "word" : "words"}
                  {wordCount > 0 && wordCount < 50 && (
                    <span className="text-semantic-warning ml-2 font-sans inline-flex items-center gap-1">
                      <AlertTriangle className="h-3 w-3" />
                      (Short text — reliable threshold is 150+ words)
                    </span>
                  )}
                </span>
                <span>Max 50,000 words</span>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              <FileDropzone
                disabled={isBusy}
                onFileAccepted={(file) => setSelectedFile(file)}
              />
            </div>
          )}

          {/* Processing Status Banner */}
          {isBusy && (
            <div
              role="status"
              className="rounded-lg border border-border-subtle bg-surface-base p-4 space-y-3 animate-in fade-in-0"
            >
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2 text-text-primary font-medium">
                  <div className="h-2 w-2 rounded-full bg-accent animate-ping" />
                  <span>
                    {processingStage === "uploading" && "Uploading document to memory buffer..."}
                    {processingStage === "extracting" && "Extracting text structure and normalizing Unicode..."}
                    {processingStage === "analyzing" && "Evaluating token perplexity, burstiness & calibration..."}
                  </span>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleCancel}
                  className="text-text-muted hover:text-semantic-critical h-7 text-xs"
                >
                  <XCircle className="h-3.5 w-3.5 mr-1" />
                  Cancel
                </Button>
              </div>

              <Progress
                value={
                  processingStage === "uploading"
                    ? 30
                    : processingStage === "extracting"
                    ? 65
                    : 90
                }
              />
            </div>
          )}

          {/* Actionable Error Banner */}
          {errorMessage && (
            <div
              role="alert"
              className="rounded-lg border border-semantic-critical/30 bg-semantic-critical-subtle/40 p-4 space-y-1 text-xs animate-in fade-in-0"
            >
              <div className="flex items-center gap-2 text-semantic-critical font-semibold">
                <AlertCircle className="h-4 w-4 flex-shrink-0" />
                <span>{errorMessage.title}</span>
              </div>
              <p className="text-text-secondary pl-6 leading-relaxed">
                {errorMessage.message}
              </p>
            </div>
          )}

          {/* Action Footer */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2 border-t border-border-subtle">
            <span className="text-xs text-text-muted">
              Privacy guarantee: Text is cleared from memory immediately post-analysis.
            </span>

            <Button
              variant="primary"
              size="md"
              onClick={handleAnalyze}
              isLoading={isBusy}
              disabled={isBusy || (activeTab === "paste" && !pastedText.trim()) || (activeTab === "upload" && !selectedFile)}
              className="w-full sm:w-auto min-w-[140px]"
            >
              <FileCheck2 className="h-4 w-4 mr-2" />
              <span>Inspect Content</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
