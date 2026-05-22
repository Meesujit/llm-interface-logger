from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

class FolderCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

class FolderUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

class FolderResponse(BaseModel):
    id: UUID; name: str; created_at: datetime; updated_at: datetime; conversation_count: int = 0
    model_config = {"from_attributes": True}

class FolderListResponse(BaseModel):
    folders: list[FolderResponse]
