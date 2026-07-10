# PaperTrail

**Paste news URLs. Ask questions. Get cited, streamed answers.**

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)
![Weaviate](https://img.shields.io/badge/Weaviate-Vector_DB-green)
![Groq](https://img.shields.io/badge/Groq-LLM_API-orange)
![License](https://img.shields.io/badge/License-MIT-blue)

---

## Demo

![PaperTrail Screenshot](docs/Application-Snapshot.png)

> Add any news article URL → ask questions → get a grounded, cited answer streamed in real time.

---

## Features

- **Paste & Ask** — drop in any news URL and start chatting immediately
- **Hybrid Search** — BM25 + dense vector retrieval via Weaviate for high recall
- **Cross-Encoder Reranking** — ms-marco-MiniLM-L-6-v2 reranks top 24 → top 6
- **SSE Streaming** — answers stream token-by-token via Server-Sent Events
- **Source Citations** — every answer links back to the exact article
- **Multi-Article Chat** — ingest multiple articles, filter by source in the sidebar
- **Intent Routing** — summary/comparison queries routed to a stronger model
- **Session Isolation** — fresh start on every server restart, no stale data

---

## How It Works

```
News URL ──► Scrape ──► Chunk ──► Embed ──► Weaviate
                                               │
Question ──► Embed ──► Hybrid Retrieve ──► Rerank ──► Groq LLM ──► Streamed Answer
```

| Step | Tool | Detail |
|------|------|--------|
| Scrape | trafilatura | Extracts clean article text from any news URL |
| Chunk | sentence-boundary | ~300 tokens / 1200 chars per chunk, with section labels |
| Embed | BAAI/bge-small-en-v1.5 (fastembed) | 384-dim dense vectors, ONNX Runtime |
| Store | Weaviate | HNSW (ef=128) + BM25 (k1=1.5, b=0.4) dual index |
| Retrieve | Hybrid | alpha=0.65 dense + 0.35 BM25, top 24 candidates |
| Diversify | custom | Max 3 chunks per article to prevent one doc flooding results |
| Rerank | ms-marco-MiniLM-L-6-v2 (fastembed) | Cross-encoder scores, keeps top 6 |
| Generate | Groq API | Llama 3.3 70B / DeepSeek-R1, SSE streaming |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + Vite + CSS Modules |
| Backend | FastAPI + Python 3.10+ |
| Vector DB | Weaviate (Docker) |
| Embeddings | BAAI/bge-small-en-v1.5 (fastembed / ONNX) |
| Reranker | ms-marco-MiniLM-L-6-v2 (fastembed / ONNX) |
| LLM | Groq API (Llama 3.3 70B + DeepSeek-R1) |
| Scraper | trafilatura |
| Metadata DB | SQLite |

---

## Project Structure

```
paper-trail/
├── backend/
│   ├── main.py            # FastAPI app, all endpoints
│   ├── scraper.py         # Article scraping with trafilatura
│   ├── chunker.py         # Sentence-boundary text chunking
│   ├── embedder.py        # BAAI/bge-small-en-v1.5 embeddings
│   ├── retriever.py       # Hybrid search + cross-encoder reranking
│   ├── llm.py             # Groq SSE streaming
│   ├── database.py        # SQLite article tracking
│   ├── query_processor.py # Intent detection + starter questions
│   ├── eval_ragas.py      # RAGAS-style LLM-as-judge evaluation
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Root layout, sidebar + chat
│   │   ├── components/
│   │   │   ├── Sidebar.jsx      # Article manager + URL ingest
│   │   │   ├── Message.jsx      # Chat bubbles with markdown
│   │   │   ├── InputBar.jsx     # Question input + send
│   │   │   ├── Welcome.jsx      # Empty state + starter cards
│   │   │   └── SourceChips.jsx  # Cited source links
│   │   ├── hooks/useChat.js     # SSE streaming hook
│   │   └── utils/markdown.js
│   ├── index.html
│   └── vite.config.js           # Proxies /api → localhost:8000
├── docker-compose.yml           # Weaviate vector database
└── docs/
    └── Application-Snapshot.png
```

---

## Prerequisites

- Python 3.10+
- Node.js 18+
- Docker Desktop
- Groq API key — free at [console.groq.com](https://console.groq.com)

---

## Setup

### 1. Start Weaviate

```bash
docker-compose up -d
```

Weaviate runs on `http://localhost:8080`. Data persists in a Docker volume.

### 2. Backend

```bash
cd backend
python -m venv .venv
```

**Activate (PowerShell):**
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.venv\Scripts\Activate.ps1
```

**Activate (Command Prompt):**
```cmd
.venv\Scripts\activate.bat
```

**Install & configure:**
```bash
pip install -r requirements.txt
cp .env.example .env   # then edit .env
```

`.env`:
```env
GROQ_API_KEY=your_groq_api_key_here
WEAVIATE_URL=http://localhost:8080
```

**Start:**
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**

---

## Usage

1. Paste one or more news article URLs in the **left sidebar**
2. Click **Add Articles** — articles are scraped, chunked, and indexed in seconds
3. Type any question in the input bar at the bottom
4. Get a **streamed, cited answer** with clickable source links
5. Use the starter question cards on the welcome screen for inspiration

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/ingest` | Scrape and index article URLs |
| `POST` | `/query` | Stream an SSE answer |
| `GET` | `/articles` | List all ingested articles |
| `DELETE` | `/articles/{doc_id}` | Remove an article |
| `GET` | `/starters` | Starter questions for the UI |
| `GET` | `/health` | Health check |

---

## Retrieval Pipeline

```
Query
  │
  ├─ embed_query()          BAAI/bge-small-en-v1.5, 384-dim
  │
  ├─ hybrid_retrieve()      BM25 (35%) + HNSW (65%), top 24
  │   ├─ BM25 weights: section^2, title^1.5, text^1
  │   └─ Weaviate HybridFusion.RANKED
  │
  ├─ diversify_hits()       max 3 chunks per article
  │
  └─ rerank_hits()          ms-marco-MiniLM-L-6-v2, keeps top 6
```

---

## Evaluation

Run the RAGAS-style evaluation (requires articles to be ingested first):

```bash
cd backend
python eval_ragas.py
```

Groq acts as the LLM judge across three metrics:

| Metric | What it measures |
|--------|-----------------|
| **Faithfulness** | Answer is grounded in retrieved chunks (no hallucination) |
| **Answer Relevancy** | Answer directly addresses the question |
| **Context Precision** | Retrieved chunks are relevant to the question |

Sample results (2 articles ingested):

```
Question                                   Faith  Relev   Prec
──────────────────────────────────────────────────────────────
Why did Sensex crash 1500 points?          1.00   1.00   0.83
Which stocks were buzzing during crash?    1.00   1.00   0.83
What happened to Kalyan Jewellers stock?   1.00   1.00   0.83
Why did Mumbai shut schools?               1.00   1.00   1.00

Overall RAG Score  ████████████████████  0.905
```

---

## Deployment

| Service | Platform |
|---------|----------|
| Frontend | Vercel |
| Backend | Render |
| Vector DB | Weaviate Cloud |

Set the following environment variables on Render:

```env
GROQ_API_KEY=...
WEAVIATE_URL=https://your-cluster.weaviate.network
WEAVIATE_API_KEY=...
```

Update `frontend/vite.config.js` proxy target to your Render backend URL for production builds.

---

## Stopping

```bash
# Stop Weaviate
docker-compose down

# Wipe all data (removes weaviate_data volume)
docker-compose down -v
```
