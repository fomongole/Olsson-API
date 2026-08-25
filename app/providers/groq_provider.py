import re
from typing import List, Dict, Any, Optional
from groq import AsyncGroq
from app.domain.interfaces.provider import BaseAIProvider, ProviderResponse
from app.config import settings


class GroqProvider(BaseAIProvider):
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self._api_key = api_key or settings.GROQ_API_KEY
        self._model_name = model_name or settings.GROQ_MODEL
        self._client: Optional[AsyncGroq] = None

    @property
    def provider_name(self) -> str:
        return "Groq"

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def client(self) -> AsyncGroq:
        if self._client is None:
            self._client = AsyncGroq(api_key=self._api_key, timeout=settings.REQUEST_TIMEOUT_SECONDS)
        return self._client

    async def generate_response(
        self,
        messages: List[Dict[str, Any]],
        system_instruction: Optional[str] = None,
        image_data: Optional[str] = None,
        temperature: float = 0.7,
    ) -> ProviderResponse:
        # Note: openai/gpt-oss-120b on Groq is text-only. If image_data is sent, signal quota/skip to fallback
        if image_data:
            return ProviderResponse(
                content="",
                model_name=self.model_name,
                provider_name=self.provider_name,
                is_quota_error=True,
                raw_error="Groq text model does not support image inputs. Auto-routing to vision model.",
            )

        payload_messages = []
        if system_instruction:
            payload_messages.append({"role": "system", "content": system_instruction})

        for m in messages:
            content = m.get("content", "")
            payload_messages.append({"role": m.get("role", "user"), "content": content})

        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=payload_messages,
                temperature=temperature,
            )
            text = response.choices[0].message.content or ""
            return ProviderResponse(
                content=text,
                model_name=self.model_name,
                provider_name=self.provider_name,
            )
        except Exception as e:
            raw_err = str(e)
            is_quota = "429" in raw_err or "rate_limit" in raw_err.lower() or "quota" in raw_err.lower()
            return ProviderResponse(
                content="",
                model_name=self.model_name,
                provider_name=self.provider_name,
                is_quota_error=is_quota,
                raw_error=raw_err,
            )
