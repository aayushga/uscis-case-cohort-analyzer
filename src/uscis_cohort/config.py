"""Configuration loaded exclusively from environment variables."""

from __future__ import annotations

from dataclasses import dataclass
import os


SANDBOX_BASE_URL = "https://api-int.uscis.gov/case-status"
SANDBOX_TOKEN_URL = "https://api-int.uscis.gov/oauth/accesstoken"


@dataclass(frozen=True)
class Settings:
    client_id: str
    client_secret: str
    environment: str = "sandbox"
    base_url: str = SANDBOX_BASE_URL
    token_url: str = SANDBOX_TOKEN_URL
    max_daily_requests: int = 1000
    requests_per_second: float = 5.0
    database_path: str = "data/cases.sqlite3"

    @classmethod
    def from_environment(cls) -> "Settings":
        environment = os.getenv("USCIS_ENVIRONMENT", "sandbox").lower()
        if environment not in {"sandbox", "production"}:
            raise ValueError("USCIS_ENVIRONMENT must be sandbox or production")

        client_id = os.getenv("USCIS_CLIENT_ID", "")
        client_secret = os.getenv("USCIS_CLIENT_SECRET", "")
        if not client_id or not client_secret:
            raise ValueError(
                "USCIS_CLIENT_ID and USCIS_CLIENT_SECRET must be set in the environment"
            )

        base_url = os.getenv("USCIS_BASE_URL", SANDBOX_BASE_URL)
        token_url = os.getenv("USCIS_TOKEN_URL", SANDBOX_TOKEN_URL)
        if environment == "production" and (
            base_url == SANDBOX_BASE_URL or token_url == SANDBOX_TOKEN_URL
        ):
            raise ValueError(
                "Production requires USCIS_BASE_URL and USCIS_TOKEN_URL supplied by USCIS"
            )

        max_daily = int(os.getenv("USCIS_MAX_DAILY_REQUESTS", "1000"))
        rate = float(os.getenv("USCIS_REQUESTS_PER_SECOND", "5"))
        if max_daily < 1 or rate <= 0:
            raise ValueError("Request limits must be positive")
        if environment == "sandbox" and (max_daily > 1000 or rate > 5):
            raise ValueError("Sandbox safety limits cannot exceed 1,000/day or 5/second")

        return cls(
            client_id=client_id,
            client_secret=client_secret,
            environment=environment,
            base_url=base_url.rstrip("/"),
            token_url=token_url,
            max_daily_requests=max_daily,
            requests_per_second=rate,
            database_path=os.getenv("USCIS_DATABASE_PATH", "data/cases.sqlite3"),
        )

