import uuid

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse

from .document_loader import load_upload_text
from .dify_client import DifyClient
from .knowledge_base import KnowledgeBase
from .models import (
  KnowledgeDocumentRequest,
  KnowledgeDocumentResponse,
  KnowledgeSearchRequest,
  KnowledgeSearchResult,
  ResearchRequest,
  ResearchTask,
  RetrievalReport,
)
from .research_pipeline import (
  build_local_report_draft,
  build_research_plan,
  clean_and_dedupe_evidence,
  evaluate_report_quality,
  extract_report_from_dify,
  format_evidence_context,
)
from .storage import list_tasks, load_task, save_task


load_dotenv()

app = FastAPI(title="Deep Research Workflow Backend")
dify_client = DifyClient()
knowledge_base = KnowledgeBase()


@app.get("/health")
def health():
  return {
    "status": "ok",
    "dify_configured": dify_client.configured,
    "knowledge_documents": len(knowledge_base.list_documents()),
  }


@app.post("/knowledge/documents", response_model=KnowledgeDocumentResponse)
def add_knowledge_document(request: KnowledgeDocumentRequest):
  if request.chunk_overlap >= request.chunk_size:
    raise HTTPException(status_code=400, detail="chunk_overlap must be smaller than chunk_size.")
  if not request.content.strip():
    raise HTTPException(status_code=400, detail="Document content cannot be empty.")
  return knowledge_base.add_document(request)


@app.post("/knowledge/files", response_model=KnowledgeDocumentResponse)
async def add_knowledge_file(
  file: UploadFile = File(...),
  title: str = Form(""),
  source_type: str = Form("local_file"),
  url: str = Form(""),
  chunk_size: int = Form(900),
  chunk_overlap: int = Form(120),
):
  try:
    content = await load_upload_text(file)
  except RuntimeError as exc:
    raise HTTPException(status_code=400, detail=str(exc)) from exc

  request = KnowledgeDocumentRequest(
    title=title or file.filename or "Uploaded document",
    content=content,
    source_type=source_type,
    url=url,
    metadata={"filename": file.filename or ""},
    chunk_size=chunk_size,
    chunk_overlap=chunk_overlap,
  )
  return add_knowledge_document(request)


@app.get("/knowledge/documents")
def list_knowledge_documents():
  return knowledge_base.list_documents()


@app.post("/knowledge/search", response_model=list[KnowledgeSearchResult])
def search_knowledge(request: KnowledgeSearchRequest):
  return knowledge_base.search(
    request.query,
    top_k=request.top_k,
    min_score=request.min_score,
  )


@app.post("/research", response_model=ResearchTask)
async def create_research_task(request: ResearchRequest):
  task_id = str(uuid.uuid4())
  retrieval = build_retrieval_report(request)
  research_sources = select_research_sources(request, retrieval)
  evidence = clean_and_dedupe_evidence(research_sources)
  plan = build_research_plan(request.topic, evidence)
  fallback_report = build_local_report_draft(request.topic, plan, evidence)
  raw_dify_response = {}

  if request.use_dify and dify_client.configured:
    raw_dify_response = await dify_client.run_workflow({
      "topic": request.topic,
      "language": request.language,
      "constraints": "\n".join(request.constraints),
      "research_plan": "\n".join(plan.sub_questions),
      "evidence_context": format_evidence_context(evidence),
    })

  report = extract_report_from_dify(raw_dify_response, fallback_report)
  quality = evaluate_report_quality(report, evidence)

  task = ResearchTask(
    task_id=task_id,
    status="completed",
    topic=request.topic,
    report_markdown=report,
    plan=plan,
    evidence=evidence,
    quality=quality,
    retrieval=retrieval,
    raw_dify_response=raw_dify_response,
  )
  save_task(task)
  return task


@app.get("/tasks")
def get_tasks():
  return list_tasks()


@app.get("/tasks/{task_id}", response_model=ResearchTask)
def get_task(task_id: str):
  try:
    return load_task(task_id)
  except FileNotFoundError as exc:
    raise HTTPException(status_code=404, detail="Task not found.") from exc


@app.get("/reports/{task_id}.md", response_class=PlainTextResponse)
def export_report(task_id: str):
  try:
    return load_task(task_id).report_markdown
  except FileNotFoundError as exc:
    raise HTTPException(status_code=404, detail="Task not found.") from exc


def build_retrieval_query(request: ResearchRequest) -> str:
  parts = [request.topic, *request.constraints]
  return "\n".join(part for part in parts if part.strip())


def build_retrieval_report(request: ResearchRequest) -> RetrievalReport:
  query = build_retrieval_query(request)
  local_matches = []
  fallback_reason = ""
  if request.use_local_kb:
    local_matches = knowledge_base.search(
      query,
      top_k=request.kb_top_k,
      min_score=request.min_relevance_score,
    )
    if len(local_matches) < request.min_local_evidence:
      fallback_reason = (
        "Local KB returned fewer matches than min_local_evidence; "
        "request sources are used as fallback evidence."
      )
  return RetrievalReport(
    query=query,
    use_local_kb=request.use_local_kb,
    local_top_k=request.kb_top_k,
    min_relevance_score=request.min_relevance_score,
    local_matches=local_matches,
    used_local_evidence_count=len(local_matches),
    external_source_count=len(request.sources),
    fallback_reason=fallback_reason,
  )


def select_research_sources(request: ResearchRequest, retrieval: RetrievalReport):
  local_sources = knowledge_base.matches_to_sources(retrieval.local_matches)
  if not request.use_local_kb:
    return request.sources
  if len(local_sources) >= request.min_local_evidence:
    return local_sources
  return local_sources + request.sources
