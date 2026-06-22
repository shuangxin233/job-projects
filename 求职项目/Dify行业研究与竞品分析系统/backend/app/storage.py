import json
from pathlib import Path

from .models import ResearchTask


STORAGE_DIR = Path(__file__).resolve().parents[1] / "data" / "tasks"


def save_task(task: ResearchTask) -> Path:
  STORAGE_DIR.mkdir(parents=True, exist_ok=True)
  path = STORAGE_DIR / f"{task.task_id}.json"
  if hasattr(task, "model_dump_json"):
    content = task.model_dump_json(indent=2)
  else:
    content = task.json(indent=2, ensure_ascii=False)
  path.write_text(content, encoding="utf-8")
  return path


def load_task(task_id: str) -> ResearchTask:
  path = STORAGE_DIR / f"{task_id}.json"
  data = json.loads(path.read_text(encoding="utf-8"))
  return ResearchTask(**data)


def list_tasks() -> list[ResearchTask]:
  if not STORAGE_DIR.exists():
    return []
  return [load_task(path.stem) for path in sorted(STORAGE_DIR.glob("*.json"))]
