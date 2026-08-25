import datetime
import uuid
from typing import List, Optional
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class ChatSession(Base):
    """
    Represents a conversation session in the mobile app.
    Persists across app restarts and stores identity verification state.
    """
    __tablename__ = "chat_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(255), default="New Chat")
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
    )
    # Stored summary of older conversation context (for memory preservation across days)
    context_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    messages: Mapped[List["Message"]] = relationship(
        "Message", back_populates="session", cascade="all, delete-orphan", order_by="Message.created_at"
    )


class Message(Base):
    """
    Represents an individual message in a chat session.
    Supports quoting/replying to earlier messages (WhatsApp-style replies).
    """
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("chat_sessions.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(20)) # "user" | "assistant" | "system"
    content: Mapped[str] = mapped_column(Text)
    image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    responded_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True) # e.g. "Groq (openai/gpt-oss-120b)"
    
    # WhatsApp-style Reply Quote Support
    reply_to_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    reply_to_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), index=True
    )

    session: Mapped["ChatSession"] = relationship("ChatSession", back_populates="messages")
