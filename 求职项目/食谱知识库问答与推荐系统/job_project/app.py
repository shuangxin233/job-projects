import argparse
import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "C8" / "cook"


@dataclass
class RecipeDoc:
  path: Path
  title: str
  category: str
  content: str


def tokenize(text: str) -> list[str]:
  text = (text or "").lower()
  chinese_chars = re.findall(r"[\u4e00-\u9fff]", text)
  words = re.findall(r"[a-z0-9_]+", text)
  return chinese_chars + words


def load_recipe_docs(data_dir: Path = DATA_DIR) -> list[RecipeDoc]:
  docs = []
  for path in sorted(data_dir.rglob("*.md")):
    content = path.read_text(encoding="utf-8", errors="ignore")
    title = path.stem
    for line in content.splitlines():
      if line.lstrip().startswith("#"):
        title = line.lstrip("#").strip() or title
        break
    try:
      category = path.relative_to(data_dir).parts[1]
    except Exception:
      category = "unknown"
    docs.append(RecipeDoc(path=path, title=title, category=category, content=content))
  return docs


def route_query(query: str) -> dict:
  relation_terms = ["搭配", "替代", "适合", "为什么", "原因", "关系", "组合", "对比", "禁忌"]
  detail_terms = ["怎么做", "步骤", "做法", "材料", "需要", "时间"]
  query_complexity = min(sum(term in query for term in relation_terms) / 3, 1.0)
  detail_intent = any(term in query for term in detail_terms)

  if query_complexity >= 0.34:
    strategy = "graph-lite-router"
    reason = "The query contains relationship or reasoning signals, so the app uses expanded entity matching."
  elif detail_intent:
    strategy = "hybrid-detail"
    reason = "The query asks for steps or ingredients, so title and content matches are both weighted."
  else:
    strategy = "hybrid-basic"
    reason = "The query is a direct lookup or recommendation request."

  return {
    "strategy": strategy,
    "query_complexity": round(query_complexity, 2),
    "reason": reason,
  }


def score_doc(query: str, doc: RecipeDoc, strategy: str) -> float:
  query_terms = set(tokenize(query))
  if not query_terms:
    return 0

  title_terms = set(tokenize(doc.title))
  content_terms = tokenize(doc.content[:4000])
  title_score = len(query_terms.intersection(title_terms)) * 3
  content_score = sum(1 for term in content_terms if term in query_terms)
  category_score = 1 if doc.category in query else 0
  strategy_bonus = 0

  if strategy == "graph-lite-router":
    relation_markers = ["搭配", "替代", "适合", "营养", "口感", "禁忌"]
    strategy_bonus = sum(marker in doc.content for marker in relation_markers)

  return title_score + content_score + category_score + strategy_bonus


def retrieve(query: str, docs: list[RecipeDoc], top_k: int = 5) -> tuple[dict, list[tuple[RecipeDoc, float]]]:
  route = route_query(query)
  scored = [(doc, score_doc(query, doc, route["strategy"])) for doc in docs]
  scored = [(doc, score) for doc, score in scored if score > 0]
  scored.sort(key=lambda item: item[1], reverse=True)
  return route, scored[:top_k]


def make_answer(query: str, route: dict, results: list[tuple[RecipeDoc, float]]) -> str:
  lines = [
    f"Question: {query}",
    f"Strategy: {route['strategy']} (complexity={route['query_complexity']})",
    f"Reason: {route['reason']}",
    "",
  ]

  if not results:
    lines.append("No matching recipe document was found. Try a dish name, ingredient, or cuisine keyword.")
    return "\n".join(lines)

  lines.append("Top evidence:")
  for index, (doc, score) in enumerate(results, start=1):
    preview = " ".join(line.strip() for line in doc.content.splitlines() if line.strip())[:220]
    relative_path = doc.path.relative_to(ROOT)
    lines.extend([
      f"[S{index}] {doc.title} | category={doc.category} | score={score}",
      f"     source={relative_path}",
      f"     preview={preview}",
    ])

  lines.extend([
    "",
    "Answer draft:",
    "Use the top evidence above as grounded context. In the full project, this context can be passed to an LLM for final generation with citations.",
  ])
  return "\n".join(lines)


def main():
  parser = argparse.ArgumentParser(description="Lightweight job-project entry for All-in-RAG.")
  parser.add_argument("--query", required=True, help="Question to ask against the C8 recipe corpus.")
  parser.add_argument("--top-k", type=int, default=5)
  args = parser.parse_args()

  docs = load_recipe_docs()
  route, results = retrieve(args.query, docs, args.top_k)
  print(make_answer(args.query, route, results))


if __name__ == "__main__":
  main()
