import uuid
import datetime
from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.database.models import ChatSession, Message


class SessionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_session(self, session_id: Optional[str] = None) -> ChatSession:
        if session_id:
            query = select(ChatSession).where(ChatSession.id == session_id).options(selectinload(ChatSession.messages))
            result = await self.db.execute(query)
            session = result.scalar_one_or_none()
            if session:
                return session

        # Create new session
        new_session = ChatSession(
            id=session_id or str(uuid.uuid4()),
            title="New Conversation",
            is_verified=False,
        )
        self.db.add(new_session)
        await self.db.flush()
        return new_session

    async def list_sessions(self) -> List[ChatSession]:
        query = select(ChatSession).options(selectinload(ChatSession.messages)).order_by(ChatSession.updated_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_session_detail(self, session_id: str) -> Optional[ChatSession]:
        query = select(ChatSession).where(ChatSession.id == session_id).options(selectinload(ChatSession.messages))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def delete_session(self, session_id: str) -> bool:
        query = delete(ChatSession).where(ChatSession.id == session_id)
        result = await self.db.execute(query)
        return result.rowcount > 0

    async def verify_session(self, session_id: str) -> bool:
        session = await self.get_or_create_session(session_id)
        session.is_verified = True
        session.updated_at = datetime.datetime.now(datetime.timezone.utc)
        await self.db.flush()
        return True

    async def get_messages_for_session(self, session_id: str) -> List[Message]:
        """Directly queries the messages table to guarantee fresh chronological order."""
        query = select(Message).where(Message.session_id == session_id).order_by(Message.created_at.asc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_message_by_id(self, message_id: str) -> Optional[Message]:
        query = select(Message).where(Message.id == message_id)
        res = await self.db.execute(query)
        return res.scalar_one_or_none()

    async def append_message(
        self,
        session_id: str,
        role: str,
        content: str,
        image_url: Optional[str] = None,
        responded_by: Optional[str] = None,
        reply_to_id: Optional[str] = None,
        reply_to_content: Optional[str] = None,
    ) -> Message:
        msg = Message(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role=role,
            content=content,
            image_url=image_url,
            responded_by=responded_by,
            reply_to_id=reply_to_id,
            reply_to_content=reply_to_content,
        )
        self.db.add(msg)

        # Update session title from first user message if still default
        query = select(ChatSession).where(ChatSession.id == session_id)
        res = await self.db.execute(query)
        session = res.scalar_one_or_none()
        if session:
            session.updated_at = datetime.datetime.now(datetime.timezone.utc)
            if role == "user" and session.title in ("New Conversation", "New Chat"):
                session.title = content[:30] + ("..." if len(content) > 30 else "")

        await self.db.flush()
        return msg

    async def get_last_turn(self, session_id: str) -> tuple[Optional[Message], Optional[Message]]:
        """
        Returns (last_user_message, last_assistant_message) for a session.
        Useful for retry actions.
        """
        session = await self.get_session_detail(session_id)
        if not session or not session.messages:
            return None, None

        user_msg = None
        asst_msg = None
        for m in reversed(session.messages):
            if m.role == "assistant" and asst_msg is None:
                asst_msg = m
            elif m.role == "user" and user_msg is None:
                user_msg = m
            if user_msg and asst_msg:
                break
        return user_msg, asst_msg

    async def update_context_summary(self, session_id: str, summary: str):
        query = select(ChatSession).where(ChatSession.id == session_id)
        res = await self.db.execute(query)
        session = res.scalar_one_or_none()
        if session:
            session.context_summary = summary
            await self.db.flush()
