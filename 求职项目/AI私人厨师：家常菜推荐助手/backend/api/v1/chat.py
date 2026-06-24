from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from backend.models.schemas import ChatHistoryResponse, ChatRequest
from backend.services.chat_store import JsonChatStore
from backend.services.ollama_client import OllamaUnavailable, stream_ollama_chat
from backend.services.recipe_engine import build_ollama_messages, chunk_text, fallback_recipe_answer


router = APIRouter()
store = JsonChatStore()


@router.post("/chat/stream")
async def chat_endpoint(request: ChatRequest):
    """Stream a personal-chef response and save the conversation."""
    user_message = request.message.strip()
    store.add_message(request.thread_id, "user", user_message, request.image_url)
    history = store.get_messages(request.thread_id)
    model_messages = build_ollama_messages(history)

    def generate():
        assistant_parts: list[str] = []
        try:
            for chunk in stream_ollama_chat(model_messages):
                assistant_parts.append(chunk)
                yield chunk
        except OllamaUnavailable as exc:
            if assistant_parts:
                note = f"\n\n[系统提示] 本地模型中断：{exc}"
                assistant_parts.append(note)
                yield note
            else:
                fallback = fallback_recipe_answer(user_message, request.image_url)
                for chunk in chunk_text(fallback):
                    assistant_parts.append(chunk)
                    yield chunk
        finally:
            assistant_text = "".join(assistant_parts).strip()
            if assistant_text:
                store.add_message(request.thread_id, "assistant", assistant_text)

    return StreamingResponse(generate(), media_type="text/plain; charset=utf-8")


@router.get("/chat/messages", response_model=ChatHistoryResponse)
async def get_chat_messages(thread_id: str):
    """Return saved messages for one conversation."""
    return {"thread_id": thread_id, "messages": store.get_messages(thread_id)}


@router.delete("/chat/messages")
async def clear_chat_messages(thread_id: str):
    """Clear saved messages for one conversation."""
    store.clear_thread(thread_id)
    return {"thread_id": thread_id, "cleared": True}
