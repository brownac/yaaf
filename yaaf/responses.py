"""Response helpers for yaaf."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterable, Tuple

from .types import ASGISend


@dataclass
class Response:
    """A minimal HTTP response object for ASGI."""
    body: bytes
    status: int = 200
    headers: list[tuple[bytes, bytes]] | None = None

    @classmethod
    def text(cls, content: str, status: int = 200, headers: Iterable[Tuple[str, str]] | None = None) -> "Response":
        """Create a text/plain response."""
        return cls._with_type(content.encode(), "text/plain; charset=utf-8", status, headers)

    @classmethod
    def json(cls, content: Any, status: int = 200, headers: Iterable[Tuple[str, str]] | None = None) -> "Response":
        """Create an application/json response."""
        payload = json.dumps(content, ensure_ascii=True).encode()
        return cls._with_type(payload, "application/json", status, headers)

    @classmethod
    def _with_type(
        cls,
        body: bytes,
        media_type: str,
        status: int,
        headers: Iterable[Tuple[str, str]] | None,
    ) -> "Response":
        """Create a response and attach content-type + length headers."""
        base_headers = [("content-type", media_type)]
        if headers:
            base_headers.extend(headers)
        encoded = [(k.encode(), v.encode()) for k, v in base_headers]
        encoded.append((b"content-length", str(len(body)).encode()))
        return cls(body=body, status=status, headers=encoded)

    async def send(self, send: ASGISend) -> None:
        """Send the response through an ASGI send callable."""
        await send({"type": "http.response.start", "status": self.status, "headers": self.headers or []})
        await send({"type": "http.response.body", "body": self.body})

    def with_status(self, status: int) -> "Response":
        """Return a new response with a different status code."""
        return Response(body=self.body, status=status, headers=self.headers)


def as_response(value: Any) -> Response:
    """Normalize handler return values into a Response."""
    if isinstance(value, Response):
        return value
    if isinstance(value, bytes):
        return Response._with_type(value, "application/octet-stream", 200, None)
    if isinstance(value, str):
        return Response.text(value)
    if isinstance(value, tuple) and len(value) == 2:
        body, status = value
        return as_response(body).with_status(int(status))
    if isinstance(value, (dict, list)):
        return Response.json(value)
    return Response.text(str(value))
