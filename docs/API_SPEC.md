# API Specification & Endpoint Contracts

All API endpoints are prefixed with `/api/v1` and strictly consume and produce `application/json` (except `/document/extract` which accepts `multipart/form-data` and report export which returns binary/text formats).

---

## 1. Global Schemas & Error Envelope

All error responses strictly follow the RFC 7807 problem details specification:

```json
{
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "Input text length exceeds 50,000 words limit.",
    "details": [
      {
        "field": "text",
        "issue": "Max word count is 50000; received 52140."
      }
    ],
    "request_id": "req_01HJ8Z8K80W..."
  }
}
```

### Standard Error Codes:
- `400 BAD_REQUEST`: Malformed syntax, invalid parameters.
- `401 UNAUTHORIZED`: Invalid or missing session token.
- `403 FORBIDDEN`: Insufficient permission.
- `413 PAYLOAD_TOO_LARGE`: Document size or word count exceeds ceiling.
- `422 UNPROCESSABLE_ENTITY`: Unsupported file type, corrupted archive, or macro detected.
- `429 TOO_MANY_REQUESTS`: Rate limit exceeded.
- `500 INTERNAL_SERVER_ERROR`: Unhandled server exception.
- `502 BAD_GATEWAY`: External LLM provider error.

---

## 2. Endpoints Overview

| Method | Path | Description | Auth Required | Processing Mode |
|---|---|---|---|---|
| `GET` | `/api/v1/health` | Service health, version, environment, active tasks count | Optional | Sync |
| `POST` | `/api/v1/documents/extract` | Ingest PDF/DOCX/TXT or JSON text; extract structured Document | Optional | Sync |
| `POST` | `/api/v1/check` | Probabilistic AI-pattern analysis & sentence attribution | Optional | Sync (<1k words) / Async (>=1k words) |
| `GET` | `/api/v1/tasks/{task_id}` | Poll status & retrieve result of asynchronous task | Optional | Sync |
| `POST` | `/api/v1/check/report` | Export analysis report as HTML or structured JSON | Optional | Sync |
| `POST` | `/api/v1/improve` | Rewrite text in specified mode with span protection | Optional | Sync (<1k words) / Async (>=1k words) |
| `POST` | `/api/v1/verify` | Standalone verification audit (source vs rewrite) | Optional | Sync |
| `POST` | `/api/v1/export` | Export rewritten text to DOCX, PDF, or TXT | Optional | Sync |
| `GET` | `/api/v1/history` | List opt-in past analyses and revisions | Optional / Cookie | Sync |
| `GET` | `/api/v1/settings` | Retrieve user preferences and configured LLM providers | Optional / Cookie | Sync |
| `PUT` | `/api/v1/settings` | Update user preferences (store_opt_in, default_improver_mode) | Optional / Cookie | Sync |
| `DELETE`| `/api/v1/delete` | Immediate hard deletion of user data or specific document | Optional / Cookie | Sync |

---

## 3. Detailed Endpoint Contracts

### 3.1 Health Check: `GET /api/v1/health`

