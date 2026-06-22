import json
import threading
from datetime import datetime, timezone
from pathlib import Path

from app.models.schemas import ChatMessage, MessageRole


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
STORE_PATH = DATA_DIR / "chat_history.json"


class JsonChatStore:
    def __init__(self, path: Path = STORE_PATH):
        self.path = path
        self._lock = threading.Lock()

    def get_messages(self, thread_id: str) -> list[ChatMessage]:
        with self._lock:
            data = self._load()
            records = data.get(thread_id, [])
        return [ChatMessage(**record) for record in records]

    def add_message(
        self,
        thread_id: str,
        role: MessageRole,
        content: str,
        image_url: str | None = None,
    ) -> ChatMessage:
        message = ChatMessage(
            role=role,
            content=content,
            image_url=image_url,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        with self._lock:
            data = self._load()
            if hasattr(message, "model_dump"):
                record = message.model_dump()
            else:
                record = message.dict()
            data.setdefault(thread_id, []).append(record)
            self._save(data)
        return message

    def clear_thread(self, thread_id: str) -> None:
        with self._lock:
            data = self._load()
            data.pop(thread_id, None)
            self._save(data)

    def _load(self) -> dict[str, list[dict]]:
        if not self.path.exists():
            return {}
        with self.path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def _save(self, data: dict[str, list[dict]]) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        tmp_path = self.path.with_suffix(".tmp")
        with tmp_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
        tmp_path.replace(self.path)
