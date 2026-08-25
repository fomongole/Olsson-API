import re
from app.config import settings

CHALLENGE_MESSAGE = (
    "🔒 Identity Verification Required: Hello! To ensure it is Fred Omongole chatting with me, "
    "please verify your identity by entering your Date of Birth (e.g., 16/08/2000) or your girlfriend's name."
)

_DOB_PATTERNS = [
    r"16[/\-\.\s]0?8[/\-\.\s]2000",
    r"2000[/\-\.\s]0?8[/\-\.\s]16",
    r"16th?\s+(?:of\s+)?aug(?:ust)?[\s,]+2000",
    r"aug(?:ust)?\s+16(?:th)?[\s,]+2000",
    r"16\s+august",
]

_GIRLFRIEND_PATTERNS = [
    r"\bjamirah\b",
    r"\bnajjemba\b",
    r"\bjamirah\s+najjemba\b",
    r"\bnajjemba\s+jamirah\b",
]


def verify_identity(user_input: str) -> bool:
    """
    Validates if the user's answer satisfies either:
    1. Fred's Date of Birth (16th August 2000)
    2. Girlfriend's name (Jamirah / Najjemba)
    """
    clean = user_input.strip().lower()

    # Check DOB patterns
    for pat in _DOB_PATTERNS:
        if re.search(pat, clean, re.IGNORECASE):
            return True

    # Check Girlfriend patterns
    for pat in _GIRLFRIEND_PATTERNS:
        if re.search(pat, clean, re.IGNORECASE):
            return True

    return False
