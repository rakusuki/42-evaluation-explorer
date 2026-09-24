from __future__ import annotations

import asyncio
from dataclasses import dataclass
import time
from typing import Any

import httpx

from app.config import Settings, settings


class FortyTwoAPIError(RuntimeError):
    def __init__(self, status_code: int, message: str, body: Any | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.body = body


@dataclass
class TokenState:
    access_token: str
    expires_at: float

    def valid_for(self, seconds: int = 60) -> bool:
        return time.time() + seconds < self.expires_at


class FortyTwoClient:
    def __init__(self, config: Settings = settings) -> None:
        self.config = config
        self._token: TokenState | None = None
        self._token_lock = asyncio.Lock()

    async def _fetch_token(self) -> TokenState:
        if not self.config.credentials_configured:
            raise FortyTwoAPIError(
                500,
                "42 API credentials are not configured. Set FT_CLIENT_ID and FT_CLIENT_SECRET.",
            )

        async with httpx.AsyncClient(timeout=self.config.request_timeout_seconds) as client:
            response = await client.post(
                self.config.ft_token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.config.ft_client_id,
                    "client_secret": self.config.ft_client_secret,
                },
                headers={"Accept": "application/json"},
            )

        data = self._safe_json(response)
        if response.status_code >= 400:
            raise FortyTwoAPIError(
                response.status_code,
                "Failed to obtain a 42 API access token.",
                data,
            )

        access_token = data.get("access_token") if isinstance(data, dict) else None
        if not access_token:
            raise FortyTwoAPIError(502, "42 API token response did not contain access_token.", data)

        expires_in = int(data.get("expires_in", 7200))
        return TokenState(access_token=access_token, expires_at=time.time() + expires_in)

    async def get_token(self) -> str:
        if self._token and self._token.valid_for():
            return self._token.access_token

        async with self._token_lock:
            if self._token and self._token.valid_for():
                return self._token.access_token
            self._token = await self._fetch_token()
            return self._token.access_token

    async def token_info(self) -> dict[str, Any]:
        token = await self.get_token()
        url = "https://api.intra.42.fr/oauth/token/info"
        return await self._request_absolute("GET", url, token=token)

    async def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        if not path.startswith("/"):
            path = "/" + path
        token = await self.get_token()
        return await self._request_absolute(
            "GET",
            f"{self.config.ft_api_base_url}{path}",
            params=params,
            token=token,
        )

    async def paginate(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        max_pages: int = 5,
        page_size: int = 100,
    ) -> list[Any]:
        params = dict(params or {})
        results: list[Any] = []

        for page_number in range(1, max_pages + 1):
            page_params = {
                **params,
                "page[number]": page_number,
                "page[size]": min(page_size, 100),
            }
            data = await self.get(path, page_params)
            if not isinstance(data, list):
                raise FortyTwoAPIError(502, f"Expected list response from {path}.", data)
            results.extend(data)
            if len(data) < min(page_size, 100):
                break

        return results

    async def _request_absolute(
        self,
        method: str,
        url: str,
        *,
        token: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        retries = 0
        while True:
            try:
                async with httpx.AsyncClient(timeout=self.config.request_timeout_seconds) as client:
                    response = await client.request(
                        method,
                        url,
                        params=params,
                        headers={
                            "Authorization": f"Bearer {token}",
                            "Accept": "application/json",
                        },
                    )
            except httpx.RequestError as exc:
                raise FortyTwoAPIError(503, f"Network error while calling 42 API: {exc}") from exc

            data = self._safe_json(response)
            if response.status_code == 429 and retries < 2:
                retry_after = self._parse_retry_after(response.headers.get("Retry-After"))
                await asyncio.sleep(retry_after)
                retries += 1
                continue

            if response.status_code >= 400:
                raise FortyTwoAPIError(
                    response.status_code,
                    self._error_message(response.status_code),
                    data,
                )
            return data

    def _parse_retry_after(self, value: str | None) -> int:
        try:
            seconds = int(value or "1")
        except ValueError:
            seconds = 1
        return max(1, min(seconds, self.config.max_retry_after_seconds))

    @staticmethod
    def _safe_json(response: httpx.Response) -> Any:
        try:
            return response.json()
        except ValueError:
            return {"raw": response.text}

    @staticmethod
    def _error_message(status_code: int) -> str:
        messages = {
            401: "42 API rejected the access token.",
            403: "42 API denied access to this resource. The endpoint may require extra roles or scopes.",
            404: "42 API resource was not found.",
            429: "42 API rate limit was reached.",
        }
        if status_code >= 500:
            return "42 API returned a server error."
        return messages.get(status_code, f"42 API request failed with HTTP {status_code}.")


forty_two_client = FortyTwoClient()
