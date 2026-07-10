 # PaperTrail

A RAG (Retrieval-Augmented Generation) web app that lets you paste news article URLs, then ask questions and get cited, streamed answers grounded in those articles.

---

## How It Works

```
News URL → Scrape → Chunk → Embed → Weaviate
Question → Embed → Hybrid Retrieve → Rerank → Groq LLM → Streamed Answer
```

1. **Scrape** — `trafilatura` extracts clean article text from any news URL
2. **Chunk** — Article is split into overlapping sections
3. **Embed** — `BAAI/bge-small-en-v1.5` generates dense vectors
4. **Store** — Weaviate stores chunks with both BM25 and HNSW indexes
5. **Retrieve** — Hybrid search (65% dense + 35% BM25) returns top 24 candidates
6. **Rerank** — `ms-marco-MiniLM-L-6-v2` cross-encoder reranks to top 6
7. **Generate** — Groq LLM streams a cited answer back via SSE

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite + CSS Modules |
| Backend | FastAPI + Python |
| Vector DB | Weaviate (Docker) |
| Embeddings | BAAI/bge-small-en-v1.5 (sentence-transformers) |
| Reranker | ms-marco-MiniLM-L-6-v2 (cross-encoder) |
| LLM | Groq API |
| Scraper | trafilatura |

---

## Project Structure

```
paper-trail/
├── backend/
│   ├── main.py            # FastAPI app, all endpoints
│   ├── scraper.py         # Article scraping with trafilatura
│   ├── chunker.py         # Text chunking
│   ├── embedder.py        # Sentence-transformer embeddings
│   ├── retriever.py       # Hybrid search + cross-encoder reranking
│   ├── llm.py             # Groq streaming
│   ├── database.py        # SQLite article tracking
│   ├── query_processor.py # Intent detection + starter questions
│   ├── eval_ragas.py      # RAGAS-style LLM-as-judge evaluation
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── Sidebar.jsx      # Article manager + URL ingest
│   │   │   ├── Message.jsx      # Chat messages with markdown
│   │   │   ├── InputBar.jsx     # Question input
│   │   │   ├── Welcome.jsx      # Empty state + starter questions
│   │   │   └── SourceChips.jsx  # Cited sources display
│   │   ├── hooks/useChat.js     # SSE streaming hook
│   │   └── utils/
│   ├── index.html
│   └── vite.config.js           # Proxies /api → localhost:8000
├── docker-compose.yml           # Weaviate vector database
└── README.md
```

---

## Prerequisites

- Python 3.10+
- Node.js 18+
- Docker Desktop
- Groq API key — get one free at [console.groq.com](https://console.groq.com)

---

## Setup

### 1. Start Weaviate (Vector Database)

```bash
docker-compose up -d
```

Weaviate runs on `http://localhost:8080`. Data persists in a Docker volume.

### 2. Backend

```bash
cd backend
python -m venv .venv
```

**Activate the venv:**

- PowerShell:
  ```powershell
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
  .venv\Scripts\Activate.ps1
  ```
- Command Prompt:
  ```cmd
  .venv\Scripts\activate.bat
  ```

**Install dependencies:**

```bash
pip install -r requirements.txt
```

**Configure environment:**

```bash
cp .env.example .env
```

Edit `.env`:

```env
GROQ_API_KEY=your_groq_api_key_here
WEAVIATE_URL=http://localhost:8080
```

**Start the backend:**

```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Backend runs on `http://localhost:8000`.

### 3. Frontend

Open a new terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:5173`.

---

## Usage

1. Open `http://localhost:5173`
2. Paste one or more news article URLs in the left sidebar (one per line)
3. Click **Add Articles** — articles are scraped, chunked, and indexed
4. Ask any question in the input bar
5. Get a streamed, cited answer with source links

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/ingest` | Scrape and index article URLs |
| `POST` | `/query` | Stream an answer (SSE) |
| `GET` | `/articles` | List all ingested articles |
| `DELETE` | `/articles/{doc_id}` | Remove an article |
| `GET` | `/starters` | Starter questions for the UI |
| `GET` | `/health` | Health check |

---

## Retrieval Pipeline Details

- **Hybrid search**: `alpha=0.65` (65% dense HNSW + 35% BM25)
- **BM25 field weights**: `section^2`, `title^1.5`, `text^1`
- **Diversification**: max 3 chunks per article before reranking
- **Cross-encoder reranking**: `ms-marco-MiniLM-L-6-v2`, keeps top 6
- **Context window**: last 10 conversation turns sent as history

---

## Evaluation

Run the RAGAS-style evaluation (requires articles to be ingested first):

```bash
cd backend
python eval_ragas.py
```

Metrics evaluated using Groq as LLM judge:
- **Faithfulness** — answer is grounded in retrieved context
- **Answer Relevancy** — answer addresses the question
- **Context Precision** — retrieved chunks are relevant

---

## Stopping the App

```bash
# Stop Weaviate
docker-compose down

# Deactivate venv (PowerShell)
deactivate
```

To wipe all stored articles and start fresh:

```bash
docker-compose down -v   # removes the weaviate_data volume
```
