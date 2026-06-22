from typing import Any, Literal

from pydantic import BaseModel, Field


class EvidenceInput(BaseModel):
  title: str = ""
  url: str = ""
  content: str
  source_type: str = "web"


class Evidence(BaseModel):
  citation_id: str
  title: str
  url: str = ""
  source_type: str
  snippet: str
  content_hash: str


class ResearchRequest(BaseModel):
  topic: str
  language: str = "zh-CN"
  constraints: list[str] = Field(default_factory=list)
  sources: list[EvidenceInput] = Field(default_factory=list)
  use_dify: bool = True
  use_local_kb: bool = True
  kb_top_k: int = Field(default=5, ge=1, le=20)
  min_relevance_score: float = Field(default=0.1, ge=0, le=1)
  min_local_evidence: int = Field(default=3, ge=0, le=20)


class KnowledgeDocumentRequest(BaseModel):
  title: str
  content: str
  source_type: str = "local_file"
  url: str = ""
  metadata: dict[str, Any] = Field(default_factory=dict)
  chunk_size: int = Field(default=900, ge=200, le=4000)
  chunk_overlap: int = Field(default=120, ge=0, le=1000)


class KnowledgeDocument(BaseModel):
  chunk_id: str
  document_id: str
  title: str
  source_type: str
  url: str = ""
  chunk_index: int
  content: str
  embedding: list[float]
  metadata: dict[str, Any] = Field(default_factory=dict)


class KnowledgeDocumentResponse(BaseModel):
  document_id: str
  title: str
  chunks_added: int
  chunk_ids: list[str]


class KnowledgeSearchRequest(BaseModel):
  query: str
  top_k: int = Field(default=5, ge=1, le=20)
  min_score: float = Field(default=0.1, ge=0, le=1)


class KnowledgeSearchResult(BaseModel):
  chunk_id: str
  document_id: str
  title: str
  source_type: str
  url: str = ""
  chunk_index: int
  content: str
  score: float
  metadata: dict[str, Any] = Field(default_factory=dict)


class ResearchPlan(BaseModel):
  topic: str
  sections: list[str]
  sub_questions: list[str]
  information_gaps: list[str]


class QualityReport(BaseModel):
  score: float
  missing_sections: list[str]
  citation_count: int
  evidence_count: int
  recommendations: list[str]


class RetrievalReport(BaseModel):
  query: str
  use_local_kb: bool
  local_top_k: int
  min_relevance_score: float
  local_matches: list[KnowledgeSearchResult] = Field(default_factory=list)
  used_local_evidence_count: int = 0
  external_source_count: int = 0
  fallback_reason: str = ""


class ResearchTask(BaseModel):
  task_id: str
  status: Literal["completed", "failed"]
  topic: str
  report_markdown: str
  plan: ResearchPlan
  evidence: list[Evidence]
  quality: QualityReport
  retrieval: RetrievalReport | None = None
  raw_dify_response: dict[str, Any] = Field(default_factory=dict)
