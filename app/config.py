import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """
    Application Settings loaded from environment variables (.env).
    """
    APP_NAME: str = os.getenv("APP_NAME", "Olsson API")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1")
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./olsson.db")

    # Security
    VERIFICATION_SECRET: str = os.getenv("VERIFICATION_SECRET", "olsson-default-secret-2026")
    
    # Fred Profile Verification Defaults
    FRED_FULL_NAME: str = "Fred Omongole"
    GIRLFRIEND_NAME: str = "Jamirah Najjemba"
    DOB_DAY: int = 16
    DOB_MONTH: int = 8
    DOB_YEAR: int = 2000

    # AI API Keys
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    MISTRAL_API_KEY: str = os.getenv("MISTRAL_API_KEY", "")
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")

    # Models
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    MISTRAL_MODEL: str = os.getenv("MISTRAL_MODEL", "mistral-small-latest")
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "openrouter/free")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

    # Vision Models
    MISTRAL_VISION_MODEL: str = os.getenv("MISTRAL_VISION_MODEL", "mistral-small-latest")
    OPENROUTER_VISION_MODEL: str = os.getenv("OPENROUTER_VISION_MODEL", "openrouter/free")
    GEMINI_VISION_MODEL: str = os.getenv("GEMINI_VISION_MODEL", "gemini-3.6-flash")

    # Token Optimization Settings
    MAX_RECENT_MESSAGES_WINDOW: int = 8     # Keep last 8 turns (16 messages) intact
    MAX_CONTEXT_CHARACTERS: int = 12000      # Soft limit on history size per call
    SUMMARY_TRIGGER_COUNT: int = 16          # Summarize older turns if history > 16 messages
    REQUEST_TIMEOUT_SECONDS: float = 12.0    # Responsive provider failover timeout


settings = Settings()
