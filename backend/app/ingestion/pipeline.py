import logging
from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session_factory
from app.models.inference_log import InferenceLog
from app.schemas.inference_log import InferenceLogCreate
from app.services.auto_title import generate_title_and_update

logger = logging.getLogger(__name__)

async def process_log(log_payload: Dict[str, Any]):
    if log_payload.get("auto_title"):
        await generate_title_and_update(conv_id_str=log_payload["conversation_id"], first_message=log_payload["first_message"])
        return
    try:
        validated = InferenceLogCreate(**log_payload)
        enriched = validated.model_dump()
        enriched["server_received_at"] = datetime.now(timezone.utc).isoformat()
        async with async_session_factory() as session:
            try:
                await _store_log(session, validated)
                await _update_conversation(session, validated)
                await session.commit()
                logger.info("Processed log: request_id=%s provider=%s latency=%dms", validated.request_id, validated.provider, validated.latency_ms)
            except Exception as db_error:
                await session.rollback()
                raise db_error
    except Exception as e:
        logger.error("Failed to process log payload: %s. Error: %s", log_payload.get("request_id", "unknown"), e)

async def _store_log(session: AsyncSession, validated: InferenceLogCreate):
    log_entry = InferenceLog(conversation_id=validated.conversation_id, message_id=validated.message_id, request_id=validated.request_id, provider=validated.provider, model=validated.model, latency_ms=validated.latency_ms, prompt_tokens=validated.prompt_tokens, completion_tokens=validated.completion_tokens, total_tokens=validated.total_tokens, status=validated.status, error_type=validated.error_type, error_message=validated.error_message, input_preview=validated.input_preview, output_preview=validated.output_preview, is_streaming=validated.is_streaming, time_to_first_token_ms=validated.time_to_first_token_ms, raw_metadata=validated.raw_metadata)
    session.add(log_entry)

async def _update_conversation(session: AsyncSession, validated: InferenceLogCreate):
    if validated.conversation_id is None: return
    await session.execute(text("""UPDATE conversations SET total_tokens = COALESCE(total_tokens, 0) + :tokens, updated_at = NOW() WHERE id = :conversation_id"""), {"tokens": validated.total_tokens or 0, "conversation_id": validated.conversation_id})
