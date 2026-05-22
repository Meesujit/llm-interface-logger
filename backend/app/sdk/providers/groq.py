import time
from typing import Any, AsyncGenerator, Dict, List
from openai import AsyncOpenAI
from app.config import settings
from app.sdk.providers.base import BaseProvider, ProviderResponse

class GroqProvider(BaseProvider):
    def __init__(self):
        self.client = AsyncOpenAI(base_url="https://api.groq.com/openai/v1", api_key=settings.groq_api_key)

    async def complete(self, messages: List[Dict[str, str]], model: str, stream: bool = False) -> ProviderResponse:
        if stream:
            chunks, usage, rid, ttf = [], {}, "", 0
            async for d in self.stream(messages, model):
                if d.get("content"): chunks.append(d["content"])
                if d.get("usage"): usage = d["usage"]
                if d.get("request_id"): rid = d["request_id"]
                ttf = d.get("time_to_first_token_ms", ttf)
                if d.get("done"): break
            return ProviderResponse(content="".join(chunks), model=model,
                prompt_tokens=usage.get("prompt_tokens", 0), completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0), request_id=rid)

        response = await self.client.chat.completions.create(model=model, messages=messages, temperature=0.7, max_tokens=4096)
        return ProviderResponse(content=response.choices[0].message.content or "", model=response.model,
            prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
            completion_tokens=response.usage.completion_tokens if response.usage else 0,
            total_tokens=response.usage.total_tokens if response.usage else 0,
            request_id=response.id, raw_metadata={"model": response.model, "created": response.created})

    async def stream(self, messages: List[Dict[str, str]], model: str) -> AsyncGenerator[Dict[str, Any], None]:
        start, first, ttf, parts, rid, pt, ct = time.time(), False, 0, [], "", 0, 0
        stream_response = await self.client.chat.completions.create(model=model, messages=messages, temperature=0.7, max_tokens=4096, stream=True)
        async for chunk in stream_response:
            rid = chunk.id or rid
            if chunk.choices and chunk.choices[0].delta.content:
                c = chunk.choices[0].delta.content
                parts.append(c)
                if not first:
                    first = True
                    ttf = int((time.time() - start) * 1000)
                yield {"content": c, "request_id": rid, "done": False, "time_to_first_token_ms": ttf}
            if hasattr(chunk, "usage") and chunk.usage:
                pt = chunk.usage.prompt_tokens or 0
                ct = chunk.usage.completion_tokens or 0
        if ct == 0 and parts:
            ct = max(1, len("".join(parts)) // 4)
        yield {"content": "", "done": True, "request_id": rid, "time_to_first_token_ms": ttf,
            "usage": {"prompt_tokens": pt, "completion_tokens": ct, "total_tokens": pt + ct}}
