import os


class Settings:
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")
    CONFIDENCE_THRESHOLD: float = 0.55
    CRITICAL_CONFIDENCE_THRESHOLD: float = 0.70
    MAX_REPLANS: int = 2


settings = Settings()
