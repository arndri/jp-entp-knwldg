# Japanese Enterprise Knowledge Assistant
<img width="1906" height="915" alt="image" src="https://github.com/user-attachments/assets/81227914-93b5-4c77-9055-698ac880803d" />

A local-first enterprise RAG web app for answering questions from Japanese business documents with citations. The project is designed as a production-shaped AI engineering portfolio build: document ingestion, local multilingual embeddings, vector retrieval, role/access filtering hooks, OpenAI answer generation, and a usable retro RPG styled frontend.

The current MVP indexes local Japanese PDF documents, stores chunk vectors in Qdrant, retrieves relevant passages by access level, and generates cited answers through an external LLM API.

## What The App Does

- Extracts text from Japanese PDF documents while preserving page numbers.
- Supports switchable PDF extraction backends: lightweight `pypdf` or structure-aware `Docling`.
- Splits documents into sentence-aware retrievable chunks with whole-sentence overlap.
- Generates local embeddings with `BAAI/bge-m3`.
- Stores vectors and metadata in Qdrant.
- Tracks documents, source metadata, chunk records, and ingestion jobs in PostgreSQL.
- Combines vector retrieval with PostgreSQL-backed BM25 lexical retrieval using reciprocal rank fusion.
- Answers user questions using retrieved context and OpenAI.
- Supports JWT login with `admin` and `user` roles.
- Shows source citations with document name, page number, excerpt, and retrieval score.
- Provides a themed web UI with document indexing, re-index/delete controls, status tracking, chat, access-level selection, and citation panels.
- Restricts document management to admins and derives query permissions from the logged-in user.
- Gives admins a retrieval evaluation dashboard with recall, MRR, latency, and per-question hit details.
- Applies chat guardrails for prompt-injection attempts, overly long questions, and weak retrieval context.

## Tech Stack

Frontend:

- React
- TypeScript
- Vite
- CSS pixel-art UI, no component framework

Backend:

- FastAPI
- Pydantic Settings
- OpenAI Python SDK
- pypdf
- Docling

AI / Retrieval:

- Local embeddings: `BAAI/bge-m3`
- Embedding runtime: `sentence-transformers`
- GPU acceleration: PyTorch CUDA, tested with RTX 4060
- Vector database: Qdrant
- LLM provider: OpenAI or DeepSeek

Local Infrastructure:

- Docker Compose
- PostgreSQL
- Qdrant
- Redis

## Project Structure

```text
backend/        FastAPI RAG API
frontend/       React/Vite web frontend
scripts/        Local run and API helper scripts
docs/           Local setup notes
docker-compose.yml
.env.example
```

## Local Setup

Create your local `.env` from the example:

```powershell
Copy-Item .env.example .env
```

Then fill in at least:

```text
OPENAI_API_KEY=
JWT_SECRET_KEY=
BOOTSTRAP_ADMIN_EMAIL=admin@example.com
BOOTSTRAP_ADMIN_PASSWORD=admin12345
BOOTSTRAP_USER_EMAIL=user@example.com
BOOTSTRAP_USER_PASSWORD=user12345
HF_TOKEN=
LLM_PROVIDER=openai
OPENAI_MODEL=
DEEPSEEK_API_KEY=
DEEPSEEK_MODEL=deepseek-v4-flash
DEEPSEEK_BASE_URL=https://api.deepseek.com
DOCUMENT_EXTRACTOR=pypdf
DOCLING_DO_OCR=false
DOCLING_DEVICE=cpu
DOCLING_FALLBACK_TO_PYPDF=true
DOCLING_LAYOUT_BATCH_SIZE=1
DOCLING_OCR_BATCH_SIZE=1
DOCLING_TABLE_BATCH_SIZE=1
DOCLING_MAX_PAGES=15
RETRIEVAL_MODE=hybrid
VECTOR_CANDIDATE_LIMIT=20
BM25_CANDIDATE_LIMIT=20
RRF_K=60
MAX_QUESTION_CHARS=1200
MIN_RETRIEVAL_SCORE=0.35
ENABLE_PROMPT_INJECTION_FILTER=true
```

