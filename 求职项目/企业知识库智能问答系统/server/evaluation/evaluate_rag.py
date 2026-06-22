import argparse
import json
from datetime import datetime
from pathlib import Path

import requests


def load_questions(path: Path) -> list[dict]:
  with path.open("r", encoding="utf-8") as f:
    return json.load(f)


def call_chat(api_url: str, provider: str, model: str, question: str, top_k: int) -> dict:
  response = requests.post(
    f"{api_url.rstrip('/')}/chat",
    json={
      "model_provider": provider,
      "model_name": model,
      "message": question,
      "top_k": top_k,
    },
    timeout=120,
  )
  response.raise_for_status()
  payload = response.json()
  if payload.get("status") != "success":
    raise RuntimeError(payload.get("message", "Chat API returned an error."))
  return payload.get("data") or {}


def evaluate(api_url: str, provider: str, model: str, questions: list[dict], top_k: int) -> dict:
  rows = []
  source_hits = 0
  cited_answers = 0

  for item in questions:
    result = call_chat(api_url, provider, model, item["question"], top_k)
    answer = result.get("answer", "")
    sources = result.get("sources", [])
    returned_files = {source.get("source_file") for source in sources}
    expected_files = set(item.get("expected_sources", []))
    hit = bool(expected_files.intersection(returned_files)) if expected_files else bool(sources)
    has_citation = "[" in answer and "]" in answer

    source_hits += int(hit)
    cited_answers += int(has_citation)
    rows.append({
      "question": item["question"],
      "expected_sources": sorted(expected_files),
      "returned_sources": sorted(file for file in returned_files if file),
      "source_hit": hit,
      "has_citation_marker": has_citation,
      "answer_preview": answer[:300],
    })

  total = max(len(questions), 1)
  return {
    "generated_at": datetime.now().isoformat(timespec="seconds"),
    "total_questions": len(questions),
    "source_hit_rate": round(source_hits / total, 4),
    "citation_marker_rate": round(cited_answers / total, 4),
    "rows": rows,
  }


def write_markdown(report: dict, path: Path):
  lines = [
    "# RAG Evaluation Report",
    "",
    f"- Generated at: {report['generated_at']}",
    f"- Total questions: {report['total_questions']}",
    f"- Source hit rate: {report['source_hit_rate']:.2%}",
    f"- Citation marker rate: {report['citation_marker_rate']:.2%}",
    "",
    "| Question | Source hit | Citation | Returned sources |",
    "| --- | --- | --- | --- |",
  ]

  for row in report["rows"]:
    sources = ", ".join(row["returned_sources"])
    lines.append(
      f"| {row['question']} | {row['source_hit']} | {row['has_citation_marker']} | {sources} |"
    )

  path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
  parser = argparse.ArgumentParser(description="Evaluate RAG retrieval and citation behavior.")
  parser.add_argument("--api-url", default="http://127.0.0.1:8000")
  parser.add_argument("--provider", required=True)
  parser.add_argument("--model", required=True)
  parser.add_argument("--questions", default="evaluation_questions.example.json")
  parser.add_argument("--top-k", type=int, default=5)
  parser.add_argument("--out", default="evaluation_report.md")
  args = parser.parse_args()

  questions_path = Path(args.questions)
  if not questions_path.is_absolute():
    questions_path = Path(__file__).parent / questions_path

  report = evaluate(args.api_url, args.provider, args.model, load_questions(questions_path), args.top_k)
  output_path = Path(args.out)
  if not output_path.is_absolute():
    output_path = Path(__file__).parent / output_path
  write_markdown(report, output_path)
  print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
  main()
