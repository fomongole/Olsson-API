from enum import Enum
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
import datetime


class ModelSelection(str, Enum):
    DEFAULT = "default"         # Intelligent 4-stage failover: Groq -> Mistral -> OpenRouter -> Gemini
    GROQ = "groq"               # Groq directly (openai/gpt-oss-120b)
    MISTRAL = "mistral"         # Mistral AI (mistral-small-latest)
    OPENROUTER = "openrouter"   # OpenRouter (meta-llama/llama-3.3-70b-instruct:free)
    GEMINI = "gemini"           # Google Gemini (gemini-3.6-flash)


class MessageItem(BaseModel):
    id: str
    role: str
    content: str
    image_url: Optional[str] = None
    responded_by: Optional[str] = None
    reply_to_id: Optional[str] = None
    reply_to_content: Optional[str] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    session_id: Optional[str] = Field(
        None, description="Existing session ID. If omitted, a new chat session is automatically created."
    )
    message: str = Field(..., description="Text prompt from the user.")
    image_data: Optional[str] = Field(
        None, description="Optional Base64-encoded image string or public image URL."
    )
    model: ModelSelection = Field(
        default=ModelSelection.DEFAULT,
        description="Target model selection or 'default' for multi-provider failover chain."
    )
    reply_to_id: Optional[str] = Field(
        None, description="Optional message ID to reply to specifically (WhatsApp-style quote reply)."
    )


class RetryRequest(BaseModel):
    session_id: str = Field(..., description="The chat session ID containing the failed turn.")
    model: ModelSelection = Field(
        default=ModelSelection.DEFAULT,
        description="Target model for the retry, or 'default' to run the failover chain."
    )


class ChatResponse(BaseModel):
    session_id: str
    message_id: str
    content: str
    responded_by: str = Field(..., description="Identifier of the specific AI provider & model that produced the answer.")
    is_verified: bool = Field(..., description="Whether the current session has passed Fred's identity verification.")
    verification_prompt: Optional[str] = Field(None, description="Challenge prompt if verification is pending.")


class VerifyRequest(BaseModel):
    session_id: str = Field(..., description="The chat session ID to verify.")
    answer: str = Field(..., description="Fred's Date of Birth or Girlfriend's name.")


class VerifyResponse(BaseModel):
    session_id: str
    is_verified: bool
    message: str


class SessionSummary(BaseModel):
    id: str
    title: str
    is_verified: bool
    message_count: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True


class SessionDetail(BaseModel):
    id: str
    title: str
    is_verified: bool
    messages: List[MessageItem]
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True
