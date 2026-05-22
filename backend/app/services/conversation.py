import uuid
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.conversation import Conversation
from app.models.message import Message

async def create_conversation(db, data):
    conv = Conversation(id=uuid.uuid4(), title=data.title, provider=data.provider, model=data.model, status="active")
    db.add(conv); await db.commit(); await db.refresh(conv)
    return conv

async def get_conversation(db, conv_id):
    r = await db.execute(select(Conversation).where(Conversation.id == conv_id))
    return r.scalar_one_or_none()

async def list_conversations(db, limit=50, offset=0):
    total = (await db.execute(select(func.count(Conversation.id)))).scalar() or 0
    q = select(Conversation).order_by(Conversation.updated_at.desc()).offset(offset).limit(limit)
    result = await db.execute(q)
    return list(result.scalars().all()), total

async def update_conversation(db, conv_id, data):
    conv = await get_conversation(db, conv_id)
    if not conv: return None
    if data.title is not None: conv.title = data.title
    if data.status is not None: conv.status = data.status
    if getattr(data, 'folder_id', None) is not None: conv.folder_id = data.folder_id
    await db.commit(); await db.refresh(conv)
    return conv

async def delete_conversation(db, conv_id):
    conv = await get_conversation(db, conv_id)
    if not conv: return False
    conv.status = "cancelled"; await db.commit()
    return True

async def get_conversation_messages(db, conv_id, limit=100, offset=0):
    total = (await db.execute(select(func.count(Message.id)).where(Message.conversation_id == conv_id))).scalar() or 0
    q = select(Message).where(Message.conversation_id == conv_id).order_by(Message.sequence_num.asc()).offset(offset).limit(limit)
    result = await db.execute(q)
    return list(result.scalars().all()), total

async def get_recent_messages(db, conv_id, limit=10):
    q = select(Message).where(Message.conversation_id == conv_id).order_by(Message.sequence_num.desc()).limit(limit)
    result = await db.execute(q)
    messages = list(result.scalars().all())
    messages.reverse()
    return messages

async def save_message(db, conv_id, role, content, sequence_num, token_count=None):
    msg = Message(id=uuid.uuid4(), conversation_id=conv_id, role=role, content=content, sequence_num=sequence_num, token_count=token_count)
    db.add(msg)
    conv = await get_conversation(db, conv_id)
    if conv:
        conv.message_count = (conv.message_count or 0) + 1
        conv.updated_at = func.now()
    await db.commit(); await db.refresh(msg)
    return msg
