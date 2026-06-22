import hashlib
import re
from typing import Any, Iterable, List

from langchain_core.documents import Document

try:
  from langchain_community.retrievers import BM25Retriever
except Exception:  # pragma: no cover - optional dependency fallback
  BM25Retriever = None


def _tokenize(text: str) -> list[str]:
  tokens = re.findall(r"[\w]+", (text or "").lower(), flags=re.UNICODE)
  if tokens:
    return tokens
  return list((text or "").lower())


def _doc_key(doc: Document) -> str:
  metadata = doc.metadata or {}
  stable_parts = [
    str(metadata.get("source_file", "")),
    str(metadata.get("page", "")),
    str(metadata.get("chunk_id", "")),
  ]
  if any(stable_parts):
    return "|".join(stable_parts)
  return hashlib.sha1(doc.page_content.encode("utf-8", errors="ignore")).hexdigest()


def _clone_doc(doc: Document, **metadata_updates: Any) -> Document:
  metadata = dict(doc.metadata or {})
  metadata.update(metadata_updates)
  return Document(page_content=doc.page_content, metadata=metadata)


def fetch_all_documents(vectorstore) -> list[Document]:
  try:
    raw = vectorstore.get(include=["documents", "metadatas"])
  except Exception:
    raw = vectorstore._collection.get(include=["documents", "metadatas"])

  documents = raw.get("documents", []) or []
  metadatas = raw.get("metadatas", []) or [{} for _ in documents]
  docs = []
  for index, content in enumerate(documents):
    if not content:
      continue
    metadata = metadatas[index] if index < len(metadatas) and metadatas[index] else {}
    metadata = dict(metadata)
    metadata.setdefault("chunk_id", index)
    docs.append(Document(page_content=content, metadata=metadata))
  return docs


def vector_search(vectorstore, query: str, limit: int) -> list[Document]:
  try:
    scored = vectorstore.similarity_search_with_relevance_scores(query, k=limit)
    return [_clone_doc(doc, vector_score=score, retrieval_channel="vector") for doc, score in scored]
  except Exception:
    return [
      _clone_doc(doc, retrieval_channel="vector")
      for doc in vectorstore.similarity_search(query, k=limit)
    ]


def keyword_search(docs: list[Document], query: str, limit: int) -> list[Document]:
  if not docs:
    return []

  if BM25Retriever is not None:
    retriever = BM25Retriever.from_documents(docs)
    retriever.k = limit
    return [_clone_doc(doc, retrieval_channel="bm25") for doc in retriever.invoke(query)]

  query_terms = set(_tokenize(query))
  ranked = []
  for doc in docs:
    doc_terms = _tokenize(doc.page_content)
    if not doc_terms:
      continue
    overlap = sum(1 for term in doc_terms if term in query_terms)
    if overlap:
      ranked.append((_clone_doc(doc, keyword_score=overlap, retrieval_channel="keyword"), overlap))

  ranked.sort(key=lambda item: item[1], reverse=True)
  return [doc for doc, _ in ranked[:limit]]


def reciprocal_rank_fusion(result_groups: Iterable[list[Document]], rrf_k: int = 60) -> list[Document]:
  scores: dict[str, float] = {}
  docs_by_key: dict[str, Document] = {}
  channels_by_key: dict[str, set[str]] = {}

  for group in result_groups:
    for rank, doc in enumerate(group):
      key = _doc_key(doc)
      scores[key] = scores.get(key, 0.0) + 1.0 / (rrf_k + rank + 1)
      docs_by_key[key] = doc
      channels_by_key.setdefault(key, set()).add(str((doc.metadata or {}).get("retrieval_channel", "unknown")))

  ranked_keys = sorted(scores, key=scores.get, reverse=True)
  fused = []
  for key in ranked_keys:
    channels = sorted(channels_by_key.get(key, []))
    fused.append(_clone_doc(
      docs_by_key[key],
      rrf_score=round(scores[key], 6),
      retrieval_channel="+".join(channels),
    ))
  return fused


def lightweight_rerank(query: str, docs: list[Document]) -> list[Document]:
  query_terms = set(_tokenize(query))
  ranked = []
  for doc in docs:
    doc_terms = _tokenize(doc.page_content)
    lexical_overlap = len(query_terms.intersection(doc_terms)) / max(len(query_terms), 1)
    rrf_score = float((doc.metadata or {}).get("rrf_score", 0))
    rerank_score = rrf_score + lexical_overlap
    ranked.append((_clone_doc(doc, rerank_score=round(rerank_score, 6)), rerank_score))
  ranked.sort(key=lambda item: item[1], reverse=True)
  return [doc for doc, _ in ranked]


def hybrid_retrieve(vectorstore, query: str, top_k: int = 5) -> list[Document]:
  candidate_k = max(top_k * 3, 10)
  all_docs = fetch_all_documents(vectorstore)
  vector_docs = vector_search(vectorstore, query, candidate_k)
  keyword_docs = keyword_search(all_docs, query, candidate_k)
  fused = reciprocal_rank_fusion([vector_docs, keyword_docs])
  reranked = lightweight_rerank(query, fused)
  return reranked[:top_k]


def serialize_document(doc: Document) -> dict[str, Any]:
  metadata = dict(doc.metadata or {})
  return {
    "page_content": doc.page_content,
    "metadata": metadata,
    "source_file": metadata.get("source_file") or metadata.get("source"),
    "page": metadata.get("page"),
    "chunk_id": metadata.get("chunk_id"),
    "retrieval_channel": metadata.get("retrieval_channel"),
    "rrf_score": metadata.get("rrf_score"),
    "rerank_score": metadata.get("rerank_score"),
  }


def format_context(docs: list[Document]) -> str:
  context_blocks = []
  for index, doc in enumerate(docs, start=1):
    metadata = doc.metadata or {}
    source = metadata.get("source_file") or metadata.get("source") or "unknown"
    page = metadata.get("page")
    page_label = f", page {page + 1}" if isinstance(page, int) else ""
    context_blocks.append(
      f"[S{index}] Source: {source}{page_label}\n{doc.page_content}"
    )
  return "\n\n".join(context_blocks)


def build_sources(docs: list[Document]) -> list[dict[str, Any]]:
  sources = []
  for index, doc in enumerate(docs, start=1):
    item = serialize_document(doc)
    item["citation_id"] = f"S{index}"
    item["preview"] = doc.page_content[:500]
    sources.append(item)
  return sources
