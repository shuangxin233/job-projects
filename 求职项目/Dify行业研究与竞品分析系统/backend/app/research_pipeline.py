import hashlib
import re

from .models import Evidence, EvidenceInput, QualityReport, ResearchPlan


REPORT_SECTIONS = [
  "Executive Summary",
  "Industry Background",
  "Market Size And Trends",
  "Competitive Landscape",
  "User Pain Points",
  "Business Models",
  "Risks And Opportunities",
  "Conclusion And Recommendations",
]


def normalize_text(text: str) -> str:
  text = re.sub(r"\s+", " ", text or "").strip()
  return text


def clean_and_dedupe_evidence(items: list[EvidenceInput], max_items: int = 20) -> list[Evidence]:
  seen = set()
  evidence = []
  for item in items:
    content = normalize_text(item.content)
    if not content:
      continue

    key_source = item.url or content[:500]
    content_hash = hashlib.sha1(key_source.encode("utf-8", errors="ignore")).hexdigest()
    if content_hash in seen:
      continue
    seen.add(content_hash)

    citation_id = f"S{len(evidence) + 1}"
    evidence.append(Evidence(
      citation_id=citation_id,
      title=normalize_text(item.title) or f"Evidence {len(evidence) + 1}",
      url=item.url,
      source_type=item.source_type,
      snippet=content[:700],
      content_hash=content_hash,
    ))
    if len(evidence) >= max_items:
      break
  return evidence


def build_research_plan(topic: str, evidence: list[Evidence]) -> ResearchPlan:
  sub_questions = [
    f"What is the current status of {topic}?",
    f"Who are the main players related to {topic}?",
    f"What user pain points and business opportunities exist in {topic}?",
    f"What risks, constraints, and recommendations should be considered for {topic}?",
  ]
  gaps = []
  if len(evidence) < 3:
    gaps.append("Need at least three independent evidence sources.")
  if not any(source.url for source in evidence):
    gaps.append("Need source URLs for citation verification.")
  return ResearchPlan(
    topic=topic,
    sections=REPORT_SECTIONS,
    sub_questions=sub_questions,
    information_gaps=gaps,
  )


def format_evidence_context(evidence: list[Evidence]) -> str:
  lines = []
  for source in evidence:
    location = f" ({source.url})" if source.url else ""
    lines.append(f"[{source.citation_id}] {source.title}{location}: {source.snippet}")
  return "\n".join(lines)


def build_local_report_draft(topic: str, plan: ResearchPlan, evidence: list[Evidence]) -> str:
  context = format_evidence_context(evidence) or "No external evidence was provided."
  sections = [
    f"# {topic} Research Report",
    "",
    "## Executive Summary",
    f"This draft summarizes the research topic `{topic}` and should be refined by the Dify workflow. Evidence available: {len(evidence)} sources.",
    "",
    "## Evidence Register",
    context,
    "",
  ]
  for section in plan.sections[1:]:
    citation = f" [{evidence[0].citation_id}]" if evidence else ""
    sections.extend([
      f"## {section}",
      f"Draft content for {section}. Replace this with Dify-generated analysis grounded in the evidence register.{citation}",
      "",
    ])
  return "\n".join(sections)


def extract_report_from_dify(raw_response: dict, fallback: str) -> str:
  data = raw_response.get("data") or {}
  outputs = data.get("outputs") or raw_response.get("outputs") or {}
  for key in ("report", "answer", "text", "markdown", "result"):
    value = outputs.get(key)
    if isinstance(value, str) and value.strip():
      return value
  answer = raw_response.get("answer")
  if isinstance(answer, str) and answer.strip():
    return answer
  return fallback


def evaluate_report_quality(report_markdown: str, evidence: list[Evidence]) -> QualityReport:
  missing_sections = [section for section in REPORT_SECTIONS if section not in report_markdown]
  citation_count = len(re.findall(r"\[S\d+\]", report_markdown))
  recommendations = []
  if missing_sections:
    recommendations.append("Regenerate or patch missing report sections.")
  if evidence and citation_count == 0:
    recommendations.append("Add citation markers linked to the evidence register.")
  if len(evidence) < 3:
    recommendations.append("Collect more independent evidence before final delivery.")

  section_score = 1 - (len(missing_sections) / len(REPORT_SECTIONS))
  citation_score = 1 if citation_count > 0 or not evidence else 0
  evidence_score = min(len(evidence) / 5, 1)
  score = round((section_score * 0.45) + (citation_score * 0.35) + (evidence_score * 0.20), 3)

  return QualityReport(
    score=score,
    missing_sections=missing_sections,
    citation_count=citation_count,
    evidence_count=len(evidence),
    recommendations=recommendations,
  )
