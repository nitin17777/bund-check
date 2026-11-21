/**
 * Typed API Client for BundCheck Backend.
 * Strictly adheres to docs/API_SPEC.md and RFC 7807 error envelopes.
 */

export interface ApiErrorDetail {
  field?: string;
  issue: string;
}

export interface ApiError {
  code: string;
  message: string;
  details?: ApiErrorDetail[];
  request_id?: string;
}

export interface ApiErrorEnvelope {
  error: ApiError;
}

export class ApiException extends Error {
  public readonly code: string;
  public readonly details: ApiErrorDetail[];
  public readonly requestId?: string;
  public readonly status: number;

  constructor(status: number, error: ApiError) {
    super(error.message);
    this.name = "ApiException";
    this.status = status;
    this.code = error.code;
    this.details = error.details || [];
    this.requestId = error.request_id;
  }
}

export type RequestState<T> =
  | { status: "idle"; data: null; error: null }
  | { status: "loading"; data: null; error: null }
  | { status: "success"; data: T; error: null }
  | { status: "error"; data: null; error: ApiException };

// Domain Types
export interface HealthResponse {
  status: string;
  version: string;
  environment: string;
  ml_engine?: {
    device: string;
    total_vram_mb: number;
    system_ram_total_mb: number;
    models_loaded: {
      gpu: string[];
      cpu: string[];
    };
  };
}

// Domain Types matching backend models exactly
export interface Sentence {
  id: string;
  index: number;
  text: string;
  start_char: number;
  end_char: number;
  char_count: number;
  word_count: number;
}

export interface Paragraph {
  id: string;
  index: number;
  raw_text: string;
  normalized_text: string;
  start_char: number;
  end_char: number;
  is_table: boolean;
  is_heading: boolean;
  heading_level?: number | null;
  char_count: number;
  word_count: number;
  sentences: Sentence[];
}

export interface DocumentStats {
  word_count: number;
  character_count: number;
  paragraph_count: number;
  sentence_count: number;
  page_count?: number | null;
}

export interface Document {
  document_id: string;
  filename?: string | null;
  mime_type: string;
  language: string;
  language_warning?: string | null;
  stats: DocumentStats;
  normalized_full_text: string;
  paragraphs: Paragraph[];
  unsupported_elements?: Array<{
    type: string;
    location: string;
    action_taken: string;
    description: string;
  }>;
}

export interface ContributingSignal {
  name: string;
  display_name: string;
  measured_value: number;
  direction: string;
  explanation: string;
}

export interface SentenceIndicator {
  index: number;
  id?: string | null;
  text: string;
  indicator_score?: number | null;
  status: string;
  is_elevated_homogeneity: boolean;
  attribution_disclaimer: string;
}

export interface ParagraphDetectionResult {
  index: number;
  id?: string | null;
  synthetic_pattern_confidence?: number | null;
  classification_band: string;
  sentences: SentenceIndicator[];
}

export interface UncertaintyInterval {
  lower: number;
  upper: number;
  confidence_level: number;
}

export interface LimitationsBlock {
  disclaimer: string;
  plain_language_limitations: string[];
  model_version: string;
  model_hash: string;
}

export interface CheckRequest {
  text?: string;
  document?: Document;
  document_id?: string;
}

export interface CheckResponse {
  analysis_id: string;
  document_id?: string | null;
  synthetic_pattern_confidence: number;
  label: string;
  classification_band: string;
  uncertainty_interval: UncertaintyInterval;
  abstain_band_thresholds: {
    lower: number;
    upper: number;
  };
  reliability_flag: string;
  length_warning?: string | null;
  stats: Record<string, number>;
  top_contributing_signals: ContributingSignal[];
  paragraphs: ParagraphDetectionResult[];
  limitations: LimitationsBlock;
}

export interface ReportRequest {
  check_response: CheckResponse;
  format?: "json" | "html" | "pdf";
  title?: string;
}

export type ImproverMode =
  | "natural_conversational"
  | "academic_clarity"
  | "professional"
  | "simple_readable"
  | "concise"
  | "formal";

export interface ImproveRequest {
  text: string;
  mode: ImproverMode;
  provider?: string;
  run_verification?: boolean;
  enable_nli?: boolean;
}

