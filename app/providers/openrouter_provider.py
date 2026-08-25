import re
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
from app.domain.interfaces.provider import BaseAIProvider, ProviderResponse
from app.config import settings


class OpenRouterProvider(BaseAIProvider):
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self._api_key = api_key or settings.OPENROUTER_API_KEY
        self._custom_model_name = model_name
        self._client: Optional[AsyncOpenAI] = None

    @property
    def provider_name(self) -> str:
        return "OpenRouter"

    @property
    def model_name(self) -> str:
        return self._custom_model_name or settings.OPENROUTER_MODEL

    @property
    def client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=self._api_key or settings.OPENROUTER_API_KEY,
                base_url="https://openrouter.ai/api/v1",
                timeout=settings.REQUEST_TIMEOUT_SECONDS,
                default_headers={
                    "HTTP-Referer": "https://olsson.aethercode.dev",
                    "X-Title": "Olsson Mobile AI",
                },
            )
        return self._client

    async def generate_response(
        self,
        messages: List[Dict[str, Any]],
        system_instruction: Optional[str] = None,
        image_data: Optional[str] = None,
        temperature: float = 0.7,
    ) -> ProviderResponse:
        # If image is attached, switch to openrouter vision model
        target_model = settings.OPENROUTER_VISION_MODEL if image_data else self.model_name

        payload_messages = []
        if system_instruction:
            payload_messages.append({"role": "system", "content": system_instruction})

        for idx, m in enumerate(messages):
            role = m.get("role", "user")
            content = m.get("content", "")

            if idx == len(messages) - 1 and role == "user" and image_data:
                img_url = image_data if (image_data.startswith("http") or image_data.startswith("data:")) else f"data:image/jpeg;base64,{image_data}"
                payload_messages.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": content or "Analyze this image:"},
                        {"type": "image_url", "image_url": {"url": img_url}},
                    ],
                })
            else:
                payload_messages.append({"role": role, "content": content})

        try:
            response = await self.client.chat.completions.create(
                model=target_model,
                messages=payload_messages,
                temperature=temperature,
            )
            text = response.choices[0].message.content or ""
            return ProviderResponse(
                content=text,
                model_name=target_model,
                provider_name=self.provider_name,
            )
        except Exception as e:
            raw_err = str(e)
            is_quota = any(kw in raw_err.lower() for kw in ("429", "rate_limit", "quota", "too many requests", "free limit", "resource_exhausted"))
            return ProviderResponse(
                content="",
                model_name=target_model,
                provider_name=self.provider_name,
                is_quota_error=is_quota,
                raw_error=raw_err,
            )
