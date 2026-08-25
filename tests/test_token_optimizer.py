import pytest
from app.core.token_optimizer import optimize_conversation_history


def test_optimize_conversation_history_short():
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi Fred!"},
    ]
    window, summary = optimize_conversation_history(messages, persisted_summary=None, max_turns=8)
    assert len(window) == 2
    assert summary is None


def test_optimize_conversation_history_sliding_window():
    messages = []
    for i in range(20):
        messages.append({"role": "user", "content": f"User message {i}"})
        messages.append({"role": "assistant", "content": f"Assistant response {i}"})

    # max_turns=4 -> max 8 messages in active window
    window, summary = optimize_conversation_history(messages, persisted_summary="Day 1 notes", max_turns=4)
    assert len(window) == 8
    assert summary is not None
    assert "Day 1 notes" in summary
    assert "Earlier Context" in summary
