from typing import Literal, Optional

from pydantic import BaseModel, Field


MessageRole = Literal["user", "assistant", "system"]


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User message")
    image_url: Optional[str] = Field(None, description="Uploaded ingredient image URL")
    thread_id: str = Field(..., min_length=1, description="Conversation ID")


class ChatMessage(BaseModel):
    role: MessageRole
    content: str
    image_url: Optional[str] = None
    created_at: str


class ChatHistoryResponse(BaseModel):
    thread_id: str
    messages: list[ChatMessage]
