# Dify Workflow Upgrade Checklist

Apply these changes inside the imported `Deep Researcher On Dify .yml` workflow.

## Citation And Evidence

- Add a retrieval/evidence register variable named `evidence_context`.
- Require every report section prompt to cite evidence with `[S1]`, `[S2]`, etc.
- Add a final `References` section that maps citation IDs to source title and URL.
- If a section has no evidence, force the model to write `Evidence missing` instead
  of inventing facts.

## Search Result Processing

- Insert a cleaning step after each web/local search node:
  - normalize whitespace
  - remove duplicate URLs
  - keep title, URL, source type, and snippet
  - truncate long pages before generation
- Save cleaned evidence into a temporary evidence register before report writing.

## Local Knowledge Base RAG

- Use the FastAPI backend to ingest local files through `/knowledge/files` or
  extracted text through `/knowledge/documents`.
- Use `/knowledge/search` to retrieve Top-K local chunks before report writing.
- Treat local chunks as primary evidence when enough matches are available.
- Only add web/search evidence when local knowledge evidence is insufficient.
- Pass the merged evidence register into Dify as `evidence_context`.
- Require section prompts to prefer `evidence_context` over unsupported model memory.

## Agent Behavior

- Add a `Research Plan` node before subtopic generation.
- Add an `Information Gap Check` node after first retrieval.
- Add a conditional branch:
  - enough evidence: continue to section generation
  - missing evidence: run one more targeted retrieval
- Add a `Quality Self Review` node before final answer.
- Regenerate sections that fail citation or completeness checks.

## Productization

- Call the workflow through the FastAPI backend in `backend/`.
- Store reports by `task_id`.
- Export final Markdown through `/reports/{task_id}.md`.
- Use `evaluation/evaluate_reports.py` to check section coverage and citations.
