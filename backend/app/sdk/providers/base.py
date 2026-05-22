from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Dict, List

@dataclass
class ProviderResponse:
    content: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    request_id: str = ""
    raw_metadata: Dict[str, Any] = field(default_factory=dict)

class BaseProvider(ABC):
    @abstractmethod
    async def complete(self, messages: List[Dict[str, str]], model: str, stream: bool = False) -> ProviderResponse:
        ...
    @abstractmethod
    async def stream(self, messages: List[Dict[str, str]], model: str) -> AsyncGenerator[Dict[str, Any], None]:
        ...
