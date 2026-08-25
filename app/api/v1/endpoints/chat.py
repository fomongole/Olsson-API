from fastapi import APIRouter, Depends, HTTPException, status
from app.domain.schemas.chat import (
    ChatRequest,
    ChatResponse,
    RetryRequest,
    VerifyRequest,
    VerifyResponse,
)
from app.services.chat_service import ChatService
from app.services.session_service import SessionService
from app.api.deps import get_chat_service, get_session_service
from app.core.security import verify_identity

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def send_chat_message(
    req: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    """
    Send a chat message to Olsson AI.
    Supports text, images, model selection, quote replies, and verification gatekeeper.
    """
    return await chat_service.handle_chat(
        session_id=req.session_id,
        user_message=req.message,
        image_data=req.image_data,
        model_choice=req.model,
        reply_to_id=req.reply_to_id,
    )


@router.post("/retry", response_model=ChatResponse)
async def retry_last_message(
    req: RetryRequest,
    chat_service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    """
    Retry/resend the last turn with a target model or the default failover chain.
    """
    return await chat_service.handle_retry(
        session_id=req.session_id,
        model_choice=req.model,
    )


@router.post("/verify", response_model=VerifyResponse)
async def verify_chat_session(
    req: VerifyRequest,
    session_service: SessionService = Depends(get_session_service),
) -> VerifyResponse:
    """
    Direct endpoint to verify a chat session with Fred's DOB or girlfriend's name.
    """
    is_valid = verify_identity(req.answer)
    if not is_valid:
        return VerifyResponse(
            session_id=req.session_id,
            is_verified=False,
            message="❌ Verification failed. Date of birth or girlfriend's name is incorrect.",
        )

    await session_service.verify_session(req.session_id)
    return VerifyResponse(
        session_id=req.session_id,
        is_verified=True,
        message="✅ Identity verified! Welcome back Fred Omongole.",
    )
