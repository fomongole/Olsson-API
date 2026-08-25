from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.domain.schemas.chat import SessionSummary, SessionDetail
from app.services.session_service import SessionService
from app.api.deps import get_session_service

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.get("", response_model=List[SessionSummary])
async def list_chat_sessions(
    session_service: SessionService = Depends(get_session_service),
) -> List[SessionSummary]:
    """
    Retrieve all persisted conversation sessions for the mobile app list view.
    """
    sessions = await session_service.list_sessions()
    return [
        SessionSummary(
            id=s.id,
            title=s.title,
            is_verified=s.is_verified,
            message_count=len(s.messages),
            created_at=s.created_at,
            updated_at=s.updated_at,
        )
        for s in sessions
    ]


@router.get("/{session_id}", response_model=SessionDetail)
async def get_session_history(
    session_id: str,
    session_service: SessionService = Depends(get_session_service),
) -> SessionDetail:
    """
    Retrieve full message history for a specific conversation session.
    """
    session = await session_service.get_session_detail(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID '{session_id}' not found.",
        )
    return session


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_session(
    session_id: str,
    session_service: SessionService = Depends(get_session_service),
) -> None:
    """
    Delete a conversation session and all its messages.
    """
    deleted = await session_service.delete_session(session_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID '{session_id}' not found.",
        )
