import json
import os
import urllib.error
import urllib.request
from collections.abc import Iterable


class OllamaUnavailable(RuntimeError):
    pass


def stream_ollama_chat(messages: list[dict[str, str]]) -> Iterable[str]:
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    model = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
    payload = json.dumps(
        {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": {"temperature": 0.4},
        },
        ensure_ascii=False,
    ).encode("utf-8")

    request = urllib.request.Request(
        f"{base_url}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            for raw_line in response:
                line = raw_line.decode("utf-8").strip()
                if not line:
                    continue
                data = json.loads(line)
                if data.get("done"):
                    break
                content = data.get("message", {}).get("content", "")
                if content:
                    yield content
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise OllamaUnavailable(f"Ollama 请求失败：{exc.code} {detail}") from exc
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        raise OllamaUnavailable(f"无法连接本地 Ollama：{exc}") from exc
