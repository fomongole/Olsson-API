from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ProviderResponse:
    content: str
    model_name: str
    provider_name: str
    is_quota_error: bool = False
    raw_error: Optional[str] = None


class BaseAIProvider(ABC):
    """
    Abstract Base Class for all AI model providers in Olsson API.
    Enforces standardized multimodal messaging and error reporting.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        pass

    @abstractmethod
    async def generate_response(
        self,
        messages: List[Dict[str, Any]],
        system_instruction: Optional[str] = None,
        image_data: Optional[str] = None,
        temperature: float = 0.7,
    ) -> ProviderResponse:
        """
        Generate a conversational response from the AI model.
        """
        pass
