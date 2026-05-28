# Local MVP

This is the first backend vertical slice for the Japanese Enterprise Knowledge Assistant.

It supports:

- PDF text extraction with page numbers
- Switchable PDF extraction with `pypdf` or `Docling`
- Sentence-aware chunking with whole-sentence overlap
- Local `BAAI/bge-m3` embeddings
- Qdrant vector indexing
- PostgreSQL document registry and ingestion job tracking
- Access-level filtering
- JWT login with `admin` and `user` roles
- OpenAI answer generation
- Citation output
- Admin retrieval evaluation dashboard

OCR, auth, persistent chat history, hybrid BM25, reranking, and evaluation dashboards come after this slice is working.

## Current Chunking

The current chunker is intentionally moderate:

- Works page by page so citations stay simple.
- Splits on Japanese and English sentence endings.
- Packs complete sentences up to the configured chunk size.
- Uses sentence overlap instead of raw character overlap.
- Falls back to hard splits only when one sentence is longer than the chunk limit.

This is more coherent than fixed character windows without adding section hierarchy or parent-child retrieval yet.

## Document Extraction

The ingestion layer supports two PDF extraction backends:

```text
DOCUMENT_EXTRACTOR=pypdf
DOCUMENT_EXTRACTOR=docling
```

Use `pypdf` for the fastest lightweight path. Use `docling` when you want richer PDF conversion and a path toward OCR/layout-aware ingestion.

For scanned PDFs:

```text
DOCUMENT_EXTRACTOR=docling
DOCLING_DO_OCR=true
DOCLING_DEVICE=cpu
DOCLING_FALLBACK_TO_PYPDF=true
DOCLING_LAYOUT_BATCH_SIZE=1
DOCLING_OCR_BATCH_SIZE=1
DOCLING_TABLE_BATCH_SIZE=1
DOCLING_MAX_PAGES=15
```

Docling OCR is slower than plain text extraction, so keep it disabled unless a document needs it. This project defaults Docling to CPU mode because the Docling layout pipeline can be memory-heavy on smaller GPUs; set `DOCLING_DEVICE=cuda` only when you want to test that path explicitly.
If Docling cannot process every page, the default fallback fills missing pages from `pypdf` so ingestion coverage stays complete.
Batch sizes default to `1` for stability. Higher values can improve throughput, but they also increase memory use.
By default, Docling is only used for PDFs with at most `15` pages. Larger PDFs automatically use `pypdf`, which matches the observed local stability profile.

## Requirements

- Docker Desktop
- Python 3.13 works for the current scaffold, but Python 3.11 or 3.12 remains safer for ML packages
- An OpenAI API key in `.env`
- Or a DeepSeek API key in `.env` with `LLM_PROVIDER=deepseek`
- `JWT_SECRET_KEY` plus bootstrap admin/user credentials in `.env`
- Optional `HF_TOKEN` in `.env` for authenticated Hugging Face model downloads

The embedding path uses `sentence-transformers` to load `BAAI/bge-m3`. If future ML packages fail on Python 3.13, create the virtual environment with Python 3.11/3.12.

## Start Local Services

```powershell
docker compose up -d
```

## Backend Setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

For RTX 4060 CUDA embeddings, install the CUDA PyTorch wheel inside the same venv:

```powershell
python -m pip install --upgrade --index-url https://download.pytorch.org/whl/cu126 torch
python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"
```

Start the backend from the project root:

```powershell
.\scripts\start_backend.ps1
```

The API will run at:

```text
http://127.0.0.1:8000
```

## Frontend Setup

From the project root:

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

Or use the project script:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start_frontend.ps1
```

The frontend will run at:

```text
http://127.0.0.1:3000
```

The frontend expects the FastAPI backend to be running at `http://127.0.0.1:8000`.

## Ingest A PDF

From the project root:

```powershell
.\scripts\ingest_pdf.ps1 -Path "jp_rag_1.pdf" -AccessLevel "public"
```

## Ask A Question

```powershell
.\scripts\chat.ps1 -Question "この文書は何について説明していますか？"
```

If Japanese output looks garbled in PowerShell, run:

```powershell
$env:PYTHONIOENCODING="utf-8"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

## API

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

## Development Checks

Install test dependencies once:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

Run the full local pre-push check from the project root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\test_project.ps1
```

The script runs:

- backend compile check
- backend unit tests with `pytest`
- frontend production build
- frontend Playwright E2E smoke test

## Retrieval Evaluation

Retrieval evaluation is local because the real PDFs are not committed to the repository.

```powershell
Copy-Item .\eval\questions.example.jsonl .\eval\questions.local.jsonl
cd backend
.\.venv\Scripts\python.exe ..\scripts\evaluate_retrieval.py --questions ..\eval\questions.local.jsonl --top-k 5
```

Edit `eval/questions.local.jsonl` with real gold questions and expected source pages before trusting the scores.
Qdrant must be running and the target documents must already be indexed.

## Current Smoke Test

Verified locally:

- Docker services: PostgreSQL, Qdrant, Redis
- CUDA PyTorch in `backend/.venv`
- GPU: NVIDIA GeForce RTX 4060
- `BAAI/bge-m3` embedding smoke test: 1024-dimensional normalized vector
- `jp_rag_1.pdf` indexed into Qdrant: 56 chunks
- Retrieval returned authorized citations
- Chat generation returned a cited Japanese answer through OpenAI
