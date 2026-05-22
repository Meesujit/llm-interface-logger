from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

class ConversationCreate(BaseModel):
    title: Optional[str] = None
    provider: str = Field(..., description="groq | gemini")
    model: str
    folder_id: Optional[UUID] = None

class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    folder_id: Optional[UUID] = Field(None, description="Move to folder, null to unassign")

class ConversationResponse(BaseModel):
    id: UUID; folder_id: Optional[UUID] = None; title: Optional[str]
    provider: str; model: str; status: str
    created_at: datetime; updated_at: datetime; message_count: int; total_tokens: int
    model_config = {"from_attributes": True}

class ConversationListResponse(BaseModel):
    conversations: list[ConversationResponse]; total: int
