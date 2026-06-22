from io import BytesIO
from pathlib import Path

from fastapi import UploadFile


async def load_upload_text(file: UploadFile) -> str:
  content = await file.read()
  suffix = Path(file.filename or "").suffix.lower()
  if suffix == ".pdf":
    return _load_pdf(content)
  if suffix == ".docx":
    return _load_docx(content)
  return _decode_text(content)


def _load_pdf(content: bytes) -> str:
  try:
    from pypdf import PdfReader
  except ImportError as exc:
    raise RuntimeError("Install pypdf to ingest PDF files.") from exc

  reader = PdfReader(BytesIO(content))
  pages = [page.extract_text() or "" for page in reader.pages]
  return "\n\n".join(page for page in pages if page.strip())


def _load_docx(content: bytes) -> str:
  try:
    from docx import Document
  except ImportError as exc:
    raise RuntimeError("Install python-docx to ingest DOCX files.") from exc

  document = Document(BytesIO(content))
  paragraphs = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]
  return "\n".join(paragraphs)


def _decode_text(content: bytes) -> str:
  for encoding in ("utf-8", "utf-8-sig", "gb18030"):
    try:
      return content.decode(encoding)
    except UnicodeDecodeError:
      continue
  return content.decode("utf-8", errors="ignore")
