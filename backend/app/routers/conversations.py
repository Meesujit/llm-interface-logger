import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.conversation import ConversationListResponse, ConversationResponse, ConversationUpdate
from app.schemas.message import MessageListResponse, MessageResponse
from app.services import delete_conversation, get_conversation, get_conversation_messages, list_conversations, update_conversation

router = APIRouter()

@router.get("/conversations", response_model=ConversationListResponse)
async def list_convs(limit: int = 50, offset: int = 0, db: AsyncSession = Depends(get_db)):
    conversations, total = await list_conversations(db, limit=limit, offset=offset)
    return ConversationListResponse(conversations=[ConversationResponse.model_validate(c) for c in conversations], total=total)

@router.get("/conversations/{conv_id}", response_model=ConversationResponse)
async def get_conv(conv_id: str, db: AsyncSession = Depends(get_db)):
    try: uid = uuid.UUID(conv_id)
    except ValueError: raise HTTPException(status_code=400, detail="Invalid UUID")
    conv = await get_conversation(db, uid)
    if not conv: raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationResponse.model_validate(conv)

@router.delete("/conversations/{conv_id}")
async def cancel_conv(conv_id: str, db: AsyncSession = Depends(get_db)):
    try: uid = uuid.UUID(conv_id)
    except ValueError: raise HTTPException(status_code=400, detail="Invalid UUID")
    deleted = await delete_conversation(db, uid)
    if not deleted: raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "cancelled", "id": conv_id}

@router.patch("/conversations/{conv_id}", response_model=ConversationResponse)
async def resume_conv(conv_id: str, data: ConversationUpdate, db: AsyncSession = Depends(get_db)):
    try: uid = uuid.UUID(conv_id)
    except ValueError: raise HTTPException(status_code=400, detail="Invalid UUID")
    conv = await update_conversation(db, uid, data)
    if not conv: raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationResponse.model_validate(conv)

@router.get("/conversations/{conv_id}/messages", response_model=MessageListResponse)
async def get_messages(conv_id: str, limit: int = 100, offset: int = 0, db: AsyncSession = Depends(get_db)):
    try: uid = uuid.UUID(conv_id)
    except ValueError: raise HTTPException(status_code=400, detail="Invalid UUID")
    messages, total = await get_conversation_messages(db, uid, limit=limit, offset=offset)
    return MessageListResponse(messages=[MessageResponse.model_validate(m) for m in messages], total=total)
