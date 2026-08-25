from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db
from app.services.session_service import SessionService
from app.services.chat_service import ChatService


async def get_session_service(db: AsyncSession = Depends(get_db)) -> SessionService:
    return SessionService(db)


async def get_chat_service(db: AsyncSession = Depends(get_db)) -> ChatService:
    return ChatService(db)
