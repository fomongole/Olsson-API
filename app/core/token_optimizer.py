from typing import List, Dict, Any, Tuple
from app.config import settings


def optimize_conversation_history(
    messages: List[Dict[str, Any]],
    persisted_summary: str = None,
    max_turns: int = settings.MAX_RECENT_MESSAGES_WINDOW,
    max_chars: int = settings.MAX_CONTEXT_CHARACTERS,
) -> Tuple[List[Dict[str, Any]], str]:
    """
    Optimizes conversation history for token preservation:
    1. Retains the most recent N turns intact (sliding window).
    2. Drops or condenses older messages into a rolling lightweight summary.
    3. Keeps total characters under budget to prevent hitting TPM/TPD rate limits.
    """
    if not messages:
        return [], persisted_summary

    # Each turn is a pair: user message + assistant response (2 messages)
    max_messages = max_turns * 2

    if len(messages) <= max_messages:
        active_window = list(messages)
        updated_summary = persisted_summary
    else:
        # Messages older than the recent window
        older_messages = messages[:-max_messages]
        active_window = list(messages[-max_messages:])

        # Generate rolling summary notes of dropped turns if we don't have one
        summary_snippets = []
        for m in older_messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            if isinstance(content, str) and content.strip():
                snippet = content[:150].replace("\n", " ")
                summary_snippets.append(f"{role}: {snippet}")

        additional_summary = " | ".join(summary_snippets[-6:]) # Keep last few points
        if persisted_summary:
            updated_summary = f"{persisted_summary}\n[Earlier Context]: {additional_summary}"
        else:
            updated_summary = f"[Earlier Context]: {additional_summary}"

    # Character budget trimming
    total_chars = sum(len(str(m.get("content", ""))) for m in active_window)
    while len(active_window) > 2 and total_chars > max_chars:
        removed = active_window.pop(0)
        total_chars -= len(str(removed.get("content", "")))

    return active_window, updated_summary