Start local services:

```powershell
docker compose up -d
```

Install backend dependencies:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Optional CUDA PyTorch install for NVIDIA GPU:

```powershell
python -m pip install --upgrade --index-url https://download.pytorch.org/whl/cu126 torch
```

Start the backend:

```powershell
cd F:\project\jp-entp-knwldg
.\scripts\start_backend.ps1
```

Install and start the frontend:

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

Open:

```text
http://127.0.0.1:3000
```

## API Endpoints

- `GET /api/health`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/ingest`
- `GET /api/documents`
- `DELETE /api/documents/{document_id}`
- `POST /api/documents/{document_id}/reindex`
- `GET /api/evaluations`
- `POST /api/evaluations/run`
- `POST /api/chat`

## Pre-Push Validation

Install backend development dependencies once:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

Before pushing changes, run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\test_project.ps1
```

This currently runs:

- backend Python compile check
- backend `pytest` suite
- frontend production build
- frontend Playwright E2E smoke test

This is intentionally small for the MVP, but it gives the project a repeatable development gate before commits and pushes.

## Retrieval Evaluation

Retrieval quality needs a gold question set and an indexed local corpus, so it is kept as a local evaluation workflow instead of a CI requirement.

1. Copy the example file:

```powershell
Copy-Item .\eval\questions.example.jsonl .\eval\questions.local.jsonl
```

2. Replace it with real questions and expected source pages from your documents.

3. Start local services and index the documents you want to evaluate.

4. Run:

```powershell
cd backend
.\.venv\Scripts\python.exe ..\scripts\evaluate_retrieval.py --questions ..\eval\questions.local.jsonl --top-k 5
```

The script reports:

- `recall_at_k`
- `mrr`

Use it to compare chunking/retrieval changes against the same gold set before deciding whether a change is actually better.
Admins can also run this evaluation from the web dashboard. The dashboard stores each run in PostgreSQL and shows recall, MRR, average retrieval latency, and question-level hit/miss details.

## Notes

- Real API keys belong only in `.env`.
- Change the bootstrap passwords before using the app beyond local development.
- Chat guardrails reject obvious prompt-injection attempts before retrieval and refuse generation when retrieved citations are below `MIN_RETRIEVAL_SCORE`.
- `RETRIEVAL_MODE=hybrid` combines Qdrant vector search with BM25 over PostgreSQL chunk text. Set `RETRIEVAL_MODE=vector` to compare against the vector-only baseline in the evaluation dashboard.
- Set `LLM_PROVIDER=deepseek` with `DEEPSEEK_API_KEY` to use DeepSeek through its OpenAI-compatible API. The default DeepSeek model in this project is `deepseek-v4-flash`.
- PDFs, local databases, vector storage, logs, build output, and virtual environments are intentionally ignored.
- OCR, persistent chat history, hybrid BM25 retrieval, reranking, and evaluation dashboards are planned follow-up layers.
- `DOCUMENT_EXTRACTOR=docling` enables Docling-backed PDF ingestion. `DOCLING_DO_OCR=true` enables Docling OCR for scanned PDFs, which is slower and may require OCR runtime dependencies depending on the selected OCR engine.
- `DOCLING_DEVICE=cpu` is the default here because Docling's layout models can be memory-heavy on smaller GPUs. Change it deliberately if you want to test `cuda`.
- `DOCLING_FALLBACK_TO_PYPDF=true` keeps ingestion complete if Docling fails on some pages by filling missing page text from the lightweight extractor.
- The Docling batch-size settings default to `1` to favor stability over throughput on local hardware; raise them only after measuring memory headroom.
- `DOCLING_MAX_PAGES=15` means Docling is only used for smaller PDFs by default; larger PDFs automatically use `pypdf`.
