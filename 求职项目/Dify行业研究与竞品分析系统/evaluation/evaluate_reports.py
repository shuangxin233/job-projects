import argparse
import json
import re
from pathlib import Path


def evaluate_report(report_path: Path, required_sections: list[str], minimum_citations: int) -> dict:
  report = report_path.read_text(encoding="utf-8", errors="ignore")
  missing_sections = [section for section in required_sections if section not in report]
  citations = re.findall(r"\[S\d+\]", report)
  return {
    "report": str(report_path),
    "missing_sections": missing_sections,
    "citation_count": len(citations),
    "passes": not missing_sections and len(citations) >= minimum_citations,
  }


def main():
  parser = argparse.ArgumentParser(description="Evaluate Deep Research Markdown reports.")
  parser.add_argument("--topics", default="topics.json")
  parser.add_argument("--reports-dir", default="../backend/data/tasks")
  parser.add_argument("--out", default="evaluation_report.md")
  args = parser.parse_args()

  base = Path(__file__).parent
  topics_path = Path(args.topics)
  if not topics_path.is_absolute():
    topics_path = base / topics_path
  reports_dir = Path(args.reports_dir)
  if not reports_dir.is_absolute():
    reports_dir = (base / reports_dir).resolve()

  topics = json.loads(topics_path.read_text(encoding="utf-8"))
  report_files = sorted(reports_dir.glob("*.json"))
  results = []

  for report_file in report_files:
    data = json.loads(report_file.read_text(encoding="utf-8"))
    report_md = reports_dir / f"{report_file.stem}.md"
    report_md.write_text(data.get("report_markdown", ""), encoding="utf-8")
    topic_rule = next((item for item in topics if item["topic"].lower() in data.get("topic", "").lower()), topics[0])
    results.append(evaluate_report(
      report_md,
      topic_rule["required_sections"],
      topic_rule["minimum_citations"],
    ))

  lines = [
    "# Deep Research Evaluation Report",
    "",
    "| Report | Missing sections | Citation count | Pass |",
    "| --- | --- | --- | --- |",
  ]
  for item in results:
    missing = ", ".join(item["missing_sections"]) or "-"
    lines.append(f"| {item['report']} | {missing} | {item['citation_count']} | {item['passes']} |")

  out_path = Path(args.out)
  if not out_path.is_absolute():
    out_path = base / out_path
  out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
  print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
  main()
