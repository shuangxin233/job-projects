from pydantic import BaseModel
from typing import Any, Optional, Literal


class SearchQueryRequest(BaseModel):
    model_provider: str
    query: str
    top_k: int = 5

class ChatRequest(BaseModel):
    model_provider: str
    model_name: str
    message: str
    top_k: int = 5

class StandardAPIResponse(BaseModel):
    status: Literal["success", "error"]
    data: Optional[Any] = None
    message: Optional[str] = None