#### Response: `200 OK`
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "environment": "production",
  "active_tasks": 0
}
```

---

### 3.2 Document Extraction: `POST /api/v1/documents/extract`
Consumes `multipart/form-data` (field `file` for .pdf, .docx, .txt, up to 10 MB) or `application/json` (`{"text": "...", "filename": "pasted.txt"}`).

#### Response: `200 OK`
```json
{
  "document_id": "doc_98a7fbc2-...",
  "filename": "draft_manuscript.docx",
  "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "word_count": 1420,
  "paragraph_count": 8,
  "paragraphs": [
    {
      "index": 0,
      "text": "First extracted body paragraph text...",
      "char_count": 284
    },
    {
      "index": 1,
      "text": "| Trial | Dosage (mg) | Response Rate |\n|---|---|---|\n| 1 | 25 | 68% |\n| 2 | 50 | 84% |",
      "char_count": 92
    }
  ],
  "unsupported_elements": [
    {
      "type": "nested_table",
      "location": "section_3_page_2",
      "action_taken": "skipped"
    },
    {
      "type": "footer",
      "location": "page_1",
      "action_taken": "skipped"
    }
  ]
}
```

---

### 3.3 Content Check: `POST /api/v1/check`

#### Request Body
```json
{
  "text": "The rapid advancement of deep learning architectures...",
  "document_id": "doc_98a7fbc2-...",
  "options": {
    "sensitivity": "balanced",
    "store_opt_in": false
  }
}
```

#### Sync Response (`200 OK`) — When Word Count < Configurable Threshold (`1,000` words):
```json
{
  "analysis_id": "an_c48b19...",
  "synthetic_pattern_confidence": 0.82,
  "classification_band": "SYNTHETIC_INDICATIVE",
  "abstain_band_thresholds": {
    "lower": 0.40,
    "upper": 0.60
  },
  "uncertainty_interval": {
    "lower": 0.74,
    "upper": 0.88,
    "confidence_level": 0.95
  },
  "reliability_flag": "NORMAL",
  "disclaimer": "This analysis reflects statistical probability based on linguistic patterns and burstiness. It does not prove authorship. Human review is recommended.",
  "document_signals": {
    "mean_perplexity": 14.8,
    "perplexity_burstiness": 0.28,
    "type_token_ratio": 0.41,
    "hapax_legomena_ratio": 0.22,
    "pos_entropy": 2.14,
    "negation_density": 0.015
  },
  "paragraphs": [
    {
      "index": 0,
      "synthetic_pattern_confidence": 0.84,
      "classification_band": "SYNTHETIC_INDICATIVE",
      "sentences": [
        {
          "index": 0,
          "text": "The rapid advancement of deep learning architectures has driven unprecedented breakthroughs across computational linguistics.",
          "score": 0.89,
          "perplexity": 12.1,
          "burstiness_contribution": 0.18,
          "highlight": true,
          "attribution_status": "ELEVATED_LOCAL_HOMOGENEITY",
          "attribution_disclaimer": "Linguistic pattern shows lower local variation; this does not prove this sentence was generated by AI."
        },
        {
          "index": 1,
          "text": "In short, we agree.",
          "score": null,
          "perplexity": null,
          "burstiness_contribution": null,
          "highlight": false,
          "attribution_status": "INSUFFICIENT_LENGTH",
          "attribution_disclaimer": "Sentence under 10 words excluded from local attribution."
        }
      ]
    }
  ]
}
```

#### Async Response (`202 Accepted`) — When Word Count >= Configurable Threshold (`1,000` words) or Background Extraction:
```json
{
  "task_id": "task_e482fa...",
  "status": "pending",
  "message": "Document exceeds synchronous analysis threshold. Processing asynchronously.",
  "poll_url": "/api/v1/tasks/task_e482fa...",
  "estimated_time_ms": 2800
}
```

---

### 3.4 Task Status Polling: `GET /api/v1/tasks/{task_id}`

#### Response: `200 OK` (Processing)
```json
{
  "task_id": "task_e482fa...",
  "status": "processing",
  "progress": 0.65,
  "created_at": "2026-11-21T10:15:00Z"
}
```

#### Response: `200 OK` (Completed)
```json
{
  "task_id": "task_e482fa...",
  "status": "completed",
  "result": {
    "analysis_id": "an_c48b19...",
    "synthetic_pattern_confidence": 0.82,
    "classification_band": "SYNTHETIC_INDICATIVE",
    "uncertainty_interval": {"lower": 0.74, "upper": 0.88, "confidence_level": 0.95},
    "disclaimer": "This analysis reflects statistical probability based on linguistic patterns and burstiness. It does not prove authorship. Human review is recommended."
  }
}
```

---

### 3.5 Writing Improver: `POST /api/v1/improve`

#### Request Body
```json
{
  "text": "On November 12, 2023, Dr. Grant did not find 42.8 kg of specimens in Area 51 (Smith et al., 2021).",
  "mode": "academic_clarity",
  "protection_config": {
    "protect_citations": true,
    "protect_numbers": true,
    "protect_dates": true,
    "protect_units": true,
    "protect_negations": true,
    "protect_urls": true,
    "protect_equations": true,
    "protect_named_entities": true
  },
  "store_opt_in": false
}
```

*Valid `mode` values*: `natural_conversational`, `academic_clarity`, `professional`, `simple_readable`, `concise`, `formal`.

#### Sync Response (`200 OK`)
```json
{
  "revision_id": "rev_78fa02...",
  "mode": "academic_clarity",
  "original_text": "On November 12, 2023, Dr. Grant did not find 42.8 kg of specimens in Area 51 (Smith et al., 2021).",
  "rewritten_text": "On November 12, 2023, Dr. Grant did not detect 42.8 kg of specimens within Area 51 (Smith et al., 2021).",
  "diff": [
    {"type": "equal", "value": "On November 12, 2023, Dr. Grant did not "},
    {"type": "delete", "value": "find"},
    {"type": "insert", "value": "detect"},
    {"type": "equal", "value": " 42.8 kg of specimens within Area 51 (Smith et al., 2021)."}
  ],
  "verification": {
    "status": "PASSED",
    "similarity_score": 0.94,
    "similarity_note": "Embedding cosine similarity evaluates proximity in latent space; it does not guarantee logical equivalence.",
    "checks": {
      "numeric_integrity": {"passed": true, "missing_numbers": []},
      "date_integrity": {"passed": true, "missing_dates": []},
      "unit_integrity": {"passed": true, "missing_units": []},
      "negation_integrity": {"passed": true, "missing_negations": []},
      "citation_integrity": {"passed": true, "missing_citations": []},
      "entity_integrity": {"passed": true, "missing_entities": []},
      "paragraph_alignment": {"passed": true, "source_count": 1, "target_count": 1},
      "contradiction_check": {"passed": true, "contradiction_probability": 0.01}
    },
    "flags": []
  }
}
```

---

### 3.6 Standalone Verification: `POST /api/v1/verify`

#### Request Body
```json
{
  "source_text": "Dr. Sarah Miller discovered 42 new exoplanets in sector 9 on January 5.",
  "target_text": "Dr. Miller discovered forty exoplanets in sector 9 on January 8."
}
```

#### Response: `200 OK`
```json
{
  "status": "NEEDS_REVIEW",
  "similarity_score": 0.86,
  "similarity_note": "Embedding cosine similarity evaluates proximity in latent space; it does not guarantee logical equivalence.",
  "checks": {
    "numeric_integrity": {
      "passed": false,
      "missing_numbers": ["42"]
    },
    "date_integrity": {
      "passed": false,
      "missing_dates": ["January 5"]
    },
    "unit_integrity": {"passed": true, "missing_units": []},
    "negation_integrity": {"passed": true, "missing_negations": []},
    "citation_integrity": {"passed": true, "missing_citations": []},
    "entity_integrity": {"passed": true, "missing_entities": []},
    "paragraph_alignment": {"passed": true, "source_count": 1, "target_count": 1},
    "contradiction_check": {"passed": true, "contradiction_probability": 0.08}
  },
  "flags": [
    {
      "severity": "CRITICAL",
      "code": "NUMERIC_MISMATCH",
      "message": "Numeric value '42' from source is missing or altered in target text."
    },
    {
      "severity": "CRITICAL",
      "code": "DATE_MISMATCH",
      "message": "Date 'January 5' from source was altered or omitted in target text."
    }
  ]
}
```

---

### 3.7 Check Report Export: `POST /api/v1/check/report`
- Accepts `analysis_id` and `format` (`pdf` or `json`). Returns PDF stream or structured analysis JSON.

### 3.8 Export Rewritten Document: `POST /api/v1/export`
- Accepts `text`, `format` (`docx`, `pdf`, `markdown`), and `title`. Returns generated document stream.

### 3.9 User History & Opt-in Data: `GET /api/v1/history`
- Query parameters: `limit`, `offset`, `type`. Returns paginated list of opted-in analyses and revisions.

### 3.10 User Settings: `GET /api/v1/settings` & `PUT /api/v1/settings`
- Manage default improver mode, opt-in defaults, and encrypted BYOK API keys (Groq, OpenRouter, Anthropic, OpenAI).

### 3.11 Hard Deletion: `DELETE /api/v1/delete`
- Request body: `{"target": "document", "id": "..."}` or `{"target": "all_user_data"}`. Cascade removes records immediately.
