# Deep Research Backend

This backend productizes the Dify workflow. Dify still owns the workflow
orchestration, while this service owns task submission, evidence processing,
report storage, export, and quality checks.

## Run

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8010
```

Optional `.env`:

```env
DIFY_API_KEY=app-xxx
DIFY_WORKFLOW_URL=http://127.0.0.1/v1/workflows/run
DIFY_TIMEOUT_SECONDS=180
VECTOR_STORE_BACKEND=json
```

If Dify credentials are not configured, `/research` returns a local report draft
using the same evidence and quality pipeline. This keeps the project runnable
even before Dify is available.

`VECTOR_STORE_BACKEND=json` uses the built-in lightweight vector store under
`backend/data/knowledge/local_vector_store.json`. Set
`VECTOR_STORE_BACKEND=chroma` to use ChromaDB persistence under
`backend/data/knowledge/chroma`. Install the optional Chroma dependency first:

```bash
pip install -r requirements-chroma.txt
```

## Example

```bash
curl -X POST http://127.0.0.1:8010/research ^
  -H "Content-Type: application/json" ^
  -d "{\"topic\":\"AI coding tools competitive analysis\",\"sources\":[{\"title\":\"Source A\",\"url\":\"https://example.com\",\"content\":\"Evidence text about the market.\"}]}"
```

## API

- `POST /research`: create a research task.
- `POST /knowledge/documents`: add plain text or pre-extracted file text to the local knowledge base.
- `POST /knowledge/files`: upload `.txt`, `.md`, `.pdf`, or `.docx` into the local knowledge base.
- `POST /knowledge/search`: run similarity search over the local knowledge base.
- `GET /knowledge/documents`: list indexed local documents.
- `GET /tasks`: list saved tasks.
- `GET /tasks/{task_id}`: read a saved task.
- `GET /reports/{task_id}.md`: export Markdown report.

## Local Knowledge Base RAG

The backend now supports a local knowledge base retrieval pipeline:

```text
file or text
-> text extraction
-> chunking
-> embedding
-> vector storage
-> similarity search
-> Top-K local evidence
-> research report generation
```

The default embedding implementation is a deterministic hashing encoder. It is
small and local, so the demo runs without a remote embedding service. In a
production version, replace `embed_text()` in `app/knowledge_base.py` with an
embedding model such as `bge-small-zh`, `text-embedding-3-small`, or the Dify
knowledge-base embedding provider.

### Add A Text Document

```bash
curl -X POST http://127.0.0.1:8010/knowledge/documents ^
  -H "Content-Type: application/json" ^
  -d "{\"title\":\"Cursor notes\",\"content\":\"Cursor is an AI code editor focused on project-level coding assistance.\",\"source_type\":\"local_file\"}"
```

### Upload A File

```bash
curl -X POST http://127.0.0.1:8010/knowledge/files ^
  -F "file=@C:\path\to\report.pdf" ^
  -F "title=AI coding tools report"
```

### Search The Local Knowledge Base

```bash
curl -X POST http://127.0.0.1:8010/knowledge/search ^
  -H "Content-Type: application/json" ^
  -d "{\"query\":\"Cursor Claude Code Codex competitive analysis\",\"top_k\":5,\"min_score\":0.1}"
```

### Local-Knowledge-First Research

`POST /research` now searches the local knowledge base first. If it finds at
least `min_local_evidence` chunks, the report uses those local chunks as
evidence. If it finds too few chunks, the backend falls back to the request
`sources`, which can represent web-search results or manually supplied external
evidence.

```bash
curl -X POST http://127.0.0.1:8010/research ^
  -H "Content-Type: application/json" ^
  -d "{\"topic\":\"AI coding tools competitive analysis\",\"use_local_kb\":true,\"kb_top_k\":5,\"min_local_evidence\":3,\"sources\":[{\"title\":\"Web source\",\"url\":\"https://example.com\",\"content\":\"External evidence about the market.\"}]}"
```

## Added Capabilities

- Evidence cleaning and deduplication.
- Local file/text ingestion.
- Text chunking.
- Embedding vectorization.
- JSON vector store by default, with optional ChromaDB persistence.
- Similarity search and Top-K retrieval.
- Local-knowledge-first research with fallback request sources.
- Citation IDs such as `[S1]`.
- Research plan generation.
- Information gap detection.
- Report quality scoring.
- Persistent task storage.
