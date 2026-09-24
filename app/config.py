from __future__ import annotations

from dataclasses import dataclass
import os

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    ft_client_id: str = os.getenv("FT_CLIENT_ID", "")
    ft_client_secret: str = os.getenv("FT_CLIENT_SECRET", "")
    ft_redirect_uri: str = os.getenv("FT_REDIRECT_URI", "http://localhost:8000/auth/callback")
    ft_api_base_url: str = os.getenv("FT_API_BASE_URL", "https://api.intra.42.fr/v2")
    ft_token_url: str = os.getenv("FT_TOKEN_URL", "https://api.intra.42.fr/oauth/token")
    request_timeout_seconds: float = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "15"))
    max_retry_after_seconds: int = int(os.getenv("MAX_RETRY_AFTER_SECONDS", "10"))

    @property
    def credentials_configured(self) -> bool:
        return bool(self.ft_client_id and self.ft_client_secret)


settings = Settings()
