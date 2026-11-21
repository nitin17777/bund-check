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

| Method | Path | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/v1/health` | Service health, model status, and provider connectivity | Optional |
| `POST` | `/api/v1/document/extract` | Ingest and parse PDF/DOCX/TXT into normalized paragraphs | Optional |
| `POST` | `/api/v1/check` | Execute probabilistic content detection and attribution | Optional |
| `POST` | `/api/v1/check/report` | Export analysis report as PDF or structured JSON | Optional |
| `POST` | `/api/v1/improve` | Rewrite text in specified mode with span protection | Optional |
| `POST` | `/api/v1/verify` | Re-run standalone verification audit on source vs. rewrite | Optional |
| `POST` | `/api/v1/export` | Export rewritten text to DOCX, PDF, or Markdown | Optional |
| `GET` | `/api/v1/history` | List opt-in past analyses and revisions | Required |
| `GET` | `/api/v1/settings` | Retrieve user preferences and configured LLM providers | Required |
| `PUT` | `/api/v1/settings` | Update user preferences or encrypted LLM keys | Required |
| `DELETE`| `/api/v1/delete` | Immediate hard deletion of user data or specific document | Required |

---

## 3. Detailed Endpoint Contracts

### 3.1 Health Check: `GET /api/v1/health`

#### Response: `200 OK`
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "production",
  "ml_engine": {
    "device": "cuda:0",
    "vram_allocated_mb": 1150.4,
    "vram_total_mb": 4096.0,
    "models_loaded": ["perplexity-small", "classifier-distilroberta"]
  },
  "providers": {
    "default_improver": "groq",
    "groq_status": "connected",
    "openrouter_status": "standby"
  }
}
```

---

### 3.2 Document Extraction: `POST /api/v1/document/extract`
Consumes `multipart/form-data`. Accepts `file` field (.pdf, .docx, .txt). Maximum 10 MB.

