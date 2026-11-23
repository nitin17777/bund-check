# Production Deployment & Infrastructure Guide

This guide details a low-cost, production-ready deployment topology for BundCheck, providing automated SSL termination, database migrations, security isolation, and exact workload-to-hardware partitioning.

---

## 1. Workload & Hardware Allocation (CPU vs. GPU vs. Hosted API)

BundCheck is intentionally engineered to avoid requiring an expensive dedicated GPU instance in production. The system partitions tasks across compute layers:

| Subsystem / Task | Execution Layer | Memory & Compute Profile | Hardware Recommendation |
|:---|:---|:---|:---|
| **Document Parsing & Normalization** | Local CPU | Fast regex, AST parsing (PyMuPDF, python-docx), streaming byte validation | Shared vCPU (0.2–0.5 vCPU) |
| **Statistical Stylometry Extraction** | Local CPU | Tokenization, TTR, Flesch reading ease, punctuation & entropy metrics | Minimal RAM (< 4 MB per doc) |
| **Calibrated Ensemble Detection** | Local CPU | scikit-learn / XGBoost + Isotonic Regression calibration head | < 50 ms latency on CPU |
| **Post-Rewrite Verification** | Local CPU | Regex numeric diffs, citation tracking, AST structural checks, sentence transformer embedding similarity | 1–2 GB RAM for sentence-transformers model |
| **Writing Improver (LLM Refinement)** | Hosted External LLM (Groq / OpenRouter / OpenAI) | Generative rewriting across 6 stylistic modes, protected span substitution | External API calls (Zero local VRAM) |
| **Optional Local Small Improver** | Dedicated GPU (RTX 2050 4GB or remote Colab) | 4-bit quantized Qwen2.5-1.5B-Instruct (~1.8 GB VRAM) | Only when strict offline isolation is requested |

---

## 2. Improver LLM Cost Analysis (Per 1,000 Words)

When users invoke the Writing Improver, text is sent through prompt templates that include system guidelines, style directives, and protected span tokens.

### Estimation Assumptions
- **Input Text**: 1,000 words ≈ **1,330 prompt input tokens** (+ ~300 tokens for system prompt and instructions ≈ **1,630 input tokens**).
- **Output Text**: 1,000 words generated ≈ **1,330 output tokens**.

### Provider Cost Breakdown (as of November 2026)

| Provider & Model | Input Price / 1M Tokens | Output Price / 1M Tokens | Cost per 1,000 Words Revised | Official Pricing Citation & Date |
|:---|:---:|:---:|:---:|:---|
| **Groq**: `llama-3.3-70b-versatile` *(Default)* | $0.59 | $0.79 | **~$0.00201** (~0.20¢) | [Groq Official Pricing](https://groq.com/pricing), verified Nov 2026 |
| **OpenAI**: `gpt-4o-mini` | $0.15 | $0.60 | **~$0.00104** (~0.10¢) | [OpenAI Pricing](https://openai.com/api/pricing/), verified Nov 2026 |
| **OpenRouter**: `meta-llama/llama-3.3-70b-instruct` | $0.60 | $0.80 | **~$0.00204** (~0.20¢) | [OpenRouter Model Registry](https://openrouter.ai/models), verified Nov 2026 |
| **Local CPU/GPU**: `Qwen2.5-1.5B-Instruct` | $0.00 | $0.00 | **$0.00** (Local Compute) | Open Weights (HuggingFace / Apache 2.0) |

> **Cost Summary**: Revising a full 10,000-word academic paper or technical report using the default high-capability `llama-3.3-70b-versatile` model on Groq costs approximately **$0.02 (2 cents)**.

---

## 3. Recommended Low-Cost Production Topology (< $20/month)

A realistic and cost-effective deployment topology:

```
                      [ User HTTPS Traffic ]
                                 │
                                 ▼
                    [ Caddy / Nginx Reverse Proxy ]
                       (Auto-TLS Let's Encrypt)
                                 │
                ┌────────────────┴────────────────┐
                │                                 │
                ▼                                 ▼
      [ Next.js Frontend ]              [ FastAPI Backend ]
      • Host: Vercel/Netlify            • Host: Small VM (Hetzner / DO)
        OR Docker on VM                   2 vCPU, 4 GB RAM (~$8-12/mo)
      • Static & SSR pages              • Runs detection & verification
                                                  │
                                                  ▼
                                      [ PostgreSQL 16 ]
                                      • Managed (Neon/Supabase free/low tier)
                                        OR Docker container with volume
```

### Monthly Cost Breakdown:
1. **Compute (Backend Container)**: Hetzner Cloud CPX21 (3 vCPU, 4 GB RAM) or DigitalOcean Basic Droplet (2 vCPU, 4 GB RAM): **~$8.00 – $14.00 / month**.
2. **Database (PostgreSQL)**: Neon Serverless Postgres or Supabase Starter: **$0.00 – $5.00 / month** (or included in Docker Compose volume).
3. **Frontend**: Vercel Hobby / Cloudflare Pages (Free) or co-hosted on same VM: **$0.00 / month**.
4. **SSL / DNS**: Cloudflare Free + Caddy Auto-HTTPS: **$0.00 / month**.
5. **LLM API Usage**: ~$1.00 – $3.00 for ~500 revisions/month on Groq.
**Total Estimated Operating Cost: ~$10.00 – $20.00 / month**.

---

## 4. Single-Server Deployment with Docker Compose

### Prerequisites
- Docker Engine 24.0+ and Docker Compose v2.
- A registered domain name pointing its `A` record to your server's public IP address.
- Ports `80` and `443` open in your cloud firewall.

### Step 1: Clone Repository and Configure Environment
```bash
git clone https://github.com/your-org/bund-check.git /opt/bund-check
cd /opt/bund-check

cp .env.example .env
# Edit .env with your domain name, database credentials, and Groq/OpenAI keys:
nano .env
```

### Step 2: Launch Stack
```bash
docker compose -f docker-compose.prod.yml up -d --build
```

### Step 3: Verify Startup & Migrations
```bash
# Check running containers
docker compose -f docker-compose.prod.yml ps

# Inspect backend startup logs and automatic Alembic migrations
docker compose -f docker-compose.prod.yml logs backend
```

The container entrypoint script (`backend/entrypoint.sh`) runs:
```bash
alembic upgrade head
```
ensuring that the PostgreSQL database schema is automatically updated to the latest revision prior to serving traffic.

---

## 5. Security & Reverse Proxy Architecture

### Reverse Proxy & HTTPS (Caddy)
The included `Caddyfile` handles automatic TLS issuance via Let's Encrypt or ZeroSSL without manual certbot crons:
- Enforces HTTP/2 and modern TLS (1.2 / 1.3).
- Automatically redirects all port 80 HTTP traffic to port 443 HTTPS.
- Passes `X-Forwarded-Proto`, `X-Real-IP`, and request IDs upstream to the backend.

### Container Hardening
- **Non-Root Execution**: Backend runs under UID `10001:10001` (`bundcheck`), frontend runs under UID `10002:10002` (`nextjs`).
- **Network Isolation**: The PostgreSQL container exposes port 5432 strictly to the internal Docker bridge network (`bundcheck-internal`) and `127.0.0.1`, not the public internet.
- **Security Headers**: Injected by the pure ASGI `SecurityHeadersMiddleware`:
  - `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload`
  - `Content-Security-Policy: default-src 'none'; ...`
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Cache-Control: no-store` on all `/api/` endpoints
