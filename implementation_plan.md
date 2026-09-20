# Implementation Plan — NGO Impact Data Commons

Building a production-ready, modular, secure, and full-stack web application called **NGO Impact Data Commons**. The platform improves NGO transparency, detects fraudulent activities using AI rules, immutably logs transactions via a SHA-256 blockchain hash-chain ledger, and provides role-based interfaces for NGOs, Donors, Admins, and the public.

---

## User Review Required

> [!IMPORTANT]
> - **Backend Framework**: Python FastAPI + Async SQLAlchemy with dual PostgreSQL / SQLite support (ensures frictionless local dev running alongside standard Docker setup).
> - **Frontend Framework**: Next.js 15 with React 19, TypeScript, and Tailwind CSS.
> - **Blockchain & Ledger**: High-reliability SHA-256 Immutable Hash-Chain Ledger with block verification API and interactive visual chain explorer.
> - **AI Components**: Dual-mode AI Fraud Detection Engine (multi-rule financial anomaly scanner) & Gemini-powered AI Transparency Chatbot (with fallback KB).

---

## Proposed Changes & Phased Architecture

### Phase 1 — Platform Skeleton & Docker Infrastructure
- **[NEW] Backend (`/backend`)**:
  - `main.py`: FastAPI app initialization, CORS middleware, `/api/health` endpoint.
  - `requirements.txt`: FastAPI, Uvicorn, SQLAlchemy, Alembic, Pydantic v2, PyJWT, Passlib, python-multipart, Google GenerativeAI.
  - `Dockerfile`: Python 3.11 runtime docker configuration.
- **[NEW] Frontend (`/frontend`)**:
  - `package.json`, `tsconfig.json`, `tailwind.config.js`: Next.js 15 + TypeScript setup.
  - `src/app/layout.tsx`, `src/app/page.tsx`: Core layout with modern glassmorphism design system & navigation header.
  - `Dockerfile`: Node 22 build docker configuration.
- **[NEW] Docker & Env Configuration**:
  - `docker-compose.yml`: Wires `backend` (FastAPI), `frontend` (Next.js), and `postgres` DB service.
  - `.env.example` & `.env`: Environment variables for database URLs, JWT secrets, storage paths, and API keys.

---

### Phase 2 — Authentication & Role-Based Access Control (RBAC)
- **[NEW] `/backend/app/core` & `/backend/app/models`**:
  - `security.py`: Password hashing (bcrypt), JWT access/refresh token generation and decoding.
  - `models/user.py`: `User` model with fields (`id`, `email`, `hashed_password`, `full_name`, `role` [ADMIN, NGO, DONOR], `is_active`, `created_at`).
  - `schemas/auth.py`: Pydantic validation schemas for Signup, Login, Token, UserResponse.
  - `routers/auth.py`: `/api/auth/register`, `/api/auth/login`, `/api/auth/me`, `/api/auth/refresh`.
  - `dependencies.py`: `get_current_user`, `require_roles(['ADMIN', 'NGO', ...])`.
- **[NEW] `/frontend/src`**:
  - `context/AuthContext.tsx`: Authentication state management, token persistence, user context.
  - `app/login/page.tsx` & `app/register/page.tsx`: Responsive login/signup pages with dynamic role selector.

---

### Phase 3 — NGO Verification & Admin Approval Workflows
- **[NEW] `/backend/app`**:
  - `models/ngo.py`: `NGODetail` model (tax_id, reg_number, category, mission, address, status: PENDING/APPROVED/REJECTED, doc_completeness_score), `NGODocument` model (filename, file_type, file_path, upload_date).
  - `routers/ngo.py`: `/api/ngos/profile`, `/api/ngos/documents` (file upload with mime validation).
  - `routers/admin.py`: `/api/admin/ngos/pending`, `/api/admin/ngos/{id}/approve`, `/api/admin/ngos/{id}/reject`.
- **[NEW] `/frontend/src`**:
  - `app/ngo/register/page.tsx`: Multi-step NGO onboard & document upload form.
  - `app/ngo/dashboard/page.tsx`: NGO management portal (view status, submit financial logs).
  - `app/admin/dashboard/page.tsx`: Comprehensive Admin review panel with document previews, approval actions, and transparency metrics.

---

### Phase 4 — Donation Engine & Public Transparency Portal
- **[NEW] `/backend/app`**:
  - `models/donation.py`: `Donation` model (id, donor_id, ngo_id, amount, currency, message, transaction_hash, status).
  - `routers/donation.py`: `/api/donations/create`, `/api/donations/history`.
  - `routers/public.py`: `/api/public/ngos`, `/api/public/stats`, `/api/public/transparency-score/{id}`.
- **[NEW] `/frontend/src`**:
  - `app/explore/page.tsx`: Public NGO directory with real-time transparency scores, filter by domain, search.
  - `app/ngo/[id]/page.tsx`: NGO public profile, verified documents list, donation breakdown, score computation details.
  - `app/donor/dashboard/page.tsx`: Donor hub with donation history, impact report summaries, mock payment modal.

---

### Phase 5 — Advanced Modules: AI Fraud Detection, Immutable Blockchain Ledger, AI Assistant
- **[NEW] `/backend/app/services`**:
  - `fraud_engine.py`: Multi-rule AI fraud detection engine evaluating:
    1. Financial mismatch (expenses > donations)
    2. Duplicate beneficiary records across NGOs
    3. Document compliance gaps
    4. Unusually high velocity transaction spikes
  - `ledger_engine.py`: SHA-256 Cryptographic Hash-Chain Ledger generator & block verifier. Hashes each donation and NGO audit event with merkle root computation and chain integrity validation `/api/ledger/verify`.
  - `ai_chatbot.py`: Gemini-powered AI Assistant endpoint `/api/chat` with structured fallback for NGO transparency criteria and platform guidance.
- **[NEW] `/frontend/src`**:
  - `app/ledger/page.tsx`: Visual Blockchain Explorer displaying real-time cryptographic blocks, hashes, and validation status.
  - `components/AiChatbotWindow.tsx`: Floating interactive AI assistant widget on all pages.
  - `components/FraudAlertBadge.tsx`: Visual risk badges (`LOW`, `MEDIUM`, `HIGH`) for Admin and NGO inspection.

---

## Verification Plan

### Automated & API Verification
- **Backend Tests**: Verify API health, auth token flow, NGO creation/approval, donation logging, hash chain integrity, and fraud scan via test scripts / curl.
- **Build Checks**: Run `npm run build` for Next.js frontend to verify clean TS compilation.

### Manual Verification
- Register User accounts for Admin, NGO, and Donor roles.
- Submit NGO verification request with document uploads.
- Log in as Admin to review and approve the NGO.
- Log in as Donor to make a mock donation and review the newly appended Blockchain ledger block.
- Verify Fraud Detection alerts when testing anomalous financial inputs.
- Test interactive AI Chatbot query for platform help.

---
