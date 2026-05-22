from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

class MessageCreate(BaseModel):
    conversation_id: UUID; role: str; content: str; sequence_num: int; token_count: Optional[int] = None

class MessageResponse(BaseModel):
    id: UUID; conversation_id: UUID; role: str; content: str; content_redacted: Optional[str] = None
    created_at: datetime; token_count: Optional[int] = None; sequence_num: int
    model_config = {"from_attributes": True}

class MessageListResponse(BaseModel):
    messages: list[MessageResponse]; total: int
