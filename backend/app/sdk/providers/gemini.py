import time
from typing import Any, AsyncGenerator, Dict, List
import google.generativeai as genai
from app.config import settings
from app.sdk.providers.base import BaseProvider, ProviderResponse

class GeminiProvider(BaseProvider):
    def __init__(self):
        genai.configure(api_key=settings.gemini_api_key)

    def _convert(self, messages):
        result, sys_inst = [], None
        for m in messages:
            if m["role"] == "system": sys_inst = m["content"]
            elif m["role"] == "user": result.append({"role": "user", "parts": [m["content"]]})
            elif m["role"] == "assistant": result.append({"role": "model", "parts": [m["content"]]})
        return result, sys_inst

    async def complete(self, messages, model, stream=False):
        conv, sys_inst = self._convert(messages)
        gen_model = genai.GenerativeModel(model_name=model, system_instruction=sys_inst)
        user_msgs = [m for m in conv if m["role"] == "user"]
        prompt = user_msgs[-1]["parts"][0] if user_msgs else ""
        if stream:
            chunks, usage, ttf = [], {}, 0
            async for d in self.stream(messages, model):
                if d.get("content"): chunks.append(d["content"])
                if d.get("usage"): usage = d["usage"]
                ttf = d.get("time_to_first_token_ms", ttf)
                if d.get("done"): break
            return ProviderResponse(content="".join(chunks), model=model,
                prompt_tokens=usage.get("prompt_tokens", 0), completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0))
        response = await gen_model.generate_content_async(prompt)
        content = response.text or ""
        um = getattr(response, "usage_metadata", None)
        pt = um.prompt_token_count if um else 0
        ct = um.candidates_token_count if um else max(1, len(content) // 4)
        return ProviderResponse(content=content, model=model, prompt_tokens=pt, completion_tokens=ct,
            total_tokens=pt + ct, request_id=getattr(response, "response_id", ""), raw_metadata={"model": model})

    async def stream(self, messages, model):
        start, first, ttf, parts, pt, ct = time.time(), False, 0, [], 0, 0
        conv, sys_inst = self._convert(messages)
        gen_model = genai.GenerativeModel(model_name=model, system_instruction=sys_inst)
        user_msgs = [m for m in conv if m["role"] == "user"]
        prompt = user_msgs[-1]["parts"][0] if user_msgs else ""
        response = await gen_model.generate_content_async(prompt, stream=True)
        async for chunk in response:
            if chunk.text:
                parts.append(chunk.text)
                if not first:
                    first = True
                    ttf = int((time.time() - start) * 1000)
                yield {"content": chunk.text, "request_id": "", "done": False, "time_to_first_token_ms": ttf}
        ct = max(1, len("".join(parts)) // 4)
        yield {"content": "", "done": True, "request_id": "", "time_to_first_token_ms": ttf,
            "usage": {"prompt_tokens": pt, "completion_tokens": ct, "total_tokens": pt + ct}}
