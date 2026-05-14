# Local MVP

This is the first backend vertical slice for the Japanese Enterprise Knowledge Assistant.

It supports:

- PDF text extraction with page numbers
- Chunking
- Local `BAAI/bge-m3` embeddings
- Qdrant vector indexing
- Access-level filtering
- OpenAI answer generation
- Citation output

OCR, auth, Postgres persistence, frontend, hybrid BM25, reranking, and evaluation dashboards come after this slice is working.

## Requirements

- Docker Desktop
- Python 3.13 works for the current scaffold, but Python 3.11 or 3.12 remains safer for ML packages
- An OpenAI API key in `.env`
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
- `POST /api/ingest`
- `POST /api/chat`

## Current Smoke Test

Verified locally:

- Docker services: PostgreSQL, Qdrant, Redis
- CUDA PyTorch in `backend/.venv`
- GPU: NVIDIA GeForce RTX 4060
- `BAAI/bge-m3` embedding smoke test: 1024-dimensional normalized vector
- `jp_rag_1.pdf` indexed into Qdrant: 56 chunks
- Retrieval returned authorized citations
- Chat generation returned a cited Japanese answer through OpenAI
