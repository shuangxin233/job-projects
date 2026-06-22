import hashlib
import json
import math
import os
import re
from pathlib import Path
from typing import Any

from .models import (
  EvidenceInput,
  KnowledgeDocument,
  KnowledgeDocumentRequest,
  KnowledgeDocumentResponse,
  KnowledgeSearchResult,
)
from .research_pipeline import normalize_text


KNOWLEDGE_DIR = Path(__file__).resolve().parents[1] / "data" / "knowledge"
DEFAULT_STORE_PATH = KNOWLEDGE_DIR / "local_vector_store.json"
DEFAULT_CHROMA_PATH = KNOWLEDGE_DIR / "chroma"
EMBEDDING_DIMENSIONS = 384


def split_text_into_chunks(text: str, chunk_size: int = 900, overlap: int = 120) -> list[str]:
  normalized = normalize_text(text)
  if not normalized:
    return []
  if chunk_size <= 0:
    raise ValueError("chunk_size must be greater than 0.")
  if overlap < 0:
    raise ValueError("overlap must be greater than or equal to 0.")
  if overlap >= chunk_size:
    raise ValueError("overlap must be smaller than chunk_size.")

  chunks = []
  start = 0
  while start < len(normalized):
    end = min(start + chunk_size, len(normalized))
    if end < len(normalized):
      boundary = _find_sentence_boundary(normalized, start, end)
      if boundary > start:
        end = boundary
    chunk = normalized[start:end].strip()
    if chunk:
      chunks.append(chunk)
    if end >= len(normalized):
      break
    start = max(end - overlap, start + 1)
  return chunks


def _find_sentence_boundary(text: str, start: int, end: int) -> int:
  window = text[start:end]
  min_offset = int(len(window) * 0.55)
  candidates = [m.end() for m in re.finditer(r"[\u3002\uff01\uff1f.!?\uff1b;]\s*", window)]
  usable = [offset for offset in candidates if offset >= min_offset]
  return start + usable[-1] if usable else end


def embed_text(text: str, dimensions: int = EMBEDDING_DIMENSIONS) -> list[float]:
  vector = [0.0] * dimensions
  for token in _tokenize_for_embedding(text):
    digest = hashlib.sha256(token.encode("utf-8", errors="ignore")).digest()
    index = int.from_bytes(digest[:4], "big") % dimensions
    sign = 1.0 if digest[4] % 2 == 0 else -1.0
    vector[index] += sign
  return _normalize_vector(vector)


def _tokenize_for_embedding(text: str) -> list[str]:
  lowered = normalize_text(text).lower()
  tokens = re.findall(r"[a-z0-9_+#.-]+|[\u4e00-\u9fff]", lowered)
  if len(tokens) <= 1 and lowered:
    tokens = [lowered[i:i + 2] for i in range(max(len(lowered) - 1, 1))]
  return tokens


def _normalize_vector(vector: list[float]) -> list[float]:
  norm = math.sqrt(sum(value * value for value in vector))
  if norm == 0:
    return vector
  return [round(value / norm, 6) for value in vector]


def cosine_similarity(left: list[float], right: list[float]) -> float:
  if not left or not right or len(left) != len(right):
    return 0.0
  return sum(a * b for a, b in zip(left, right))


class JsonVectorStore:
  def __init__(self, path: Path = DEFAULT_STORE_PATH):
    self.path = path
    self.path.parent.mkdir(parents=True, exist_ok=True)

  def add_chunks(self, chunks: list[KnowledgeDocument]) -> None:
    records = self._load()
    existing = {record["chunk_id"] for record in records}
    for chunk in chunks:
      if chunk.chunk_id in existing:
        continue
      records.append(chunk.model_dump() if hasattr(chunk, "model_dump") else chunk.dict())
    self._save(records)

  def search(self, query: str, top_k: int = 5, min_score: float = 0.1) -> list[KnowledgeSearchResult]:
    query_vector = embed_text(query)
    results = []
    for record in self._load():
      score = cosine_similarity(query_vector, record.get("embedding", []))
      if score < min_score:
        continue
      results.append(self._to_search_result(record, score))
    return sorted(results, key=lambda item: item.score, reverse=True)[:top_k]

  def list_documents(self) -> list[dict[str, Any]]:
    summary: dict[str, dict[str, Any]] = {}
    for record in self._load():
      document_id = record["document_id"]
      item = summary.setdefault(document_id, {
        "document_id": document_id,
        "title": record["title"],
        "source_type": record["source_type"],
        "url": record.get("url", ""),
        "chunk_count": 0,
      })
      item["chunk_count"] += 1
    return sorted(summary.values(), key=lambda item: item["title"])

  def _load(self) -> list[dict[str, Any]]:
    if not self.path.exists():
      return []
    return json.loads(self.path.read_text(encoding="utf-8"))

  def _save(self, records: list[dict[str, Any]]) -> None:
    self.path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")

  def _to_search_result(self, record: dict[str, Any], score: float) -> KnowledgeSearchResult:
    return KnowledgeSearchResult(
      chunk_id=record["chunk_id"],
      document_id=record["document_id"],
      title=record["title"],
      source_type=record["source_type"],
      url=record.get("url", ""),
      chunk_index=record["chunk_index"],
      content=record["content"],
      score=round(score, 4),
      metadata=record.get("metadata", {}),
    )