#### Response: `200 OK`
```json
{
  "document_id": "doc_98a7fbc2-...",
  "filename": "draft_chapter.pdf",
  "mime_type": "application/pdf",
  "word_count": 1420,
  "paragraph_count": 8,
  "paragraphs": [
    {
      "index": 0,
      "text": "First extracted paragraph text...",
      "char_count": 284
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

#### Response: `200 OK`
```json
{
  "analysis_id": "an_c48b19...",
  "calibrated_score": 0.82,
  "classification_band": "ELEVATED_STATISTICAL_PRESENCE",
  "uncertainty_interval": {
    "lower": 0.74,
    "upper": 0.88,
    "confidence_level": 0.95
  },
  "disclaimer": "This analysis reflects statistical probability based on linguistic patterns and burstiness. It does not prove authorship. Human review is recommended.",
  "document_signals": {
    "mean_perplexity": 14.8,
    "perplexity_burstiness": 0.28,
    "type_token_ratio": 0.41,
    "hapax_legomena_ratio": 0.22,
    "pos_entropy": 2.14
  },
  "paragraphs": [
    {
      "index": 0,
      "calibrated_score": 0.84,
      "classification_band": "ELEVATED_STATISTICAL_PRESENCE",
      "sentences": [
        {
          "index": 0,
          "text": "The rapid advancement of deep learning architectures...",
          "score": 0.89,
          "perplexity": 12.1,
          "burstiness_contribution": 0.18,
          "highlight": true
        }
      ]
    }
  ]
}
```

---

### 3.4 Check Report Export: `POST /api/v1/check/report`

#### Request Body
```json
{
  "analysis_id": "an_c48b19...",
  "format": "pdf",
  "include_sentence_breakdown": true
}
```

#### Response: `200 OK`
- Content-Type: `application/pdf` or `application/json`
- Content-Disposition: `attachment; filename="analysis-report-an_c48b19.pdf"`

---

### 3.5 Writing Improver: `POST /api/v1/improve`

#### Request Body
```json
{
  "text": "We utilized a multi-stage approach because we wanted to verify...",
  "mode": "academic_clarity",
  "protection_config": {
    "protect_citations": true,
    "protect_numbers": true,
    "protect_urls": true,
    "protect_equations": true,
    "protect_named_entities": true
  },
  "store_opt_in": false
}
```

*Valid `mode` values*: `natural_conversational`, `academic_clarity`, `professional`, `simple_readable`, `concise`, `formal`.

#### Response: `200 OK`
```json
{
  "revision_id": "rev_78fa02...",
  "mode": "academic_clarity",
  "original_text": "We utilized a multi-stage approach because we wanted to verify...",
  "rewritten_text": "A multi-stage methodology was implemented to verify...",
  "diff": [
    {"type": "delete", "value": "We utilized"},
    {"type": "insert", "value": "A multi-stage methodology was implemented"},
    {"type": "equal", "value": " to verify"}
  ],
  "verification": {
    "status": "PASSED",
    "similarity_score": 0.92,
    "checks": {
      "numeric_integrity": {"passed": true, "missing_numbers": []},
      "citation_integrity": {"passed": true, "missing_citations": []},
      "entity_integrity": {"passed": true, "missing_entities": []},
      "paragraph_alignment": {"passed": true, "source_count": 1, "target_count": 1},
      "contradiction_check": {"passed": true, "contradiction_probability": 0.02}
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
  "source_text": "Dr. Sarah Miller discovered 42 new exoplanets in sector 9.",
  "target_text": "Dr. Miller discovered forty exoplanets in sector 9."
}
```

#### Response: `200 OK`
```json
{
  "status": "NEEDS_REVIEW",
  "similarity_score": 0.86,
  "checks": {
    "numeric_integrity": {
      "passed": false,
      "missing_numbers": ["42"]
    },
    "citation_integrity": {"passed": true, "missing_citations": []},
    "entity_integrity": {
      "passed": true,
      "missing_entities": []
    },
    "paragraph_alignment": {"passed": true, "source_count": 1, "target_count": 1},
    "contradiction_check": {"passed": true, "contradiction_probability": 0.08}
  },
  "flags": [
    {
      "severity": "CRITICAL",
      "code": "NUMERIC_MISMATCH",
      "message": "Numeric value '42' from source is missing or altered in target text."
    }
  ]
}
```

---

### 3.7 Export Rewritten Document: `POST /api/v1/export`

#### Request Body
```json
{
  "text": "The finalized rewritten text content...",
  "format": "docx",
  "title": "Manuscript_Revised"
}
```

#### Response: `200 OK`
- Returns binary stream (`application/vnd.openxmlformats-officedocument.wordprocessingml.document` or `application/pdf`).

---

### 3.8 User History & Opt-in Data: `GET /api/v1/history`

#### Query Parameters:
- `limit` (default: 20, max: 100)
- `offset` (default: 0)
- `type` (`check` | `improve` | `all`)

#### Response: `200 OK`
```json
{
  "total": 3,
  "items": [
    {
      "id": "an_c48b19...",
      "type": "check",
      "created_at": "2026-11-21T10:14:00Z",
      "summary": "The rapid advancement of deep learning...",
      "calibrated_score": 0.82,
      "status": "completed"
    }
  ]
}
```

---

### 3.9 User Settings: `GET /api/v1/settings` & `PUT /api/v1/settings`

#### `GET /api/v1/settings` Response: `200 OK`
```json
{
  "store_history_default": false,
  "default_mode": "academic_clarity",
  "sensitivity_preference": "balanced",
  "custom_providers": {
    "groq_configured": true,
    "openrouter_configured": false,
    "anthropic_configured": false
  }
}
```

#### `PUT /api/v1/settings` Request Body
```json
{
  "store_history_default": true,
  "default_mode": "professional",
  "custom_api_keys": {
    "groq_api_key": "gsk_..."
  }
}
```

---

### 3.10 Hard Deletion: `DELETE /api/v1/delete`

#### Request Body
```json
{
  "target": "document",
  "id": "doc_98a7fbc2-..."
}
```
*(Or `"target": "all_user_data"` to trigger an immediate cascade purge of user account, settings, revisions, and analyses).*

#### Response: `200 OK`
```json
{
  "status": "purged",
  "records_deleted": 14,
  "timestamp": "2026-11-21T10:30:00Z"
}
```
