from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID
from pydantic import BaseModel, Field

class InferenceLogCreate(BaseModel):
    conversation_id: Optional[UUID] = None; message_id: Optional[UUID] = None; request_id: Optional[str] = None
    provider: str; model: str; latency_ms: int
    prompt_tokens: Optional[int] = None; completion_tokens: Optional[int] = None; total_tokens: Optional[int] = None
    status: str; error_type: Optional[str] = None; error_message: Optional[str] = None
    input_preview: Optional[str] = Field(None, max_length=300); output_preview: Optional[str] = Field(None, max_length=300)
    is_streaming: bool = False; time_to_first_token_ms: Optional[int] = None; raw_metadata: Optional[Dict[str, Any]] = None

class InferenceLogResponse(BaseModel):
    id: UUID; conversation_id: Optional[UUID]; message_id: Optional[UUID]; request_id: Optional[str]
    provider: str; model: str; latency_ms: int; prompt_tokens: Optional[int]; completion_tokens: Optional[int]
    total_tokens: Optional[int]; status: str; error_type: Optional[str]; error_message: Optional[str]
    input_preview: Optional[str]; output_preview: Optional[str]; is_streaming: bool
    time_to_first_token_ms: Optional[int]; created_at: datetime; raw_metadata: Optional[Dict[str, Any]]
    model_config = {"from_attributes": True}

class InferenceLogListResponse(BaseModel):
    logs: list[InferenceLogResponse]; total: int

class MetricsResponse(BaseModel):
    avg_latency_ms: float = 0.0; p50_latency_ms: float = 0.0; p95_latency_ms: float = 0.0; p99_latency_ms: float = 0.0
    total_requests: int = 0; error_rate: float = 0.0; requests_per_minute: float = 0.0; total_tokens: int = 0
    by_provider: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    latency_over_time: list[Dict[str, Any]] = Field(default_factory=list)
    errors_over_time: list[Dict[str, Any]] = Field(default_factory=list)
