import os
from pathlib import Path
import aiofiles

from typing import List
from fastapi import UploadFile

from langchain_core.documents import Document
from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader, TextLoader
from langchain_text_splitters import TokenTextSplitter

from config.settings import TEMPFILE_UPLOAD_DIRECTORY
from utils.logger import logger


SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".markdown", ".docx"}


def validate_document(file: UploadFile, max_size_mb: int = 200):
  suffix = Path(file.filename or "").suffix.lower()
  if suffix not in SUPPORTED_EXTENSIONS:
    supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
    logger.warning(f"Invalid file type: {file.filename}")
    raise ValueError(f"{file.filename} is not supported. Supported types: {supported}.")

  file_size_mb = len(file.file.read()) / (1024 * 1024)
  file.file.seek(0)

  if file_size_mb > max_size_mb:
    logger.warning(f"File too large: {file.filename} ({file_size_mb:.2f} MB)")
    raise ValueError(f"PDF file size exceeds the maximum allowed size of {max_size_mb} MB.")

  logger.debug(f"Validated document: {file.filename} ({file_size_mb:.2f} MB)")

async def save_uploaded_file(files: List[UploadFile]) -> List[str]:
  os.makedirs(TEMPFILE_UPLOAD_DIRECTORY, exist_ok=True)
  file_paths = []

  for file in files:
    validate_document(file)
    file_path = os.path.join(TEMPFILE_UPLOAD_DIRECTORY, file.filename)
    async with aiofiles.open(file_path, "wb") as f:
      content = await file.read()
      await f.write(content)
    file_paths.append(file_path)
    logger.debug(f"Saved uploaded file: {file.filename} to {file_path}")

  return file_paths


def _loader_for_path(file_path: str):
  suffix = Path(file_path).suffix.lower()
  if suffix == ".pdf":
    return PyPDFLoader(file_path)
  if suffix in {".txt", ".md", ".markdown"}:
    return TextLoader(file_path, encoding="utf-8", autodetect_encoding=True)
  if suffix == ".docx":
    return Docx2txtLoader(file_path)
  raise ValueError(f"Unsupported document type: {suffix}")


def _normalize_metadata(doc: Document, file_path: str, index: int) -> Document:
  path = Path(file_path)
  metadata = dict(doc.metadata or {})
  metadata.update({
    "source": str(path),
    "source_file": path.name,
    "file_type": path.suffix.lower().lstrip("."),
    "page": metadata.get("page"),
    "loader_index": index,
  })
  return Document(page_content=doc.page_content, metadata=metadata)


def load_documents_from_paths(file_paths: List[str]):
  docs = []
  for file_path in file_paths:
    loader = _loader_for_path(file_path)
    loaded = loader.load()
    loaded = [_normalize_metadata(doc, file_path, idx) for idx, doc in enumerate(loaded)]
    logger.debug(f"Loaded {len(loaded)} documents from {file_path}")
    docs.extend(loaded)

  return docs

def split_documents_to_chunks(docs) -> List[Document]:
  text_splitter = TokenTextSplitter(chunk_size=500, chunk_overlap=50)
  chunks = text_splitter.split_documents(docs)
  for idx, chunk in enumerate(chunks):
    chunk.metadata["chunk_id"] = idx
    chunk.metadata["chunk_chars"] = len(chunk.page_content)
  logger.debug(f"Split {len(docs)} docs into {len(chunks)} chunks")
  return chunks
