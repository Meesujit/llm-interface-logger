import time, uuid
from typing import Any, AsyncGenerator, Dict, List, Literal, Optional
from app.config import settings
from app.ingestion.queue import enqueue_log
from app.sdk.pii_redactor import PIIRedactor
from app.sdk.providers import GeminiProvider, GroqProvider
from app.sdk.providers.base import BaseProvider, ProviderResponse

ProviderName = Literal["groq", "gemini"]
_providers = {"groq": GroqProvider(), "gemini": GeminiProvider()}
_redactor = PIIRedactor()

def _get_provider(provider: ProviderName):
    p = _providers.get(provider)
    if p is None: raise ValueError(f"Unknown provider: {provider}")
    return p

def _build_log_payload(*, provider, model, response, latency_ms, conversation_id, message_id, last_user_message, status="success", is_streaming=False, time_to_first_token_ms=None, error_type=None, error_message=None):
    inp = _redactor.redact(last_user_message[:300]) if last_user_message else ""
    out = _redactor.redact(response.content[:300]) if response.content else ""
    return {"conversation_id": str(conversation_id) if conversation_id else None,
        "message_id": str(message_id) if message_id else None,
        "request_id": response.request_id or str(uuid.uuid4()), "provider": provider, "model": model,
        "latency_ms": latency_ms, "prompt_tokens": response.prompt_tokens, "completion_tokens": response.completion_tokens,
        "total_tokens": response.total_tokens, "status": status, "error_type": error_type, "error_message": error_message,
        "input_preview": inp, "output_preview": out, "is_streaming": is_streaming,
        "time_to_first_token_ms": time_to_first_token_ms, "raw_metadata": response.raw_metadata}

class LLMLogger:
    def __init__(self, provider: ProviderName, conversation_id: Optional[uuid.UUID] = None):
        self.provider_name = provider
        self.provider = _get_provider(provider)
        self.conversation_id = conversation_id
        self._last_user_message = ""

    async def complete(self, messages, model=None, stream=False):
        if model is None: model = settings.groq_model if self.provider_name == "groq" else settings.gemini_model
        umsgs = [m for m in messages if m.get("role") == "user"]
        self._last_user_message = umsgs[-1]["content"] if umsgs else ""
        start = time.time()
        try:
            response = await self.provider.complete(messages, model, stream=stream)
            latency = int((time.time() - start) * 1000)
            enqueue_log(_build_log_payload(provider=self.provider_name, model=model, response=response, latency_ms=latency, conversation_id=self.conversation_id, message_id=None, last_user_message=self._last_user_message, status="success", is_streaming=stream))
            return response
        except Exception as e:
            latency = int((time.time() - start) * 1000)
            enqueue_log(_build_log_payload(provider=self.provider_name, model=model, response=ProviderResponse(content="", model=model), latency_ms=latency, conversation_id=self.conversation_id, message_id=None, last_user_message=self._last_user_message, status="error", is_streaming=stream, error_type=type(e).__name__, error_message=str(e)[:500]))
            raise

    async def stream(self, messages, model=None):
        if model is None: model = settings.groq_model if self.provider_name == "groq" else settings.gemini_model
        umsgs = [m for m in messages if m.get("role") == "user"]
        self._last_user_message = umsgs[-1]["content"] if umsgs else ""
        start = time.time()
        final_content, usage, rid, ttf = [], {}, "", 0
        try:
            async for chunk_data in self.provider.stream(messages, model):
                if chunk_data.get("content"): final_content.append(chunk_data["content"])
                if chunk_data.get("usage"): usage = chunk_data["usage"]
                if chunk_data.get("request_id"): rid = chunk_data["request_id"]
                ttf = chunk_data.get("time_to_first_token_ms", ttf)
                yield chunk_data
            latency = int((time.time() - start) * 1000)
            response = ProviderResponse(content="".join(final_content), model=model,
                prompt_tokens=usage.get("prompt_tokens", 0), completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0), request_id=rid)
            enqueue_log(_build_log_payload(provider=self.provider_name, model=model, response=response, latency_ms=latency, conversation_id=self.conversation_id, message_id=None, last_user_message=self._last_user_message, status="success", is_streaming=True, time_to_first_token_ms=ttf))
        except Exception as e:
            latency = int((time.time() - start) * 1000)
            enqueue_log(_build_log_payload(provider=self.provider_name, model=model, response=ProviderResponse(content="".join(final_content), model=model), latency_ms=latency, conversation_id=self.conversation_id, message_id=None, last_user_message=self._last_user_message, status="error", is_streaming=True, time_to_first_token_ms=ttf, error_type=type(e).__name__, error_message=str(e)[:500]))
            yield {"content": "", "done": True, "error": str(e), "usage": {}}