export interface SentenceChange {
  sentence_index: number;
  original: string;
  revised: string;
  accepted: boolean;
}

export interface ParagraphImprovement {
  paragraph_index: number;
  original_text: string;
  revised_text: string;
  is_heading: boolean;
  status: "SUCCESS" | "SKIPPED_HEADING" | "FAILED";
  changes: SentenceChange[];
  error_message?: string;
  verification_report?: VerificationReport;
}

export interface ImproveResponse {
  revision_id: string;
  mode: string;
  provider_used: string;
  model_used: string;
  paragraphs: ParagraphImprovement[];
  stats: {
    original_word_count: number;
    paragraph_count: number;
    improved_paragraphs_count: number;
  };
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
    estimated_cost_usd: number;
  };
}

export interface VerifyRequest {
  source_text: string;
  target_text: string;
  enable_nli?: boolean;
}

export interface VerificationFinding {
  category: "numbers" | "citations" | "entities" | "structure" | "negations" | "semantics";
  severity: "INFO" | "WARN" | "CRITICAL";
  code: string;
  message: string;
  paragraph_index?: number;
  details?: Record<string, unknown>;
}

export interface VerificationReport {
  status: "PASSED" | "NEEDS_REVIEW" | "FAILED";
  overall_similarity_score: number;
  similarity_note: string;
  needs_review: boolean;
  findings: VerificationFinding[];
  paragraph_verifications: Array<{
    paragraph_index: number;
    status: "PASSED" | "NEEDS_REVIEW" | "FAILED";
    needs_review: boolean;
    similarity_score: number;
    findings: VerificationFinding[];
  }>;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;
  
  const headers = new Headers(options.headers);
  if (!(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorBody: ApiError;
    try {
      const data = await response.json();
      errorBody = data.error || {
        code: `HTTP_${response.status}`,
        message: response.statusText || "Request failed",
      };
    } catch {
      errorBody = {
        code: `HTTP_${response.status}`,
        message: response.statusText || "Request failed",
      };
    }
    throw new ApiException(response.status, errorBody);
  }

  return response.json();
}

export const apiClient = {
  getHealth: (options: { signal?: AbortSignal } = {}) =>
    request<HealthResponse>("/health", { signal: options.signal }),

  extractDocument: (
    input: FormData | { text: string; filename?: string },
    options: { signal?: AbortSignal } = {}
  ) => {
    const isFormData = input instanceof FormData;
    return request<Document>("/documents/extract", {
      method: "POST",
      body: isFormData ? input : JSON.stringify(input),
      signal: options.signal,
    });
  },

  checkContent: (
    payload: CheckRequest,
    options: { signal?: AbortSignal } = {}
  ) =>
    request<CheckResponse>("/check", {
      method: "POST",
      body: JSON.stringify(payload),
      signal: options.signal,
    }),

  exportReport: async (
    payload: ReportRequest,
    options: { signal?: AbortSignal } = {}
  ): Promise<{ blob: Blob; filename: string }> => {
    const url = `${API_BASE_URL}/check/report`;
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: options.signal,
    });
    if (!response.ok) {
      let errorBody: ApiError;
      try {
        const data = await response.json();
        errorBody =
          data.error || {
            code: `HTTP_${response.status}`,
            message: "Failed to generate report",
          };
      } catch {
        errorBody = {
          code: `HTTP_${response.status}`,
          message: "Failed to generate report",
        };
      }
      throw new ApiException(response.status, errorBody);
    }
    const disposition = response.headers.get("content-disposition") || "";
    const match = disposition.match(/filename="?([^"]+)"?/);
    const filename = match ? match[1] : `analysis_report.${payload.format || "html"}`;
    const blob = await response.blob();
    return { blob, filename };
  },

  improveContent: (
    payload: ImproveRequest,
    options: { signal?: AbortSignal } = {}
  ) =>
    request<ImproveResponse>("/improve", {
      method: "POST",
      body: JSON.stringify(payload),
      signal: options.signal,
    }),

  verifyRevision: (
    payload: VerifyRequest,
    options: { signal?: AbortSignal } = {}
  ) =>
    request<VerificationReport>("/verify", {
      method: "POST",
      body: JSON.stringify(payload),
      signal: options.signal,
    }),
};
