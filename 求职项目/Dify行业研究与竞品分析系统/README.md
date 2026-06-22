# Deep Researcher On Dify

This project reproduces a Deep Research style workflow on Dify and extends it
into an interview-ready research-report generation system.

## Positioning

The system is designed for:

- industry research
- competitive analysis
- topic investigation
- structured Markdown report generation

Dify is responsible for workflow orchestration. The added FastAPI backend is
responsible for task submission, local knowledge-base retrieval, evidence
cleaning, report persistence, export, and evaluation.

## Core Workflow

```text
User topic
-> clarification / constraints
-> research plan
-> local knowledge-base retrieval
-> fallback external evidence collection
-> evidence cleaning and deduplication
-> information gap check
-> section-by-section report generation
-> citation and quality review
-> Markdown export
```

## Main Files

- `Deep Researcher On Dify .yml`: Dify workflow DSL.
- `Deep Researcher On Dify - Powered by Dify.pdf`: original run example.
- `backend/`: FastAPI productization layer.
- `evaluation/`: report evaluation scripts and fixed test topics.
- `DIFY_WORKFLOW_UPGRADE_CHECKLIST.md`: changes to apply inside Dify.
- `UPGRADE_NOTES.md`: summary of implemented improvements.

## Backend Demo

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
```

If Dify is not configured, the backend still returns a local draft report using
the same evidence and quality-control pipeline.

### Local Knowledge Base RAG

The backend supports a local-knowledge-first RAG path:

```text
upload local file / add text
-> extract text
-> split into chunks
-> create embeddings
-> store vectors in JSON or ChromaDB
-> retrieve Top-K similar chunks
-> use local chunks as report evidence
-> if local evidence is insufficient, add request sources as fallback evidence
```

Default storage is a lightweight local JSON vector store. Set
`VECTOR_STORE_BACKEND=chroma` to use ChromaDB persistence.

## Evaluation

```bash
python evaluation/evaluate_reports.py
```

The evaluator checks:

- required section coverage
- citation marker count
- pass/fail status per generated report

## Interview Highlights

- Dify Workflow orchestration for multi-step AI applications.
- Agent-style research planning and information gap checking.
- Local file/text knowledge base with chunking, embeddings, vector storage, and Top-K retrieval.
- Local-knowledge-first RAG with fallback external/request sources when evidence is insufficient.
- Search result cleaning, deduplication, and evidence register construction.
- Citation-aware report generation with `[S1]`, `[S2]` evidence markers.
- FastAPI wrapper for task management and Markdown export.
- Evaluation workflow for report completeness and citation behavior.

## License

LGPL-3.0, following the original workflow project.
