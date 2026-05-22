import asyncio, json, uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.database import get_db
from app.ingestion.queue import enqueue_log
from app.schemas.conversation import ConversationCreate
from app.sdk import LLMLogger
from app.services import create_conversation, get_recent_messages, save_message

router = APIRouter()

class ChatRequest(BaseModel):
    conversation_id: Optional[str] = Field(None)
    message: str
    provider: str = Field(..., description="groq | gemini")
    model: Optional[str] = None
    stream: bool = False

class ChatResponse(BaseModel):
    conversation_id: str; message_id: str; content: str; provider: str; model: str
    usage: dict = Field(default_factory=dict)

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    provider = request.provider.lower()
    if provider not in ("groq", "gemini"):
        raise HTTPException(status_code=400, detail="Provider must be 'groq' or 'gemini'")
    model = request.model or (settings.groq_model if provider == "groq" else settings.gemini_model)

    if request.conversation_id:
        try: conv_id = uuid.UUID(request.conversation_id)
        except ValueError: raise HTTPException(status_code=400, detail="Invalid conversation_id UUID")
    else:
        conv = await create_conversation(db, ConversationCreate(provider=provider, model=model))
        conv_id = conv.id

    recent_msgs = await get_recent_messages(db, conv_id, limit=10)
    next_seq = (max((m.sequence_num for m in recent_msgs), default=0) + 1)
    await save_message(db, conv_id, "user", request.message, next_seq)
    next_seq += 1

    messages_for_llm = [{"role": m.role, "content": m.content} for m in recent_msgs]
    messages_for_llm.append({"role": "user", "content": request.message})

    logger = LLMLogger(provider=provider, conversation_id=conv_id)
    try:
        response = await logger.complete(messages=messages_for_llm, model=model, stream=request.stream)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM provider error: {str(e)}")

    assistant_msg = await save_message(db, conv_id, "assistant", response.content, next_seq, token_count=response.total_tokens)

    if not recent_msgs:
        enqueue_log({"auto_title": True, "conversation_id": str(conv_id), "first_message": request.message[:500]})

    return ChatResponse(conversation_id=str(conv_id), message_id=str(assistant_msg.id), content=response.content, provider=provider, model=model, usage={"prompt_tokens": response.prompt_tokens, "completion_tokens": response.completion_tokens, "total_tokens": response.total_tokens, "model": model})

@router.get("/chat/stream")
async def chat_stream(conversation_id: str = Query(...), message: str = Query(...), provider: str = Query("groq"), model: Optional[str] = Query(None), db: AsyncSession = Depends(get_db)):
    provider = provider.lower()
    if provider not in ("groq", "gemini"): raise HTTPException(status_code=400, detail="Provider must be 'groq' or 'gemini'")
    model = model or (settings.groq_model if provider == "groq" else settings.gemini_model)
    try: conv_id = uuid.UUID(conversation_id)
    except ValueError: raise HTTPException(status_code=400, detail="Invalid conversation_id UUID")

    recent_msgs = await get_recent_messages(db, conv_id, limit=10)
    next_seq = (max((m.sequence_num for m in recent_msgs), default=0) + 1)
    await save_message(db, conv_id, "user", message, next_seq)
    next_seq += 1

    messages_for_llm = [{"role": m.role, "content": m.content} for m in recent_msgs]
    messages_for_llm.append({"role": "user", "content": message})

    async def event_generator():
        full_content, usage_data = [], {}
        logger = LLMLogger(provider=provider, conversation_id=conv_id)
        try:
            async for chunk_data in logger.stream(messages=messages_for_llm, model=model):
                if chunk_data.get("content"):
                    full_content.append(chunk_data["content"])
                    yield f"data: {json.dumps({'chunk': chunk_data['content'], 'done': False})}\n\n"
                    await asyncio.sleep(0)
                if chunk_data.get("usage"): usage_data = chunk_data["usage"]
                if chunk_data.get("done"): break
            content = "".join(full_content)
            await save_message(db, conv_id, "assistant", content, next_seq, token_count=usage_data.get("total_tokens", 0))
            yield f"data: {json.dumps({'chunk': '', 'done': True, 'usage': usage_data})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'chunk': '', 'done': True, 'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"})
