# Japanese Enterprise Knowledge Assistant
<img width="1906" height="915" alt="image" src="https://github.com/user-attachments/assets/81227914-93b5-4c77-9055-698ac880803d" />

A local-first enterprise RAG web app for answering questions from Japanese business documents with citations. The project is designed as a production-shaped AI engineering portfolio build: document ingestion, local multilingual embeddings, vector retrieval, role/access filtering hooks, OpenAI answer generation, and a usable retro RPG styled frontend.

The current MVP indexes local Japanese PDF documents, stores chunk vectors in Qdrant, retrieves relevant passages by access level, and generates cited answers through an external LLM API.

## What The App Does

- Extracts text from Japanese PDF documents while preserving page numbers.
- Splits documents into retrievable chunks.
- Generates local embeddings with `BAAI/bge-m3`.
- Stores vectors and metadata in Qdrant.
- Answers user questions using retrieved context and OpenAI.
- Shows source citations with document name, page number, excerpt, and retrieval score.
- Provides a themed web UI with document indexing, chat, access-level selection, and citation panels.

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

AI / Retrieval:

- Local embeddings: `BAAI/bge-m3`
- Embedding runtime: `sentence-transformers`
- GPU acceleration: PyTorch CUDA, tested with RTX 4060
- Vector database: Qdrant
- LLM provider: OpenAI

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
HF_TOKEN=
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
- `POST /api/ingest`
- `POST /api/chat`

## Notes

- Real API keys belong only in `.env`.
- PDFs, local databases, vector storage, logs, build output, and virtual environments are intentionally ignored.
- OCR, authentication UI, persistent chat history, hybrid BM25 retrieval, reranking, and evaluation dashboards are planned follow-up layers.

