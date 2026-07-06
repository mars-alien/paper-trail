# JEE & NEET Counselling RAG — Setup Guide

## Project Structure

```
counselling-rag/
├── backend/
│   ├── main.py              ← FastAPI app (start this)
│   ├── pdf_processor.py     ← PDF text extraction
│   ├── chunker.py           ← Section-aware chunking
│   ├── embedder.py          ← BAAI/bge-small-en-v1.5
│   ├── retriever.py         ← Hybrid BM25 + HNSW + reranking
│   ├── llm.py               ← Groq LLM (llama-3.3-70b)
│   ├── query_processor.py   ← Intent detection
│   ├── database.py          ← SQLite document tracker
│   └── requirements.txt
├── scripts/
│   ├── download_pdfs.py     ← Auto-download brochures
│   └── ingest.py            ← Process PDFs → Weaviate
├── data/
│   ├── josaa/               ← Put josaa_YYYY.pdf here
│   └── neet/                ← Put neet_YYYY.pdf here
├── frontend/
│   └── index.html           ← Open in browser
└── docker-compose.yml       ← Weaviate vector DB
```

---

## Step-by-Step Setup

### 1. Start Weaviate (Vector Database)
```bash
docker-compose up -d
```
Wait 10 seconds for Weaviate to be ready.

### 2. Install Python dependencies
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 3. Configure environment
```bash
copy .env.example .env
# Edit .env and add your Groq API key:
# GROQ_API_KEY=gsk_your_key_here
# Get free key at: https://console.groq.com
```

### 4. Start backend (creates Weaviate collection)
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```
Keep this running. You will see: `[startup] Models warmed up.`

### 5. Download PDF brochures
```bash
# Option A — Auto download (may fail if govt URLs changed)
python scripts/download_pdfs.py

# Option B — Manual download
# JoSAA: https://josaa.nic.in → Information Brochure (each year)
# NEET:  https://mcc.nic.in  → Information Bulletin (each year)
# Rename and place as:
#   data/josaa/josaa_2026.pdf
#   data/josaa/josaa_2025.pdf
#   data/josaa/josaa_2024.pdf
#   data/josaa/josaa_2023.pdf
#   data/josaa/josaa_2022.pdf
#   data/neet/neet_2026.pdf
#   data/neet/neet_2025.pdf
#   data/neet/neet_2024.pdf
#   data/neet/neet_2023.pdf
#   data/neet/neet_2022.pdf
```

### 6. Ingest PDFs into Weaviate
```bash
python scripts/ingest.py
```
This will:
- Extract text sections from each PDF
- Create ~1200-char overlapping chunks
- Embed with BAAI/bge-small-en-v1.5
- Store in Weaviate with year + source metadata

Ingestion takes ~2-5 minutes per PDF depending on size.

### 7. Open the frontend
```
Open frontend/index.html in your browser
```
Or serve it:
```bash
cd frontend
python -m http.server 3000
# Visit http://localhost:3000
```

---

## What Questions It Can Answer (Phase 1)

| Category | Example Questions |
|---|---|
| Process | "How does JoSAA counselling work step by step?" |
| Process | "How many rounds are there in JoSAA 2024?" |
| Eligibility | "Who is eligible for JoSAA counselling?" |
| Eligibility | "What is the age limit for NEET 2024?" |
| Documents | "What documents are needed for JoSAA reporting?" |
| Documents | "Is Aadhaar mandatory for NEET counselling?" |
| Compare | "What is the difference between AIQ and state quota?" |
| Compare | "Difference between slide, float, and freeze options?" |
| Rules | "What happens if I don't report after seat allotment?" |
| Rules | "Can I participate in JoSAA and state counselling both?" |

## Phase 2 (Not Yet Built)
- Opening/closing rank lookup per college, branch, category, year
- "Can I get CSE at NIT Trichy with OBC rank 5000?"

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/query` | SSE streaming answer |
| GET | `/documents` | List ingested PDFs |
| GET | `/starters` | Suggested questions |
| GET | `/health` | Health check |

### Query Request Body
```json
{
  "question": "What documents are required for JoSAA reporting?",
  "history":  [],
  "source":   "josaa",
  "year":     2024
}
```
Leave `source` and `year` as `null` to search all documents.
