import base64
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types
from app.domain.interfaces.provider import BaseAIProvider, ProviderResponse
from app.config import settings


class GeminiProvider(BaseAIProvider):
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self._api_key = api_key or settings.GEMINI_API_KEY
        self._model_name = model_name or settings.GEMINI_MODEL
        self._client: Optional[genai.Client] = None

    @property
    def provider_name(self) -> str:
        return "Google Gemini"

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def client(self) -> genai.Client:
        if self._client is None:
            self._client = genai.Client(api_key=self._api_key)
        return self._client

    async def generate_response(
        self,
        messages: List[Dict[str, Any]],
        system_instruction: Optional[str] = None,
        image_data: Optional[str] = None,
        temperature: float = 0.7,
    ) -> ProviderResponse:
        contents = []

        for idx, m in enumerate(messages):
            role = "user" if m.get("role") == "user" else "model"
            content_text = m.get("content", "")

            # If image is attached to the last user message
            if idx == len(messages) - 1 and role == "user" and image_data:
                parts = [types.Part.from_text(text=content_text or "Analyze this image:")]

                # Decode base64 image if provided
                if image_data.startswith("data:"):
                    # data:image/png;base64,xxxx
                    header, b64_str = image_data.split(",", 1)
                    mime = header.split(";")[0].split(":")[1]
                    raw_bytes = base64.b64decode(b64_str)
                    parts.append(types.Part.from_bytes(data=raw_bytes, mime_type=mime))
                elif not image_data.startswith("http"):
                    raw_bytes = base64.b64decode(image_data)
                    parts.append(types.Part.from_bytes(data=raw_bytes, mime_type="image/jpeg"))

                contents.append(types.Content(role="user", parts=parts))
            else:
                contents.append(types.Content(role=role, parts=[types.Part.from_text(text=content_text)]))

        try:
            config_params = types.GenerateContentConfig(
                temperature=temperature,
            )
            if system_instruction:
                config_params.system_instruction = system_instruction

            # Asynchronous execution
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config_params,
            )
            text = response.text or ""
            return ProviderResponse(
                content=text,
                model_name=self.model_name,
                provider_name=self.provider_name,
            )
        except Exception as e:
            raw_err = str(e)
            is_quota = any(kw in raw_err.lower() for kw in ("429", "resource_exhausted", "quota", "rate_limit"))
            return ProviderResponse(
                content="",
                model_name=self.model_name,
                provider_name=self.provider_name,
                is_quota_error=is_quota,
                raw_error=raw_err,
            )
