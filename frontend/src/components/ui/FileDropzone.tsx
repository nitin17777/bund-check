"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { UploadCloud, FileText, AlertCircle, X } from "lucide-react";

export interface FileDropzoneProps {
  onFileAccepted: (file: File) => void;
  maxSizeBytes?: number; // Default 10 MB per API spec
  allowedExtensions?: string[]; // Default [".pdf", ".docx", ".txt"]
  className?: string;
  disabled?: boolean;
}

export function FileDropzone({
  onFileAccepted,
  maxSizeBytes = 10 * 1024 * 1024, // 10 MB
  allowedExtensions = [".pdf", ".docx", ".txt"],
  className,
  disabled = false,
}: FileDropzoneProps) {
  const [isDragOver, setIsDragOver] = React.useState(false);
  const [selectedFile, setSelectedFile] = React.useState<File | null>(null);
  const [errorMessage, setErrorMessage] = React.useState<string | null>(null);
  const inputRef = React.useRef<HTMLInputElement | null>(null);

  const validateAndHandle = (file: File) => {
    setErrorMessage(null);

    // Extension check
    const ext = "." + file.name.split(".").pop()?.toLowerCase();
    if (!allowedExtensions.includes(ext)) {
      setErrorMessage(
        `Invalid file type (${ext}). Allowed types: ${allowedExtensions.join(", ")}`
      );
      return;
    }

    // Size check
    if (file.size > maxSizeBytes) {
      const maxMb = (maxSizeBytes / (1024 * 1024)).toFixed(0);
      const fileMb = (file.size / (1024 * 1024)).toFixed(1);
      setErrorMessage(
        `File is too large (${fileMb} MB). Maximum size is ${maxMb} MB.`
      );
      return;
    }

    setSelectedFile(file);
    onFileAccepted(file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    if (disabled) return;
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (disabled) return;

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndHandle(e.dataTransfer.files[0]);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndHandle(e.target.files[0]);
    }
  };

  const clearSelection = (e: React.MouseEvent) => {
    e.stopPropagation();
    setSelectedFile(null);
    setErrorMessage(null);
    if (inputRef.current) inputRef.current.value = "";
  };

  return (
    <div className={cn("w-full space-y-2", className)}>
      <div
        tabIndex={disabled ? -1 : 0}
        onClick={() => !disabled && !selectedFile && inputRef.current?.click()}
        onKeyDown={(e) => {
          if (!disabled && !selectedFile && (e.key === "Enter" || e.key === " ")) {
            e.preventDefault();
            inputRef.current?.click();
          }
        }}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={cn(
          "relative flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 text-center transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent",
          !selectedFile && "cursor-pointer",
          isDragOver
            ? "border-accent bg-accent-subtle"
            : "border-border hover:border-border-strong bg-surface-card/60 hover:bg-surface-card",
          disabled && "cursor-not-allowed opacity-50 pointer-events-none"
        )}
      >
        <input
          ref={inputRef}
          type="file"
          aria-label="Upload document file"
          accept={allowedExtensions.join(",")}
          onChange={handleInputChange}
          className="hidden"
          disabled={disabled}
        />

        {selectedFile ? (
          <div className="flex items-center gap-3 bg-surface-overlay border border-border-subtle rounded-md px-4 py-2.5 max-w-sm w-full justify-between">
            <div className="flex items-center gap-2.5 truncate">
              <FileText className="h-5 w-5 text-accent flex-shrink-0" />
              <div className="truncate text-left">
                <p className="text-sm font-medium text-text-primary truncate">
                  {selectedFile.name}
                </p>
                <p className="text-xs text-text-muted">
                  {(selectedFile.size / 1024).toFixed(1)} KB
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={clearSelection}
              aria-label="Remove selected file"
              className="text-text-muted hover:text-text-primary rounded p-1 transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        ) : (
          <div className="flex flex-col items-center space-y-2">
            <div className="rounded-full bg-surface-overlay p-3 border border-border-subtle">
              <UploadCloud className="h-6 w-6 text-text-secondary" />
            </div>
            <div>
              <p className="text-sm font-medium text-text-primary">
                Drag and drop your document here, or{" "}
                <span className="text-accent underline underline-offset-2">browse</span>
              </p>
              <p className="text-xs text-text-muted mt-1">
                Supported formats: PDF, DOCX, TXT (up to 10 MB)
              </p>
            </div>
          </div>
        )}
      </div>

      {errorMessage && (
        <div className="flex items-center gap-2 text-xs text-semantic-critical bg-semantic-critical-subtle border border-semantic-critical/20 rounded p-2.5">
          <AlertCircle className="h-4 w-4 flex-shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}
    </div>
  );
}
