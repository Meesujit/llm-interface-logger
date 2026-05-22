import logging, uuid
from app.config import settings
from app.database import async_session_factory
from app.sdk.providers.groq import GroqProvider

logger = logging.getLogger(__name__)

async def generate_title_and_update(conv_id_str: str, first_message: str):
    conv_id = uuid.UUID(conv_id_str)
    provider = GroqProvider()
    try:
        response = await provider.complete(
            messages=[
                {"role": "system", "content": "Generate a very short title (3-5 words max) for this chat. Return ONLY the title - no quotes, punctuation, or explanation."},
                {"role": "user", "content": first_message},
            ],
            model=settings.groq_model, stream=False,
        )
        title = response.content.strip()
        title = title.split("\n")[0]
        title = title.strip("\"'*#- \u2022")
        for prefix in ["Title:", "title:", "**"]:
            if title.startswith(prefix): title = title[len(prefix):].strip()
        if title.endswith("**"): title = title[:-2].strip()
        title = title[:80]
        if not title: title = first_message[:40]
    except Exception as e:
        logger.warning("Title generation failed: %s, using fallback", e)
        title = first_message[:40]
    try:
        async with async_session_factory() as session:
            from sqlalchemy import text
            await session.execute(text("UPDATE conversations SET title = :title WHERE id = :id"), {"title": title, "id": conv_id})
            await session.commit()
        logger.info("Auto-titled conversation %s: %s", conv_id, title)
    except Exception as e:
        logger.error("Failed to update title for %s: %s", conv_id, e)
