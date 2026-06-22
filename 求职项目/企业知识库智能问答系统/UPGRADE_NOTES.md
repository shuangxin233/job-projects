# Project 1 Upgrade Notes

## Scope

This project has been upgraded from a PDF-only RAG bot to a small knowledge-base
question-answering system.

## Improvements

1. Citation-aware answers
   - The chat API now returns `answer` and `sources`.
   - Each retrieved chunk carries `source_file`, `page`, `chunk_id`, retrieval channel, and scores.
   - The prompt asks the model to cite evidence with markers such as `[S1]`.

2. Hybrid retrieval
   - Vector retrieval and BM25 keyword retrieval are fused with Reciprocal Rank Fusion.
   - A lightweight lexical reranker is applied after RRF.
   - The Inspector view shows retrieval channel and scores for debugging.

3. More document formats
   - Supported uploads: PDF, TXT, Markdown, DOCX.
   - Source metadata is preserved through loading, splitting, retrieval, and generation.

4. Evaluation workflow
   - `server/evaluation/evaluate_rag.py` calls the running API and produces a Markdown report.
   - The report tracks source hit rate and citation marker rate.
   - `evaluation_questions.example.json` is the template for a project-specific test set.

## Demo Flow

1. Start the backend:

```bash
cd server
uvicorn main:app --reload
```

2. Start the frontend:

```bash
cd client
streamlit run app.py
```

3. Upload representative PDF/TXT/Markdown/DOCX files.
4. Ask a question and expand `Sources` to inspect citations.
5. Use the `Inspector` view to compare retrieval behavior.
6. Run the evaluation script after preparing `evaluation_questions.json`.