class ChromaVectorStore:
  def __init__(self, path: Path = DEFAULT_CHROMA_PATH, collection_name: str = "project3_local_knowledge"):
    try:
      import chromadb
    except ImportError as exc:
      raise RuntimeError("chromadb is not installed.") from exc

    path.mkdir(parents=True, exist_ok=True)
    self.client = chromadb.PersistentClient(path=str(path))
    self.collection = self.client.get_or_create_collection(
      name=collection_name,
      metadata={"hnsw:space": "cosine"},
    )

  def add_chunks(self, chunks: list[KnowledgeDocument]) -> None:
    if not chunks:
      return
    self.collection.upsert(
      ids=[chunk.chunk_id for chunk in chunks],
      documents=[chunk.content for chunk in chunks],
      embeddings=[chunk.embedding for chunk in chunks],
      metadatas=[{
        "document_id": chunk.document_id,
        "title": chunk.title,
        "source_type": chunk.source_type,
        "url": chunk.url,
        "chunk_index": chunk.chunk_index,
        "metadata_json": json.dumps(chunk.metadata, ensure_ascii=False),
      } for chunk in chunks],
    )

  def search(self, query: str, top_k: int = 5, min_score: float = 0.1) -> list[KnowledgeSearchResult]:
    response = self.collection.query(
      query_embeddings=[embed_text(query)],
      n_results=top_k,
      include=["documents", "metadatas", "distances"],
    )
    results = []
    ids = response.get("ids", [[]])[0]
    documents = response.get("documents", [[]])[0]
    metadatas = response.get("metadatas", [[]])[0]
    distances = response.get("distances", [[]])[0]
    for chunk_id, content, metadata, distance in zip(ids, documents, metadatas, distances):
      score = max(0.0, 1.0 - float(distance))
      if score < min_score:
        continue
      results.append(KnowledgeSearchResult(
        chunk_id=chunk_id,
        document_id=metadata["document_id"],
        title=metadata["title"],
        source_type=metadata["source_type"],
        url=metadata.get("url", ""),
        chunk_index=int(metadata["chunk_index"]),
        content=content,
        score=round(score, 4),
        metadata=json.loads(metadata.get("metadata_json") or "{}"),
      ))
    return results

  def list_documents(self) -> list[dict[str, Any]]:
    response = self.collection.get(include=["metadatas"])
    summary: dict[str, dict[str, Any]] = {}
    for metadata in response.get("metadatas", []):
      document_id = metadata["document_id"]
      item = summary.setdefault(document_id, {
        "document_id": document_id,
        "title": metadata["title"],
        "source_type": metadata["source_type"],
        "url": metadata.get("url", ""),
        "chunk_count": 0,
      })
      item["chunk_count"] += 1
    return sorted(summary.values(), key=lambda item: item["title"])


def create_vector_store():
  backend = os.getenv("VECTOR_STORE_BACKEND", "json").lower()
  if backend == "chroma":
    return ChromaVectorStore()
  return JsonVectorStore()


class KnowledgeBase:
  def __init__(self):
    self.store = create_vector_store()

  def add_document(self, request: KnowledgeDocumentRequest) -> KnowledgeDocumentResponse:
    document_id = _stable_document_id(request.title, request.content)
    raw_chunks = split_text_into_chunks(
      request.content,
      chunk_size=request.chunk_size,
      overlap=request.chunk_overlap,
    )
    chunks = []
    for index, content in enumerate(raw_chunks):
      chunk_id = f"{document_id}-{index + 1}"
      chunks.append(KnowledgeDocument(
        chunk_id=chunk_id,
        document_id=document_id,
        title=request.title,
        source_type=request.source_type,
        url=request.url,
        chunk_index=index,
        content=content,
        embedding=embed_text(content),
        metadata=request.metadata,
      ))
    self.store.add_chunks(chunks)
    return KnowledgeDocumentResponse(
      document_id=document_id,
      title=request.title,
      chunks_added=len(chunks),
      chunk_ids=[chunk.chunk_id for chunk in chunks],
    )

  def search(self, query: str, top_k: int = 5, min_score: float = 0.1) -> list[KnowledgeSearchResult]:
    if not query.strip():
      return []
    return self.store.search(query, top_k=top_k, min_score=min_score)

  def list_documents(self) -> list[dict[str, Any]]:
    return self.store.list_documents()

  def matches_to_sources(self, matches: list[KnowledgeSearchResult]) -> list[EvidenceInput]:
    sources = []
    for match in matches:
      location = match.url or f"kb://{match.document_id}#chunk-{match.chunk_index + 1}"
      sources.append(EvidenceInput(
        title=f"Local KB: {match.title} chunk {match.chunk_index + 1}",
        url=location,
        content=match.content,
        source_type=match.source_type,
      ))
    return sources


def _stable_document_id(title: str, content: str) -> str:
  digest = hashlib.sha1(f"{title}\n{content}".encode("utf-8", errors="ignore")).hexdigest()
  return digest[:16]
