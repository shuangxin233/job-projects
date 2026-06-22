# Project 3 Upgrade Notes

## Scope

The original project is a Dify Deep Research workflow. It has been extended
with a productization layer and evaluation workflow.

## Improvements

1. Citation and source evidence
   - Evidence items are normalized into an evidence register.
   - Each source receives a citation ID such as `[S1]`.
   - Report prompts should cite these IDs and expose a final references section.

2. Local knowledge-base RAG
   - Users can add plain text or upload `.txt`, `.md`, `.pdf`, and `.docx`
     files into a local knowledge base.
   - Documents are split into overlapping chunks.
   - Chunks are embedded and stored in a local vector store.
   - The backend supports Top-K similarity search.
   - Research tasks search the local knowledge base first. If local evidence is
     insufficient, request `sources` are used as fallback external evidence.
   - The default store is JSON for easy demos; `VECTOR_STORE_BACKEND=chroma`
     enables ChromaDB persistence.

3. Search result processing
   - Search/local knowledge results are cleaned, deduplicated, truncated, and
     stored before report generation.
   - This separates evidence preparation from report writing.

4. Agent planning and quality control
   - The backend generates a research plan.
   - It detects information gaps before final report generation.
   - It scores the final report for section coverage, evidence count, and citation use.

5. Productized backend
   - `backend/` exposes a FastAPI service around the Dify workflow.
   - It supports local knowledge ingestion, task submission, task history,
     Markdown export, and local fallback drafts.

6. Evaluation
   - `evaluation/topics.json` defines fixed test topics and expected sections.
   - `evaluation/evaluate_reports.py` checks generated reports for section coverage and citations.

## Recommended Demo

1. Import `Deep Researcher On Dify .yml` into Dify.
2. Apply `DIFY_WORKFLOW_UPGRADE_CHECKLIST.md`.
3. Start the backend:

```bash
cd backend
uvicorn app.main:app --reload --port 8010
```

4. Add local documents through `/knowledge/documents` or `/knowledge/files`.
5. Verify Top-K retrieval through `/knowledge/search`.
6. Submit a research task through `/research`.
7. Export the Markdown report with `/reports/{task_id}.md`.
8. Run `python evaluation/evaluate_reports.py`.
