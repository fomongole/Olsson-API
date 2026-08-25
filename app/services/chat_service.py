from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.schemas.chat import ModelSelection, ChatResponse
from app.services.session_service import SessionService
from app.core.security import verify_identity, CHALLENGE_MESSAGE
from app.core.persona import build_system_prompt
from app.core.token_optimizer import optimize_conversation_history
from app.providers.groq_provider import GroqProvider
from app.providers.mistral_provider import MistralProvider
from app.providers.openrouter_provider import OpenRouterProvider
from app.providers.gemini_provider import GeminiProvider


class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.session_service = SessionService(db)
        self.groq_provider = GroqProvider()
        self.mistral_provider = MistralProvider()
        self.openrouter_provider = OpenRouterProvider()
        self.gemini_provider = GeminiProvider()

    async def _execute_model_dispatch(
        self,
        history: List[Dict[str, Any]],
        system_instruction: str,
        image_data: Optional[str] = None,
        model_choice: ModelSelection = ModelSelection.DEFAULT,
    ) -> tuple[str, str]:
        """
        Executes model selection or the 4-stage failover chain:
        Groq -> Mistral AI -> OpenRouter -> Google Gemini
        """
        final_text = ""
        responded_by = ""

        if model_choice == ModelSelection.GROQ:
            resp = await self.groq_provider.generate_response(history, system_instruction, image_data)
            final_text = resp.content or f"Groq Error: {resp.raw_error}"
            responded_by = f"{resp.provider_name} ({resp.model_name})"

        elif model_choice == ModelSelection.MISTRAL:
            resp = await self.mistral_provider.generate_response(history, system_instruction, image_data)
            final_text = resp.content or f"Mistral Error: {resp.raw_error}"
            responded_by = f"{resp.provider_name} ({resp.model_name})"

        elif model_choice == ModelSelection.OPENROUTER:
            resp = await self.openrouter_provider.generate_response(history, system_instruction, image_data)
            final_text = resp.content or f"OpenRouter Error: {resp.raw_error}"
            responded_by = f"{resp.provider_name} ({resp.model_name})"

        elif model_choice == ModelSelection.GEMINI:
            resp = await self.gemini_provider.generate_response(history, system_instruction, image_data)
            final_text = resp.content or f"Gemini Error: {resp.raw_error}"
            responded_by = f"{resp.provider_name} ({resp.model_name})"

        else:
            # ── DEFAULT 4-STAGE FAILOVER CHAIN ──────────────────────────────
            # Groq -> Mistral -> OpenRouter -> Gemini
            providers = [
                self.groq_provider,
                self.mistral_provider,
                self.openrouter_provider,
                self.gemini_provider,
            ]

            for p in providers:
                resp = await p.generate_response(history, system_instruction, image_data)
                if resp.content and not resp.is_quota_error:
                    final_text = resp.content
                    responded_by = f"{resp.provider_name} ({resp.model_name})"
                    break
                elif resp.is_quota_error:
                    # Continue to next in chain
                    continue
                else:
                    # Non-quota error, still attempt next provider
                    continue

            if not final_text:
                final_text = (
                    "⚠️ All AI providers in the Olsson failover chain currently have their free daily rate limits reached. "
                    "Please wait a few moments or try again on tomorrow's daily reset."
                )
                responded_by = "Olsson System"

        return final_text, responded_by

    async def handle_chat(
        self,
        session_id: Optional[str],
        user_message: str,
        image_data: Optional[str] = None,
        model_choice: ModelSelection = ModelSelection.DEFAULT,
        reply_to_id: Optional[str] = None,
    ) -> ChatResponse:
        session = await self.session_service.get_or_create_session(session_id)

        # ── 1. Identity Verification Gatekeeper ────────────────────────────
        if not session.is_verified:
            if verify_identity(user_message):
                await self.session_service.verify_session(session.id)
                session.is_verified = True
                greeting = (
                    "🎉 Identity Verified! Welcome back Fred. It is great to chat with you again. "
                    "How can I assist you with your projects, apps, or anything on your mind today?"
                )
                await self.session_service.append_message(session.id, role="user", content=user_message)
                bot_msg = await self.session_service.append_message(
                    session.id, role="assistant", content=greeting, responded_by="Olsson Security Gatekeeper"
                )
                return ChatResponse(
                    session_id=session.id,
                    message_id=bot_msg.id,
                    content=greeting,
                    responded_by="Olsson Security Gatekeeper",
                    is_verified=True,
                )
            else:
                await self.session_service.append_message(session.id, role="user", content=user_message)
                bot_msg = await self.session_service.append_message(
                    session.id, role="assistant", content=CHALLENGE_MESSAGE, responded_by="Olsson Security Gatekeeper"
                )
                return ChatResponse(
                    session_id=session.id,
                    message_id=bot_msg.id,
                    content=CHALLENGE_MESSAGE,
                    responded_by="Olsson Security Gatekeeper",
                    is_verified=False,
                    verification_prompt=CHALLENGE_MESSAGE,
                )

        # ── 2. Handle WhatsApp-Style Quote Reply ────────────────────────────
        quoted_content = None
        prompt_with_quote = user_message
        if reply_to_id:
            quoted_msg = await self.session_service.get_message_by_id(reply_to_id)
            if quoted_msg:
                quoted_content = quoted_msg.content[:200]
                prompt_with_quote = (
                    f'[Replying specifically to: "{quoted_content}"]\n\n{user_message}'
                )

        # ── 3. Persist User Message ─────────────────────────────────────────
        user_msg = await self.session_service.append_message(
            session.id,
            role="user",
            content=user_message,
            image_url=image_data,
            reply_to_id=reply_to_id,
            reply_to_content=quoted_content,
        )

        # ── 4. Build Complete History from Database ────────────────────────
        all_messages = await self.session_service.get_messages_for_session(session.id)
        raw_history = []
        for m in all_messages:
            if m.responded_by == "Olsson Security Gatekeeper":
                continue
            # If this is the active turn and has a quoted reply, inject the quote context
            if m.reply_to_content and m.content == user_message and m.id == user_msg.id:
                raw_history.append({"role": m.role, "content": prompt_with_quote})
            else:
                raw_history.append({"role": m.role, "content": m.content})

        # ── 5. Token Optimization & Sliding Window ─────────────────────────
        optimized_history, updated_summary = optimize_conversation_history(
            raw_history, persisted_summary=session.context_summary
        )
        if updated_summary != session.context_summary:
            await self.session_service.update_context_summary(session.id, updated_summary)

        system_instruction = build_system_prompt(context_summary=updated_summary)

        # ── 5. Dispatch Model ──────────────────────────────────────────────
        final_text, responded_by = await self._execute_model_dispatch(
            optimized_history, system_instruction, image_data, model_choice
        )

        # ── 6. Persist Assistant Response ──────────────────────────────────
        bot_msg = await self.session_service.append_message(
            session.id, role="assistant", content=final_text, responded_by=responded_by
        )

        return ChatResponse(
            session_id=session.id,
            message_id=bot_msg.id,
            content=final_text,
            responded_by=responded_by,
            is_verified=True,
        )

    async def handle_retry(
        self,
        session_id: str,
        model_choice: ModelSelection = ModelSelection.DEFAULT,
    ) -> ChatResponse:
        """
        Retries the last user message turn in a session with a target model or failover chain.
        """
        session = await self.session_service.get_session_detail(session_id)
        if not session or not session.messages:
            return ChatResponse(
                session_id=session_id,
                message_id="",
                content="No message found to retry in this session.",
                responded_by="Olsson System",
                is_verified=session.is_verified if session else False,
            )

        last_user_msg, _ = await self.session_service.get_last_turn(session_id)
        if not last_user_msg:
            return ChatResponse(
                session_id=session_id,
                message_id="",
                content="No previous user message found to retry.",
                responded_by="Olsson System",
                is_verified=session.is_verified,
            )

        # Build history excluding any last failed assistant message
        raw_history = [
            {"role": m.role, "content": m.content}
            for m in session.messages
            if m.responded_by != "Olsson Security Gatekeeper" and m.role != "assistant" or m.id != session.messages[-1].id
        ]

        optimized_history, updated_summary = optimize_conversation_history(
            raw_history, persisted_summary=session.context_summary
        )
        system_instruction = build_system_prompt(context_summary=updated_summary)

        final_text, responded_by = await self._execute_model_dispatch(
            optimized_history, system_instruction, last_user_msg.image_url, model_choice
        )

        bot_msg = await self.session_service.append_message(
            session.id, role="assistant", content=final_text, responded_by=responded_by
        )

        return ChatResponse(
            session_id=session.id,
            message_id=bot_msg.id,
            content=final_text,
            responded_by=responded_by,
            is_verified=True,
        )
