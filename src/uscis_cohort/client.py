"""Small USCIS API client with token caching, throttling, and safe errors."""

from __future__ import annotations

from dataclasses import dataclass
import json
import time
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .cohort import normalize_receipt
from .config import Settings


@dataclass
class ApiError(RuntimeError):
    status: int
    messages: tuple[str, ...]
    retryable: bool = False

    def __str__(self) -> str:
        return f"USCIS API error ({self.status}): {'; '.join(self.messages)}"


Transport = Callable[[Request, float], tuple[int, dict[str, str], bytes]]


def default_transport(request: Request, timeout: float) -> tuple[int, dict[str, str], bytes]:
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.status, dict(response.headers), response.read()
    except HTTPError as exc:
        return exc.code, dict(exc.headers), exc.read()
    except URLError as exc:
        raise ApiError(0, (f"Network error: {exc.reason}",), retryable=True) from exc


class UscisClient:
    def __init__(
        self,
        settings: Settings,
        *,
        transport: Transport = default_transport,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
        timeout: float = 20.0,
    ) -> None:
        self.settings = settings
        self._transport = transport
        self._clock = clock
        self._sleep = sleep
        self._timeout = timeout
        self._token: str | None = None
        self._token_expires_at = 0.0
        self._last_request_at: float | None = None

    def _json_request(self, request: Request) -> tuple[int, dict[str, str], dict[str, Any]]:
        status, headers, raw = self._transport(request, self._timeout)
        try:
            payload = json.loads(raw.decode("utf-8")) if raw else {}
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ApiError(status, ("USCIS returned a non-JSON response",)) from exc
        return status, headers, payload

    def _access_token(self) -> str:
        now = self._clock()
        if self._token and now < self._token_expires_at:
            return self._token

        body = urlencode(
            {
                "grant_type": "client_credentials",
                "client_id": self.settings.client_id,
                "client_secret": self.settings.client_secret,
            }
        ).encode()
        request = Request(
            self.settings.token_url,
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        status, _, payload = self._json_request(request)
        token = payload.get("access_token")
        if status >= 400 or not isinstance(token, str) or not token:
            raise self._api_error(status, payload)
        expires_in = int(payload.get("expires_in", 1799))
        self._token, self._token_expires_at = token, now + max(0, expires_in - 30)
        return token

    def _throttle(self) -> None:
        if self._last_request_at is not None:
            wait = (1 / self.settings.requests_per_second) - (
                self._clock() - self._last_request_at
            )
            if wait > 0:
                self._sleep(wait)
        self._last_request_at = self._clock()

    def get_case(self, receipt_number: str) -> dict[str, Any]:
        receipt = normalize_receipt(receipt_number)
        self._throttle()
        request = Request(
            f"{self.settings.base_url}/{receipt}",
            headers={
                "Authorization": f"Bearer {self._access_token()}",
                "Accept": "application/json",
                "User-Agent": "uscis-case-cohort-analyzer/0.1",
            },
            method="GET",
        )
        status, _, payload = self._json_request(request)
        if status >= 400:
            raise self._api_error(status, payload)
        if not isinstance(payload.get("case_status"), dict):
            raise ApiError(status, ("Response did not contain case_status",))
        return payload

    @staticmethod
    def _api_error(status: int, payload: dict[str, Any]) -> ApiError:
        messages: list[str] = []
        errors = payload.get("errors", [])
        if isinstance(errors, list):
            for item in errors:
                if isinstance(item, dict) and item.get("message"):
                    messages.append(str(item["message"]))
        if not messages:
            messages.append(str(payload.get("message", "Unknown USCIS API error")))
        return ApiError(status, tuple(messages), retryable=status == 429 or status >= 500)

